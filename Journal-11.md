# Journal 11 — Model candidate pipeline

Status: partial as of 2 October 2026. Added a local, optional, bounded CPU
semantic candidate stage to `process-capture` for photo and standalone video.
It writes versioned, source-linked `visual_candidates.json` and mask PNGs;
the plan records proposal counts but does not promote them to verified
openings, links, or measurements. Missing weights and inference errors are
reported as `unavailable`. LiDAR RGB inference now runs independently, with
timing and sampled spatial registration reports that gate any wall link. The stage is off by default and can be
compared with the no-model path through the same CLI.

The selected pilot is quantized SegFormer B0 ADE20K on ONNX Runtime CPU.
Weights, dependencies, preprocessing, component extraction, and license are
recorded in [docs/dependencies.md](docs/dependencies.md) and
[docs/visual_candidates.md](docs/visual_candidates.md). Its noncommercial
research/evaluation license prevents production adoption as-is.

The paired photo/video run IDs, source revisions, timings, proposal counts,
and observed misses/false positives are in
[reports/model_candidate_pilot.md](reports/model_candidate_pilot.md).
Owner review items are in [docs/model_label_review.md](docs/model_label_review.md).
The first photo attempt exposed a room-level MP4 inside `Flat-805/`; the
pilot copied only the JPEG stills to a temporary photo input tree. Original
captures remain untouched.

Open: owner-reviewed labels and splits; precision/recall and wall/door
association scoring; a model choice justified by accuracy and license;
full-frame RGB/depth/pose correspondence for Stray; candidate association, merging,
rejection, and placement optimization; metric validation and calibrated
intervals; visible damage examples; untouched all-tier evaluation. Current
photo and video plans remain unresolved. A model-on run producing proposals
does not satisfy the scored benchmark or show final-plan improvement.

The owner subsequently confirmed the bedroom–hall and toilet–hall doorways
face each other and that the open kitchen doorway connects to the hall.
These development labels are in `docs/model_label_review.md`. A hall-only
model-on run across the seven `room-hall` photos, `hall.mp4`, and `hall.zip`
is documented in `reports/hall_model_pipeline.md`. Photo/video plans remain
unresolved. The first LiDAR run skipped RGB model inference; the later
implementation extracts RGB proposals and checks sampled RGB/depth alignment.
The latest hall run `run-d421e1bc9d614527af63cfb6703dbfde` supported
depth offset +1 from image boundaries. Its two door proposals miss the
provisional depth-gap location, so the hall plan retains an unverified
doorway. See `reports/lidar_rgb_candidate_integration.md`. Private run files
remain under ignored `runs/`.

## Mixed RGB and LiDAR pilot — 3 October 2026

Added optional OWLv2 Base with a pinned local checkpoint and SHA-256, fixed
text prompts, CPU provenance, an explicit hall RGB display rotation, and raw
pixel back-mapping. LiDAR candidate links now inspect the paired depth and
confidence inside each box, compare rays with fitted walls and depth gaps,
record conflicting/missing returns, and require repeated qualified views.
The first unrotated OWLv2 run promoted broad sideways boxes; replay through
the corrected height and box-size gates removes that support. The corrected
90° run is documented in `reports/hall_mixed_pipeline.md` with exact commands,
run IDs, model versions, source hashes, runtime, and failure counts.

Current hall plan: 3.926 × 3.3958 m, 2.7682 m height, one provisionally
inferred open passage of 0.705 m depth-gap width and unknown height. Laser
errors remain +0.026, +0.1858, and -0.0718 m. OWLv2 added opening evidence
but did not change measurements. The selected 12-frame run took 367.5 s and
about 2.3 GiB peak RSS; 147 boxes were proposed, only 7 boxes supported the
single opening after geometric gates, and many remain unresolved. Schema and
semantic plan validation passed. The hall scan had no verified pose closure,
so the exported trajectory was not corrected.

Next: inspect hall short-side and ceiling surface support without using laser
values during fitting; record plane residuals, per-frame support, alternative
wall fits, and confidence-weighted multi-view fusion. Audit pose/IMU timing
and drift evidence before adding independent VIO. Compare raw/corrected
geometry and model on/off against held-out laser measurements. Owner-reviewed
opening labels and an untouched property capture are still needed to score
candidate precision/recall and interval coverage. ESANet and SAM 2 remain
unadopted candidates; photo/video geometry, property placement, and damage
evaluation remain unresolved.

## Measurement diagnostic continuation — 3 October 2026

