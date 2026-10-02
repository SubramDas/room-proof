"""Reference-only evaluation; this module is never imported by capture inference."""

import json
import hashlib
from pathlib import Path

from .plan import validate

SCORER_VERSION = "0.1.0"


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _measurement_rows(plan, truth):
    rooms = {room["id"]: room for room in plan["rooms"]}
    surfaces = {surface["id"]: surface for room in plan["rooms"] for surface in room["surfaces"]}
    openings = {opening["id"]: opening for room in plan["rooms"] for opening in room["openings"]}
    damages = {damage["id"]: damage for damage in plan["damage_regions"]}
    lookup = {"room": rooms, "surface": surfaces, "opening": openings, "damage": damages, "plan": {"property": plan["plan"]}}
    rows = []
    for reference in truth["measurements"]:
        kind, object_id, quantity = reference["object_type"], reference["object_id"], reference["quantity"]
        predicted = lookup.get(kind, {}).get(object_id, {}).get(quantity)
        value = predicted.get("value") if isinstance(predicted, dict) else None
        interval = predicted.get("interval", {}) if isinstance(predicted, dict) else {}
        lower, upper = interval.get("lower"), interval.get("upper")
        actual = reference["value"]
        if value is not None and predicted["unit"] != reference["unit"]:
            raise ValueError(f"unit mismatch for {reference['id']}")
        width = upper - lower if lower is not None and upper is not None else None
        covered = lower <= actual <= upper if width is not None else None
        rows.append({"reference_id": reference["id"], "object_type": kind, "object_id": object_id,
                     "quantity": quantity, "unit": reference["unit"], "truth": actual,
                     "prediction": value, "absolute_error": abs(value-actual) if value is not None else None,
                     "relative_error": abs(value-actual)/actual if value is not None and actual else None,
                     "interval_lower": lower, "interval_upper": upper, "interval_width": width,
                     "interval_covers_truth": covered, "status": "missing" if value is None else "reported"})
    return rows


