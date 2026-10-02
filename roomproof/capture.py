"""Tier-aware capture input checks used by the one-command pipeline skeleton."""

import hashlib
import json
from pathlib import Path

from . import __version__
from .cli import sha256, write_json


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".heic", ".heif"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}


def image_signature(path):
    """Check image container integrity and confirm at least one decoded frame."""
    size = path.stat().st_size
    if size < 12:
        return False
    with path.open("rb") as stream:
        head = stream.read(32)
        stream.seek(max(0, size - 2))
        tail = stream.read(2)
    suffix = path.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        return head.startswith(b"\xff\xd8\xff") and tail == b"\xff\xd9"
    if suffix == ".png":
        if not head.startswith(b"\x89PNG\r\n\x1a\n") or head[12:16] != b"IHDR":
            return False
        from .stray_audit import png_info
        png_info(path)
        return True
    if suffix in (".heic", ".heif"):
        if not (len(head) >= 12 and head[4:8] == b"ftyp" and (b"heic" in head or b"heif" in head or b"mif1" in head)):
            return False
    elif suffix not in (".jpg", ".jpeg", ".png"):
        return False
    import imageio_ffmpeg
    frames = imageio_ffmpeg.read_frames(str(path), pix_fmt="rgb24")
    header = next(frames, None)
    return bool(header and header.get("size") and sum(1 for _ in frames) > 0)


def input_files(root):
    return sorted(path for path in root.rglob("*") if path.is_file())


def inspect_photo(root, device_has_lidar):
    errors, warnings, metrics = [], [], {"room_count": 0, "photo_count": 0}
    if not root.is_dir():
        return ["photo input must be a directory with one subfolder per room"], warnings, metrics
    room_dirs = sorted(path for path in root.iterdir() if path.is_dir())
    if not room_dirs:
        errors.append("photo input has no room subfolders")
    metrics["room_count"] = len(room_dirs)
    hashes = {}
    for room in room_dirs:
        photos = sorted(path for path in room.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)
        metrics["photo_count"] += len(photos)
        if len(photos) < 2 or len(photos) > 8:
            errors.append(f"room '{room.name}' has {len(photos)} photos; expected 2–8")
        for photo in photos:
            try:
                supported = image_signature(photo)
            except Exception:
                supported = False
            if not supported:
                errors.append(f"unsupported or corrupt image file: {photo.relative_to(root).as_posix()}")
                continue
            digest = sha256(photo)
            if digest in hashes:
                errors.append(f"duplicate photo content: {photo.relative_to(root).as_posix()} matches {hashes[digest]}")
            else:
                hashes[digest] = photo.relative_to(root).as_posix()
    other_media = [path for path in input_files(root) if path.suffix.lower() in VIDEO_SUFFIXES or path.suffix.lower() == ".png" and path.parent == root]
    if other_media:
        errors.append("photo tier accepts room-folder still images only; found video or root-level PNG media")
    if device_has_lidar == "false":
        warnings.append("photo tier does not require LiDAR; selected device is marked without LiDAR")
    if metrics["photo_count"]:
        warnings.append("photo-only input cannot guarantee metric scale or room adjacency without visible linking evidence")
    return errors, warnings, metrics


def inspect_video(root, device_has_lidar):
    errors, warnings, metrics = [], [], {"video_count": 0, "decoded_frames": None}
    if not root.is_file():
        return ["video input must be one standalone video file"], warnings, metrics
    if root.suffix.lower() not in VIDEO_SUFFIXES:
        return [f"unsupported video extension: {root.suffix or '(none)'}"], warnings, metrics
    if root.stat().st_size == 0:
        return ["video file is empty"], warnings, metrics
    try:
        import imageio_ffmpeg

        metadata = imageio_ffmpeg.read_frames(str(root), pix_fmt="rgb24")
        header = next(metadata, None)
        if header is None or not header.get("size") or not header.get("fps"):
            errors.append("video has no decodable frame metadata")
        else:
            metrics.update({"width": header["size"][0], "height": header["size"][1], "fps": header["fps"]})
            metrics["decoded_frames"] = sum(1 for _ in metadata)
            metrics["video_count"] = 1
            if metrics["decoded_frames"] == 0:
                errors.append("video contains no decodable frames")
    except Exception as error:
        errors.append(f"video decode failed: {type(error).__name__}: {error}")
    if device_has_lidar == "false":
        warnings.append("ordinary video tier does not require LiDAR; selected device is marked without LiDAR")
    if metrics["decoded_frames"] is not None:
        warnings.append("ordinary video alone does not guarantee metric scale")
    return errors, warnings, metrics


