"""Associate saved Grounding DINO passage boxes across independent captures.

This stage reuses candidate and learned-match reports. It does not run a model,
and visual correspondence cannot establish a LiDAR width by itself.
"""

from collections import defaultdict
import json
import math
from pathlib import Path
import statistics

from .cli import sha256, write_json


DINO_ID = "IDEA-Research/grounding-dino-tiny"
OPENING_CLASSES = {"doorway", "open_passage"}
MIN_REGION_MATCHES = 8
MIN_PAIR_INLIERS = 24


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _box_in_view(candidate, size, rotation=0):
    """Map a saved candidate box into the linker's displayed image pixels."""
    x0, y0, x1, y1 = candidate["geometry"]["xyxy_px"]
    width = candidate["geometry"]["image_width"]
    height = candidate["geometry"]["image_height"]
    if rotation == 90:
        x0, y0, x1, y1 = height-y1, x0, height-y0, x1
        width, height = height, width
    elif rotation == 180:
        x0, y0, x1, y1 = width-x1, height-y1, width-x0, height-y0
    elif rotation == 270:
        x0, y0, x1, y1 = y0, width-x1, y1, width-x0
        width, height = height, width
    return (x0*size[0]/width, y0*size[1]/height,
            x1*size[0]/width, y1*size[1]/height)


def _inside(point, box):
    return box[0] <= point[0] <= box[2] and box[1] <= point[1] <= box[3]


def _intersection_over_union(first, second):
    left, top = max(first[0], second[0]), max(first[1], second[1])
    right, bottom = min(first[2], second[2]), min(first[3], second[3])
    overlap = max(0, right-left)*max(0, bottom-top)
    first_area = (first[2]-first[0])*(first[3]-first[1])
    second_area = (second[2]-second[0])*(second[3]-second[1])
    return overlap / (first_area+second_area-overlap) if overlap else 0


def _load_dino_candidates(run_dir):
    report_path = run_dir / "visual_candidates.json"
    report = _read(report_path)
    if report.get("model", {}).get("id") != DINO_ID or not report.get("status", "").startswith("proposals"):
        raise ValueError(f"expected a completed Grounding DINO candidate run: {run_dir}")
    return report


