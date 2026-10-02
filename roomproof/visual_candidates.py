"""Local semantic proposals from selected RGB frames.

This stage produces image-space evidence only. Its labels and scores cannot
verify an opening, room connection, physical dimension, or prediction interval.
"""

from collections import deque
import hashlib
from pathlib import Path
import time

import imageio_ffmpeg

from .cli import sha256, write_json


MODEL_ID = "Xenova/segformer-b0-finetuned-ade-512-512/onnx/model_quantized.onnx"
MODEL_SHA256 = "9a98d6daf3d926869ab8cc4c2ed7374a2bc23b889bb7ca3b0915d15e3c4756bb"
DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / ".room-proof/models/segformer-b0-ade-quantized.onnx"
LABELS = {0: "wall", 3: "floor", 5: "ceiling", 8: "window", 14: "door", 58: "door"}
MAX_COMPONENTS = {"wall": 2, "floor": 1, "ceiling": 1, "window": 5, "door": 5}


def _selected_frames(index, maximum):
    """Deterministic round-robin room coverage for photos, temporal coverage for video."""
    frames = index["frames"]
    if len(frames) <= maximum:
        return list(frames)
    if index["tier"] in ("video", "lidar"):
        positions = sorted({i * (len(frames) - 1) // (maximum - 1) for i in range(maximum)}) if maximum > 1 else [0]
        return [frames[i] for i in positions]
    groups = {room_id: [] for room_id in index["room_ids"]}
    for frame in frames:
        groups[frame["room_id"]].append(frame)
    selected = []
    while len(selected) < maximum and any(groups.values()):
        for room_id in index["room_ids"]:
            if groups[room_id] and len(selected) < maximum:
                selected.append(groups[room_id].pop(0))
    return selected


def _rgb_image(source, run_dir, tier, frame):
    from PIL import Image

    if frame.get("sampled_path"):
        rgb = (run_dir / "frames" / frame["sampled_path"]).read_bytes()
        width, height = frame["width"], frame["height"]
    else:
        image_path = source / frame["source_path"]
        stream = imageio_ffmpeg.read_frames(str(image_path), pix_fmt="rgb24", output_params=["-vsync", "0"])
        header = next(stream, None)
        rgb = next(stream, None)
        stream.close()
        if header is None or rgb is None:
            raise ValueError(f"cannot decode model source: {frame['source_ref']}")
        width, height = header["size"]
    if (width, height) != (frame["width"], frame["height"]) or len(rgb) != width * height * 3:
        raise ValueError(f"decoded model frame dimensions disagree with index: {frame['frame_id']}")
    return Image.frombytes("RGB", (width, height), rgb)


def _components(mask, minimum_pixels, maximum):
    """Return the largest 4-connected regions at the model output resolution."""
    import numpy as np

    height, width = mask.shape
    visited = np.zeros((height, width), dtype=np.bool_)
    found = []
    for y in range(height):
        for x in range(width):
            if not mask[y, x] or visited[y, x]:
                continue
            queue = deque([(x, y)])
            visited[y, x] = True
            pixels = []
            while queue:
                px, py = queue.popleft()
                pixels.append((px, py))
                for nx, ny in ((px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)):
                    if 0 <= nx < width and 0 <= ny < height and mask[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        queue.append((nx, ny))
            if len(pixels) >= minimum_pixels:
                found.append(pixels)
    found.sort(key=lambda pixels: (-len(pixels), min(y for _, y in pixels), min(x for x, _ in pixels)))
    return found[:maximum]


def _frame_candidates(segmentation, probability, frame, mask_path):
    import numpy as np

    grid_height, grid_width = segmentation.shape
    source_width, source_height = frame["width"], frame["height"]
    candidates = []
    for label, kind in LABELS.items():
        mask = segmentation == label
        minimum = max(4, round(mask.size * (.002 if kind in ("door", "window") else .02)))
        for pixels in _components(mask, minimum, MAX_COMPONENTS[kind]):
            xs = [point[0] for point in pixels]
            ys = [point[1] for point in pixels]
            box = [round(min(xs) * source_width / grid_width, 1),
                   round(min(ys) * source_height / grid_height, 1),
                   round((max(xs) + 1) * source_width / grid_width, 1),
                   round((max(ys) + 1) * source_height / grid_height, 1)]
            score = float(np.mean(probability[ys, xs]))
            digest = hashlib.sha256(f"{frame['source_ref']}:{label}:{min(xs)}:{min(ys)}:{max(xs)}:{max(ys)}".encode()).hexdigest()[:16]
            candidates.append({"candidate_id": f"candidate-{digest}", "class": kind,
                               "label_id": label, "status": "proposed",
                               "status_reason": "semantic mask proposal; geometry and cross-view evidence pending",
                               "frame_id": frame["frame_id"], "room_id": frame.get("room_id"),
                               "source_ref": frame["source_ref"],
                               "source_sha256": frame["source_sha256"],
                               "sampled_sha256": frame.get("sampled_sha256"),
                               "timestamp_seconds": frame.get("timestamp_seconds"),
                               "depth_frame_id": frame.get("depth_frame_id"),
                               "rgb_depth_pairing_status": frame.get("rgb_depth_pairing_status"),
                               "geometry": {"type": "box", "xyxy_px": box,
                                            "image_width": source_width, "image_height": source_height,
                                            "coordinate_space": "sampled_rgb_frame" if frame.get("sampled_path") else "source_photo",
                                            "source_image_width": frame.get("source_width", source_width),
                                            "source_image_height": frame.get("source_height", source_height)},
                               "mask_ref": mask_path, "mask_label_id": label,
                               "mask_grid_size": [grid_width, grid_height],
                               "mask_pixels": len(pixels),
                               "raw_model_score": round(score, 4),
                               "supporting_evidence": [frame["source_ref"]],
                               "conflicting_evidence": []})
    return candidates


def _session(model_path):
    import onnxruntime as ort

    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    options.inter_op_num_threads = 1
    options.log_severity_level = 3
    return ort.InferenceSession(str(model_path), sess_options=options, providers=["CPUExecutionProvider"])


def validate_candidate_report(report, index):
    """Reject broken references or pixel boxes before publishing proposals."""
    if report.get("report_version") != "0.1.0" or report.get("tier") != index["tier"]:
        raise ValueError("visual candidate report version or tier mismatch")
    frames = {frame["frame_id"]: frame for frame in index["frames"]}
    seen = set()
    for item in report["candidates"]:
        if (item["capture_id"] != index["capture_id"] or item["tier"] != index["tier"] or
                item["model_id"] != report["model"]["id"] or
                item["model_sha256"] != report["model"]["sha256"] or
                item["preprocessing_version"] != report["model"]["preprocessing_version"]):
            raise ValueError(f"visual candidate provenance mismatch: {item['candidate_id']}")
        if item["candidate_id"] in seen:
            raise ValueError(f"duplicate visual candidate ID: {item['candidate_id']}")
        seen.add(item["candidate_id"])
        source = frames.get(item["frame_id"])
        if source is None or item["source_ref"] != source["source_ref"]:
            raise ValueError(f"visual candidate has an invalid frame reference: {item['candidate_id']}")
        if item["class"] not in ("wall", "floor", "ceiling", "door", "window", "doorway", "open_passage", "cabinet_door"):
            raise ValueError(f"unknown visual candidate class: {item['class']}")
        box = item["geometry"]["xyxy_px"]
        width, height = source["width"], source["height"]
        if (item["source_sha256"] != source.get("source_sha256", index.get("source_sha256")) or
                item["geometry"]["image_width"] != source["width"] or
                item["geometry"]["image_height"] != source["height"] or
                item["geometry"]["type"] != "box" or len(box) != 4 or
                not 0 <= box[0] < box[2] <= width or
                not 0 <= box[1] < box[3] <= height):
            raise ValueError(f"visual candidate box is outside its source image: {item['candidate_id']}")
        if item["status"] not in ("proposed", "rejected", "verified"):
            raise ValueError(f"invalid visual candidate status: {item['candidate_id']}")
        if (not item["status_reason"] or not isinstance(item["supporting_evidence"], list) or
                not isinstance(item["conflicting_evidence"], list) or
                not 0 <= item["raw_model_score"] <= 1 or
                (item.get("mask_ref") is not None and
                 (not item["mask_ref"].startswith("candidate_masks/") or
                  ".." in Path(item["mask_ref"]).parts))):
            raise ValueError(f"invalid visual candidate evidence: {item['candidate_id']}")


def generate_candidates(source, index, run_dir, maximum=24, model_path=None):
    """Run a pinned local checkpoint and preserve proposals separately from the plan."""
    import numpy as np
    from PIL import Image
    import onnxruntime as ort

    model_path = Path(model_path or DEFAULT_MODEL_PATH).resolve()
    if not model_path.is_file():
        raise FileNotFoundError(f"visual model weights missing: {model_path}")
    digest = sha256(model_path)
    if digest != MODEL_SHA256:
        raise ValueError(f"visual model checksum mismatch: {model_path}")
    session = _session(model_path)
    inputs = session.get_inputs()
    if len(inputs) != 1 or inputs[0].name != "pixel_values":
        raise ValueError("unexpected visual model input contract")
    selected = _selected_frames(index, maximum)
    if index["tier"] == "video":
        selected = [{**frame, "source_sha256": index["source_sha256"]} for frame in selected]
    mask_dir = run_dir / "candidate_masks"
    mask_dir.mkdir(exist_ok=True)
    candidates, artifacts, frame_results = [], [], []
    mean = np.array([.485, .456, .406], dtype=np.float32)
    std = np.array([.229, .224, .225], dtype=np.float32)
    for frame in selected:
        started = time.monotonic()
        image = _rgb_image(source, run_dir, index["tier"], frame)
        resized = image.resize((512, 512), Image.Resampling.BILINEAR)
        values = np.asarray(resized, dtype=np.float32) / 255.0
        values = np.transpose((values - mean) / std, (2, 0, 1))[None].copy()
        logits = session.run(None, {"pixel_values": values})[0][0]
        if logits.ndim != 3 or logits.shape[0] < 59:
            raise ValueError(f"unexpected visual model output shape: {logits.shape}")
        winning = np.argmax(logits, axis=0).astype(np.uint8)
        shifted = logits - np.max(logits, axis=0, keepdims=True)
        probability = 1.0 / np.sum(np.exp(shifted), axis=0)
        mask_path = mask_dir / f"{frame['frame_id']}.png"
        Image.fromarray(winning).save(mask_path)
        relative_mask = mask_path.relative_to(run_dir).as_posix()
        frame_candidates = _frame_candidates(winning, probability, frame, relative_mask)
        for item in frame_candidates:
            item.update({"capture_id": index["capture_id"], "tier": index["tier"],
                         "model_id": MODEL_ID, "model_sha256": digest,
                         "preprocessing_version": "segformer-rgb-512-imagenet-v1"})
        candidates.extend(frame_candidates)
        artifacts.append({"path": str(mask_path), "sha256": sha256(mask_path)})
        frame_results.append({"frame_id": frame["frame_id"], "source_ref": frame["source_ref"],
                              "candidate_count": len(frame_candidates),
                              "seconds": round(time.monotonic() - started, 4)})
    report = {"report_version": "0.1.0", "status": "proposals_only",
              "capture_id": index["capture_id"], "tier": index["tier"],
              "model": {"id": MODEL_ID, "sha256": digest, "path": str(model_path),
                        "preprocessing_version": "segformer-rgb-512-imagenet-v1",
                        "runtime": "onnxruntime CPU", "runtime_version": ort.__version__,
                        "numpy_version": np.__version__, "input_size": [512, 512],
                        "component_rule": "4-connected; minimum 0.2% image for door/window, 2% for wall/floor/ceiling; max 5 opening and 2 wall components per label",
                        "preprocessing": "bilinear RGB resize; divide by 255; ImageNet mean/std; no crop",
                        "labels": LABELS},
              "selection": {"available_frames": len(index["frames"]),
                            "selected_frame_ids": [frame["frame_id"] for frame in selected],
                            "maximum": maximum,
                            "rule": "all frames under cap; otherwise round-robin per photo room or evenly spaced sampled video frames"},
              "frames": frame_results, "candidates": candidates,
              "warnings": ["Semantic masks are visual proposals; scores are not calibrated probabilities of correct openings or measurement intervals."]}
    validate_candidate_report(report, index)
    path = run_dir / "visual_candidates.json"
    write_json(path, report)
    artifacts.append({"path": str(path), "sha256": sha256(path)})
    return report, artifacts
