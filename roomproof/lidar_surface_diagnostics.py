"""Frame-balanced wall and height diagnostics for a provisional LiDAR room fit.

This stage reads accepted sensor points only. It never reads reference or tape
measurements and does not silently replace the existing plan dimensions.
"""

from collections import Counter, defaultdict
import math
import statistics


def _quantile(values, fraction):
    ordered = sorted(values)
    if not ordered:
        return None
    return ordered[round((len(ordered) - 1) * fraction)]


def _weighted_median(values):
    """Confidence code 2 gets twice the weight of code 1."""
    ordered = sorted(values)
    target = sum(weight for _, weight in ordered) / 2
    cumulative = 0
    for value, weight in ordered:
        cumulative += weight
        if cumulative >= target:
            return value
    return ordered[-1][0]


def _summarize(frame_samples, original_offset, minimum_per_frame=30):
    per_frame = []
    all_residuals = []
    for frame_id, samples in sorted(frame_samples.items()):
        if len(samples) < minimum_per_frame:
            continue
        estimate = _weighted_median(samples)
        per_frame.append((estimate, frame_id, len(samples)))
        all_residuals.extend(abs(value-original_offset) for value, _ in samples)
    estimates = [item[0] for item in per_frame]
    if len(estimates) < 4:
        return {"status": "insufficient_frame_support", "original_offset_m": original_offset,
                "qualified_frame_count": len(estimates), "qualified_frame_ids": [item[1] for item in per_frame],
                "qualified_point_count": sum(item[2] for item in per_frame)}
    center = statistics.median(estimates)
    return {"status": "diagnostic_only", "original_offset_m": original_offset,
            "frame_balanced_offset_m": round(center, 4),
            "frame_estimate_p10_p90_m": [round(_quantile(estimates, .1), 4),
                                         round(_quantile(estimates, .9), 4)],
            "frame_estimate_mad_m": round(statistics.median(abs(value-center) for value in estimates), 4),
            "original_fit_residual_p50_p90_m": [round(_quantile(all_residuals, .5), 4),
                                                 round(_quantile(all_residuals, .9), 4)],
            "qualified_frame_count": len(estimates),
            "qualified_frame_ids": [item[1] for item in per_frame],
            "qualified_point_count": sum(item[2] for item in per_frame),
            "per_frame": [{"frame_id": frame_id, "offset_m": round(value, 4), "point_count": count}
                          for value, frame_id, count in per_frame]}


