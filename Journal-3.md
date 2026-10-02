# Journal 3 — LiDAR geometry and drift

## Hall-first working pipeline — 2 October 2026

The user prioritized a complete output pipeline over reducing the current measurement error. The hall-only archive `Flat-805/room-hall/hall.zip` was processed through the normal `process-capture` command with `--room-id room-hall --room-kind connector --max-lidar-frames 128`. Run `run-e36d1c3019d94640b77f890eaaa466f9` in `/tmp/roomproof-hall-pilot/` completed in 89.28 seconds with `valid_low_confidence` input and schema/semantic-valid `property_plan.json` and `property_plan.svg`. It selected 128 frames, retained 366,019 filtered 3D points, inferred four wall lines, a floor and ceiling, a 13.3319 m² hall footprint, and a 2.7682 m ceiling height. The rectangle sides are 3.926 m and 3.3958 m. Each surface has depth/pose source references and every numeric measurement keeps an unbounded interval pending calibration.

The scan's corrected projection uses positive-Z-forward vision camera coordinates before the exported camera-to-world quaternion. This resolved the previous broad vertical extent and allowed horizontal floor/ceiling bands and perpendicular wall directions to support a single-room fit. A depth gap now flows into the common plan as one possible door on wall 1, width 0.705 m and offset 2.919 m, with unknown height and `unresolved` status. No RGB or occlusion check confirms it. The owner laser values, held separate from inference, are 3.90 m × 3.21 m × 2.84 m; resulting side errors are +0.026 m and +0.1858 m, and height error is −0.0718 m. Accuracy tuning is deferred. See `reports/hall_pilot.md` for the hall-first results.

T24 and T25 have a working single-room acceptance example. T26 still needs RGB confirmation, full opening height and windows; T27 needs automatic multiroom room placement and adjacency; T28 needs on/off stitched **room** footprints rather than point-coverage cells; T29 needs material-specific failure warnings and affected intervals. These remain open. The hall run found no verified same-view revisit, so no hall drift correction was applied.

## Replacement Flat-805 scan — 2 October 2026

The owner replaced `Flat-805-lidar/flat_805.zip` with a different recording (SHA-256 `2cd6e14c1b89f7dea502200b79e67eafabe0c8c0c75eff83b4b69dfef02068da`). The original archive was not modified by analysis. The new ZIP has 9,745 depth/confidence/pose frames and 9,744 decoded RGB frames, versus 3,302/3,301 in the earlier ZIP. The extracted copy at `/tmp/roomproof-flat805-lidar-new/c7d28f72c6` was byte-verified against the new ZIP; audit run `run-c1a65000dfea4ce6af2f7335a3af8f1e` reports 214.93 s of poses and 214.92 s of video. The earlier scan's near-0.5 video/pose duration ratio is gone. Exact RGB frame offset is still unknown because one frame is missing and the export lacks per-frame video timestamps.

The new recording has much stronger depth coverage: a 32-frame diagnostic retained 97,527 points and had zero frames below the 15% retained-pixel threshold (the earlier 32-frame run had 33,044 points and 11 weak frames). It also has pose-near, similarly oriented returns around frames `000000` and `005130`. The original quality-only sampler missed the first return view, so it reported no verified closure. The sampler now reserves up to six of its bounded frame slots for pose-return candidates, while still requiring 3D overlap before any correction.

Full one-command run `run-8fc39dd03f79458faeee4b4d7b6175e1` used the new sampler, selected 32 frames, retained 96,525 points, and produced schema-valid JSON and SVG in 220.78 s. It verified one same-view constraint: frames `000000` and `005130`, 1,567 nearby 3D point matches, 0.571 overlap fraction, 0.0351 m median residual spread, and a 0.0565 m estimated translation correction. With drift **on**, occupied-depth-cell area changed from 34.29 to 34.23 m². A matched drift **off** diagnostic using the same frame index and selection kept 34.29 m² before and after. The 0.06 m² difference is a quantitative point-coverage ablation, **not** a measured property footprint or proof of absolute drift accuracy.

The new plan still contains one unresolved room entry. No room boundaries, transitions, openings, or calibrated wall/ceiling dimensions were inferred. Floor support remains weak, and a tape-linked wall is still needed to check scale and axes. T24–T29 therefore remain open at their full acceptance gates, although the new scan makes real drift correction possible.

## Drift and quality diagnostic update — 2 October 2026

Added `--lidar-drift on|off` (default `on`). A correction is applied only when sampled views are separated by at least 20 seconds, have poses within 0.4 m and orientations within 30°, and share enough nearby 3D points for a stable translation constraint. A single accepted translation is distributed between the revisit frames. Both modes record the raw and resulting 10 cm occupied-depth-cell footprints and write a second PLY. These cells are diagnostic point coverage, not a stitched property footprint or room boundary. The algorithm is checked on synthetic same-view and disjoint-view cases in `tests/test_lidar_drift.py`; the synthetic scale check does not replace a tape check.

