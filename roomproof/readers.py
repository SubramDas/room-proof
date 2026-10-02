"""Tier-specific frame readers with explicit links to the unmodified source."""

from pathlib import Path

import imageio_ffmpeg

from .cli import sha256, valid_id, write_json


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".heic", ".heif"}


def read_photo_folders(root, capture_id, run_dir, room_id=None):
    """Index stills by room folder or one explicitly labelled root room."""
    root = Path(root)
    frames = []
    room_dirs = sorted(path for path in root.iterdir() if path.is_dir())
    sources = ([(root, valid_id(room_id, "room"))]
               if not room_dirs and room_id is not None else
               [(path, valid_id(path.name, "room")) for path in room_dirs])
    for room_dir, source_room_id in sources:
        for path in sorted(item for item in room_dir.iterdir() if item.is_file() and item.suffix.lower() in IMAGE_SUFFIXES):
            stream = imageio_ffmpeg.read_frames(str(path), pix_fmt="rgb24")
            header = next(stream, None)
            if header is None or sum(1 for _ in stream) < 1:
                raise ValueError(f"no decoded image frame: {path}")
            source_path = path.relative_to(root).as_posix()
            digest = sha256(path)
            frames.append({
                "frame_id": "frame-" + digest[:16],
                "room_id": source_room_id,
                "width": header["size"][0],
                "height": header["size"][1],
                "pixel_format": "rgb24",
                "source_ref": f"{capture_id}/{source_path}",
                "source_sha256": digest,
                "source_path": source_path,
            })
    index = {
        "index_version": "0.1.0",
        "tier": "photo",
        "capture_id": capture_id,
        "room_ids": [source_room_id for _, source_room_id in sources],
        "adjacency_inferred": False,
        "frame_count": len(frames),
        "frames": frames,
    }
    index_path = run_dir / "frames.json"
    write_json(index_path, index)
    return [{"path": str(index_path), "sha256": sha256(index_path)}]


