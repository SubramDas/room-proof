"""Review images for visual proposals. These do not verify openings."""

from collections import defaultdict
from pathlib import Path

from .cli import sha256, write_json
from .visual_candidates import _rgb_image


COLORS = {"open_passage": "#00df32", "doorway": "#ff5a34",
          "door": "#ffa500", "window": "#00e5ff",
          "cabinet_door": "#b064ff", "wall": "#f7e348",
          "floor": "#62b6ff", "ceiling": "#ffffff"}


def render_candidate_overlays(source, index, report, run_dir, rotation_degrees=0):
    """Render one PNG per model-selected frame and index its source reference."""
    from PIL import Image, ImageDraw, ImageFont

    if rotation_degrees not in (0, 90, 180, 270):
        raise ValueError("overlay rotation must be 0, 90, 180, or 270 degrees")
    frames_by_id = {frame["frame_id"]: frame for frame in index["frames"]}
    candidates_by_frame = defaultdict(list)
    for item in report["candidates"]:
        candidates_by_frame[item["frame_id"]].append(item)
    selected = report["selection"]["selected_frame_ids"]
    overlay_dir = run_dir / "candidate_overlays"
    overlay_dir.mkdir(exist_ok=True)
    artifacts, entries = [], []
    for frame_id in selected:
        frame = frames_by_id[frame_id]
        image = _rgb_image(source, run_dir, index["tier"], frame)
        source_width, source_height = image.size
        if rotation_degrees:
            image = image.rotate(-rotation_degrees, expand=True)
        display_width = min(1024, image.width)
        display_height = round(image.height * display_width / image.width)
        image = image.resize((display_width, display_height), Image.Resampling.BILINEAR)
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        items = candidates_by_frame[frame_id]
        display_source_width = source_height if rotation_degrees in (90, 270) else source_width
        display_source_height = source_width if rotation_degrees in (90, 270) else source_height
        sx = image.width / display_source_width
        sy = image.height / display_source_height
        for item in items:
            x1, y1, x2, y2 = item["geometry"]["xyxy_px"]
            if rotation_degrees == 90:
                x1, y1, x2, y2 = source_height-y2, x1, source_height-y1, x2
            elif rotation_degrees == 180:
                x1, y1, x2, y2 = source_width-x2, source_height-y2, source_width-x1, source_height-y1
            elif rotation_degrees == 270:
                x1, y1, x2, y2 = y1, source_width-x2, y2, source_width-x1
            box = (round(x1*sx), round(y1*sy), round(x2*sx), round(y2*sy))
            color = COLORS[item["class"]]
            draw.rectangle(box, outline=color, width=3)
            score = (f" {item['raw_model_score']:.2f}"
                     if item.get("model_score_available", True) else "")
            label = item["class"] + score
            text_x, text_y = max(0, min(box[0], image.width-1)), max(0, box[1]-12)
            text_box = draw.textbbox((text_x, text_y), label, font=font)
            draw.rectangle(text_box, fill="black")
            draw.text((text_x, text_y), label, fill=color, font=font)
        prefix = f"{Path(frame['source_ref']).stem}__" if index["tier"] == "photo" else ""
        path = overlay_dir / f"{prefix}{frame_id}.png"
        image.save(path)
        artifacts.append({"path": str(path), "sha256": sha256(path)})
        entries.append({"frame_id": frame_id, "source_ref": frame["source_ref"],
                        "png": path.relative_to(run_dir).as_posix(),
                        "candidate_count": len(items),
                        "display_size": [image.width, image.height]})
    manifest = {"report_version": "0.1.0", "visual_candidates": "visual_candidates.json",
                "status": "review_only", "model_id": report["model"]["id"],
                "rotation_clockwise_degrees": rotation_degrees,
                "colors": COLORS, "frames": entries,
                "warning": "Boxes are model proposals, not verified openings or measurements."}
    manifest_path = run_dir / "candidate_overlays.json"
    write_json(manifest_path, manifest)
    artifacts.append({"path": str(manifest_path), "sha256": sha256(manifest_path)})
    return manifest, artifacts
