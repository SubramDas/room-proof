"""Bounded RGB proposals for Stray scans with explicit timing uncertainty.

Video PTS can support a candidate depth-frame map, but a common clock origin
and RGB/depth pixel registration still require independent checks. This module
never promotes a timed candidate to a measured opening by itself.
"""

from bisect import bisect_left
from collections import Counter
from pathlib import Path
import re
import statistics
import subprocess

import imageio_ffmpeg

from .cli import sha256, write_json


PTS_PATTERN = re.compile(r"\bn:\s*(\d+)\s+pts:\s*\S+\s+pts_time:([+-]?(?:\d+(?:\.\d*)?|\.\d+))")


def video_presentation_times(path):
    """Read actual decoded presentation timestamps without assuming fixed FPS."""
    result = subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "info",
         "-i", str(path), "-vf", "showinfo", "-an", "-f", "null", "-"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise ValueError(f"RGB timestamp extraction failed: ffmpeg exit {result.returncode}")
    pairs = [(int(number), float(when)) for number, when in PTS_PATTERN.findall(result.stderr)]
    if not pairs or any(number != position for position, (number, _) in enumerate(pairs)):
        raise ValueError("RGB presentation timestamps are absent or out of order")
    times = [when for _, when in pairs]
    if any(right <= left for left, right in zip(times, times[1:])):
        raise ValueError("RGB presentation timestamps are not strictly increasing")
    return times


def timing_alignment(index, presentation_times):
    """Find nearby poses from relative times and expose, rather than hide, origin assumptions."""
    frames = index["frames"]
    pose_times = [frame["pose"]["timestamp_seconds"] for frame in frames]
    rgb_relative = [time - presentation_times[0] for time in presentation_times]
    pose_relative = [time - pose_times[0] for time in pose_times]
    pose_step = statistics.median(b - a for a, b in zip(pose_relative, pose_relative[1:]))
    threshold = min(.008, .45 * pose_step)
    links = []
    used = set()
    for rgb_index, time in enumerate(rgb_relative):
        insertion = bisect_left(pose_relative, time)
        options = [position for position in (insertion - 1, insertion) if 0 <= position < len(frames)]
        closest = min(options, key=lambda position: abs(pose_relative[position] - time))
        residual = time - pose_relative[closest]
        supported = abs(residual) <= threshold and closest not in used
        if supported:
            used.add(closest)
        links.append({"rgb_frame_index": rgb_index, "rgb_pts_seconds": round(presentation_times[rgb_index], 6),
                      "relative_time_seconds": round(time, 6),
                      "depth_frame_id": frames[closest]["frame_id"] if supported else None,
                      "timing_residual_seconds": round(residual, 6),
                      "status": "timing_candidate" if supported else "unpaired"})
    residuals = sorted(abs(item["timing_residual_seconds"]) for item in links if item["status"] == "timing_candidate")
    unmatched = [frame["frame_id"] for frame in frames if frame["frame_id"] not in
                 {item["depth_frame_id"] for item in links if item["depth_frame_id"]}]
    return {"report_version": "0.1.0", "status": "timing_candidates_only",
            "method": "nearest relative RGB PTS to relative pose timestamp; first RGB and first pose assumed same origin",
            "origin_assumption_verified": False, "frame_offset_supported_by_images": False,
            "spatial_registration_verified": False,
            "max_timing_residual_seconds": threshold,
            "rgb_frame_count": len(presentation_times), "depth_pose_frame_count": len(frames),
            "timing_candidate_count": len(residuals), "unpaired_rgb_count": len(links) - len(residuals),
            "unpaired_depth_frame_ids": unmatched,
            "p95_absolute_residual_seconds": residuals[int(.95 * (len(residuals) - 1))] if residuals else None,
            "links": links,
            "warnings": ["Relative PTS agreement is not proof of a shared clock origin or registered RGB/depth pixels."]}