After the OWLv2 checkpoint was pushed, added `lidar_pose_audit.json` and
`lidar_surface_diagnostics.json` to the same LiDAR command. The pose audit
records timestamp continuity, nearest IMU timing, camera motion, quaternion
norms, and verified closure count without claiming new VIO. The surface
diagnostic preserves per-frame wall and horizontal-surface estimates,
confidence-weighted within-frame medians, equal-frame aggregate alternatives,
support counts, and residuals. It flags unstable wall support in the plan.

The hall run `run-f701a6cf5c9241cd8792b2be12c91713` found no verified
closure and one unstable wall (axis 1, side 1). Existing room lengths remain
3.9260 × 3.3958 m. A frame-balanced diagnostic would produce
3.9308 × 3.4133 m, making the short-side laser error worse (+0.2033 m versus
+0.1858 m). It was therefore **not** promoted into the plan. See
`reports/hall_measurement_diagnostics.md` for exact metrics and command.

## Standalone video full-sequence correction — 3 October 2026

The owner clarified that the ordinary property video is independent of the
LiDAR scan's own `rgb.mp4`. The previous overview conflated their roles.
Changed `coarse_scene_profile` to stream every decoded standalone-video
frame, with no 180-second or one-frame-per-second cap. The resulting
`visual_geometry.json` records source frame index, nominal-FPS timestamp,
brightness, dark-pixel fraction, pixel change, appearance change, and
possible scene changes. `quality_report.json` records the full-sequence frame
count and candidate scene-change count. This supplies output from the full
clip while leaving expensive feature matching and optional model inference
explicitly bounded. It does not infer a metric building structure or a
verified room transition. The photo/video candidate model remains optional;
no learned structured-LiDAR building-reconstruction model is in the live
path. A full-sequence model/geometry integration and new-capture evaluation
remain open.

Ran the new standalone-video path on `Flat-805/IMG_0031.mp4` as
`run-6916bb2cc05e4c1787160f703975ccd5` with the visual model off. All
3,328 decoded frames contributed to the 64×48 timeline. It recorded one
large appearance-change candidate at source frame 1848 (nominal 61.6 s,
score 61.94), while the bounded 24-frame matcher recorded 11 supported
overlaps and 7 tracking gaps. The run completed `valid_low_confidence`; its
plan correctly remains unresolved, with no verified room transition,
adjacency, or metric scale. `visual_geometry.json`, `quality_report.json`,
and the plan remain in the ignored run directory. This is a functional
full-sequence output, not evidence that the scene-change candidate is a
doorway.

## Kitchen first integration slice — 3 October 2026

The owner supplied `kitchen/` with eight photos at the root, a standalone
video, and a Stray ZIP. Added explicit `--room-id` support for root-level
single-room photo collections without reading the top-level video or ZIP as
photo input. Processed the three captures independently. The kitchen video
has 1,270 decoded frames and a full-sequence timeline. The LiDAR run inferred
a provisional 2.4909 × 2.3777 m rectangle, 2.7781 m height, and one
unverified 0.697 m depth gap. These runs finished before kitchen reference
measurements were supplied.

Added `link-captures` and `roomproof/cross_capture.py`. They read prior run
artifacts, compare bounded photo/video/scan-RGB views, preserve source refs
and optional model proposals, and write `cross_capture_links.json` plus an
observation-only `visual_room_graph.json`. The command requires at least nine
scan RGB views because fewer cannot satisfy the existing RGB/depth
registration gate. Kitchen's 12-view run supported the scan's +1 sampled
RGB/depth frame offset and found five video-to-scan RGB 2D overlaps; no
photo cross-capture pair passed the current matcher. This is not a 3D
transform or room adjacency.

OWLv2 proposed 200 boxes on eight kitchen photos and took 386.97 s for its
CPU model stage; many were cabinet-door or passage boxes. The existing
SegFormer evaluation pilot produced 106 wall/floor/ceiling/door/window
regions on 24 standalone-video samples. Candidate labels and physical
opening identity have not been reviewed. See
`reports/kitchen_pipeline_pilot.md` for all run IDs and commands.

The later scan RGB OWLv2 run proposed 171 boxes across 12 frames. Of its 92
opening-like boxes, 49 projected to a fitted wall and 36 coincided with a
depth gap, but none passed the structural-opening confirmation gate. A fresh
link run with all three model runs again found five video-to-scan RGB image
overlaps, zero photo links, and no metric cross-capture transform or inferred
adjacency. Separately, the owner supplied independent kitchen spans 2.36 and 2.30 m,
height 2.80 m, and hall-facing passage width 2.26 m. Sorted-span LiDAR errors
are +0.1309 and +0.0777 m; height error is −0.0219 m. The detected 0.697 m
gap lacks a verified identity and the detector's 1.6 m maximum excludes the
2.26 m passage in that initial run. A later general candidate ceiling of
3.2 m still did not detect the passage. The reference values were used only for comparison, never
as pipeline input. Kitchen is now development evidence, so changed rules
need a separate untouched evaluation capture.