def surface_diagnostics(points, frame_offsets, fit):
    """Measure per-frame surface stability using confidence-filtered 3D points."""
    if fit.get("status") != "inferred":
        return {"status": "unavailable", "reason": "room fit is unresolved"}
    if fit.get('shape') == 'supported_convex_irregular':
        return {'status': 'unavailable',
                'reason': 'rectangular axis-balanced diagnostic does not apply to a convex multi-wall room',
                'warnings': ['Per-wall frame-balanced diagnostics are not yet available for irregular rooms.']}
    angles = [math.radians(fit["axes"]["first_angle_degrees"]),
              math.radians(fit["axes"]["second_angle_degrees"])]
    normals = [(math.cos(angle), math.sin(angle)) for angle in angles]
    wall_offsets = [[wall["offset_m"] for wall in pair] for pair in fit["walls"]]
    floor_y, ceiling_y = fit["floor"]["height_m"], fit["ceiling"]["height_m"]
    wall_samples = [[defaultdict(list), defaultdict(list)] for _ in range(2)]
    height_samples = [defaultdict(list), defaultdict(list)]
    rejection = Counter()
    for point, frame_id, confidence in points:
        shift = frame_offsets[frame_id]
        x, y, z = (point[0]+shift[0], point[1]+shift[1], point[2]+shift[2])
        projected = [normal[0]*x + normal[1]*z for normal in normals]
        weight = 2 if confidence >= 2 else 1
        if (wall_offsets[0][0]-.2 <= projected[0] <= wall_offsets[0][1]+.2 and
                wall_offsets[1][0]-.2 <= projected[1] <= wall_offsets[1][1]+.2):
            if abs(y-floor_y) <= .08:
                height_samples[0][frame_id].append((y, weight))
            if abs(y-ceiling_y) <= .08:
                height_samples[1][frame_id].append((y, weight))
        else:
            rejection["outside_provisional_footprint"] += 1
        if not floor_y+.25 <= y <= ceiling_y-.25:
            continue
        for axis in range(2):
            other = 1-axis
            if not wall_offsets[other][0]+.15 <= projected[other] <= wall_offsets[other][1]-.15:
                continue
            distances = [abs(projected[axis]-offset) for offset in wall_offsets[axis]]
            nearest = 0 if distances[0] <= distances[1] else 1
            if distances[nearest] <= .12:
                wall_samples[axis][nearest][frame_id].append((projected[axis], weight))
    wall_results = [[_summarize(wall_samples[axis][side], wall_offsets[axis][side])
                     for side in range(2)] for axis in range(2)]
    height_results = [_summarize(height_samples[side], target)
                      for side, target in enumerate((floor_y, ceiling_y))]
    alternatives = []
    for pair in wall_results:
        if all(wall["status"] == "diagnostic_only" for wall in pair):
            alternatives.append(round(pair[1]["frame_balanced_offset_m"] -
                                      pair[0]["frame_balanced_offset_m"], 4))
        else:
            alternatives.append(None)
    height = (round(height_results[1]["frame_balanced_offset_m"] -
                    height_results[0]["frame_balanced_offset_m"], 4)
              if all(item["status"] == "diagnostic_only" for item in height_results) else None)
    weak_walls = []
    for axis, pair in enumerate(wall_results):
        for side, wall in enumerate(pair):
            if wall["status"] != "diagnostic_only":
                weak_walls.append({"axis_index": axis, "side_index": side,
                                   "reason": "insufficient qualified frames"})
                continue
            spread = wall["frame_estimate_p10_p90_m"][1] - wall["frame_estimate_p10_p90_m"][0]
            if spread > .1 or wall["frame_estimate_mad_m"] > .04:
                weak_walls.append({"axis_index": axis, "side_index": side,
                                   "frame_estimate_p10_p90_span_m": round(spread, 4),
                                   "frame_estimate_mad_m": wall["frame_estimate_mad_m"],
                                   "reason": "frame-to-frame surface position varies beyond the diagnostic gate"})
    warnings = ["Alternative dimensions are diagnostics, not calibrated replacements for the plan.",
                "A narrow slab around the current fit can inherit that fit's wall-selection bias; competing plane selection still needs evaluation."]
    for wall in weak_walls:
        warnings.append(f"Wall axis {wall['axis_index']}, side {wall['side_index']} has unstable per-frame depth support; its length remains uncalibrated.")
    return {"report_version": "0.1.0", "status": "diagnostic_only",
            "method": "accepted metric points, 0.12 m wall slabs, 0.08 m horizontal slabs; confidence-weighted per-frame medians then equal-frame median",
            "selection": {"minimum_points_per_frame": 30,
                          "minimum_qualified_frames": 4,
                          "confidence_code_weights": {"1": 1, "2": 2},
                          "interior_margin_from_other_walls_m": .15},
            "original_axis_lengths_m": fit["axis_lengths_m"],
            "frame_balanced_axis_lengths_m": alternatives,
            "original_ceiling_height_m": fit["ceiling_height_m"],
            "frame_balanced_ceiling_height_m": height,
            "wall_surfaces": wall_results,
            "weak_walls": weak_walls,
            "horizontal_surfaces": {"floor": height_results[0], "ceiling": height_results[1]},
            "rejection_counts": dict(rejection),
            "warnings": warnings}
