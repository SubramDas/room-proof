"""Inspect a Stray Scanner 1.4 export without modifying original files."""

import csv
import hashlib
import math
from pathlib import Path, PurePosixPath
import statistics
import struct
import zipfile
import zlib

from .cli import sha256, utc_now, write_json


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
FORMAT_SOURCE = "https://github.com/strayrobots/scanner/blob/main/docs/format.md"


def png_info(path, decode=False):
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError(f"invalid PNG signature: {path}")
    offset = 8
    width = height = depth = color = None
    compressed = bytearray()
    ended = False
    while offset + 12 <= len(data):
        length = struct.unpack_from(">I", data, offset)[0]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError(f"truncated PNG chunk: {path}")
        tag = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        expected_crc = struct.unpack_from(">I", data, offset + 8 + length)[0]
        if zlib.crc32(tag + payload) & 0xFFFFFFFF != expected_crc:
            raise ValueError(f"PNG CRC mismatch: {path}")
        if tag == b"IHDR":
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if (compression, filtering, interlace) != (0, 0, 0):
                raise ValueError(f"unsupported PNG layout: {path}")
        elif tag == b"IDAT" and decode:
            compressed.extend(payload)
        elif tag == b"IEND":
            ended = True
            break
        offset = end
    if not ended or width is None:
        raise ValueError(f"incomplete PNG: {path}")
    result = {"width": width, "height": height, "bit_depth": depth, "color_type": color}
    if not decode:
        return result
    if color != 0 or depth not in (8, 16):
        raise ValueError(f"expected 8- or 16-bit grayscale PNG: {path}")
    bpp = depth // 8
    row_size = width * bpp
    raw = zlib.decompress(compressed)
    if len(raw) != (row_size + 1) * height:
        raise ValueError(f"unexpected decompressed PNG length: {path}")
    pixels = bytearray()
    prior = bytearray(row_size)
    position = 0
    for _ in range(height):
        filter_kind = raw[position]
        position += 1
        row = bytearray(raw[position:position + row_size])
        position += row_size
        for i in range(row_size):
            left = row[i - bpp] if i >= bpp else 0
            up = prior[i]
            upper_left = prior[i - bpp] if i >= bpp else 0
            if filter_kind == 1:
                prediction = left
            elif filter_kind == 2:
                prediction = up
            elif filter_kind == 3:
                prediction = (left + up) // 2
            elif filter_kind == 4:
                base = left + up - upper_left
                distances = (abs(base - left), abs(base - up), abs(base - upper_left))
                prediction = (left, up, upper_left)[distances.index(min(distances))]
            elif filter_kind == 0:
                prediction = 0
            else:
                raise ValueError(f"invalid PNG filter {filter_kind}: {path}")
            row[i] = (row[i] + prediction) & 255
        pixels.extend(row)
        prior = row
    values = list(pixels) if depth == 8 else [item[0] for item in struct.iter_unpack(">H", pixels)]
    result["pixel_count"] = len(values)
    result["zero_pixels"] = values.count(0)
    result["min"] = min(values)
    result["max"] = max(values)
    result["median_nonzero"] = statistics.median(value for value in values if value > 0) if any(values) else None
    if depth == 8:
        result["value_counts"] = {str(value): values.count(value) for value in sorted(set(values))}
    return result


def csv_rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream, skipinitialspace=True)
        return list(reader)


def time_summary(values):
    differences = [b - a for a, b in zip(values, values[1:])]
    return {
        "first_seconds": values[0] if values else None,
        "last_seconds": values[-1] if values else None,
        "duration_seconds": values[-1] - values[0] if len(values) > 1 else None,
        "median_step_seconds": statistics.median(differences) if differences else None,
        "largest_step_seconds": max(differences) if differences else None,
        "non_increasing_steps": sum(step <= 0 for step in differences),
    }