def _targeted_depth_edges(scan_source, frame, candidate, boundary, rotation, wall_index):
    """Seek a wall/behind-wall/wall sequence around a matched scan box.

    This is a diagnostic until RGB-to-depth pixels are independently aligned.
    A detector box is used only to choose which depth rows to inspect.
    """
    from PIL import Image

    from .lidar_candidate_links import _wall_hit

    if wall_index is None:
        return {"status": "no_fitted_wall_hit", "row_spans": [], "raw_span_m": None}
    with Image.open(scan_source / "depth" / f"{frame['frame_id']}.png") as image:
        depth = image.copy()
    with Image.open(scan_source / "confidence" / f"{frame['frame_id']}.png") as image:
        confidence = image.copy()
    raw_width = candidate["geometry"]["image_width"]
    raw_height = candidate["geometry"]["image_height"]
    view_size = ((raw_height, raw_width) if rotation in (90, 270)
                 else (raw_width, raw_height))
    box = _box_in_view(candidate, view_size, rotation)
    first_x = max(0, int(box[0] - .10*view_size[0]))
    last_x = min(view_size[0]-1, int(box[2] + .10*view_size[0]))
    row_spans = []
    for fraction in (.35, .5, .65):
        y = int(box[1] + fraction*(box[3]-box[1]))
        samples = []
        for x in range(first_x, last_x+1, 4):
            if rotation == 90:
                u, v = y, raw_height-1-x
            elif rotation == 180:
                u, v = raw_width-1-x, raw_height-1-y
            elif rotation == 270:
                u, v = raw_width-1-y, x
            else:
                u, v = x, y
            pixel = {"geometry": {"xyxy_px": [u, v, u+.01, v+.01],
                                    "image_width": raw_width, "image_height": raw_height,
                                    "source_image_width": candidate["geometry"]["source_image_width"],
                                    "source_image_height": candidate["geometry"]["source_image_height"]}}
            hit = _wall_hit(frame, pixel, boundary)
            if hit is None or hit["wall_index"] != wall_index:
                samples.append((x, "outside_wall", None))
                continue
            du = min(depth.width-1, max(0, int(u*depth.width/raw_width)))
            dv = min(depth.height-1, max(0, int(v*depth.height/raw_height)))
            measured = depth.getpixel((du, dv))/1000
            if confidence.getpixel((du, dv)) < 1 or not .25 <= measured <= 6:
                kind = "missing"
            elif measured > hit["distance_from_camera_m"]+.25:
                kind = "behind_wall"
            elif abs(measured-hit["distance_from_camera_m"]) <= .25:
                kind = "at_wall"
            else:
                kind = "foreground"
            samples.append((x, kind, hit["offset_along_wall_m"]))
        behind = [number for number, (_, kind, _) in enumerate(samples)
                  if kind == "behind_wall"]
        if not behind:
            continue
        first, last = behind[0], behind[-1]
        if sum(samples[number][1] == "behind_wall" for number in range(first, last+1)) < 6:
            continue
        before = [entry for entry in samples[:first] if entry[1] == "at_wall"]
        after = [entry for entry in samples[last+1:] if entry[1] == "at_wall"]
        if len(before) < 3 or len(after) < 3:
            continue
        left, right = before[-1], after[0]
        span = abs(left[2]-right[2])
        row_spans.append({"view_y_px": y, "left_flank_x_px": left[0],
                          "right_flank_x_px": right[0],
                          "left_wall_offset_m": left[2], "right_wall_offset_m": right[2],
                          "raw_span_m": round(span, 3)})
    spans = [item["raw_span_m"] for item in row_spans]
    middle = statistics.median(spans) if spans else None
    agreeing = [value for value in spans if middle is not None and abs(value-middle) <= .2]
    return {"status": ("single_view_depth_edge_hypothesis" if len(agreeing) >= 2
                       else "both_flanks_not_supported"),
            "row_spans": row_spans,
            "raw_span_m": round(statistics.median(agreeing), 3) if len(agreeing) >= 2 else None,
            "warning": "A single timed scan view is not a calibrated repeated-view opening measurement."}


def _provisional_box_height(frame, candidate, boundary, wall_index, floor_y, rotation):
    """Project DINO's displayed top edge to a wall and compare it to the scan floor.

    This deliberately accepts the detector edge as a hypothesis. It is not a
    verified lintel: the RGB/depth pairing and box semantics remain uncertain.
    """
    from .lidar_candidate_links import _wall_hit

    if wall_index is None or floor_y is None:
        return {"status": "no_wall_or_floor", "height_m": None}
    # Stray scan RGB is displayed after a clockwise quarter turn. Its upright
    # vertical axis is the raw image's horizontal axis.
    if rotation == 90:
        top_samples = [_wall_hit(frame, candidate, boundary, 0, fy)
                       for fy in (.25, .5, .75)]
        bottom_samples = [_wall_hit(frame, candidate, boundary, 1, fy)
                          for fy in (.25, .5, .75)]
        left_hit = _wall_hit(frame, candidate, boundary, .5, 1)
        right_hit = _wall_hit(frame, candidate, boundary, .5, 0)
    elif rotation == 270:
        top_samples = [_wall_hit(frame, candidate, boundary, 1, fy)
                       for fy in (.25, .5, .75)]
        bottom_samples = [_wall_hit(frame, candidate, boundary, 0, fy)
                          for fy in (.25, .5, .75)]
        left_hit = _wall_hit(frame, candidate, boundary, .5, 0)
        right_hit = _wall_hit(frame, candidate, boundary, .5, 1)
    elif rotation == 180:
        top_samples = [_wall_hit(frame, candidate, boundary, fx, 1)
                       for fx in (.25, .5, .75)]
        bottom_samples = [_wall_hit(frame, candidate, boundary, fx, 0)
                          for fx in (.25, .5, .75)]
        left_hit = _wall_hit(frame, candidate, boundary, 1, .5)
        right_hit = _wall_hit(frame, candidate, boundary, 0, .5)
    else:
        top_samples = [_wall_hit(frame, candidate, boundary, fx, 0)
                       for fx in (.25, .5, .75)]
        bottom_samples = [_wall_hit(frame, candidate, boundary, fx, 1)
                          for fx in (.25, .5, .75)]
        left_hit = _wall_hit(frame, candidate, boundary, 0, .5)
        right_hit = _wall_hit(frame, candidate, boundary, 1, .5)
    top = [hit["height_world_y_m"] for hit in top_samples
           if hit is not None and hit["wall_index"] == wall_index]
    bottom = [hit["height_world_y_m"] for hit in bottom_samples
              if hit is not None and hit["wall_index"] == wall_index]
    if len(top) < 2:
        return {"status": "top_edge_not_projectable", "height_m": None}
    top_y = statistics.median(top)
    bottom_y = statistics.median(bottom) if len(bottom) >= 2 else None
    side_width = (abs(right_hit["offset_along_wall_m"]-left_hit["offset_along_wall_m"])
                  if left_hit and right_hit and
                  left_hit["wall_index"] == right_hit["wall_index"] == wall_index else None)
    return {"status": "detector_top_to_fitted_floor_hypothesis",
            "height_m": round(top_y-floor_y, 3),
            "provisional_box_side_width_m": round(side_width, 3) if side_width is not None else None,
            "top_edge_world_y_m": round(top_y, 3),
            "fitted_floor_world_y_m": floor_y,
            "box_bottom_world_y_m": round(bottom_y, 3) if bottom_y is not None else None,
            "box_bottom_reaches_floor": (abs(bottom_y-floor_y) <= .15
                                         if bottom_y is not None else None),
            "assumption": "DINO box top and sides are provisional structural edges; the fitted scan floor continues through the passage",
            "warning": "Image-box edges and this timed RGB/depth pose are not independently calibrated."}