def _spread(items, count):
    if not items or count <= 0:
        return []
    if len(items) <= count:
        return list(items)
    if count == 1:
        return [items[len(items) // 2]]
    return [items[position * (len(items) - 1) // (count - 1)] for position in range(count)]


def _select_rgb_indices(pairing, geometry, maximum):
    """Cover the scan and preferentially inspect frames supporting depth gaps."""
    links_by_depth = {item["depth_frame_id"]: item["rgb_frame_index"] for item in pairing["links"]
                      if item["depth_frame_id"] is not None}
    gap_frames = sorted({links_by_depth[frame_id]
                         for gap in geometry["room_fit"].get("opening_gap_candidates", [])
                         for frame_id in gap["frame_ids"] if frame_id in links_by_depth})
    chosen = set(_spread(gap_frames, min(maximum // 2, len(gap_frames))))
    for frame_index in _spread(list(range(len(pairing["links"]))), maximum):
        if len(chosen) < maximum:
            chosen.add(frame_index)
    if len(chosen) < maximum:
        for frame_index in range(len(pairing["links"])):
            chosen.add(frame_index)
            if len(chosen) >= maximum:
                break
    return sorted(chosen)


def _edge_scores(scan, sample, depth_center_position, frame_ids):
    """Compare RGB image boundaries with nearby measured depth discontinuities."""
    import numpy as np
    from PIL import Image

    rgb = np.frombuffer(sample["path"].read_bytes(), dtype=np.uint8)
    rgb = rgb.reshape(sample["height"], sample["width"], 3)
    gray = np.asarray(Image.fromarray(rgb).convert("L").resize((256, 192)), dtype=np.float32)
    color_edge = np.zeros_like(gray)
    color_edge[:, 1:-1] = np.abs(gray[:, 2:] - gray[:, :-2])
    color_edge[1:-1, :] += np.abs(gray[2:, :] - gray[:-2, :])
    controls = [np.roll(color_edge, (dy, dx), axis=(0, 1))
                for dx, dy in ((32, 0), (-32, 0), (0, 24), (0, -24))]
    scores = {}
    for offset in (-2, -1, 0, 1, 2):
        position = depth_center_position + offset
        if not 0 <= position < len(frame_ids):
            continue
        depth_path = Path(scan) / "depth" / f"{frame_ids[position]}.png"
        if not depth_path.is_file():
            continue
        depth = np.asarray(Image.open(depth_path), dtype=np.float32) / 1000
        if depth.shape != gray.shape:
            continue
        depth_x = np.zeros_like(depth)
        depth_y = np.zeros_like(depth)
        depth_x[:, 1:-1] = np.abs(depth[:, 2:] - depth[:, :-2])
        depth_y[1:-1, :] = np.abs(depth[2:, :] - depth[:-2, :])
        boundary = (depth_x + depth_y > .2) & (depth > .3) & (depth < 6)
        count = int(boundary.sum())
        if count < 100:
            continue
        aligned = float(color_edge[boundary].mean())
        control = statistics.mean(float(shifted[boundary].mean()) for shifted in controls)
        scores[offset] = {"rgb_edge_at_depth_boundary": round(aligned, 3),
                          "shifted_control_edge": round(control, 3),
                          "boundary_pixels": count}
    return scores


def _assess_registration(scan, index, pairing, samples):
    """Infer a stable integer frame offset only with scan-wide image evidence."""
    records = []
    frame_ids = [frame["frame_id"] for frame in index["frames"]]
    frame_positions = {frame_id: position for position, frame_id in enumerate(frame_ids)}
    for sample in samples:
        link = pairing["links"][sample["rgb_frame_index"]]
        if link["depth_frame_id"] is None:
            continue
        scores = _edge_scores(scan, sample, frame_positions[link["depth_frame_id"]], frame_ids)
        if not scores:
            continue
        best = max(scores, key=lambda offset: scores[offset]["rgb_edge_at_depth_boundary"])
        records.append({"rgb_frame_index": sample["rgb_frame_index"],
                        "timing_depth_frame_id": link["depth_frame_id"],
                        "best_depth_offset_frames": best,
                        "scores": {str(offset): value for offset, value in scores.items()}})
    votes = Counter(item["best_depth_offset_frames"] for item in records)
    chosen, count = votes.most_common(1)[0] if votes else (None, 0)
    chosen_scores = [item["scores"][str(chosen)] for item in records
                     if chosen is not None and str(chosen) in item["scores"]]
    contrast = statistics.median(
        item["rgb_edge_at_depth_boundary"] / max(1, item["shifted_control_edge"])
        for item in chosen_scores) if chosen_scores else 0
    third_votes = []
    for third in range(3):
        part = [item for item in records
                if third * len(pairing["links"]) // 3 <= item["rgb_frame_index"] <
                (third + 1) * len(pairing["links"]) // 3]
        third_votes.append(sum(item["best_depth_offset_frames"] == chosen for item in part) / len(part)
                           if part else 0)
    supported = (len(records) >= 9 and count / len(records) >= .7 and
                 min(third_votes) >= .5 and contrast >= 2.0)
    pairing["spatial_registration"] = {
        "status": "supported_sampled_frames" if supported else "unresolved",
        "method": "RGB gradient at measured depth discontinuities versus nearby frame offsets and shifted-pixel controls",
        "sampled_frame_count": len(samples), "usable_frame_count": len(records),
        "best_offset_votes": {str(key): value for key, value in sorted(votes.items())},
        "chosen_depth_offset_frames": chosen if supported else None,
        "chosen_vote_fraction": round(count / len(records), 3) if records else None,
        "third_vote_fractions": [round(value, 3) for value in third_votes],
        "median_rgb_edge_to_shifted_control_ratio": round(contrast, 3),
        "frames": records,
        "warning": "This checks sampled RGB/depth boundary alignment, not independent metric scale or every frame."}
    if not supported:
        return
    pose_times = [frame["pose"]["timestamp_seconds"] for frame in index["frames"]]
    pose_relative = [time - pose_times[0] for time in pose_times]
    clock_offsets = []
    for record in records:
        candidate = pairing["links"][record["rgb_frame_index"]]
        target = frame_positions[candidate["depth_frame_id"]] + chosen
        if 0 <= target < len(pose_relative):
            clock_offsets.append(candidate["relative_time_seconds"] - pose_relative[target])
    clock_offset = statistics.median(clock_offsets)
    sampled_checks = {}
    for record in records:
        aligned = record["scores"].get(str(chosen))
        best_strength = max(value["rgb_edge_at_depth_boundary"] for value in record["scores"].values())
        sampled_checks[record["rgb_frame_index"]] = bool(
            aligned and aligned["rgb_edge_at_depth_boundary"] >= .9 * best_strength and
            aligned["rgb_edge_at_depth_boundary"] >= 2 * max(1, aligned["shifted_control_edge"]))
    # A Stray export may contain one initial depth/pose frame before RGB starts.
    # If frame counts, an image-verified offset, and the entire timestamp
    # sequence agree, index mapping is stronger than nearest-time matching
    # from an assumed shared first-frame origin.
    direct_offset = (chosen is not None and chosen >= 0 and
                     len(index["frames"]) == len(pairing["links"]) + chosen)
    if direct_offset:
        direct_residuals = [link["relative_time_seconds"] - pose_relative[i + chosen]
                            for i, link in enumerate(pairing["links"])]
        direct_clock_offset = statistics.median(direct_residuals)
        direct_offset = all(abs(value - direct_clock_offset) <= pairing["max_timing_residual_seconds"]
                            for value in direct_residuals)
    if direct_offset:
        clock_offset = direct_clock_offset
        for i, link in enumerate(pairing["links"]):
            link["depth_frame_id"] = index["frames"][i + chosen]["frame_id"]
            link["corrected_timing_residual_seconds"] = round(direct_residuals[i] - clock_offset, 6)
            link["status"] = ("registered_candidate" if sampled_checks.get(i)
                              else "timing_offset_candidate")
        pairing["alignment_method"] = "image-verified integer offset plus full-sequence index and timestamp agreement"
    else:
        used = set()
        for link in pairing["links"]:
            if link["depth_frame_id"] is None:
                continue
            target = frame_positions[link["depth_frame_id"]] + chosen
            if not 0 <= target < len(index["frames"]):
                link["status"] = "unpaired"
                link["depth_frame_id"] = None
                continue
            corrected = link["relative_time_seconds"] - pose_relative[target] - clock_offset
            if abs(corrected) > pairing["max_timing_residual_seconds"] or target in used:
                link["status"] = "unpaired"
                link["depth_frame_id"] = None
                continue
            used.add(target)
            link["depth_frame_id"] = index["frames"][target]["frame_id"]
            link["corrected_timing_residual_seconds"] = round(corrected, 6)
            link["status"] = ("registered_candidate" if sampled_checks.get(link["rgb_frame_index"])
                              else "timing_offset_candidate")
        pairing["alignment_method"] = "image-verified offset from bounded nearest-time candidates"
    pairing["frame_offset_supported_by_images"] = True
    pairing["spatial_registration_verified"] = True
    pairing["estimated_rgb_minus_pose_clock_offset_seconds"] = round(clock_offset, 6)
    pairing["status"] = "sampled_rgb_depth_registration_supported"
    pairing["timing_candidate_count"] = sum(item["depth_frame_id"] is not None for item in pairing["links"])
    pairing["registered_sampled_frame_count"] = sum(item["status"] == "registered_candidate" for item in pairing["links"])
    pairing["unpaired_rgb_count"] = len(pairing["links"]) - pairing["timing_candidate_count"]
    pairing["unpaired_depth_frame_ids"] = [frame["frame_id"] for frame in index["frames"]
                                           if frame["frame_id"] not in
                                           {item["depth_frame_id"] for item in pairing["links"]}]
    pairing["warnings"] = [f"A stable {chosen:+d}-frame offset is supported by sampled RGB/depth edges; unsampled frames retain timing-only status.",
                           "This registration check does not calibrate LiDAR scale or verify every model opening."]


def read_lidar_rgb_samples(scan, index, geometry, run_dir, maximum):
    """Decode selected RGB frames and preserve both source and sampled pixels."""
    video = Path(scan) / "rgb.mp4"
    times = video_presentation_times(video)
    if len(times) != index["rgb_decoded_frame_count"]:
        raise ValueError("RGB PTS count differs from the validated decoded frame count")
    pairing = timing_alignment(index, times)
    chosen = _select_rgb_indices(pairing, geometry, min(maximum, len(times)))
    pairing["selected_rgb_frame_indices"] = chosen
    artifacts = []
    stream = imageio_ffmpeg.read_frames(str(video), pix_fmt="rgb24",
                                        output_params=["-vf", "scale=640:-2", "-vsync", "0"])
    header = next(stream, None)
    if header is None:
        raise ValueError("RGB video has no decoded header")
    width, height = header["size"]
    source_stream = imageio_ffmpeg.read_frames(str(video), pix_fmt="rgb24", output_params=["-vsync", "0"])
    source_header = next(source_stream, None)
    source_stream.close()
    if source_header is None:
        raise ValueError("RGB video has no source dimensions")
    source_width, source_height = source_header["size"]
    out_dir = run_dir / "frames"
    out_dir.mkdir(exist_ok=True)
    chosen_set = set(chosen)
    sampled = []
    registration_samples = []
    count = 0
    video_digest = sha256(video)
    for number, rgb in enumerate(stream):
        count += 1
        if number not in chosen_set:
            continue
        if len(rgb) != width * height * 3:
            raise ValueError(f"RGB sample {number} has unexpected size")
        path = out_dir / f"lidar-rgb-{number:06d}.rgb"
        path.write_bytes(rgb)
        link = pairing["links"][number]
        registration_samples.append({"rgb_frame_index": number, "path": path,
                                     "width": width, "height": height})
        sampled.append({"frame_id": f"rgb-{number:06d}",
                        "source_ref": f"{index['capture_id']}/rgb.mp4#frame={number}",
                        "source_path": "rgb.mp4", "source_frame_index": number,
                        "source_sha256": video_digest,
                        "sampled_path": path.name, "sampled_sha256": sha256(path),
                        "width": width, "height": height,
                        "source_width": source_width, "source_height": source_height,
                        "timestamp_seconds": link["rgb_pts_seconds"],
                        "depth_frame_id": link["depth_frame_id"],
                        "rgb_depth_pairing_status": link["status"]})
        artifacts.append({"path": str(path), "sha256": sha256(path)})
    if count != len(times) or len(sampled) != len(chosen):
        raise ValueError("RGB decode count changed after presentation-time inspection")
    _assess_registration(scan, index, pairing, registration_samples)
    for frame in sampled:
        link = pairing["links"][frame["source_frame_index"]]
        frame["depth_frame_id"] = link["depth_frame_id"]
        frame["rgb_depth_pairing_status"] = link["status"]
    pairing_path = run_dir / "rgb_pairing.json"
    write_json(pairing_path, pairing)
    artifacts.append({"path": str(pairing_path), "sha256": sha256(pairing_path)})
    rgb_index = {"index_version": "0.1.0", "tier": "lidar", "capture_id": index["capture_id"],
                 "source_ref": index["rgb_source_ref"], "source_sha256": video_digest,
                 "room_ids": [], "frames": sampled,
                 "selection": "up to half near provisional depth-gap supporting frames; remainder spread across scan"}
    index_path = run_dir / "rgb_frames.json"
    write_json(index_path, rgb_index)
    artifacts.append({"path": str(index_path), "sha256": sha256(index_path)})
    return rgb_index, pairing, artifacts
