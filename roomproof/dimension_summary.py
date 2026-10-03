"""Consolidate plan dimensions and explicitly provisional geometry hypotheses."""

import json
from pathlib import Path
import statistics

from .cli import sha256, write_json


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _dimension(measurement, source_path):
    """Use the word provisional for inferred plan values in this review file."""
    if measurement is None:
        return {"value": None, "unit": None, "status": "unresolved",
                "accepted_in_plan": False, "source_path": str(source_path)}
    plan_status = measurement.get("status", "unresolved")
    return {"value": measurement.get("value"),
            "unit": measurement.get("unit"),
            "status": "provisional" if plan_status == "inferred" else plan_status,
            "accepted_in_plan": measurement.get("value") is not None,
            "plan_status": plan_status,
            "interval": measurement.get("interval"),
            "source_refs": measurement.get("source_refs", []),
            "source_path": str(source_path)}


def _hypothesis(value, unit, source_path, reason, source_refs=()):
    return {"value": value, "unit": unit,
            "status": "provisional" if value is not None else "unresolved",
            "accepted_in_plan": False,
            "reason": reason,
            "source_refs": list(source_refs),
            "source_path": str(source_path)}


def generate_dimension_summary(source_run, output_dir=None):
    """Write one machine-readable report from saved pipeline outputs.

    No reference/tape measurement or new model inference is read here.
    When output_dir differs from source_run, this supports a cheap summary
    refresh of an existing completed run without modifying that run.
    """
    source_run = Path(source_run).resolve(strict=True)
    output_dir = Path(output_dir).resolve() if output_dir else source_run
    plan_path = source_run / "property_plan.json"
    plan = _read(plan_path)
    links_path = source_run / "cross_capture_links.json"
    lidar_run = source_run
    if links_path.is_file():
        links = _read(links_path)
        lidar_run = Path(links["source_runs"]["lidar"]).resolve(strict=True)
    geometry_path = lidar_run / "lidar_geometry.json"
    geometry = _read(geometry_path)["room_fit"] if geometry_path.is_file() else None
    rooms = []
    for room in plan["rooms"]:
        wall_lengths = [
            {"surface_id": surface["id"],
             "length": _dimension(surface.get("length"), plan_path)}
            for surface in room.get("surfaces", []) if surface.get("kind") == "wall"]
        axis_spans = []
        if (geometry and room.get("boundary") is not None and
                geometry.get("axis_lengths_m") and room["id"] == plan["rooms"][0]["id"]):
            axis_spans = [
                _hypothesis(value, "m", geometry_path,
                            "LiDAR room-fit axis; scale and fit are not independently calibrated")
                for value in geometry["axis_lengths_m"]]
        rooms.append({"room_id": room["id"],
                      "room_status": room["status"],
                      "axis_spans": axis_spans,
                      "wall_lengths": wall_lengths,
                      "ceiling_height": _dimension(room.get("ceiling_height"), plan_path),
                      "floor_area": _dimension(room.get("floor_area"), plan_path)})
    openings = []
    for room in plan["rooms"]:
        for opening in room.get("openings", []):
            openings.append({"opening_id": opening["id"],
                             "room_id": room["id"], "kind": opening["kind"],
                             "plan_status": opening["status"],
                             "width": _dimension(opening.get("width"), plan_path),
                             "height": _dimension(opening.get("height"), plan_path),
                             "offset_along_wall": _dimension(
                                 opening.get("offset_along_wall"), plan_path)})
    hypotheses = []
    if geometry:
        for number, gap in enumerate(geometry.get("opening_gap_candidates", []), 1):
            plan_opening_id = None
            if plan["rooms"]:
                expected_id = (f"opening-{plan['rooms'][0]['id'].removeprefix('room-')}"
                               f"-candidate-{number}")
                if any(item["opening_id"] == expected_id for item in openings):
                    plan_opening_id = expected_id
            hypotheses.append({"hypothesis_id": f"lidar-opening-gap-{number}",
                               "kind": "lidar_depth_gap",
                               "room_id": plan["rooms"][0]["id"] if plan["rooms"] else None,
                               "possible_plan_opening_id": plan_opening_id,
                               "status": "provisional",
                               "width": _hypothesis(
                                   gap["width_m"], "m", geometry_path,
                                   "Depth-gap width; structural opening not verified"),
                               "height": None,
                               "source_detail": {"wall_index": gap["wall_index"],
                                                 "gap_status": gap["status"]}})
    dino_path = source_run / "photo_guided_openings.json"
    if dino_path.is_file():
        dino = _read(dino_path)
        candidates = {item["photo_candidate_id"]: item for item in dino["candidates"]}
        for passage in dino["passages"]:
            candidate = candidates[passage["representative_photo_candidate_id"]]
            views = []
            for support in candidate["scan_support"]:
                projected = support.get("targeted_scan_geometry", {}).get("provisional_height", {})
                if projected.get("height_m") is None and projected.get("provisional_box_side_width_m") is None:
                    continue
                views.append({"scan_source_ref": support["scan_source_ref"],
                              "scan_candidate_id": support["scan_candidate_id"],
                              "rgb_depth_pairing_status": support["rgb_depth_pairing_status"],
                              "height": _hypothesis(
                                  projected.get("height_m"), "m", dino_path,
                                  "DINO box top projected to fitted LiDAR wall, then compared with fitted floor",
                                  [support["scan_source_ref"]]),
                              "width": _hypothesis(
                                  projected.get("provisional_box_side_width_m"), "m", dino_path,
                                  "DINO box sides projected to fitted LiDAR wall",
                                  [support["scan_source_ref"]]),
                              "box_bottom_reaches_floor": projected.get("box_bottom_reaches_floor")})
            widths = [view["width"]["value"] for view in views
                      if view["width"]["value"] is not None]
            hypotheses.append({
                "hypothesis_id": passage["passage_id"],
                "kind": "dino_photo_scan_passage",
                "room_id": plan["rooms"][0]["id"] if plan["rooms"] else None,
                "photo_source_ref": passage["photo_source_ref"],
                "representative_photo_candidate_id": passage["representative_photo_candidate_id"],
                "review_png": str(source_run / passage["review_png"]),
                "possible_plan_opening_id": None,
                "status": "provisional",
                "height": _hypothesis(
                    passage.get("provisional_dino_top_to_floor_height_m"), "m", dino_path,
                    "Median DINO box-top-to-fitted-floor estimate; not a verified lintel",
                    [passage["photo_source_ref"]] + passage["scan_source_refs"]),
                "width": _hypothesis(
                    round(statistics.median(widths), 3) if widths else None,
                    "m", dino_path,
                    "Median DINO box-side projection; unverified opening identity and edges",
                    [passage["photo_source_ref"]] + passage["scan_source_refs"]),
                "scan_views": views})
    report = {"report_version": "0.1.0",
              "source_run_id": source_run.name,
              "property_id": plan["property_id"],
              "source_plan_path": str(plan_path),
              "source_lidar_geometry_path": str(geometry_path) if geometry else None,
              "source_photo_guided_path": str(dino_path) if dino_path.is_file() else None,
              "reference_measurements_used": False,
              "rooms": rooms,
              "openings": openings,
              "opening_hypotheses": hypotheses,
              "notes": [
                  "Provisional values are pipeline estimates, not independently validated measurements.",
                  "Separate opening hypotheses are not asserted to be the same physical opening.",
                  "The property plan remains the authority for accepted room and opening fields."
              ]}
    path = output_dir / "dimensions_summary.json"
    write_json(path, report)
    return report, {"path": str(path), "sha256": sha256(path)}
