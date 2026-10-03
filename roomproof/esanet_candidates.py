"""Optional ESANet RGB-D semantic proposals for registered Stray scan samples."""

from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from .cli import sha256, write_json
from .visual_candidates import _rgb_image, validate_candidate_report


MODEL_ID = "TUI-NICR/ESANet-R34-NBt1D-NYUv2"
SOURCE_REVISION = "820c5bb633e49e69dcd075d4330165bb540a0cc9"
CHECKPOINT_SHA256 = "eb1e5ee8b7c8f46f0d3014ac8684069b8ae6f52ddc24d655ef163be5ef962150"
DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / ".room-proof/models/ESANet"
PREPROCESSING = "esanet-nyuv2-40-rgbd-raw-mm-upright-v1"
# NYUv2 labels with the void label removed, as used by the official checkpoint.
LABELS = {0: "wall", 1: "floor", 7: "door", 8: "window", 21: "ceiling"}


def _upstream(model_root):
    if not (model_root / "src/build_model.py").is_file():
        raise FileNotFoundError("ESANet source tree missing; fetch the pinned upstream source")
    revision = subprocess.run(["git", "-C", str(model_root), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    if revision != SOURCE_REVISION:
        raise ValueError("ESANet source revision differs from the pinned revision")
    os.environ.setdefault("MPLCONFIGDIR", str(model_root / ".matplotlib-cache"))
    if str(model_root) not in sys.path:
        sys.path.insert(0, str(model_root))
    from src.args import ArgumentParserRGBDSegmentation
    from src.build_model import build_model
    from src.preprocessing import get_preprocessor
    return ArgumentParserRGBDSegmentation, build_model, get_preprocessor


def _make_model(model_root, checkpoint):
    import torch

    parser_type, build_model, get_preprocessor = _upstream(model_root)
    parser = parser_type()
    parser.set_common_args()
    args = parser.parse_args(["--dataset", "nyuv2", "--raw_depth", "--no_imagenet_pretraining"])
    with redirect_stdout(io.StringIO()):
        model, device = build_model(args, n_classes=40)
    if device.type != "cpu":
        model.to("cpu")
    weights = torch.load(checkpoint, map_location="cpu", weights_only=True)
    model.load_state_dict(weights["state_dict"], strict=True)
    model.eval()
    preprocessor = get_preprocessor(height=480, width=640,
                                    depth_mean=2841.94941272766,
                                    depth_std=1417.2594281672277,
                                    depth_mode="raw", phase="test")
    return model, preprocessor


def generate_candidates(source, index, run_dir, maximum=24, model_path=None, rotation_degrees=0):
    """Segment only scan RGB samples with supported RGB/depth registration."""
    import cv2
    import numpy as np
    from PIL import Image
    import torch
    import torch.nn.functional as F

    if index["tier"] != "lidar":
        raise ValueError("ESANet needs paired LiDAR RGB and depth; use --tier lidar")
    if rotation_degrees not in (0, 90, 180, 270):
        raise ValueError("ESANet RGB/depth rotation must be 0, 90, 180, or 270 degrees")
    model_root = Path(model_path or DEFAULT_MODEL_PATH).resolve(strict=True)
    checkpoint = model_root / "nyuv2/r34_NBt1D.pth"
    if not checkpoint.is_file() or sha256(checkpoint) != CHECKPOINT_SHA256:
        raise ValueError("ESANet NYUv2 checkpoint missing or SHA-256 mismatch")
    pairing = json.loads((run_dir / "rgb_pairing.json").read_text(encoding="utf-8"))
    selected = [frame for frame in index["frames"]
                if frame["rgb_depth_pairing_status"] == "registered_candidate" and frame["depth_frame_id"]]
    if not pairing["spatial_registration_verified"] or not pairing["frame_offset_supported_by_images"]:
        selected = []
    torch.set_num_threads(min(4, torch.get_num_threads()))
    model, preprocessor = _make_model(model_root, checkpoint) if selected else (None, None)
    mask_dir = run_dir / "candidate_masks"
    mask_dir.mkdir(exist_ok=True)
    candidates, frame_results, artifacts = [], [], []
    k = (rotation_degrees // 90) % 4
    for frame in selected:
        started = time.monotonic()
        image = np.asarray(_rgb_image(source, run_dir, "lidar", frame))
        depth_path = Path(source) / "depth" / f"{frame['depth_frame_id']}.png"
        confidence_path = Path(source) / "confidence" / f"{frame['depth_frame_id']}.png"
        depth = np.asarray(Image.open(depth_path), dtype=np.float32)
        confidence = np.asarray(Image.open(confidence_path), dtype=np.uint8)
        if depth.shape != confidence.shape or depth.shape != (192, 256):
            raise ValueError(f"ESANet depth/confidence layout mismatch: {frame['depth_frame_id']}")
        depth[(confidence < 1) | (depth < 250) | (depth > 6000)] = 0
        if k:
            image = np.ascontiguousarray(np.rot90(image, -k))
            depth = np.ascontiguousarray(np.rot90(depth, -k))
        # Official preprocessing resizes RGB bilinearly and depth with nearest neighbor.
        # The scan is portrait after correction, whereas NYUv2 training is landscape.
        sample = preprocessor({"image": image, "depth": depth})
        with torch.inference_mode():
            logits = model(sample["image"][None], sample["depth"][None])
            logits = F.interpolate(logits, (image.shape[0], image.shape[1]),
                                   mode="bilinear", align_corners=False)[0]
            score, winning = torch.softmax(logits, dim=0).max(dim=0)
        winning = winning.cpu().numpy().astype(np.uint8)
        score = score.cpu().numpy()
        if k:
            winning = np.ascontiguousarray(np.rot90(winning, k))
            score = np.ascontiguousarray(np.rot90(score, k))
        if winning.shape != (frame["height"], frame["width"]):
            raise ValueError("ESANet mask did not map back to sampled RGB pixels")
        mask_path = mask_dir / f"{frame['frame_id']}.png"
        Image.fromarray(winning).save(mask_path)
        artifacts.append({"path": str(mask_path), "sha256": sha256(mask_path)})
        frame_count = 0
        for label, kind in LABELS.items():
            count, component_map, stats, _ = cv2.connectedComponentsWithStats(
                (winning == label).astype(np.uint8), connectivity=8)
            minimum = max(4, round(winning.size * (.002 if kind in ("door", "window") else .02)))
            component_ids = [i for i in range(1, count) if stats[i, cv2.CC_STAT_AREA] >= minimum]
            component_ids.sort(key=lambda i: -stats[i, cv2.CC_STAT_AREA])
            for component_id in component_ids[:5 if kind in ("door", "window") else 2]:
                x, y, width, height, pixels = map(int, stats[component_id])
                box = [x, y, x + width, y + height]
                token = hashlib.sha256(f"{frame['source_ref']}:{label}:{box}".encode()).hexdigest()[:16]
                candidates.append({"candidate_id": f"candidate-{token}", "class": kind,
                                   "label_id": label, "status": "proposed",
                                   "status_reason": "ESANet semantic region; structural geometry unverified",
                                   "frame_id": frame["frame_id"], "room_id": frame.get("room_id"),
                                   "source_ref": frame["source_ref"],
                                   "source_sha256": frame["source_sha256"],
                                   "sampled_sha256": frame.get("sampled_sha256"),
                                   "timestamp_seconds": frame.get("timestamp_seconds"),
                                   "depth_frame_id": frame["depth_frame_id"],
                                   "depth_sha256": sha256(depth_path),
                                   "confidence_sha256": sha256(confidence_path),
                                   "rgb_depth_pairing_status": frame["rgb_depth_pairing_status"],
                                   "geometry": {"type": "box", "xyxy_px": box,
                                                "image_width": frame["width"],
                                                "image_height": frame["height"],
                                                "coordinate_space": "sampled_rgb_frame",
                                                "source_image_width": frame["source_width"],
                                                "source_image_height": frame["source_height"]},
                                   "mask_ref": mask_path.relative_to(run_dir).as_posix(),
                                   "mask_label_id": label, "mask_grid_size": [frame["width"], frame["height"]],
                                   "mask_pixels": pixels,
                                   "raw_model_score": round(float(score[component_map == component_id].mean()), 4),
                                   "supporting_evidence": [frame["source_ref"],
                                                           f"depth/{frame['depth_frame_id']}.png"],
                                   "conflicting_evidence": [],
                                   "capture_id": index["capture_id"], "tier": "lidar",
                                   "model_id": MODEL_ID, "model_sha256": CHECKPOINT_SHA256,
                                   "preprocessing_version": PREPROCESSING})
                frame_count += 1
        frame_results.append({"frame_id": frame["frame_id"], "source_ref": frame["source_ref"],
                              "depth_frame_id": frame["depth_frame_id"],
                              "candidate_count": frame_count,
                              "seconds": round(time.monotonic() - started, 4)})
    report = {"report_version": "0.1.0", "status": "proposals_only",
              "capture_id": index["capture_id"], "tier": "lidar",
              "model": {"id": MODEL_ID, "sha256": CHECKPOINT_SHA256,
                        "path": str(model_root), "source_revision": SOURCE_REVISION,
                        "checkpoint": str(checkpoint), "preprocessing_version": PREPROCESSING,
                        "runtime": "PyTorch CPU", "torch_version": torch.__version__,
                        "input_size": [640, 480], "rotation_clockwise_degrees": rotation_degrees,
                        "labels": LABELS, "depth_units": "millimetres", "confidence_minimum": 1},
              "selection": {"available_frames": len(index["frames"]),
                            "selected_frame_ids": [f["frame_id"] for f in selected],
                            "maximum": maximum,
                            "rule": "registered_candidate sampled RGB/depth pairs only"},
              "frames": frame_results, "candidates": candidates,
              "warnings": ["NYUv2 has no open-passage class; door labels and masks do not establish a structural opening.",
                           "Scan RGB must be rotated into an upright portrait view, then resized to the checkpoint's landscape training size; this domain mismatch may reduce accuracy.",
                           "ESANet scores are uncalibrated semantic scores, not measurement confidence."]}
    if not selected:
        report["warnings"].append("No sampled RGB/depth pairs passed the registration gate; ESANet produced no candidates.")
    validate_candidate_report(report, index)
    path = run_dir / "visual_candidates.json"
    write_json(path, report)
    artifacts.append({"path": str(path), "sha256": sha256(path)})
    return report, artifacts
