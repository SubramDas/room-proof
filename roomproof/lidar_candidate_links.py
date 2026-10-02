"""Conservative image-to-wall hypotheses for time-linked Stray RGB candidates."""

from collections import Counter
import math
from pathlib import Path
import statistics

from PIL import Image

from .cli import sha256, write_json
from .lidar_geometry import rotate


def _wall_hit(frame, candidate, boundary, fraction_x=.5, fraction_y=.5):
    """Project one image ray to the first fitted wall segment under stated pose assumptions."""
    box = candidate["geometry"]["xyxy_px"]
    sampled_width = candidate["geometry"]["image_width"]
    sampled_height = candidate["geometry"]["image_height"]
    source_width = candidate["geometry"]["source_image_width"]
    source_height = candidate["geometry"]["source_image_height"]
    u = (box[0] + fraction_x * (box[2] - box[0])) * source_width / sampled_width
    v = (box[1] + fraction_y * (box[3] - box[1])) * source_height / sampled_height
    pose = frame["pose"]
    intrinsic = pose["intrinsics_px"]
    direction = rotate(pose["quaternion_xyzw"],
                       ((u - intrinsic["cx"]) / intrinsic["fx"],
                        (v - intrinsic["cy"]) / intrinsic["fy"], 1.0))
    origin = pose["translation_m"]
    hits = []
    for wall_index in range(len(boundary)):
        start, end = boundary[wall_index], boundary[(wall_index + 1) % len(boundary)]
        side_x, side_z = end[0] - start[0], end[1] - start[1]
        determinant = direction[0] * (-side_z) + side_x * direction[2]
        if abs(determinant) < 1e-8:
            continue
        offset_x, offset_z = start[0] - origin[0], start[1] - origin[2]
        travel = (offset_x * (-side_z) + side_x * offset_z) / determinant
        fraction = (direction[0] * offset_z - direction[2] * offset_x) / determinant
        if travel > 0 and 0 <= fraction <= 1:
            hits.append({"wall_index": wall_index,
                         "distance_from_camera_m": round(travel, 3),
                         "offset_along_wall_m": round(fraction * math.hypot(side_x, side_z), 3),
                         "height_world_y_m": round(origin[1] + travel * direction[1], 3)})
    return min(hits, key=lambda item: item["distance_from_camera_m"]) if hits else None


def _candidate_wall_hit(frame, candidate, boundary):
    """Require most sampled rays in a region to reach the same fitted wall."""
    hits = [_wall_hit(frame, candidate, boundary, x, y)
            for y in (.35, .65) for x in (.25, .5, .75)]
    present = [hit for hit in hits if hit is not None]
    if not present:
        return None
    wall_index, count = Counter(hit["wall_index"] for hit in present).most_common(1)[0]
    if count < 4:
        return None
    support = [hit for hit in present if hit["wall_index"] == wall_index]
    edge_hits = [_wall_hit(frame, candidate, boundary, x, y)
                 for x in (.1, .9) for y in (.1, .9)]
    edge_heights = [hit["height_world_y_m"] for hit in edge_hits
                    if hit is not None and hit["wall_index"] == wall_index]
    return {"wall_index": wall_index,
            "distance_from_camera_m": round(statistics.median(hit["distance_from_camera_m"] for hit in support), 3),
            "offset_along_wall_m": round(statistics.median(hit["offset_along_wall_m"] for hit in support), 3),
            "height_world_y_m": round(statistics.median(hit["height_world_y_m"] for hit in support), 3),
            "projected_height_span_m": round(max(edge_heights)-min(edge_heights), 3) if len(edge_heights) >= 3 else None,
            "ray_support_count": count, "ray_count": len(hits),
            "offset_range_m": [min(hit["offset_along_wall_m"] for hit in support),
                               max(hit["offset_along_wall_m"] for hit in support)]}


