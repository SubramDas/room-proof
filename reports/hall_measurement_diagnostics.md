# Hall trajectory and surface diagnostics — 3 October 2026

Run `run-f701a6cf5c9241cd8792b2be12c91713` processed the unchanged hall
Stray export with 128 selected depth frames, exported poses, and the visual
model off. It wrote `lidar_pose_audit.json` and
`lidar_surface_diagnostics.json` alongside a schema-valid plan. The scan's
independent laser dimensions were held out from both fitting stages.

The pose audit found 3,165 exported poses and 5,280 IMU records. Median pose
and IMU intervals were 0.016668 s and 0.009994 s respectively. The p95
nearest IMU timestamp difference was 0.004751 s. No consecutive pose step
exceeded 0.10 m. No candidate return view passed the existing 3D closure
gate, so no pose correction was applied. These timing checks do not verify
IMU axes or establish an independent visual-inertial trajectory.

The surface diagnostic gathers accepted depth points near each provisional
wall/floor/ceiling, weights Stray confidence code 2 twice code 1 within each
frame, and takes the median of qualified frame estimates. This is an
alternative *diagnostic* tied to the current plane selection, not a corrected
plan or a calibrated interval.

| Quantity | Existing fit | Frame-balanced diagnostic | Separate laser | Existing error | Diagnostic error |
| --- | ---: | ---: | ---: | ---: | ---: |
| Long side | 3.9260 m | 3.9308 m | 3.90 m | +0.0260 m | +0.0308 m |
| Short side | 3.3958 m | 3.4133 m | 3.21 m | +0.1858 m | +0.2033 m |
| Height | 2.7682 m | 2.7697 m | 2.84 m | −0.0718 m | −0.0703 m |

The alternative **worsens** both wall-length errors and barely changes
height. The wall at axis 1, side 1 has 51 qualified frames but a 0.147 m
p10–p90 spread of frame estimates and 0.0582 m median absolute deviation;
the other three walls have smaller frame variation. Its original-fit point
residual p90 is 0.0999 m. This wall is flagged in the quality report and
plan warnings. Narrow slabs around existing planes can inherit the existing
wall-selection error, so further work must compare competing surface
hypotheses and inspect source views. No offset was adjusted toward the laser
value during inference.

## Replay command

```bash
.venv/bin/python -m roomproof process-capture /tmp/roomproof-hall-lidar/b41a75401a --tier lidar --property-id prop-flat-805 --capture-id cap-flat-805-hall-pose-surface-audit --room-id room-hall --room-kind connector --max-lidar-frames 128 --visual-model off --runs-dir runs
```

Next: identify which physical surface the unstable wall samples represent,
fit competing planes with outlier and occlusion handling, compare the resulting
plan dimensions against held-out laser truth, and repeat on another property.
Only add a pose-graph or independent VIO correction if future scans supply
geometrically verified closure or tracking failures; timestamp continuity
alone does not justify changing the trajectory.
