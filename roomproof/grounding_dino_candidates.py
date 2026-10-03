"""Optional local Grounding DINO Tiny boxes for the visual candidate contract."""

import hashlib
from pathlib import Path
import resource
import time

from .cli import sha256, write_json
from .owlv2_candidates import _source_box
from .visual_candidates import _rgb_image, _selected_frames, validate_candidate_report


MODEL_ID = "IDEA-Research/grounding-dino-tiny"
MODEL_REVISION = "a2bb814dd30d776dcf7e30523b00659f4f141c71"
WEIGHTS_SHA256 = "1a2412ef99bd74bcd3c2a246fa1e48581f8889a1300c9051974741314fc042f3"
DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / ".room-proof/models/grounding-dino-tiny"
PHRASES = {"doorway": "doorway", "door": "door", "open_passage": "open passage",
           "window": "window", "cabinet_door": "cabinet door"}
PROMPT = ". ".join(PHRASES.values()) + "."
PREPROCESSING = "grounding-dino-tiny-processor-local-v1"
BOX_THRESHOLD = .2
TEXT_THRESHOLD = .2


def _model_files(model_dir):
    names = ("config.json", "preprocessor_config.json", "tokenizer.json",
             "tokenizer_config.json", "vocab.txt", "special_tokens_map.json",
             "added_tokens.json", "model.safetensors")
    files = []
    for name in names:
        path = model_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"Grounding DINO model file missing: {path}")
        files.append({"path": name, "sha256": sha256(path), "bytes": path.stat().st_size})
    if next(item for item in files if item["path"] == "model.safetensors")["sha256"] != WEIGHTS_SHA256:
        raise ValueError("Grounding DINO checkpoint SHA-256 mismatch")
    return files


def _kind(label):
    phrase = label.strip().lower().rstrip(".")
    return {value: key for key, value in PHRASES.items()}.get(phrase)


def generate_candidates(source, index, run_dir, maximum=24, model_path=None, rotation_degrees=0):
    if rotation_degrees not in (0, 90, 180, 270):
        raise ValueError("model-view rotation must be 0, 90, 180, or 270 degrees clockwise")
    model_dir = Path(model_path or DEFAULT_MODEL_PATH).resolve(strict=True)
    files = _model_files(model_dir)
    digest = hashlib.sha256("".join(f"{item['path']}:{item['sha256']}\n" for item in files).encode()).hexdigest()
    try:
        import torch
        import transformers
        from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor
    except ImportError as error:
        raise RuntimeError("Grounding DINO needs locally installed torch and transformers") from error

    torch.set_num_threads(min(4, torch.get_num_threads()))
    processor = AutoProcessor.from_pretrained(model_dir, local_files_only=True)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(
        model_dir, local_files_only=True, use_safetensors=True).to("cpu").eval()
    selected = _selected_frames(index, maximum)
    if index["tier"] == "video":
        selected = [{**frame, "source_sha256": index["source_sha256"]} for frame in selected]
    candidates, frame_results = [], []
    for frame in selected:
        started = time.monotonic()
        image = _rgb_image(source, run_dir, index["tier"], frame)
        model_image = image.rotate(-rotation_degrees, expand=True) if rotation_degrees else image
        inputs = processor(images=model_image, text=PROMPT, return_tensors="pt")
        with torch.inference_mode():
            output = model(**inputs)
        found = processor.post_process_grounded_object_detection(
            outputs=output, input_ids=inputs["input_ids"],
            threshold=BOX_THRESHOLD, text_threshold=TEXT_THRESHOLD,
            target_sizes=[(model_image.height, model_image.width)])[0]
        detections = sorted(zip(found["boxes"], found["scores"], found["text_labels"]),
                            key=lambda item: float(item[1]), reverse=True)[:30]
        frame_count = 0
        for box_tensor, score_tensor, label in detections:
            kind = _kind(label)
            if kind is None:
                continue
            model_box = [round(float(value), 2) for value in box_tensor]
            box = _source_box(model_box, image.width, image.height, rotation_degrees)
            box = [max(0., min(float(box[0]), image.width)),
                   max(0., min(float(box[1]), image.height)),
                   max(0., min(float(box[2]), image.width)),
                   max(0., min(float(box[3]), image.height))]
            if box[2] <= box[0] or box[3] <= box[1]:
                continue
            token = hashlib.sha256(f"{MODEL_ID}:{frame['source_ref']}:{kind}:{box}".encode()).hexdigest()[:16]
            candidates.append({"candidate_id": f"candidate-{token}", "class": kind,
                               "label_id": list(PHRASES).index(kind), "prompt": PHRASES[kind],
                               "status": "proposed", "status_reason":
                               "Grounding DINO image box only; geometry and cross-view evidence pending",
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
                        "revision": MODEL_REVISION, "files": files,
                        "runtime": "PyTorch CPU", "torch_version": torch.__version__,
                        "transformers_version": transformers.__version__,
                        "peak_process_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
                        "preprocessing_version": PREPROCESSING,
                        "model_view_rotation_clockwise_degrees": rotation_degrees,
                        "phrase_prompt": PROMPT, "box_threshold": BOX_THRESHOLD,
                        "text_threshold": TEXT_THRESHOLD, "max_boxes_per_frame": 30},
              "selection": {"available_frames": len(index["frames"]),
                            "selected_frame_ids": [frame["frame_id"] for frame in selected],
                            "maximum": maximum,
                            "rule": "all frames under cap; otherwise round-robin photo room or temporal coverage"},
              "frames": frame_results, "candidates": candidates,
              "warnings": ["Grounding DINO box scores are uncalibrated; boxes do not prove structural openings or dimensions."]}
    validate_candidate_report(report, index)
    path = run_dir / "visual_candidates.json"
    write_json(path, report)
    return report, [{"path": str(path), "sha256": sha256(path)}]
