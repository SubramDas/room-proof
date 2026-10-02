"""Tier-specific frame readers with explicit links to the unmodified source."""

from pathlib import Path

import imageio_ffmpeg

from .cli import sha256, valid_id, write_json


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".heic", ".heif"}


def read_photo_folders(root, capture_id, run_dir):
    """Index stills independently by room folder; infer no room adjacency."""
    root = Path(root)
    frames = []
    room_dirs = sorted(path for path in root.iterdir() if path.is_dir())
    for room_dir in room_dirs:
        room_id = valid_id(room_dir.name, "room")
        for path in sorted(item for item in room_dir.iterdir() if item.is_file() and item.suffix.lower() in IMAGE_SUFFIXES):
            stream = imageio_ffmpeg.read_frames(str(path), pix_fmt="rgb24")
            header = next(stream, None)
            if header is None or sum(1 for _ in stream) < 1:
                raise ValueError(f"no decoded image frame: {path}")
            source_path = path.relative_to(root).as_posix()
            digest = sha256(path)
            frames.append({
                "frame_id": "frame-" + digest[:16],
                "room_id": room_id,
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
        "room_ids": [valid_id(path.name, "room") for path in room_dirs],
        "adjacency_inferred": False,
        "frame_count": len(frames),
        "frames": frames,
    }
    index_path = run_dir / "frames.json"
    write_json(index_path, index)
    return [{"path": str(index_path), "sha256": sha256(index_path)}]


def read_video_samples(path, capture_id, run_dir, frame_count, fps, max_frames=24):
    """Decode a bounded, even sample to downscaled RGB files with frame refs."""
    selected_count = min(max_frames, frame_count)
    if selected_count < 1:
        raise ValueError("video has no frames to sample")
    if selected_count == 1:
        selected_indices = {0}
    else:
        selected_indices = {index * (frame_count - 1) // (selected_count - 1) for index in range(selected_count)}
    out_dir = run_dir / "frames"
    out_dir.mkdir(parents=True, exist_ok=True)
    stream = imageio_ffmpeg.read_frames(
        str(path), pix_fmt="rgb24", output_params=["-vf", "scale=640:-2"],
    )
    header = next(stream, None)
    if header is None:
        raise ValueError("video has no decoded frame header")
    frames = []
    index = 0
    for rgb in stream:
        if index in selected_indices:
            frame_path = out_dir / f"frame-{index:06d}.rgb"
            frame_path.write_bytes(rgb)
            frames.append({
                "frame_id": f"frame-{index:06d}",
                "source_ref": f"{capture_id}/{Path(path).name}#frame={index}",
                "source_path": Path(path).name,
                "source_frame_index": index,
                "timestamp_seconds": round(index / fps, 6),
                "width": header["size"][0],
                "height": header["size"][1],
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
        "sampling": "evenly spaced from first to last decoded frame; maximum count is configurable",
        "max_frames": max_frames,
        "frame_count": len(frames),
        "frames": frames,
    }
    index_path = run_dir / "frames.json"
    write_json(index_path, index_value)
    return [
        {"path": str(frame_path), "sha256": sha256(frame_path)}
        for frame_path in sorted(out_dir.glob("*.rgb"))
    ] + [{"path": str(index_path), "sha256": sha256(index_path)}]
