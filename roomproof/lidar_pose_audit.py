"""Timestamp and motion audit for exported Stray poses and IMU samples."""

from bisect import bisect_left
import math
import statistics


def _percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[round((len(ordered)-1)*fraction)], 6)


def audit_pose_imu(index, verified_closures):
    frames = index["frames"]
    poses = [frame["pose"] for frame in frames]
    times = [pose["timestamp_seconds"] for pose in poses]
    imu = index.get("imu_records", [])
    imu_times = [sample["timestamp"] for sample in imu]
    pose_steps = [b-a for a, b in zip(times, times[1:])]
    imu_steps = [b-a for a, b in zip(imu_times, imu_times[1:])]
    timing_continuous = bool(pose_steps and all(step > 0 for step in pose_steps))
    imu_continuous = bool(imu_steps and all(step > 0 for step in imu_steps))
    position_steps = [math.dist(a["translation_m"], b["translation_m"])
                      for a, b in zip(poses, poses[1:])]
    rotation_steps = []
    quaternion_norm_errors = []
    for pose in poses:
        quaternion_norm_errors.append(abs(math.sqrt(sum(value*value for value in pose["quaternion_xyzw"]))-1))
    for a, b in zip(poses, poses[1:]):
        dot = abs(sum(x*y for x, y in zip(a["quaternion_xyzw"], b["quaternion_xyzw"])))
        rotation_steps.append(math.degrees(2*math.acos(min(1., dot))))
    nearest_imu_residuals = []
    for time in times:
        if not imu_continuous or time < imu_times[0] or time > imu_times[-1]:
            continue
        at = bisect_left(imu_times, time)
        nearest_imu_residuals.append(min(abs(imu_times[position]-time)
                                         for position in (at-1, at) if 0 <= position < len(imu_times)))
    pose_median_step = statistics.median(pose_steps) if pose_steps else None
    imu_median_step = statistics.median(imu_steps) if imu_steps else None
    warnings = []
    if not timing_continuous or not imu_continuous:
        warnings.append("Pose or IMU timestamps are nonmonotonic; independent inertial fusion is unsupported.")
    if verified_closures == 0:
        warnings.append("No independently verified 3D closure; recorded pose drift cannot be corrected from this scan alone.")
    if any(step > .10 for step in position_steps):
        warnings.append("Consecutive recorded camera positions include jumps over 0.10 m.")
    return {"report_version": "0.1.0", "status": "audit_only",
            "pose_count": len(poses), "imu_count": len(imu),
            "pose_time_range_seconds": [times[0], times[-1]] if times else None,
            "imu_time_range_seconds": [imu_times[0], imu_times[-1]] if imu_times else None,
            "pose_timestamps_strictly_increasing": timing_continuous,
            "imu_timestamps_strictly_increasing": imu_continuous,
            "pose_step_seconds": {"median": round(pose_median_step, 6) if pose_median_step else None,
                                  "p95": _percentile(pose_steps, .95), "max": max(pose_steps, default=None)},
            "imu_step_seconds": {"median": round(imu_median_step, 6) if imu_median_step else None,
                                 "p95": _percentile(imu_steps, .95), "max": max(imu_steps, default=None)},
            "pose_position_step_m": {"median": _percentile(position_steps, .5),
                                     "p95": _percentile(position_steps, .95),
                                     "max": round(max(position_steps), 6) if position_steps else None,
                                     "over_0_10_m_count": sum(step > .10 for step in position_steps)},
            "pose_rotation_step_degrees": {"median": _percentile(rotation_steps, .5),
                                           "p95": _percentile(rotation_steps, .95),
                                           "max": round(max(rotation_steps), 6) if rotation_steps else None},
            "quaternion_unit_norm_error_max": round(max(quaternion_norm_errors), 8) if quaternion_norm_errors else None,
            "pose_samples_within_imu_time_range": len(nearest_imu_residuals),
            "nearest_imu_time_residual_seconds": {"median": _percentile(nearest_imu_residuals, .5),
                                                  "p95": _percentile(nearest_imu_residuals, .95)},
            "verified_closure_count": verified_closures,
            "imu_fields": index.get("imu_fields", []),
            "warnings": warnings + ["This audit checks timing and exported trajectory continuity only; IMU axis and calibration semantics are not yet verified, so it does not claim VIO accuracy."]}
