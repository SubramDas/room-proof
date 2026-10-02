"""Optional local OWLv2 RGB box proposals; no metric claims or online inference."""

import hashlib
from pathlib import Path
import resource
import time

from .cli import sha256, write_json
from .visual_candidates import _rgb_image, _selected_frames, validate_candidate_report


MODEL_ID = "google/owlv2-base-patch16-ensemble"
MODEL_REVISION = "cfd3195ba4ea9592eec887ded089f4c08eff231d"
WEIGHTS_SHA256 = "e1e130b9e404cf91a75ad45644c1da9d7fa5284085eecc864266a6923efb99e7"
PROMPTS = {
    "doorway": "an interior doorway opening",
    "door": "an interior door",
    "open_passage": "an open passage between rooms",
    "window": "a window in a wall",
    "cabinet_door": "a cabinet door",
}
PREPROCESSING = "owlv2-processor-local-v1"


def _model_files(model_dir):
    files = sorted(path for path in model_dir.rglob("*")
                   if path.is_file() and ".cache" not in path.relative_to(model_dir).parts
                   and path.suffix in (".json", ".txt", ".safetensors"))
    if not files or not any(path.name.endswith(".safetensors") for path in files):
        raise FileNotFoundError(f"OWLv2 local directory needs safetensors weights: {model_dir}")
    return [{"path": path.relative_to(model_dir).as_posix(), "sha256": sha256(path),
             "bytes": path.stat().st_size} for path in files]


def _source_box(box, width, height, rotation):
    """Map a clockwise-rotated model-view box to the original sampled pixels."""
    x1, y1, x2, y2 = box
    if rotation == 90:
        return [y1, height-x2, y2, height-x1]
    if rotation == 180:
        return [width-x2, height-y2, width-x1, height-y1]
    if rotation == 270:
        return [width-y2, x1, width-y1, x2]
    return box