def _review_image(passage, candidates, photo_by_id, scan_by_id, photo_run,
                  lidar_run, photo_source, rgb_by_source, rotation, output_dir):
    """Show the matched boxes in one photo and up to two scan views."""
    from PIL import Image, ImageDraw, ImageFont

    from .visual_candidates import _rgb_image

    photo_index = _read(photo_run / "frames.json")
    photo_frame = next(frame for frame in photo_index["frames"]
                       if frame["source_ref"] == passage["photo_source_ref"])
    photo_image = _rgb_image(photo_source, photo_run, "photo", photo_frame)
    photo = photo_by_id[passage["representative_photo_candidate_id"]]
    panels = [(photo_image, photo, "PHOTO " + Path(photo_frame["source_ref"]).name, 0)]
    representative = next(item for item in candidates if
                          item["photo_candidate_id"] == passage["representative_photo_candidate_id"])
    for support in representative["scan_support"][:2]:
        rgb_frame = rgb_by_source[support["scan_source_ref"]]
        image = _rgb_image(photo_source, lidar_run, "lidar", rgb_frame)
        panels.append((image, scan_by_id[support["scan_candidate_id"]],
                       "SCAN " + support["scan_source_ref"].rsplit("=", 1)[-1], rotation))
    panel_width, panel_height, header_height = 480, 640, 28
    canvas = Image.new("RGB", (panel_width*len(panels), panel_height+header_height), "#171717")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for index, (source_image, box_candidate, title, turn) in enumerate(panels):
        image = source_image.rotate(-turn, expand=True) if turn else source_image
        image = image.resize((panel_width, panel_height), Image.Resampling.BILINEAR)
        canvas.paste(image, (index*panel_width, header_height))
        box = _box_in_view(box_candidate, (panel_width, panel_height), turn)
        shifted = (round(box[0]+index*panel_width), round(box[1]+header_height),
                   round(box[2]+index*panel_width), round(box[3]+header_height))
        draw.rectangle(shifted, outline="#00ff50", width=4)
        draw.text((index*panel_width+8, 8), title, fill="white", font=font)
    path = output_dir / f"{passage['passage_id']}.png"
    canvas.save(path)
    return path