def inspect_lidar(root, device_has_lidar):
    errors, warnings, metrics = [], [], {"pose_count": 0, "depth_count": 0, "confidence_count": 0, "rgb_frames": None}
    if not root.is_dir():
        return ["LiDAR input must be an extracted Stray Scanner folder"], warnings, metrics
    if device_has_lidar == "false":
        errors.append("LiDAR tier is unsupported because the selected device is marked without a LiDAR Scanner")
    required = ("rgb.mp4", "camera_matrix.csv", "odometry.csv", "imu.csv")
    missing = [name for name in required if not (root / name).is_file()]
    for name in missing:
        errors.append(f"missing required Stray file: {name}")
    if not (root / "depth").is_dir():
        errors.append("missing required depth/ directory")
    if not (root / "confidence").is_dir():
        errors.append("missing required confidence/ directory")
    if errors:
        return errors, warnings, metrics
    from .stray_audit import csv_rows

    try:
        poses = csv_rows(root / "odometry.csv")
        metrics["pose_count"] = len(poses)
        if not poses:
            errors.append("odometry.csv has no pose rows")
        elif "frame" not in poses[0]:
            errors.append("odometry.csv is missing the frame ID column")
        depth = sorted((root / "depth").glob("*.png"))
        confidence = sorted((root / "confidence").glob("*.png"))
        metrics["depth_count"], metrics["confidence_count"] = len(depth), len(confidence)
        if not depth:
            errors.append("depth/ contains no PNG samples")
        if not confidence:
            errors.append("confidence/ contains no PNG samples")
        for collection, label in ((depth, "depth"), (confidence, "confidence")):
            ids = [path.stem for path in collection]
            if len(ids) != len(set(ids)):
                errors.append(f"{label}/ contains duplicate frame IDs")
            if any(not path.is_file() or path.stat().st_size == 0 for path in collection):
                errors.append(f"{label}/ contains an empty file")
        pose_ids = [f"{int(row['frame']):06d}" for row in poses] if poses and "frame" in poses[0] else []
        if pose_ids and [path.stem for path in depth] != pose_ids:
            errors.append("depth frame IDs do not match odometry frame IDs")
        if pose_ids and [path.stem for path in confidence] != pose_ids:
            errors.append("confidence frame IDs do not match odometry frame IDs")
        if not depth or not confidence:
            pass
        else:
            from .stray_audit import png_info
            for collection, label, expected in (
                (depth, "depth", (256, 192, 16, 0)),
                (confidence, "confidence", (256, 192, 8, 0)),
            ):
                for path in collection:
                    info = png_info(path)
                    layout = (info["width"], info["height"], info["bit_depth"], info["color_type"])
                    if layout != expected:
                        errors.append(f"unsupported {label} PNG layout {layout}: {path.relative_to(root).as_posix()}")
        import imageio_ffmpeg

        stream = imageio_ffmpeg.read_frames(str(root / "rgb.mp4"), pix_fmt="rgb24")
        header = next(stream, None)
        if header is None:
            errors.append("rgb.mp4 contains no decodable frame")
        else:
            metrics["rgb_frames"] = sum(1 for _ in stream)
            if metrics["rgb_frames"] == 0:
                errors.append("rgb.mp4 contains no decodable frames")
            if metrics["rgb_frames"] != metrics["pose_count"]:
                warnings.append(f"RGB has {metrics['rgb_frames']} frames and LiDAR metadata has {metrics['pose_count']} frames; exact RGB pairing is unresolved")
        if errors:
            warnings.append("a fatal input issue prevents a usable low-confidence result")
    except Exception as error:
        errors.append(f"LiDAR input inspection failed: {type(error).__name__}: {error}")
    return errors, warnings, metrics


def process_capture(args, run_dir, run):
    given_source = Path(args.capture)
    if given_source.is_symlink():
        raise ValueError("capture path must not be a symlink")
    source = given_source.resolve()
    from .cli import valid_id
    valid_id(args.property_id, "prop")
    valid_id(args.capture_id, "cap")
    device_has_lidar = args.device_has_lidar
    inspectors = {"photo": inspect_photo, "video": inspect_video, "lidar": inspect_lidar}
    errors, warnings, metrics = inspectors[args.tier](source, device_has_lidar)
    status = "invalid" if errors else "valid_low_confidence" if warnings else "valid"
    paths = input_files(source) if source.is_dir() else ([source] if source.is_file() else [])
    runs_root = Path(args.runs_dir).resolve()
    paths = [path for path in paths if not (runs_root == source or runs_root in path.parents)]
    source_files = [{
        "path": path.relative_to(source).as_posix() if source.is_dir() else path.name,
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
    } for path in paths]
    source_revision = hashlib.sha256(json.dumps(source_files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    output_artifacts = []
    next_stage = "not_implemented"
    if not errors and args.tier in ("photo", "video"):
        try:
            from .readers import read_photo_folders, read_video_samples
            if args.tier == "photo":
                output_artifacts = read_photo_folders(source, args.capture_id, run_dir)
            else:
                output_artifacts = read_video_samples(
                    source, args.capture_id, run_dir,
                    metrics["decoded_frames"], metrics["fps"], args.max_video_frames,
                )
            next_stage = "frames_indexed"
        except Exception as error:
            errors.append(f"frame reader failed: {type(error).__name__}: {error}")
    status = "invalid" if errors else "valid_low_confidence" if warnings else "valid"
    report = {
        "report_version": "0.1.0",
        "software_version": __version__,
        "run_id": run["run_id"],
        "property_id": args.property_id,
        "capture_id": args.capture_id,
        "tier": args.tier,
        "input_path": str(source),
        "device_model": args.device_model,
        "device_has_lidar": device_has_lidar,
        "validity": status,
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics,
        "source_files": source_files,
        "next_stage": next_stage,
    }
    report_path = run_dir / "quality_report.json"
    write_json(report_path, report)
    run["status"] = "complete" if status != "invalid" else "failed"
    run["warnings"].extend(warnings)
    run["metrics"] = {**metrics, "validity": status, "error_count": len(errors)}
    run["data_revision"] = source_revision
    run["artifacts"] = output_artifacts + [{"path": str(report_path), "sha256": sha256(report_path)}]
    print(f"capture quality: {status}")
    print(f"quality report: {report_path}")
    if errors:
        raise ValueError(f"capture invalid: {errors[0]}")