def _summary(rows):
    by_type = {}
    for row in rows:
        key = row["quantity"]
        group = by_type.setdefault(key, {"n": 0, "reported": 0, "finite_intervals": 0, "covered": 0,
                                         "absolute_errors": [], "interval_widths": []})
        group["n"] += 1
        if row["prediction"] is not None:
            group["reported"] += 1
            group["absolute_errors"].append(row["absolute_error"])
        if row["interval_width"] is not None:
            group["finite_intervals"] += 1
            group["covered"] += int(row["interval_covers_truth"])
            group["interval_widths"].append(row["interval_width"])
    for group in by_type.values():
        group["missing_rate"] = (group["n"]-group["reported"])/group["n"]
        group["finite_coverage"] = group["covered"]/group["finite_intervals"] if group["finite_intervals"] else None
        group["unbounded_rate"] = (group["n"]-group["finite_intervals"])/group["n"]
        for field in ("absolute_errors", "interval_widths"):
            vals = sorted(group.pop(field))
            group["median_" + field[:-1]] = vals[len(vals)//2] if vals else None
    return by_type


def _opening_score(plan, truth):
    """Greedy one-to-one match by known wall and center position, no truth leakage."""
    predicted = [(room["id"], item) for room in plan["rooms"] for item in room["openings"]]
    real = truth.get("openings", [])
    candidates = []
    for i, ref in enumerate(real):
        for j, (room_id, item) in enumerate(predicted):
            center = item["offset_along_wall"]["value"]
            if room_id == ref["room_id"] and item["surface_id"] == ref["surface_id"] and item["kind"] == ref["kind"] and center is not None:
                distance = abs(center-ref["offset_along_wall_m"])
                if distance <= .30:
                    candidates.append((distance, ref["id"], item["id"], i, j))
    used_real, used_pred, rows = set(), set(), []
    for distance, _, _, i, j in sorted(candidates):
        if i in used_real or j in used_pred:
            continue
        used_real.add(i); used_pred.add(j)
        width = predicted[j][1]["width"]["value"]
        error = abs(width-real[i]["width_m"]) if width is not None else None
        rows.append({"reference_id": real[i]["id"], "prediction_id": predicted[j][1]["id"],
                     "position_error_m": distance, "width_error_m": error,
                     "result": "success" if error is not None and error <= .02 else "width_miss"})
    rows.extend({"reference_id": ref["id"], "prediction_id": None, "result": "missed"} for i, ref in enumerate(real) if i not in used_real)
    rows.extend({"reference_id": None, "prediction_id": item["id"], "result": "phantom"} for j, (_, item) in enumerate(predicted) if j not in used_pred)
    successes = sum(row["result"] == "success" for row in rows)
    denominator = len(real)+len(predicted)-len(used_pred)
    return {"rows": rows, "successes": successes, "denominator": denominator,
            "rate": successes/denominator if denominator else None,
            "pass": successes/denominator >= .85 if denominator else None}


def _geometry_score(plan, truth, rows):
    heights, walls = [], []
    for row in rows:
        if row["object_type"] == "room" and row["quantity"] == "ceiling_height":
            heights.append({**row, "pass": row["absolute_error"] is not None and row["absolute_error"] <= .015})
        if row["object_type"] == "surface" and row["quantity"] == "length":
            limit = .08 if plan["capture"]["tier"] == "photo" else .03 if plan["capture"]["tier"] == "video" else None
            walls.append({**row, "limit": limit, "pass": row["relative_error"] is not None and limit is not None and row["relative_error"] <= limit if limit is not None else None})
    actual_area = next((r for r in rows if r["object_type"] == "plan" and r["quantity"] == "floor_area"), None)
    area_result = None if actual_area is None else {**actual_area, "pass_8pct": actual_area["relative_error"] is not None and actual_area["relative_error"] <= .08}
    reference_edges = {tuple(sorted(pair)) for pair in truth.get("adjacency", [])}
    predicted_edges = {tuple(sorted((edge["room_a_id"], edge["room_b_id"]))) for edge in plan["adjacency"]}
    return {"ceiling_heights": heights, "walls": walls, "footprint_area": area_result,
            "adjacency": {"reference": sorted(map(list, reference_edges)), "predicted": sorted(map(list, predicted_edges)),
                          "pass": reference_edges == predicted_edges if reference_edges else None}}


def _damage_score(plan, truth):
    """Stable-ID class/surface accounting; polygon scoring awaits reference geometry."""
    predicted = {item["id"]: item for item in plan["damage_regions"]}
    real = {item["id"]: item for item in truth.get("damage_regions", [])}
    rows = []
    for damage_id, ref in sorted(real.items()):
        item = predicted.get(damage_id)
        rows.append({"reference_id": damage_id, "prediction_id": item["id"] if item else None,
                     "class_correct": item["class"] == ref["class"] if item else False,
                     "surface_correct": item["room_id"] == ref["room_id"] and item["surface_id"] == ref["surface_id"] if item else False,
                     "result": "missed" if item is None else "matched"})
    rows.extend({"reference_id": None, "prediction_id": item["id"], "result": "phantom"}
                for damage_id, item in sorted(predicted.items()) if damage_id not in real)
    return {"rows": rows, "real_count": len(real), "phantom_count": sum(row["result"] == "phantom" for row in rows),
            "class_and_surface_correct": sum(row.get("class_correct", False) and row.get("surface_correct", False) for row in rows)}


def _repeatability(plans, manifest):
    by_capture = {plan["capture"]["capture_id"]: plan for plan in plans}
    results = []
    for pair in manifest.get("repeat_pairs", []):
        first_id, second_id = pair["capture_ids"]
        first, second = by_capture[first_id], by_capture[second_id]
        if first["capture"]["tier"] != second["capture"]["tier"]:
            raise ValueError("repeat pair must use the same tier")
        def quantities(plan):
            values = {}
            for room in plan["rooms"]:
                values[("ceiling_height", room["id"])] = room["ceiling_height"]["value"]
                for surface in room["surfaces"]:
                    if surface["kind"] == "wall":
                        values[("wall_length", surface["id"])] = surface["length"]["value"]
            return values
        a, b = quantities(first), quantities(second)
        rows = []
        for kind, object_id in sorted(set(a) | set(b)):
            one, two = a.get((kind, object_id)), b.get((kind, object_id))
            difference = abs(one-two) if one is not None and two is not None else None
            if kind == "ceiling_height":
                strict_limit = permissive_limit = .01
            else:
                fractional = .005*(one+two)/2 if difference is not None else None
                strict_limit = min(.01, fractional) if fractional is not None else None
                permissive_limit = max(.01, fractional) if fractional is not None else None
            rows.append({"object_type": kind, "object_id": object_id, "first_m": one, "second_m": two,
                         "spread_m": difference, "strict_limit_m": strict_limit,
                         "permissive_limit_m": permissive_limit,
                         "strict_pass": difference <= strict_limit if difference is not None else False,
                         "permissive_pass": difference <= permissive_limit if difference is not None else False})
        results.append({"capture_ids": [first_id, second_id], "tier": first["capture"]["tier"], "rows": rows,
                        "strict_pass": bool(rows) and all(row["strict_pass"] for row in rows)})
    return results


def evaluate(manifest_path):
    manifest_path = Path(manifest_path).resolve(strict=True)
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema_version") != "0.1.0":
        raise ValueError("unsupported benchmark manifest version")
    if not manifest.get("captures") or not manifest.get("truth", {}).get("measurements"):
        raise ValueError("benchmark requires captures and independent measurements")
    reference_ids = [row["id"] for row in manifest["truth"]["measurements"]]
    if len(reference_ids) != len(set(reference_ids)):
        raise ValueError("duplicate reference ID")
    capture_results = []
    plans = []
    for capture in manifest["captures"]:
        path = (manifest_path.parent / capture["plan_path"]).resolve(strict=True)
        plan = json.loads(path.read_text())
        errors = validate(plan)
        if errors:
            raise ValueError(f"invalid plan {path}: {errors[:3]}")
        if plan["capture"]["capture_id"] != capture["capture_id"] or plan["property_id"] != manifest["property_id"]:
            raise ValueError(f"capture/property mismatch: {path}")
        rows = _measurement_rows(plan, manifest["truth"])
        plans.append(plan)
        capture_results.append({"capture_id": capture["capture_id"], "run_id": plan["run_id"],
                                "tier": plan["capture"]["tier"], "plan_path": str(path),
                                "plan_sha256": _sha256(path),
                                "measurements": rows, "summary": _summary(rows),
                                "opening_gate": _opening_score(plan, manifest["truth"]),
                                "geometry_gates": _geometry_score(plan, manifest["truth"], rows),
                                "damage_gate": _damage_score(plan, manifest["truth"]),
                                "execution_gate": {"schema_valid": True, "rendered_plan_exists": (path.parent / plan["plan"]["rendered_plan_path"]).is_file()}})
    return {"scorer_version": SCORER_VERSION, "property_id": manifest["property_id"],
            "reference_manifest": str(manifest_path), "reference_manifest_sha256": _sha256(manifest_path),
            "captures": capture_results,
            "repeatability": _repeatability(plans, manifest),
            "limitations": ["No interval calibration claim without a property-held-out split.",
                            "Footprint shape alignment, drift ablation, and damage polygon scoring are pending."]}
