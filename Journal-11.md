# Journal 11 — Model candidate pipeline

Status: partial as of 2 October 2026. Added a local, optional, bounded CPU
semantic candidate stage to `process-capture` for photo and standalone video.
It writes versioned, source-linked `visual_candidates.json` and mask PNGs;
the plan records proposal counts but does not promote them to verified
openings, links, or measurements. Missing weights and inference errors are
reported as `unavailable`; LiDAR RGB is gated as
`skipped_rgb_pairing_unresolved`. The stage is off by default and can be
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
RGB/depth/pose correspondence for Stray; candidate association, merging,
rejection, and placement optimization; metric validation and calibrated
intervals; visible damage examples; untouched all-tier evaluation. Current
photo and video plans remain unresolved. A model-on run producing proposals
does not satisfy the scored benchmark or show final-plan improvement.

The owner subsequently confirmed the bedroom–hall and toilet–hall doorways
face each other and that the open kitchen doorway connects to the hall.
These development labels are in `docs/model_label_review.md`. A hall-only
model-on run across the seven `room-hall` photos, `hall.mp4`, and `hall.zip`
is documented in `reports/hall_model_pipeline.md`. Photo/video plans remain
unresolved; LiDAR produces the same provisional single-hall geometry and
skips RGB model inference because exact pairing remains unresolved. The
private output bundle is under ignored `runs/`.
