"""Optional local Florence-2 phrase-grounded boxes for the candidate contract."""

import hashlib
import os
from pathlib import Path
import resource
import time

from .cli import sha256, write_json
from .owlv2_candidates import _source_box
from .visual_candidates import _rgb_image, _selected_frames, validate_candidate_report


MODEL_ID = "microsoft/Florence-2-base"
MODEL_REVISION = "5ca5edf5bd017b9919c05d08aebef5e4c7ac3bac"
WEIGHTS_SHA256 = "03075d2d2d2bbd3e180b9ba0afae4aa8563226e2d32911656966e05b2f2ee060"
CODE_SHA256 = {
    "configuration_florence2.py": "de2e45a975b3582de05d2f4d963a3e9f9a3d20dccf78d28e0052932a0be93bdf",
    "modeling_florence2.py": "5162bf465e61b6e29cc113a467630ec3cb56ed8e4d46eb6207157f10fb9b8a24",
    "processing_florence2.py": "f146023a507c009f425a49ee39aa037f4f25c64e14336e3e4f3f1d7377a68e98",
}
DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / ".room-proof/models/florence-2-base"
TASK = "<CAPTION_TO_PHRASE_GROUNDING>"
PHRASES = {"doorway": "doorway", "door": "door", "open_passage": "open passage",
           "window": "window", "cabinet_door": "cabinet door"}
PROMPT = ". ".join(PHRASES.values()) + "."
PREPROCESSING = "florence2-phrase-grounding-fast-processor-eager-no-cache-v1"


def _model_files(model_dir):
    names = ("config.json", "preprocessor_config.json", "tokenizer.json",
             "tokenizer_config.json", "vocab.json", "configuration_florence2.py",
             "modeling_florence2.py", "processing_florence2.py", "model.safetensors")
    files = []
    for name in names:
        path = model_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"Florence-2 model file missing: {path}")
        files.append({"path": name, "sha256": sha256(path), "bytes": path.stat().st_size})
    if next(item for item in files if item["path"] == "model.safetensors")["sha256"] != WEIGHTS_SHA256:
        raise ValueError("Florence-2 checkpoint SHA-256 mismatch")
    for item in files:
        if item["path"] in CODE_SHA256 and item["sha256"] != CODE_SHA256[item["path"]]:
            raise ValueError(f"Florence-2 pinned model code SHA-256 mismatch: {item['path']}")
    return files


def generate_candidates(source, index, run_dir, maximum=24, model_path=None, rotation_degrees=0):
    if rotation_degrees not in (0, 90, 180, 270):
        raise ValueError("model-view rotation must be 0, 90, 180, or 270 degrees clockwise")
    model_dir = Path(model_path or DEFAULT_MODEL_PATH).resolve(strict=True)
    files = _model_files(model_dir)
    digest = hashlib.sha256("".join(f"{item['path']}:{item['sha256']}\n" for item in files).encode()).hexdigest()
    os.environ.setdefault("HF_MODULES_CACHE", str(Path(__file__).resolve().parents[1] /
                                                   ".room-proof/models/hf_modules"))
    try:
        import torch
        import transformers
        import einops
        import timm
        from transformers import AutoModelForCausalLM, AutoProcessor
    except ImportError as error:
        raise RuntimeError("Florence-2 needs torch, transformers, einops, and timm locally installed") from error

    torch.set_num_threads(min(4, torch.get_num_threads()))
    processor = AutoProcessor.from_pretrained(model_dir, local_files_only=True,
                                              trust_remote_code=True, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_dir, local_files_only=True, use_safetensors=True,
        trust_remote_code=True, attn_implementation="eager").to("cpu").eval()
    selected = _selected_frames(index, maximum)
    if index["tier"] == "video":
        selected = [{**frame, "source_sha256": index["source_sha256"]} for frame in selected]
    labels = {phrase: kind for kind, phrase in PHRASES.items()}
    candidates, frame_results = [], []
    for frame in selected:
        started = time.monotonic()
        image = _rgb_image(source, run_dir, index["tier"], frame)
        model_image = image.rotate(-rotation_degrees, expand=True) if rotation_degrees else image
        inputs = processor(text=TASK + PROMPT, images=model_image, return_tensors="pt")
        with torch.inference_mode():
            generated = model.generate(input_ids=inputs["input_ids"],
                                       pixel_values=inputs["pixel_values"],
                                       max_new_tokens=256, num_beams=1,
                                       do_sample=False, use_cache=False)
        decoded = processor.batch_decode(generated, skip_special_tokens=False)[0]
        parsed = processor.post_process_generation(
            decoded, task=TASK, image_size=(model_image.width, model_image.height)).get(TASK, {})
        boxes, phrases = parsed.get("bboxes", []), parsed.get("labels", [])
        if len(boxes) != len(phrases):
            raise ValueError("Florence-2 returned mismatched boxes and labels")
        frame_count = 0
        for model_box, phrase in list(zip(boxes, phrases))[:30]:
            kind = labels.get(phrase.strip().lower())
            if kind is None:
                continue
            model_box = [round(float(value), 2) for value in model_box]
            box = _source_box(model_box, image.width, image.height, rotation_degrees)
            box = [max(0., min(float(box[0]), image.width)),
                   max(0., min(float(box[1]), image.height)),
                   max(0., min(float(box[2]), image.width)),
                   max(0., min(float(box[3]), image.height))]
            if box[2] <= box[0] or box[3] <= box[1]:
                continue
            token = hashlib.sha256(f"{MODEL_ID}:{frame['source_ref']}:{kind}:{box}".encode()).hexdigest()[:16]
            candidates.append({"candidate_id": f"candidate-{token}", "class": kind,
                               "label_id": list(PHRASES).index(kind), "prompt": phrase,
                               "status": "proposed", "status_reason":
                               "Florence-2 grounded phrase box only; geometry and cross-view evidence pending",
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
                               "mask_ref": None, "raw_model_score": 0.0,
                               "model_score_available": False,
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
                        "einops_version": einops.__version__, "timm_version": timm.__version__,
                        "peak_process_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
                        "preprocessing_version": PREPROCESSING,
                        "model_view_rotation_clockwise_degrees": rotation_degrees,
                        "task": TASK, "phrase_prompt": PROMPT,
                        "generation": {"max_new_tokens": 256, "num_beams": 1,
                                       "do_sample": False, "use_cache": False},
                        "score_available": False, "max_boxes_per_frame": 30},
              "selection": {"available_frames": len(index["frames"]),
                            "selected_frame_ids": [frame["frame_id"] for frame in selected],
                            "maximum": maximum,
                            "rule": "all frames under cap; otherwise round-robin photo room or temporal coverage"},
              "frames": frame_results, "candidates": candidates,
              "warnings": ["Florence-2 phrase grounding can return a box for an absent phrase; every box remains an unverified proposal.",
                           "Florence-2 supplies no comparable box score here; raw_model_score=0 is a missing-score sentinel, not a probability."]}
    validate_candidate_report(report, index)
    path = run_dir / "visual_candidates.json"
    write_json(path, report)
    return report, [{"path": str(path), "sha256": sha256(path)}]