def compare_archive(scan, archive_path):
    archive_path = Path(archive_path).resolve(strict=True)
    found = set()
    mismatches = []
    matched = 0
    root = None
    with zipfile.ZipFile(archive_path) as archive:
        members = [item for item in archive.infolist() if not item.is_dir()]
        for item in members:
            parts = PurePosixPath(item.filename).parts
            if len(parts) < 2 or ".." in parts or PurePosixPath(item.filename).is_absolute():
                mismatches.append(f"unsafe or unrooted ZIP path: {item.filename}")
                continue
            if root is None:
                root = parts[0]
            if parts[0] != root:
                mismatches.append(f"multiple ZIP roots: {item.filename}")
                continue
            relative = PurePosixPath(*parts[1:]).as_posix()
            found.add(relative)
            extracted = scan / relative
            if not extracted.is_file() or extracted.stat().st_size != item.file_size:
                mismatches.append(f"missing or size mismatch: {relative}")
                continue
            digest = hashlib.sha256()
            with archive.open(item) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != sha256(extracted):
                mismatches.append(f"byte mismatch: {relative}")
            else:
                matched += 1
    extras = sorted(path.relative_to(scan).as_posix() for path in scan.rglob("*") if path.is_file() and path.relative_to(scan).as_posix() not in found)
    mismatches.extend(f"extra extracted file: {path}" for path in extras)
    return {"archive_path": str(archive_path), "archive_sha256": sha256(archive_path),
            "zip_root": root, "zip_file_count": len(members), "matched_file_count": matched,
            "mismatch_count": len(mismatches), "mismatches_first_10": mismatches[:10],
            "status": "byte_identical" if not mismatches else "mismatch"}


