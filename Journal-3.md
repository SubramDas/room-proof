# Journal 3 — LiDAR geometry and drift

## Flat-805 matched scan update — 2 October 2026

The owner supplied `Flat-805-lidar/flat_805.zip`. The archive SHA-256 is
`c5bf24265bff21a150e36ed9ce1c2c784eb111d3362e6c66e0458f21fe548950`.
An extracted copy in `/tmp/roomproof-flat805-lidar/7a3183a649` matched all
6,608 archive files byte for byte. Audit run
`run-413b2a445fe1417c9a83edd02a97628d` found 3,302 pose/depth/confidence
frames and 3,301 decoded RGB frames. Pose timestamps span 110.04 seconds; RGB
metadata reports 55.02 seconds, a near-exact 0.5 ratio. The revised audit
warns against time-based RGB/pose alignment. Process run
`run-0292663a46e44a7ba792dfcc5cbc72ee` completed in 26.78 seconds with a
schema-valid unresolved plan and 20,730 provisional depth points. Seventeen
of 32 sampled frames retained fewer than 500 points. No room dimensions,
drift correction, or measured-scale claim follows from this run.


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
