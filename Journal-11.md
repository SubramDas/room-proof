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