def audit_stray(args, run_dir, run):
    import imageio_ffmpeg

    scan = Path(args.scan).resolve(strict=True)
    if not scan.is_dir():
        raise ValueError("scan path must be a directory")
    required = ("camera_matrix.csv", "odometry.csv", "imu.csv", "rgb.mp4")
    missing = [name for name in required if not (scan / name).is_file()]
    if missing:
        raise ValueError(f"missing Stray files: {', '.join(missing)}")
    poses = csv_rows(scan / "odometry.csv")
    imu = csv_rows(scan / "imu.csv")
    if not poses:
        raise ValueError("odometry.csv has no poses")
    pose_ids = [int(row["frame"]) for row in poses]
    depth_paths = sorted((scan / "depth").glob("*.png"))
    confidence_paths = sorted((scan / "confidence").glob("*.png"))
    depth_ids = [int(path.stem) for path in depth_paths]
    confidence_ids = [int(path.stem) for path in confidence_paths]
    warnings = []
    if not depth_paths or not confidence_paths:
        warnings.append("depth or confidence PNG directory is empty")
    if len(pose_ids) != len(set(pose_ids)):
        warnings.append("duplicate pose frame IDs")
    if pose_ids != list(range(len(pose_ids))):
        warnings.append("pose frame IDs are not contiguous from zero")
    if depth_ids != pose_ids:
        warnings.append("depth frame IDs differ from pose IDs")
    if confidence_ids != pose_ids:
        warnings.append("confidence frame IDs differ from pose IDs")
    depth_layouts = set()
    confidence_layouts = set()
    for path in depth_paths:
        info = png_info(path)
        depth_layouts.add((info["width"], info["height"], info["bit_depth"], info["color_type"]))
    for path in confidence_paths:
        info = png_info(path)
        confidence_layouts.add((info["width"], info["height"], info["bit_depth"], info["color_type"]))
    if depth_layouts != {(256, 192, 16, 0)}:
        warnings.append(f"unexpected depth PNG layouts: {sorted(depth_layouts)}")
    if confidence_layouts != {(256, 192, 8, 0)}:
        warnings.append(f"unexpected confidence PNG layouts: {sorted(confidence_layouts)}")
    sample_indices = sorted({0, 1, len(depth_paths) // 2, len(depth_paths) - 2, len(depth_paths) - 1}) if depth_paths else []
    samples = []
    for index in sample_indices:
        if 0 <= index < len(depth_paths) and index < len(confidence_paths):
            depth = png_info(depth_paths[index], decode=True)
            confidence = png_info(confidence_paths[index], decode=True)
            samples.append({"frame_id": depth_paths[index].stem, "depth": depth, "confidence": confidence})
            if any(value not in ("0", "1", "2") for value in confidence.get("value_counts", {})):
                warnings.append(f"unexpected confidence code in frame {depth_paths[index].stem}")
    with (scan / "camera_matrix.csv").open(newline="", encoding="utf-8") as stream:
        matrix_rows = list(csv.reader(stream, skipinitialspace=True))
    matrix = [[float(item) for item in row] for row in matrix_rows]
    if len(matrix) != 3 or any(len(row) != 3 for row in matrix):
        warnings.append("camera_matrix.csv is not 3 x 3")
    pose_times = [float(row["timestamp"]) for row in poses]
    imu_times = [float(row["timestamp"]) for row in imu]
    pose_timing = time_summary(pose_times)
    imu_timing = time_summary(imu_times)
    if pose_timing["non_increasing_steps"] or imu_timing["non_increasing_steps"]:
        warnings.append("non-increasing timestamps detected")
    norms = [math.sqrt(sum(float(row[key]) ** 2 for key in ("qx", "qy", "qz", "qw"))) for row in poses]
    if max(abs(value - 1) for value in norms) > 0.02:
        warnings.append("pose quaternion norm differs from one by more than 0.02")
    positions = [tuple(float(row[key]) for key in ("x", "y", "z")) for row in poses]
    jumps = [math.dist(a, b) for a, b in zip(positions, positions[1:])]
    intrinsics = {key: [float(row[key]) for row in poses] for key in ("fx", "fy", "cx", "cy")}
    if any(not all(math.isfinite(value) and value > 0 for value in intrinsics[key]) for key in ("fx", "fy")):
        warnings.append("invalid per-frame focal length")
    video = {"decoder_package": "imageio-ffmpeg 0.6.0", "ffmpeg_version": imageio_ffmpeg.get_ffmpeg_version()}
    try:
        counted_frames, counted_seconds = imageio_ffmpeg.count_frames_and_secs(str(scan / "rgb.mp4"))
        frames = imageio_ffmpeg.read_frames(str(scan / "rgb.mp4"), pix_fmt="rgb24")
        metadata = next(frames)
        decoded_frames = sum(1 for _ in frames)
        video.update({"codec": metadata.get("codec"), "width": metadata["size"][0], "height": metadata["size"][1],
                      "fps": metadata.get("fps"), "duration_seconds": metadata.get("duration"),
                      "counted_frames": counted_frames, "counted_seconds": counted_seconds, "decoded_frames": decoded_frames})
        if decoded_frames != len(poses):
            warnings.append(f"RGB frames ({decoded_frames}) differ from pose/depth frames ({len(poses)})")
    except Exception as error:
        video["decode_error"] = f"{type(error).__name__}: {error}"
        warnings.append("RGB video could not be fully decoded")
    archive_check = compare_archive(scan, args.archive) if args.archive else None
    if archive_check and archive_check["status"] != "byte_identical":
        warnings.append("extracted scan differs from the original ZIP")
    report = {
        "report_version": "0.1.0", "generated_at_utc": utc_now(), "scan_path": str(scan),
        "app_name": "Stray Scanner", "app_version": args.app_version,
        "device_model": args.device_model, "ios_version": args.ios_version,
        "format_source": FORMAT_SOURCE,
        "counts": {"pose_rows": len(poses), "depth_pngs": len(depth_paths), "confidence_pngs": len(confidence_paths), "imu_rows": len(imu)},
        "frame_ids": {"pose_first": pose_ids[0], "pose_last": pose_ids[-1],
                      "depth_match_pose": depth_ids == pose_ids, "confidence_match_pose": confidence_ids == pose_ids},
        "png_layouts": {"depth": sorted(depth_layouts), "confidence": sorted(confidence_layouts)},
        "sampled_pngs": samples, "camera_matrix": matrix,
        "per_frame_intrinsics": {key: {"first": values[0], "last": values[-1], "minimum": min(values), "maximum": max(values)} for key, values in intrinsics.items()},
        "distortion_rows_with_center": sum(bool(row.get("distortion_center_x", "").strip()) for row in poses),
        "pose_translation_unit": "metres per developer format; no independent scale check",
        "depth_unit": "millimetres per developer format; no independent scale check",
        "pose_rotation_fields": "qx,qy,qz,qw; coordinate handedness and camera-to-world direction not independently verified",
        "pose_timing": pose_timing, "imu_timing": imu_timing,
        "pose_quaternion_norm": {"minimum": min(norms), "maximum": max(norms)},
        "max_interframe_translation_metres": max(jumps) if jumps else None,
        "video": video,
        "original_archive": archive_check,
        "timestamp_alignment": "Pose/depth linked by frame ID; exact RGB-to-pose offset unavailable without per-frame video timestamps",
        "transfer_completeness": "byte_identical_to_archive" if archive_check and archive_check["status"] == "byte_identical" else "unverified_or_mismatch",
        "export_internal_alignment": "needs_attention" if warnings else "counts_consistent",
        "warnings": warnings,
    }
    report_path = Path(args.report).resolve()
    write_json(report_path, report)
    run["warnings"].extend(warnings)
    run["metrics"] = {"pose_rows": len(poses), "depth_pngs": len(depth_paths), "confidence_pngs": len(confidence_paths),
                      "video_frames": video.get("decoded_frames"), "warning_count": len(warnings)}
    run["artifacts"] = [{"path": str(report_path), "sha256": sha256(report_path)}]
    if args.capture_manifest:
        run["data_revision"] = sha256(Path(args.capture_manifest).resolve(strict=True))
    print(f"scan format report: {report_path}")