Flat-805 paired runs used the same extracted scan and 32 sampled frames. With correction **off**, run `run-29a6221758b0469e83642c4750919a48` completed in 34.77 s. With correction **on**, run `run-9a3f63f7e5524db487e8638281af8fd6` completed in 43.15 s. Both retained 33,044 points, found zero verified same-view closure constraints, and reported 21.34 m² of occupied depth cells both before and after correction: **0.00 m² change**. Both wrote schema-valid plans that remain a single unresolved room entry. Eleven sampled frames retained under 15% of sampled pixels. Lower horizontal evidence did not meet the current multi-frame support threshold. This is a measured null ablation, not evidence that drift is absent or that a multiroom plan is complete.

The frame report now includes rejected-depth counts and weak-depth frame IDs. The plan and quality report carry the corresponding warnings. Reflective materials, low light, true room transitions, walls, openings, and ceiling height still lack validated detection. The floor/ceiling warning reports weak horizontal support without assigning floor or ceiling identity from normal sign alone. T24–T29 remain open at their stated acceptance gates; the new diagnostics are marked only as substeps in `TASK.md`.
The current wall-candidate audit also warns when it lacks two strongly supported perpendicular directions, because a single dominant direction cannot establish room corners.

The later `run-98abb22496f84e4e90e8ee80a66bfca1` (48.34 s) adds a scan-level RGB brightness audit: 32 evenly spaced decoded RGB frames, zero with median luminance below 40/255. This does not align those RGB frames with individual depth frames and cannot rule out local shadow or reflective material failures. A failed development run `run-85f7689f4be3444bbb814cdcf9d37394` caught an unexpected three-channel decoder output and was followed by the corrected run; no benchmark result uses the failed output.

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
- Initially sampled at most 32 evenly spaced depth frames and every fourth depth pixel, retaining only confidence codes 1–2, depths 0.25–6 m, and pixels without a large local depth discontinuity. The confidence ordering follows [Stray's format document](https://github.com/strayrobots/scanner/blob/main/docs/format.md). RGB is not paired to depth, so none of this uses RGB evidence.
- After the Flat-805 audit exposed weak evenly spaced frames, changed the selection to one frame from each evenly spaced time window, choosing the strongest raw depth/confidence coverage among up to four deterministic candidates. Run `run-666042b95394415587b2ec66455ca306` retained 33,044 points versus 20,730 before, with weak selected frames falling from 17 to 11 of 32; processing rose from 26.78 to 28.88 seconds. Selection probes and chosen frame IDs are saved in `lidar_geometry.json`.
- Added frame-supported horizontal height bins and vertical plane-normal/distance bins. Run `run-f88a07cf2db14f21ac58eb71c77559ac` records 12,627 vertical-patch samples and explicit supporting frame IDs for wall-like candidates. Multiple 1.35–1.8 m upper horizontal bands appear, while lower horizontal evidence is dispersed. Furniture and pose/depth alignment can produce such bands; no wall, floor, ceiling, or height has been promoted into the plan.
- A denser 128-frame diagnostic run `run-f40d8101c36e41f4b0f138397a8a6e7d` retained 118,242 points in 63.30 seconds. Lower horizontal candidates remained spread over roughly −0.8 to 0.05 m. More samples alone did not establish a common floor plane.
- Added a bounded pose-return diagnostic for frame pairs at least 20 seconds apart. Run `run-07c0e07ced594ab29a1afc9eced34642` shows that the Flat-805 trajectory ends 3.80 m from its start. It returns within 0.4 m of several earlier positions, but none of the sampled return pairs also faces within 45° of the earlier view. This is not a verified loop closure; drift correction still needs matched geometry or a new capture with a clear revisit. The report records frame pairs and orientations without modifying poses.
- Each LiDAR `process-capture` run now writes `lidar_points.ply` and `lidar_geometry.json` alongside the common contract. The report records source frame IDs, filter counts, coordinate extents, horizontal-surface candidates, and pose jumps. The property-plan JSON remains unresolved because no tape check has established the projection's metric correctness.

## Evidence

| Scan | Run | Selected frames | Retained points | Finding |
| --- | --- | ---: | ---: | --- |
| Owner `dummy_room` | `run-01fd33c3c05f46898405b4c0612f6625` | 16 of 570 | 46,085 | Horizontal candidates concentrate around y ≈ −0.8 m, but spread across several bins; no accepted floor plane. Largest consecutive pose step: 0.0054 m. |
| Starter with ceiling | `run-248165bb876246eca0f7055102de8793` | 24 of 9,745 | 71,692 | Candidate y heights are dispersed, so a defensible ceiling height cannot yet be reported. |

Runs and point clouds are under `/tmp/roomproof-phase3-runs`. They are development diagnostics, not scored room plans.

## Remaining gates

- **T24:** Check axis convention, camera-to-depth calibration, and point distances against a known tape-measured target. Do not mark complete from point-cloud appearance.
- Flat-805 room-level laser dimensions are now available in an ignored reference file, but no wall/room correspondence has yet been inferred, so they cannot validate the projection by themselves.
- **T25–T26:** Fit planes and openings robustly enough to make a consistent room plan. Current horizontal candidates are exploratory only.
- **T27–T28:** Obtain and process a complete multiroom capture; implement transitions and drift correction with an on/off ablation.
- The Flat-805 multiroom capture has now been processed; pose proximity alone has not provided a trustworthy loop-closure constraint.
- **T29:** Expand tracking and depth-quality warnings into actual glass/mirror/low-light/ceiling coverage diagnostics.