## Kitchen learned correspondence and fused plan — 3 October 2026

Implemented optional CPU ALIKED/LightGlue matching with pinned source and
weight hashes. The linker retains patch-match results on the same pairs,
epipolar inliers, matched source pixels, provisional depth-backed PnP
hypotheses, and locally supported opening-box links. It writes separate
2D, registration, opening, and room-graph reports plus a schema-valid fused
property plan and SVG. The standalone video processes all decoded frames
in its coarse scene timeline before selecting detailed windows. Unverified
LiDAR gap width and type now remain unknown in the plan.

Ran OWLv2 on all eight kitchen photos, 12 selected standalone-video frames,
and 12 scan-RGB views, along with 128 selected depth frames. An earlier
learned linker run is `run-dc79cc91e51243fab3100e1018dfb6a3`. It found
148 supported 2D view pairs from 336 tests, compared with five for the
patch matcher on the same model-on source runs. It produced 52 constrained
opening-region links in 19 unverified groups and three consistent pose
hypotheses under assumed camera focal lengths. None established calibrated
metric registration or adjacency. The owner later identified kitchen
`IMG_0004.jpeg` as showing both edges of the hall-facing 2.26 m passage.
One model box roughly covers that visible passage, but its jambs were not
registered to the LiDAR wall. That plan retained the 2.4909 × 2.3777 m
provisional kitchen fit, 2.7781 m height, and an unresolved opening with
null width. The serial model-on pass took 1,081.65 s (18.0 min) on this
CPU, above the 15-minute target. See
`reports/kitchen_pipeline_pilot.md` for run IDs, errors, and limits.

## Visual map, irregular LiDAR, registration, and assembly pass — 3 October 2026

Implemented stages 2–6 as evidence-gated paths. `video_temporal.py` decodes
every standalone-video frame for low-resolution image motion and tracks
opening-region texture between model-selected views. `visual_odometry.py`
estimates sparse, arbitrary-scale camera motion on adjacent selected views.
The visual graph now records opening tracks, possible transitions, room
label hypotheses, and explicit unknown adjacency. `room_transitions.py`
can accept a crossing only when calibrated video poses straddle a registered
LiDAR opening on one wall.

`lidar_irregular.py` fits a convex multi-wall boundary only when every side
has repeated depth-plane evidence. The existing rectangular fit remains
available, while unsupported concave or multiroom geometry stays unknown.
Depth gaps now preserve left/right 3D edge locations, supporting frames,
behind-wall evidence, and grid quantization. Width enters the plan only
after repeated edge support and consistent registered RGB evidence.

`metric_registration.py` now accepts optional explicit camera intrinsics
and a scan-RGB-to-depth pixel mapping, checks 3D landmark spread and
held-out PnP error, and seeks agreement across separated scan views.
`registered_openings.py` compares ordinary-image jamb rays with the same
LiDAR wall gap. `assemble-property` combines separate linked room scans
only through shared calibrated opening evidence; its placement solver checks
widths, opposing wall directions, overlap, and inconsistent connection
cycles. An unplaced room retains local measurements but no property-frame
boundary. A synthetic two-room fixture passed one supported connection,
nonoverlapping placement, adjacency, and schema validation. Controlled
synthetic 3D landmarks also passed calibrated PnP across two separated scan
views, registered opening-ray agreement, and the wall-crossing gate. These
exercise implementation branches, not real-property accuracy.

The final kitchen LiDAR run is `run-8bc96a7785874b168c202b0c681dee2a`;
the linker run is `run-dbe819d692074d83af4d698741ff5786`. It matched
172 of 375 2D view pairs; all 1,270 video frames contributed to optical
flow, seven opening segments had image-region continuity, and seven sparse
motion edges had arbitrary scale. The irregular fit was rejected for an
unsupported edge. No calibrated metric registration, wall crossing,
adjacency, or 2.26 m hall-facing width was accepted. The fused kitchen
plan remains schema-valid with provisional 2.4909 × 2.3777 × 2.7781 m
geometry and an unresolved opening. Updated serial model-on time is
1,076.13 s (17.9 min). Exact stage counts and limits are in
`reports/kitchen_pipeline_pilot.md`.