def generate_candidates(source, index, run_dir, maximum=24, model_path=None, rotation_degrees=0):
    if rotation_degrees not in (0, 90, 180, 270):
        raise ValueError("model-view rotation must be 0, 90, 180, or 270 degrees clockwise")
    if model_path is None:
        raise FileNotFoundError("OWLv2 requires --visual-model-path pointing to a local checkpoint directory")
    model_dir = Path(model_path).resolve(strict=True)
    if not model_dir.is_dir():
        raise ValueError("OWLv2 model path must be a directory")
    files = _model_files(model_dir)
    weights = next((item for item in files if item["path"] == "model.safetensors"), None)
    if weights is None or weights["sha256"] != WEIGHTS_SHA256:
        raise ValueError("OWLv2 checkpoint SHA-256 mismatch")
    digest = hashlib.sha256("".join(f"{item['path']}:{item['sha256']}\n" for item in files).encode()).hexdigest()
    try:
        import torch
        import transformers
        from transformers import Owlv2ForObjectDetection, Owlv2Processor
    except ImportError as error:
        raise RuntimeError("OWLv2 needs locally installed torch and transformers packages") from error

    torch.set_num_threads(min(4, torch.get_num_threads()))
    processor = Owlv2Processor.from_pretrained(model_dir, local_files_only=True, use_fast=False)
    model = Owlv2ForObjectDetection.from_pretrained(
        model_dir, local_files_only=True, use_safetensors=True).to("cpu").eval()
    selected = _selected_frames(index, maximum)
    if index["tier"] == "video":
        selected = [{**frame, "source_sha256": index["source_sha256"]} for frame in selected]
    prompts = list(PROMPTS.values())
    classes = list(PROMPTS)
    candidates, frame_results = [], []
    for frame in selected:
        started = time.monotonic()
        image = _rgb_image(source, run_dir, index["tier"], frame)
        model_image = image.rotate(-rotation_degrees, expand=True) if rotation_degrees else image
        inputs = processor(text=[prompts], images=model_image, return_tensors="pt")
        with torch.inference_mode():
            output = model(**inputs)
        found = processor.post_process_grounded_object_detection(
            outputs=output, threshold=.1,
            target_sizes=torch.tensor([(model_image.height, model_image.width)]),
            text_labels=[prompts])[0]
        ranked = sorted(zip(found["boxes"], found["scores"], found["labels"]),
                        key=lambda item: float(item[1]), reverse=True)[:30]
        frame_count = 0
        for box_tensor, score_tensor, label_tensor in ranked:
            label = int(label_tensor)
            if not 0 <= label < len(classes):
                continue
            model_box = [round(float(value), 2) for value in box_tensor]
            box = _source_box(model_box, image.width, image.height, rotation_degrees)
            box = [max(0., min(box[0], image.width)), max(0., min(box[1], image.height)),
                   max(0., min(box[2], image.width)), max(0., min(box[3], image.height))]
            if box[2] <= box[0] or box[3] <= box[1]:
                continue
            token = hashlib.sha256(f"{frame['source_ref']}:{label}:{box}".encode()).hexdigest()[:16]
            candidates.append({"candidate_id": f"candidate-{token}", "class": classes[label],
                               "label_id": label, "prompt": prompts[label], "status": "proposed",
                               "status_reason": "OWLv2 image box only; geometry and cross-view evidence pending",
                               "frame_id": frame["frame_id"], "room_id": frame.get("room_id"),
                               "source_ref": frame["source_ref"], "source_sha256": frame["source_sha256"],
                               "sampled_sha256": frame.get("sampled_sha256"),
                               "timestamp_seconds": frame.get("timestamp_seconds"),
                               "depth_frame_id": frame.get("depth_frame_id"),
                               "rgb_depth_pairing_status": frame.get("rgb_depth_pairing_status"),
                               "geometry": {"type": "box", "xyxy_px": box,
                                            "image_width": frame["width"], "image_height": frame["height"],
                                            "coordinate_space": "sampled_rgb_frame" if frame.get("sampled_path") else "source_photo",
                                            "source_image_width": frame.get("source_width", frame["width"]),
                                            "source_image_height": frame.get("source_height", frame["height"])},
                               "model_view": {"rotation_clockwise_degrees": rotation_degrees,
                                              "xyxy_px": model_box,
                                              "image_width": model_image.width,
                                              "image_height": model_image.height},
                               "mask_ref": None, "raw_model_score": round(float(score_tensor), 4),
                               "supporting_evidence": [frame["source_ref"]], "conflicting_evidence": [],
                               "capture_id": index["capture_id"], "tier": index["tier"],
                               "model_id": MODEL_ID, "model_sha256": digest,
                               "preprocessing_version": PREPROCESSING})
            frame_count += 1
        frame_results.append({"frame_id": frame["frame_id"], "source_ref": frame["source_ref"],
                              "candidate_count": frame_count,
                              "seconds": round(time.monotonic() - started, 4)})
    report = {"report_version": "0.1.0", "status": "proposals_only",
              "capture_id": index["capture_id"], "tier": index["tier"],
              "model": {"id": MODEL_ID, "sha256": digest, "path": str(model_dir),
                        "revision": MODEL_REVISION,
                        "files": files, "runtime": "PyTorch CPU", "torch_version": torch.__version__,
                        "transformers_version": transformers.__version__,
                        "peak_process_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
                        "preprocessing_version": PREPROCESSING,
                        "model_view_rotation_clockwise_degrees": rotation_degrees,
                        "prompts": PROMPTS, "score_threshold": .1, "max_boxes_per_frame": 30},
              "selection": {"available_frames": len(index["frames"]),
                            "selected_frame_ids": [frame["frame_id"] for frame in selected],
                            "maximum": maximum,
                            "rule": "all frames under cap; otherwise round-robin photo room or temporal coverage"},
              "frames": frame_results, "candidates": candidates,
              "warnings": ["OWLv2 box scores are uncalibrated candidate scores; boxes alone do not prove structural openings or dimensions."]}
    validate_candidate_report(report, index)
    path = run_dir / "visual_candidates.json"
    write_json(path, report)
    return report, [{"path": str(path), "sha256": sha256(path)}]