def _depth_evidence(scan, frame, candidate, boundary):
    """Compare aligned measured depths with the wall predicted by the fitted plan.

    Missing returns are reported separately: glass, dark surfaces, and occlusion
    can all make a depth hole without there being a structural opening.
    """
    depth_path = Path(scan) / "depth" / f"{frame['frame_id']}.png"
    confidence_path = Path(scan) / "confidence" / f"{frame['frame_id']}.png"
    with Image.open(depth_path) as depth_image, Image.open(confidence_path) as confidence_image:
        if depth_image.size != confidence_image.size:
            raise ValueError(f"depth/confidence size mismatch: {frame['frame_id']}")
        depth = depth_image.load()
        confidence = confidence_image.load()
        depth_width, depth_height = depth_image.size
        counts = Counter()
        examples = []
        box = candidate["geometry"]["xyxy_px"]
        for fy in (.3, .5, .7):
            for fx in (.2, .4, .6, .8):
                hit = _wall_hit(frame, candidate, boundary, fx, fy)
                if hit is None:
                    counts["no_wall_ray"] += 1
                    continue
                u = int((box[0] + fx * (box[2] - box[0])) * depth_width /
                        candidate["geometry"]["image_width"])
                v = int((box[1] + fy * (box[3] - box[1])) * depth_height /
                        candidate["geometry"]["image_height"])
                u = min(depth_width - 1, max(0, u))
                v = min(depth_height - 1, max(0, v))
                observed = depth[u, v] / 1000
                predicted = hit["distance_from_camera_m"]
                if confidence[u, v] < 1 or not .25 <= observed <= 6:
                    kind = "missing_or_low_confidence"
                elif observed > predicted + .25:
                    kind = "behind_wall"
                elif observed < predicted - .25:
                    kind = "foreground_occlusion"
                else:
                    kind = "at_wall"
                counts[kind] += 1
                examples.append({"pixel_xy": [u, v], "observed_depth_m": round(observed, 3),
                                 "predicted_wall_depth_m": predicted, "kind": kind})
    return {"sample_count": 12, "counts": dict(counts), "samples": examples,
            "method": "12 box-interior rays; depth beyond fitted wall by >0.25 m supports an opening, missing depth alone does not"}


