# Journal 3 — LiDAR geometry and drift

**Status:** In progress on 2 October 2026. Completed substeps in T24 and T29 are checked in `TASK.md`; no full Phase 3 task has met its acceptance gate. Tape-measured scale and a multiroom capture are still required for T24 and T27–T28 acceptance.

## Work landed

- Added a bounded depth-to-world converter in `roomproof/lidar_geometry.py`. It joins the existing frame-indexed depth, confidence, pose, and intrinsics records. The 16-bit depth PNG is read as millimetres; per-frame intrinsics are scaled from 1920×1440 RGB coordinates to 256×192 depth coordinates. A camera-to-world xyzw quaternion and ARKit-style camera axes are **hypotheses**, explicitly recorded in each report.
- Sampled at most 32 evenly spaced depth frames by default and every fourth depth pixel, retaining only confidence codes 1–2, depths 0.25–6 m, and pixels without a large local depth discontinuity. The confidence ordering follows [Stray's format document](https://github.com/strayrobots/scanner/blob/main/docs/format.md). RGB is not paired to depth, so none of this uses RGB evidence.
- Each LiDAR `process-capture` run now writes `lidar_points.ply` and `lidar_geometry.json` alongside the common contract. The report records source frame IDs, filter counts, coordinate extents, horizontal-surface candidates, and pose jumps. The property-plan JSON remains unresolved because no tape check has established the projection's metric correctness.

## Evidence

| Scan | Run | Selected frames | Retained points | Finding |
| --- | --- | ---: | ---: | --- |
| Owner `dummy_room` | `run-01fd33c3c05f46898405b4c0612f6625` | 16 of 570 | 46,085 | Horizontal candidates concentrate around y ≈ −0.8 m, but spread across several bins; no accepted floor plane. Largest consecutive pose step: 0.0054 m. |
| Starter with ceiling | `run-248165bb876246eca0f7055102de8793` | 24 of 9,745 | 71,692 | Candidate y heights are dispersed, so a defensible ceiling height cannot yet be reported. |

Runs and point clouds are under `/tmp/roomproof-phase3-runs`. They are development diagnostics, not scored room plans.

## Remaining gates

- **T24:** Check axis convention, camera-to-depth calibration, and point distances against a known tape-measured target. Do not mark complete from point-cloud appearance.
- **T25–T26:** Fit planes and openings robustly enough to make a consistent room plan. Current horizontal candidates are exploratory only.
- **T27–T28:** Obtain and process a complete multiroom capture; implement transitions and drift correction with an on/off ablation.
- **T29:** Expand tracking and depth-quality warnings into actual glass/mirror/low-light/ceiling coverage diagnostics.