def analyze_linked_dino_openings(linked_run, output_dir, photo_name=None):
    """Rank same-passage image evidence, then audit independent metric support."""
    linked_run = Path(linked_run).resolve(strict=True)
    output_dir = Path(output_dir).resolve()
    links = _read(linked_run / "cross_capture_links.json")
    photo_run = Path(links["source_runs"]["photo"]).resolve(strict=True)
    lidar_run = Path(links["source_runs"]["lidar"]).resolve(strict=True)
    photo_report = _load_dino_candidates(photo_run)
    scan_report = _load_dino_candidates(lidar_run)
    photo_boxes = defaultdict(list)
    scan_boxes = defaultdict(list)
    for candidate in photo_report["candidates"]:
        if candidate["class"] in OPENING_CLASSES:
            photo_boxes[candidate["source_ref"]].append(candidate)
    for candidate in scan_report["candidates"]:
        if candidate["class"] in OPENING_CLASSES:
            scan_boxes[candidate["source_ref"]].append(candidate)
    scan_links = _read(lidar_run / "lidar_candidate_links.json")
    scan_link_by_id = {item["candidate_id"]: item for item in scan_links["records"]}
    scan_by_id = {item["candidate_id"]: item for item in scan_report["candidates"]}
    registration = _read(linked_run / "cross_capture_registration.json")
    registered_openings = _read(linked_run / "registered_openings.json")
    geometry = _read(lidar_run / "lidar_geometry.json")
    pairing = _read(lidar_run / "rgb_pairing.json")
    lidar_index = _read(lidar_run / "lidar_frames.json")
    lidar_frames_by_id = {frame["frame_id"]: frame for frame in lidar_index["frames"]}
    rgb_index = _read(lidar_run / "rgb_frames.json")
    rgb_by_source = {frame["source_ref"]: frame for frame in rgb_index["frames"]}
    scan_source = Path(_read(lidar_run / "quality_report.json")["input_path"])
    from .lidar_candidate_links import _candidate_wall_hit, _depth_evidence
    from .lidar_rgb import _edge_scores
    pose_by_depth = {frame["frame_id"]: frame["pose"]["translation_m"]
                     for frame in lidar_index["frames"]}
    frame_ids = [frame["frame_id"] for frame in lidar_index["frames"]]
    frame_positions = {frame_id: position for position, frame_id in enumerate(frame_ids)}
    matched = []
    rotation = links["lidar_rgb_rotation_clockwise_degrees"]
    for pair in links["records"]:
        if (pair["left_tier"] != "photo" or pair["right_tier"] != "scan_rgb" or
                not pair["overlap_supported"] or pair["inliers"] < MIN_PAIR_INLIERS):
            continue
        if photo_name and Path(pair["left_source_ref"]).name != photo_name:
            continue
        points = pair.get("inlier_coordinates", [])
        if not points:
            continue
        best_by_photo = {}
        for photo in photo_boxes.get(pair["left_source_ref"], []):
            left_box = _box_in_view(photo, pair["left_image_size"])
            for scan in scan_boxes.get(pair["right_source_ref"], []):
                right_box = _box_in_view(scan, pair["right_image_size"], rotation)
                shared = sum(_inside(item["left_xy"], left_box) and
                             _inside(item["right_xy"], right_box) for item in points)
                if shared < MIN_REGION_MATCHES:
                    continue
                area_fraction = ((right_box[2]-right_box[0])*(right_box[3]-right_box[1]) /
                                 (pair["right_image_size"][0]*pair["right_image_size"][1]))
                if area_fraction >= .5:
                    continue
                record = {"photo_candidate_id": photo["candidate_id"],
                          "photo_source_ref": photo["source_ref"],
                          "scan_candidate_id": scan["candidate_id"],
                          "scan_source_ref": scan["source_ref"],
                          "photo_class": photo["class"], "scan_class": scan["class"],
                          "matched_feature_count": shared,
                          "pair_inlier_count": pair["inliers"],
                          "scan_box_area_fraction": round(area_fraction, 4),
                          "photo_box_in_link_view": [round(x, 2) for x in left_box],
                          "scan_box_in_link_view": [round(x, 2) for x in right_box]}
                # Keep one scan box per photo box and scan view. Discard boxes
                # covering half the frame, then prefer actual shared matches.
                # A small box over furniture may be more compact but is not
                # necessarily the same structural opening.
                rank = (shared, scan["raw_model_score"], -area_fraction)
                current = best_by_photo.get(photo["candidate_id"])
                if current is None or rank > current[0]:
                    best_by_photo[photo["candidate_id"]] = (rank, record)
        matched.extend(item[1] for item in best_by_photo.values())
    groups = defaultdict(list)
    for item in matched:
        groups[item["photo_candidate_id"]].append(item)
    candidates = []
    photo_by_id = {item["candidate_id"]: item for item in photo_report["candidates"]}
    scan_geometry_cache = {}
    for photo_id, items in groups.items():
        items.sort(key=lambda item: (-item["matched_feature_count"],
                                     item["scan_box_area_fraction"], item["scan_source_ref"]))
        support = []
        positions = []
        for item in items:
            scan_link = scan_link_by_id.get(item["scan_candidate_id"], {})
            frame_number = int(item["scan_source_ref"].rsplit("=", 1)[-1])
            timing = pairing["links"][frame_number]
            depth_id = timing.get("depth_frame_id")
            if depth_id in pose_by_depth:
                positions.append(pose_by_depth[depth_id])
            if item["scan_candidate_id"] not in scan_geometry_cache:
                geometry_evidence = {"status": "no_timed_depth_frame", "nearest_wall": None,
                                     "depth_counts": None, "possible_gap_ids": [],
                                     "local_rgb_depth_probe": None}
                if depth_id in lidar_frames_by_id and geometry["room_fit"].get("boundary_xz_m"):
                    frame = lidar_frames_by_id[depth_id]
                    box = scan_by_id[item["scan_candidate_id"]]
                    boundary = geometry["room_fit"]["boundary_xz_m"]
                    hit = _candidate_wall_hit(frame, box, boundary)
                    counts = (_depth_evidence(scan_source, frame, box, boundary)["counts"]
                              if hit else None)
                    possible_gaps = []
                    if hit:
                        for number, gap in enumerate(geometry["room_fit"].get("opening_gap_candidates", []), 1):
                            left, right = hit["offset_range_m"]
                            if (gap["wall_index"] == hit["wall_index"] and
                                    right >= gap["offset_along_wall_m"]-.1 and
                                    left <= gap["offset_along_wall_m"]+gap["width_m"]+.1):
                                possible_gaps.append(f"opening-gap-{number}")
                    rgb_frame = rgb_by_source.get(item["scan_source_ref"])
                    local_probe = None
                    if rgb_frame:
                        scores = _edge_scores(scan_source, {
                            "path": lidar_run / "frames" / rgb_frame["sampled_path"],
                            "width": rgb_frame["width"], "height": rgb_frame["height"]},
                            frame_positions[depth_id], frame_ids)
                        if scores and 0 in scores:
                            aligned = scores[0]
                            strongest = max(value["rgb_edge_at_depth_boundary"] for value in scores.values())
                            ratio = (aligned["rgb_edge_at_depth_boundary"] /
                                     max(1, aligned["shifted_control_edge"]))
                            local_probe = {"best_neighbor_offset": max(
                                scores, key=lambda offset: scores[offset]["rgb_edge_at_depth_boundary"]),
                                "timing_depth_frame_edge_ratio": round(ratio, 3),
                                "timing_depth_frame_near_best": aligned["rgb_edge_at_depth_boundary"] >= .9*strongest,
                                "meets_sampled_frame_edge_gate": ratio >= 2 and
                                aligned["rgb_edge_at_depth_boundary"] >= .9*strongest}
                    geometry_evidence = {"status": ("registered_scan_pixels" if timing["status"] == "registered_candidate"
                                                    else "timing_only_geometry_hypothesis"),
                                         "nearest_wall": hit,
                                         "depth_counts": counts,
                                         "possible_gap_ids": possible_gaps,
                                         "local_rgb_depth_probe": local_probe,
                                         "provisional_height": _provisional_box_height(
                                             frame, box, boundary, hit["wall_index"] if hit else None,
                                             geometry["room_fit"].get("floor", {}).get("height_m"), rotation),
                                         "targeted_edge_profile": _targeted_depth_edges(
                                             scan_source, frame, box, boundary, rotation,
                                             hit["wall_index"] if hit else None)}
                scan_geometry_cache[item["scan_candidate_id"]] = geometry_evidence
            support.append({**item,
                            "rgb_depth_pairing_status": timing["status"],
                            "timing_depth_frame_id": depth_id,
                            "scan_wall_status": scan_link.get("status", "unavailable"),
                            "scan_wall_reason": scan_link.get("reason"),
                            "matching_depth_gap_ids": scan_link.get("matching_depth_gap_ids", []),
                            "targeted_scan_geometry": scan_geometry_cache[item["scan_candidate_id"]]})
        maximum_separation = max((math.dist(a, b) for a in positions for b in positions), default=0)
        supported_gap_ids = {gap for item in support
                             if item["scan_wall_status"] == "supported_proposal"
                             for gap in item["matching_depth_gap_ids"]}
        metric_opening = next((opening for opening in registered_openings["accepted_openings"]
                               if any(view["candidate_id"] == photo_id
                                      for view in opening["source_views"])), None)
        metric_width = None
        if metric_opening:
            gap_id = metric_opening["lidar_gap_id"]
            gap_number = int(gap_id.removeprefix("opening-gap-"))
            gaps = geometry["room_fit"].get("opening_gap_candidates", [])
            if 1 <= gap_number <= len(gaps):
                metric_width = gaps[gap_number-1]["width_m"]
        status = ("metric_opening_supported" if metric_opening else
                  "visual_passage_correspondence" if len(support) >= 2 and
                  maximum_separation >= .10 else "single_view_visual_hypothesis")
        provisional_heights = [item["targeted_scan_geometry"].get("provisional_height", {}).get("height_m")
                               for item in support]
        provisional_heights = [value for value in provisional_heights if value is not None]
        candidates.append({"photo_candidate_id": photo_id,
                           "photo_source_ref": photo_by_id[photo_id]["source_ref"],
                           "photo_class": photo_by_id[photo_id]["class"],
                           "status": status,
                           "distinct_scan_view_count": len(support),
                           "max_scan_camera_separation_m": round(maximum_separation, 4),
                           "total_region_feature_matches": sum(x["matched_feature_count"] for x in support),
                           "scan_support": support,
                           "supported_depth_gap_ids": sorted(supported_gap_ids),
                           "metric_width_m": metric_width,
                           "provisional_dino_top_to_floor_height_m": (
                               round(statistics.median(provisional_heights), 3)
                               if provisional_heights else None),
                           "metric_reason": (None if metric_opening else
                                             "No accepted calibrated photo pose and repeated scan-supported 3D opening edges")})
    candidates.sort(key=lambda item: (item["status"] != "metric_opening_supported",
                                      item["status"] != "visual_passage_correspondence",
                                      -item["total_region_feature_matches"],
                                      item["photo_candidate_id"]))
    passages = []
    assigned = set()
    for candidate in candidates:
        first_id = candidate["photo_candidate_id"]
        if first_id in assigned:
            continue
        cluster = [candidate]
        assigned.add(first_id)
        changed = True
        while changed:
            changed = False
            for other in candidates:
                other_id = other["photo_candidate_id"]
                if other_id in assigned or other["photo_source_ref"] != candidate["photo_source_ref"]:
                    continue
                if any(_intersection_over_union(
                        photo_by_id[other_id]["geometry"]["xyxy_px"],
                        photo_by_id[member["photo_candidate_id"]]["geometry"]["xyxy_px"]) >= .45
                       for member in cluster):
                    cluster.append(other)
                    assigned.add(other_id)
                    changed = True
        def representative_rank(item):
            box = photo_by_id[item["photo_candidate_id"]]["geometry"]
            x0, y0, x1, y1 = box["xyxy_px"]
            area = (x1-x0)*(y1-y0)/(box["image_width"]*box["image_height"])
            return item["total_region_feature_matches"]/(1+2*area)
        representative = max(cluster, key=representative_rank)
        passages.append({"passage_id": f"passage-hypothesis-{len(passages)+1}",
                         "status": representative["status"],
                         "photo_source_ref": candidate["photo_source_ref"],
                         "representative_photo_candidate_id": representative["photo_candidate_id"],
                         "overlapping_photo_candidate_ids": sorted(assigned &
                             {item["photo_candidate_id"] for item in cluster}),
                         "scan_source_refs": sorted({item["scan_source_ref"]
                                                      for member in cluster
                                                      for item in member["scan_support"]}),
                         "metric_width_m": representative["metric_width_m"]})
        passages[-1]["provisional_dino_top_to_floor_height_m"] = representative[
            "provisional_dino_top_to_floor_height_m"]
    passages.sort(key=lambda item: (item["status"] != "metric_opening_supported",
                                    item["status"] != "visual_passage_correspondence",
                                    -len(item["scan_source_refs"]), item["photo_source_ref"]))
    review_artifacts = []
    photo_source = Path(_read(photo_run / "quality_report.json")["input_path"])
    review_dir = output_dir / "photo_guided_reviews"
    review_dir.mkdir(exist_ok=True)
    for passage in passages:
        png = _review_image(passage, candidates, photo_by_id, scan_by_id,
                            photo_run, lidar_run, photo_source, rgb_by_source,
                            rotation, review_dir)
        passage["review_png"] = png.relative_to(output_dir).as_posix()
        review_artifacts.append({"path": str(png), "sha256": sha256(png)})
    report = {"report_version": "0.1.0", "status": "visual_correspondence_only"
              if not any(item["status"] == "metric_opening_supported" for item in candidates)
              else "metric_opening_supported",
              "model_inference_performed": False,
              "source_runs": {"linked": str(linked_run), "photo": str(photo_run),
                              "lidar": str(lidar_run)},
              "model_id": DINO_ID,
              "selection": {"photo_scan_pair_minimum_inliers": MIN_PAIR_INLIERS,
                            "box_pair_minimum_shared_feature_matches": MIN_REGION_MATCHES,
                            "scan_box_maximum_image_fraction": .5,
                            "photo_name_filter": photo_name,
                            "scan_views": "previously selected Grounding DINO scan frames only"},
              "photo_scan_metric_registration_accepted": registration["metric_registration_accepted"],
              "existing_lidar_gap_candidates": [
                  {"gap_id": f"opening-gap-{number}", "status": gap["status"],
                   "width_m": gap["width_m"], "wall_index": gap["wall_index"]}
                  for number, gap in enumerate(geometry["room_fit"].get("opening_gap_candidates", []), 1)],
              "candidate_count": len(candidates), "candidates": candidates,
              "passage_hypothesis_count": len(passages), "passages": passages,
              "warnings": ["Matched features inside detector boxes support the same visible scene region, not calibrated box edges or doorway width.",
                           "Detector top edges are provisionally treated as lintels for a top-to-floor height hypothesis, but are not verified structural edges.",
                           "Timing-only scan RGB/depth pairs cannot support a metric opening.",
                           "Independent reference lengths were not read or used."]}
    path = output_dir / "photo_guided_openings.json"
    write_json(path, report)
    return report, review_artifacts + [{"path": str(path), "sha256": sha256(path)}]


def review_existing_dino_openings(args, run_dir, run):
    report, artifacts = analyze_linked_dino_openings(args.linked_run, run_dir,
                                                      photo_name=args.photo_name)
    run["artifacts"] = artifacts
    run["data_revision"] = sha256(Path(args.linked_run).resolve(strict=True) / "cross_capture_links.json")
    run["model_or_api"] = {"id": DINO_ID, "inference_performed": False}
    run["metrics"] = {"candidate_count": report["candidate_count"],
                      "visual_correspondence_count": sum(
                          item["status"] == "visual_passage_correspondence"
                          for item in report["candidates"]),
                      "metric_opening_count": sum(
                          item["status"] == "metric_opening_supported"
                          for item in report["candidates"])}
    print(f"photo-guided opening report: {run_dir / 'photo_guided_openings.json'}")