def link_lidar_candidates(scan, index, geometry, candidates, pairing, run_dir):
    """Record projected wall/gap matches; promote only after registration is verified."""
    fit = geometry["room_fit"]
    boundary = fit.get("boundary_xz_m")
    gaps = fit.get("opening_gap_candidates", [])
    frames = {frame["frame_id"]: frame for frame in index["frames"]}
    records = []
    for item in candidates["candidates"]:
        if item["class"] not in ("door", "doorway", "open_passage", "window"):
            continue
        record = {"candidate_id": item["candidate_id"], "class": item["class"],
                  "source_ref": item["source_ref"], "depth_frame_id": item.get("depth_frame_id"),
                  "rgb_depth_pairing_status": item.get("rgb_depth_pairing_status"),
                  "status": "unresolved", "nearest_wall": None,
                  "matching_depth_gap_ids": [], "depth_evidence": None, "reason": None}
        box = item["geometry"]["xyxy_px"]
        record["box_area_fraction"] = round((box[2]-box[0])*(box[3]-box[1]) /
                                            (item["geometry"]["image_width"]*item["geometry"]["image_height"]), 4)
        frame = frames.get(item.get("depth_frame_id"))
        if item.get("rgb_depth_pairing_status") != "registered_candidate" or frame is None:
            record["reason"] = "no RGB/depth frame with supported timing and sampled pixel registration"
        elif fit["status"] != "inferred" or not boundary:
            record["reason"] = "no fitted single-room walls"
        else:
            hit = _candidate_wall_hit(frame, item, boundary)
            record["nearest_wall"] = hit
            if hit is None:
                record["reason"] = "image ray does not intersect a fitted wall segment"
            else:
                record["depth_evidence"] = _depth_evidence(scan, frame, item, boundary)
                matching = []
                for gap_index, gap in enumerate(gaps, 1):
                    left, right = hit["offset_range_m"]
                    if (gap["wall_index"] == hit["wall_index"] and
                            right >= gap["offset_along_wall_m"] - .1 and
                            left <= gap["offset_along_wall_m"] + gap["width_m"] + .1):
                        matching.append(f"opening-gap-{gap_index}")
                record["matching_depth_gap_ids"] = matching
                if not matching:
                    if record["depth_evidence"]["counts"].get("at_wall", 0) >= 10:
                        record["status"] = "rejected_structural_opening"
                        record["reason"] = "box projects to a fitted wall with at-wall depth in at least 10 of 12 samples"
                    else:
                        record["reason"] = "projected rays do not overlap a fitted wall depth gap"
                elif not pairing["spatial_registration_verified"] or not pairing["frame_offset_supported_by_images"]:
                    record["reason"] = "projected gap agrees, but RGB/depth pixel registration or frame offset is unverified"
                elif record["depth_evidence"]["counts"].get("behind_wall", 0) < 2:
                    record["reason"] = "wall gap overlaps the image box, but this paired depth frame has fewer than two behind-wall returns"
                elif hit["projected_height_span_m"] is None or hit["projected_height_span_m"] < 1.5:
                    record["reason"] = "box does not span enough fitted wall height to establish a structural opening"
                elif record["box_area_fraction"] >= .5:
                    record["reason"] = "box covers at least half of the frame and is too broad for opening confirmation"
                else:
                    record["reason"] = "projected gap and paired depth agree; waiting for an independent repeated view"
        records.append(record)
    groups = []
    assigned = set()
    for first in records:
        hit = first["nearest_wall"]
        if hit is None or first["candidate_id"] in assigned:
            continue
        members = [item for item in records
                   if item["nearest_wall"] is not None and
                   item["class"] == first["class"] and
                   item["nearest_wall"]["wall_index"] == hit["wall_index"] and
                   abs(item["nearest_wall"]["offset_along_wall_m"] - hit["offset_along_wall_m"]) <= .2 and
                   item["candidate_id"] not in assigned]
        if len(members) < 2:
            continue
        positions = [frames[item["depth_frame_id"]]["pose"]["translation_m"]
                     for item in members if item["depth_frame_id"] in frames]
        separation = max((math.dist(a, b) for a in positions for b in positions), default=0)
        common_gaps = set(members[0]["matching_depth_gap_ids"])
        for member in members[1:]:
            common_gaps.intersection_update(member["matching_depth_gap_ids"])
        group = {"group_id": f"view-group-{len(groups)+1}",
                 "candidate_ids": [item["candidate_id"] for item in members],
                 "wall_index": hit["wall_index"], "class": first["class"],
                 "max_camera_separation_m": round(separation, 3),
                 "shared_depth_gap_ids": sorted(common_gaps),
                 "independent_views_supported": separation >= .15}
        groups.append(group)
        assigned.update(group["candidate_ids"])
        supported_depth = [member for member in members if
                           member["depth_evidence"] is not None and
                           member["depth_evidence"]["counts"].get("behind_wall", 0) >= 2 and
                           member["nearest_wall"]["projected_height_span_m"] is not None and
                           member["nearest_wall"]["projected_height_span_m"] >= 1.5 and
                           member["box_area_fraction"] < .5 and
                           member["rgb_depth_pairing_status"] == "registered_candidate"]
        supporting_positions = [frames[item["depth_frame_id"]]["pose"]["translation_m"]
                                for item in supported_depth if item["depth_frame_id"] in frames]
        supporting_separation = max((math.dist(a, b) for a in supporting_positions
                                     for b in supporting_positions), default=0)
        group["qualified_candidate_ids"] = [item["candidate_id"] for item in supported_depth]
        group["qualified_view_separation_m"] = round(supporting_separation, 3)
        if (common_gaps and len({item["depth_frame_id"] for item in supported_depth}) >= 2 and
                supporting_separation >= .15 and
                pairing["spatial_registration_verified"] and pairing["frame_offset_supported_by_images"]):
            for member in supported_depth:
                member["status"] = "supported_proposal"
                member["reason"] = "registered pixels, paired behind-wall depth, fitted gap, and independent views agree"
    report = {"report_version": "0.1.0", "status": "hypotheses_only",
              "capture_id": index["capture_id"],
              "projection_assumptions": "RGB intrinsics and pose applied to sampled RGB pixels after scale-up; sampled edge alignment supports frame offset, but RGB/depth extrinsics and scale are not independently calibrated",
              "candidate_count": len(records),
              "projected_to_wall_count": sum(item["nearest_wall"] is not None for item in records),
              "gap_coincidence_count": sum(bool(item["matching_depth_gap_ids"]) for item in records),
              "supported_proposal_count": sum(item["status"] == "supported_proposal" for item in records),
              "rejected_structural_opening_count": sum(item["status"] == "rejected_structural_opening" for item in records),
              "repeated_view_groups": groups,
              "records": records,
              "warnings": ["A 2D ray/wall hit is only a placement hypothesis; it does not validate RGB/depth registration or a metric opening."]}
    path = Path(run_dir) / "lidar_candidate_links.json"
    write_json(path, report)
    return report, [{"path": str(path), "sha256": sha256(path)}]
