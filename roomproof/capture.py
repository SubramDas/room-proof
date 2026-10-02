"""Tier-aware capture input checks used by the one-command pipeline skeleton."""

import hashlib
import json
from pathlib import Path
import time

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
    other_media = [path for path in input_files(root)
                   if (path.suffix.lower() in VIDEO_SUFFIXES and path.parent != root)
                   or (path.suffix.lower() in IMAGE_SUFFIXES and path.parent == root)]
    if other_media:
        errors.append("photo tier accepts stills in room folders only; found video inside a room or root-level still media")
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

        metadata = imageio_ffmpeg.read_frames(str(root), pix_fmt="rgb24", output_params=["-vsync", "0"])
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

        stream = imageio_ffmpeg.read_frames(str(root / "rgb.mp4"), pix_fmt="rgb24", output_params=["-vsync", "0"])
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
    if args.tier == "video" and source.is_dir():
        candidates = sorted(path for path in source.iterdir() if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES)
        if len(candidates) != 1:
            raise ValueError(f"video property folder must contain exactly one top-level clip; found {len(candidates)}")
        if candidates[0].is_symlink():
            raise ValueError("video capture must not be a symlink")
        source = candidates[0]
    from .cli import valid_id
    valid_id(args.property_id, "prop")
    valid_id(args.capture_id, "cap")
    if args.room_id is not None:
        valid_id(args.room_id, "room")
    device_has_lidar = args.device_has_lidar
    inspectors = {"photo": inspect_photo, "video": inspect_video, "lidar": inspect_lidar}
    errors, warnings, metrics = inspectors[args.tier](source, device_has_lidar)
    status = "invalid" if errors else "valid_low_confidence" if warnings else "valid"
    paths = input_files(source) if source.is_dir() else ([source] if source.is_file() else [])
    if args.tier == "photo":
        paths = [path for path in paths if path.parent != source and path.suffix.lower() in IMAGE_SUFFIXES]
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
    if not errors:
        try:
            from .readers import read_photo_folders, read_stray_scan, read_video_samples
            if args.tier == "photo":
                output_artifacts = read_photo_folders(source, args.capture_id, run_dir)
                next_stage = "frames_indexed"
            elif args.tier == "video":
                output_artifacts = read_video_samples(
                    source, args.capture_id, run_dir,
                    metrics["decoded_frames"], metrics["fps"], args.max_video_frames,
                    source_size=(metrics["width"], metrics["height"]),
                )
                next_stage = "frames_indexed"
            else:
                output_artifacts = read_stray_scan(source, args.capture_id, run_dir, metrics["rgb_frames"])
                next_stage = "frames_indexed"
            from .plan import build_plan, render, validate
            index_name = "lidar_frames.json" if args.tier == "lidar" else "frames.json"
            index = json.loads((run_dir / index_name).read_text(encoding="utf-8"))
            if args.tier in ("photo", "video"):
                from .visual_geometry import analyze_photos, analyze_video
                visual, visual_artifacts = (analyze_photos(source, index, run_dir) if args.tier == "photo"
                                            else analyze_video(index, run_dir, source))
                output_artifacts.extend(visual_artifacts)
                warnings.extend(visual["warnings"])
                metrics["visual_frame_count"] = len(visual["frames"])
                if args.tier == "video":
                    metrics["supported_visual_transitions"] = visual["supported_transition_count"]
                    metrics["visual_tracking_gap_count"] = len(visual["tracking_gap_after_sample_indices"])
                else:
                    metrics["supported_photo_pairs"] = sum(pair["overlap_supported"] for pair in visual["pairs"])
            if args.tier == "lidar":
                from .lidar_geometry import extract_geometry
                geometry, geometry_artifacts = extract_geometry(source, index, run_dir, args.max_lidar_frames,
                                                                drift_correction=args.lidar_drift == "on",
                                                                single_room=args.room_id is not None)
                output_artifacts.extend(geometry_artifacts)
                metrics["lidar_point_count"] = geometry["point_count"]
                metrics["lidar_horizontal_candidates"] = geometry["horizontal_candidate_count"]
                metrics["lidar_verified_closure_count"] = geometry["drift_ablation"]["candidate_count"]
                metrics["lidar_drift_area_change_m2"] = geometry["drift_ablation"]["area_change_m2"]
                metrics["lidar_room_fit_status"] = geometry["room_fit"]["status"]
                metrics["lidar_opening_candidate_count"] = len(geometry["room_fit"].get("opening_gap_candidates", []))
                warnings.extend(geometry["warnings"])
            if args.visual_model == "on":
                model_started = time.monotonic()
                if args.tier == "lidar":
                    candidate_report = {
                        "report_version": "0.1.0", "status": "skipped_rgb_pairing_unresolved",
                        "capture_id": args.capture_id, "tier": args.tier, "model": None,
                        "selection": {"available_frames": 0, "selected_frame_ids": [],
                                      "maximum": args.max_model_frames,
                                      "rule": "LiDAR RGB inference requires verified RGB/depth/pose correspondence"},
                        "frames": [], "candidates": [],
                        "warnings": ["Exact Stray RGB/depth pairing is unresolved; RGB candidates cannot be linked to metric walls."],
                    }
                    candidate_path = run_dir / "visual_candidates.json"
                    write_json(candidate_path, candidate_report)
                    output_artifacts.append({"path": str(candidate_path), "sha256": sha256(candidate_path)})
                else:
                    try:
                        from .visual_candidates import generate_candidates
                        candidate_report, candidate_artifacts = generate_candidates(
                            source, index, run_dir, maximum=args.max_model_frames,
                            model_path=args.visual_model_path)
                        output_artifacts.extend(candidate_artifacts)
                        run["model_or_api"] = candidate_report["model"]
                    except Exception as model_error:
                        candidate_report = {
                            "report_version": "0.1.0", "status": "unavailable",
                            "capture_id": args.capture_id, "tier": args.tier, "model": None,
                            "selection": {"available_frames": len(index["frames"]),
                                          "selected_frame_ids": [], "maximum": args.max_model_frames,
                                          "rule": "model stage stopped before candidate output"},
                            "frames": [], "candidates": [],
                            "warnings": [f"Visual model unavailable: {type(model_error).__name__}: {model_error}"],
                        }
                        candidate_path = run_dir / "visual_candidates.json"
                        write_json(candidate_path, candidate_report)
                        output_artifacts.append({"path": str(candidate_path), "sha256": sha256(candidate_path)})
                run["stage_seconds"]["visual_candidates"] = round(time.monotonic() - model_started, 6)
                metrics["visual_model_status"] = candidate_report["status"]
                metrics["visual_candidate_count"] = len(candidate_report["candidates"])
                metrics["visual_model_selected_frame_ids"] = candidate_report["selection"]["selected_frame_ids"]
                warnings.extend(candidate_report["warnings"])
            plan = build_plan(args, run["run_id"], index, warnings,
                              geometry=geometry if args.tier == "lidar" else None,
                              candidates=candidate_report if args.visual_model == "on" else None)
            validation_errors = validate(plan)
            if validation_errors:
                raise ValueError("property plan validation: " + "; ".join(validation_errors[:5]))
            plan_path = run_dir / "property_plan.json"
            svg_path = run_dir / "property_plan.svg"
            write_json(plan_path, plan)
            render(plan, svg_path)
            output_artifacts.extend({"path": str(path), "sha256": sha256(path)} for path in (plan_path, svg_path))
            metrics["schema_valid"] = True
            metrics["semantic_valid"] = True
            next_stage = ("provisional_single_room_layout" if plan["plan"]["status"] == "inferred"
                          else "provisional_depth_points_geometry_unresolved" if args.tier == "lidar"
                          else "visual_evidence_geometry_unresolved")
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