def read_video_samples(path, capture_id, run_dir, frame_count, fps, max_frames=24,
                       source_size=None):
    """Decode bounded bursts, reserving windows near full-video appearance changes."""
    if frame_count < 1:
        raise ValueError("video has no frames to sample")
    from .visual_geometry import coarse_scene_profile
    profile = coarse_scene_profile(path, frame_count, fps, f'{capture_id}/{Path(path).name}')
    profile_path = run_dir/'coarse_scene_profile.json'
    write_json(profile_path, profile)
    if frame_count <= max_frames or max_frames < 6:
        selected_indices = {i: 0 for i in range(min(max_frames, frame_count))}
    else:
        group_count = min(6, max_frames // 3)
        group_size = max_frames // group_count
        step = 2
        span = (group_size - 1) * step
        selected_indices = {}
        events = sorted(profile['scene_change_candidates'],
                        key=lambda item: -item['appearance_change_score'])[:min(2, group_count-2)]
        regular = group_count-len(events)
        starts = [group * max(0, frame_count - 1 - span) // max(1, regular - 1)
                  for group in range(regular)]
        starts += [max(0, min(frame_count-1-span,
                              event['source_frame_index']-span//2)) for event in events]
        for group, start in enumerate(sorted(starts)):
            for offset in range(group_size):
                selected_indices[min(frame_count - 1, start + offset * step)] = group
    out_dir = run_dir / "frames"
    out_dir.mkdir(parents=True, exist_ok=True)
    stream = imageio_ffmpeg.read_frames(
        str(path), pix_fmt="rgb24", output_params=["-vf", "scale=640:-2", "-vsync", "0"],
    )
    header = next(stream, None)
    if header is None:
        raise ValueError("video has no decoded frame header")
    frames = []
    index = 0
    sampled_height = None
    for rgb in stream:
        if index in selected_indices:
            if len(rgb) % (640 * 3):
                raise ValueError(f"sampled frame {index} has unexpected RGB byte count")
            height = len(rgb) // (640 * 3)
            if sampled_height is not None and height != sampled_height:
                raise ValueError("sampled video frame dimensions changed")
            sampled_height = height
            frame_path = out_dir / f"frame-{index:06d}.rgb"
            frame_path.write_bytes(rgb)
            frames.append({
                "frame_id": f"frame-{index:06d}",
                "source_ref": f"{capture_id}/{Path(path).name}#frame={index}",
                "source_path": Path(path).name,
                "source_frame_index": index,
                "sampling_group": selected_indices[index],
                "timestamp_seconds": round(index / fps, 6),
                "width": 640,
                "height": height,
                "source_width": source_size[0] if source_size else None,
                "source_height": source_size[1] if source_size else None,
                "pixel_format": "rgb24",
                "sampled_path": frame_path.name,
                "sampled_sha256": sha256(frame_path),
            })
        index += 1
    if index != frame_count:
        raise ValueError(f"video frame count changed during sampling: validated {frame_count}, decoded {index}")
    index_value = {
        "index_version": "0.1.0",
        "tier": "video",
        "capture_id": capture_id,
        "source_ref": f"{capture_id}/{Path(path).name}",
        "source_sha256": sha256(path),
        "source_frame_count": frame_count,
        "source_fps": fps,
        "sampling": "up to six short bursts; strongest full-sequence appearance changes reserve up to two interior bursts; source frames two apart",
        "full_sequence_profile_path": profile_path.name,
        "max_frames": max_frames,
        "frame_count": len(frames),
        "frames": frames,
    }
    index_path = run_dir / "frames.json"
    write_json(index_path, index_value)
    return [
        {"path": str(frame_path), "sha256": sha256(frame_path)}
        for frame_path in sorted(out_dir.glob("*.rgb"))
    ] + [{"path": str(index_path), "sha256": sha256(index_path)},
         {"path": str(profile_path), "sha256": sha256(profile_path)}]


def read_stray_scan(root, capture_id, run_dir, rgb_frame_count):
    """Build a lossless-reference index for Stray fields without guessing RGB pairing."""
    import csv

    from .stray_audit import csv_rows, png_info

    root = Path(root)
    pose_rows = csv_rows(root / "odometry.csv")
    imu_rows = csv_rows(root / "imu.csv")
    depth_by_id = {path.stem: path for path in (root / "depth").glob("*.png")}
    confidence_by_id = {path.stem: path for path in (root / "confidence").glob("*.png")}
    camera_rows = []
    with (root / "camera_matrix.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.reader(stream, skipinitialspace=True):
            camera_rows.append([float(value) for value in row])
    frames = []
    for row in pose_rows:
        frame_id = f"{int(row['frame']):06d}"
        depth_path = depth_by_id.get(frame_id)
        confidence_path = confidence_by_id.get(frame_id)
        if depth_path is None or confidence_path is None:
            raise ValueError(f"missing depth/confidence for pose frame {frame_id}")
        depth_info = png_info(depth_path)
        confidence_info = png_info(confidence_path)
        frames.append({
            "frame_id": frame_id,
            "rgb_frame_index": None,
            "rgb_pairing_status": "unresolved",
            "pose": {
                "timestamp_seconds": float(row["timestamp"]),
                "translation_m": [float(row[key]) for key in ("x", "y", "z")],
                "quaternion_xyzw": [float(row[key]) for key in ("qx", "qy", "qz", "qw")],
                "intrinsics_px": {key: float(row[key]) for key in ("fx", "fy", "cx", "cy")},
            },
            "depth": {
                "source_ref": f"{capture_id}/depth/{depth_path.name}",
                "unit": "mm per Stray format documentation; no independent scale validation",
                "width": depth_info["width"],
                "height": depth_info["height"],
                "bit_depth": depth_info["bit_depth"],
            },
            "confidence": {
                "source_ref": f"{capture_id}/confidence/{confidence_path.name}",
                "width": confidence_info["width"],
                "height": confidence_info["height"],
                "bit_depth": confidence_info["bit_depth"],
                "codes_semantics": "raw app codes; not interpreted here",
            },
            "pose_source_ref": f"{capture_id}/odometry.csv#frame={frame_id}",
        })
    imu = [{key: float(value) for key, value in row.items()} for row in imu_rows]
    index = {
        "index_version": "0.1.0",
        "tier": "lidar",
        "capture_id": capture_id,
        "rgb_source_ref": f"{capture_id}/rgb.mp4",
        "rgb_decoded_frame_count": rgb_frame_count,
        "rgb_pairing_status": "unresolved; no offset inferred from count",
        "camera_matrix": camera_rows,
        "camera_matrix_source_ref": f"{capture_id}/camera_matrix.csv",
        "odometry_source_ref": f"{capture_id}/odometry.csv",
        "imu_source_ref": f"{capture_id}/imu.csv",
        "imu_sample_count": len(imu),
        "imu_fields": list(imu_rows[0]) if imu_rows else [],
        "imu_records": imu,
        "depth_unit_basis": "Stray format documentation; physical scale not independently validated",
        "pose_translation_unit": "m per Stray format documentation; physical scale not independently validated",
        "frame_count": len(frames),
        "frames": frames,
    }
    index_path = run_dir / "lidar_frames.json"
    write_json(index_path, index)
    return [{"path": str(index_path), "sha256": sha256(index_path)}]
