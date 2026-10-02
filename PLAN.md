# RoomProof visual structure and LiDAR measurement plan

Status: implementation plan, 3 October 2026. The existing code is a partial
pipeline; model choices below are candidates until compared on labelled
captures. `TASK.md` remains the detailed work tracker.

## Intended result

The ordinary property video and room photos provide evidence for visible room
structure: surfaces, openings, repeated views, room transitions, and possible
adjacency. Each LiDAR scan provides metric evidence for surfaces and openings
it actually covers. These are independent captures; the standalone video is
not the scan's `rgb.mp4`. The scan's RGB may help register its own depth and
match shared views across captures, but no cross-capture timing relationship
may be assumed. A final property plan requires visual correspondence and
geometric agreement. A visual detection alone cannot establish a measured
length, a room connection, or a complete property layout.

## Implementation order

### 1. Build the visual room map

- Consume every decoded standalone-video frame in order for a lightweight
  quality, motion, and scene-change timeline. This is already present at
  64×48 in `visual_geometry.json`; the Flat-805 clip has 3,328 source frames.
  Use this full timeline to select trackable keyframes and short windows near
  possible doorway crossings. Keep their source frame IDs and times. Run
  expensive models on documented keyframes/windows unless a measured runtime
  budget supports denser inference.
- Index every room photo under its `room-*` source folder. Detect visible
  walls, floor/ceiling boundaries, doors, doorways, windows, and open
  passages in photos and selected video frames. Preserve boxes or masks,
  source pixels, model/version/hash, and rejected candidates in
  `visual_candidates.json`. Review occluded and ambiguous views.
- Match features across video keyframes, room photos, and candidate doorway
  views. Estimate relative camera motion and sparse visual geometry; retain
  track breaks and competing matches. Treat appearance changes as possible
  transitions only. Group repeated sightings of the same physical opening
  and propose room connections from a continuous crossing or two-sided
  doorway correspondence. Folder IDs are labels, not adjacency proof.
- Output a visual room graph with room hypotheses, opening hypotheses,
  supporting frame/photo IDs, conflicts, and unresolved connections. It may
  have arbitrary scale until registered to metric evidence.

### 2. Build metric geometry from each LiDAR scan

- Read depth, confidence, intrinsics, exported poses, timestamps, IMU, and
  the scan's own RGB. Preserve raw frame IDs and coordinate assumptions.
  Audit pose continuity and RGB/depth registration; use corrected poses only
  where a verified geometric constraint supports the correction.
- Fuse confidence-filtered depth from overlapping views. Fit competing
  floor, ceiling, and wall planes, corners, and possible wall gaps, recording
  supporting frames, residuals, occlusions, and weak/transparent surfaces.
  The current hall rectangle is a baseline; do not force a rectangle on
  irregular or multiroom scans.
- Derive wall lengths, room area, ceiling height, and opening width/offset
  from supported 3D geometry. Doorway height remains unknown until its
  vertical boundaries are supported. A hall-only scan cannot directly
  measure unscanned walls inside the bed, toilet, or kitchen rooms.

### 3. Register the independent captures

- Match the standalone video and photos to the LiDAR scan's RGB using shared
  features, surfaces, and openings. Estimate a visual-to-LiDAR transform from
  geometrically consistent matches; record inliers, reprojection error,
  spatial coverage, and alternative transforms. Do not pair frames by index
  or wall-clock time across captures.
- Anchor the visual room graph at the verified hall geometry. Accept an
  opening or room placement only when its visual identity agrees with a
  measured wall/gap and independent views. Reject a transform supported only
  by repeated texture, one ambiguous doorway, or incompatible room geometry.
  Keep an unresolved link when overlap is insufficient.
- Start with the hall openings visible in its photos, walkthrough, and scan
  RGB. Then test the owner-confirmed hall connections to bed, toilet, and
  open kitchen. Those owner labels are evaluation/reference evidence, not
  automatic prediction inputs.

### 4. Assemble the property plan

- Optimize room placements subject to accepted doorway correspondences,
  measured walls, plausible shared boundaries, and non-overlap constraints.
  Preserve multiple layouts or unknown connections where constraints do not
  identify a unique solution.
- Write the common `property_plan.json` and SVG with stable room/surface/
  opening IDs, source references, model and geometric evidence, inferred or
  unresolved statuses, warnings, and measurement intervals. Keep model
  scores distinct from calibrated physical uncertainty.

### 5. Evaluate each stage and the final plan

- Compare model-on and model-off outputs on the same labelled frames. Score
  visible opening and surface candidates, matched doorway identity, visual
  camera/room graph, cross-capture registration, final adjacency, metric
  dimensions, unknown rate, runtime, and memory separately.
- Keep laser/tape values out of prediction input. Use the hall's separate
  3.90 × 3.21 × 2.84 m values only for scoring, then repeat on an untouched
  capture. Calibrate finite intervals only from independent held-out data.
  A schema-valid plan with unresolved structure is an honest incomplete
  result, not evidence of reconstruction success.

## Free local component candidates

"Free" here means downloadable for local use with no paid API. License,
checkpoint terms, model size, CPU speed, and commercial suitability are
separate checks. Pin every adopted checkpoint and record its file hash.

| Role | Candidate | Fit and decision |
| --- | --- | --- |
| Visible doors, doorways, passages, windows in photos/video/scan RGB | [OWLv2 Base](https://huggingface.co/google/owlv2-base-patch16-ensemble) | Apache-2.0 model card; already integrated as an optional local candidate adapter. It produces boxes, not walls or a floor plan. The hall pilot needed 242 s CPU inference for 12 frames and many boxes were unverified. Benchmark on reviewed labels before using it for the visual room graph. |
| Alternative visual interpretation | [Florence-2 Base](https://huggingface.co/microsoft/Florence-2-base) | MIT model card; offers detection, phrase grounding, and region descriptions. Compare on the **same** doorway and wall labels if OWLv2 misses structural cues. Its generated descriptions are hypotheses and its local code/dependencies need inspection and pinning. Do not make both models mandatory. |
| Cross-view feature detection and matching | [ALIKED + LightGlue](https://github.com/cvg/LightGlue) | ALIKED is BSD-3-Clause and LightGlue code/weights are Apache-2.0 per the maintainers. Candidate for linking video/photo/scan RGB views and doorway identity. Start with the current feature matcher as a CPU baseline and measure whether learned matching improves verified correspondences. Avoid the original SuperPoint weights, which have different restrictive terms. |
| Camera poses and sparse visual geometry | [COLMAP/pycolmap](https://github.com/colmap/colmap) | BSD-licensed structure-from-motion software, not a learned model; can reconstruct ordered or unordered views. Check bundled dependency licenses for the exact distribution. Run on selected keyframes plus photos, not every nearly identical video frame. Monocular output has no guaranteed metric scale. |
| Relative depth cues from ordinary images | [Depth Anything V2 Small](https://github.com/DepthAnything/Depth-Anything-V2) | Small checkpoint is Apache-2.0 and predicts relative depth. Optional cue for occlusion and rough plane ordering; never use it directly as a meter reading. Larger Base/Large/Giant checkpoints have noncommercial terms. |
| Semantic surfaces on paired scan RGB and depth | [ESANet](https://github.com/TUI-NICR/ESANet) | Apache-2.0 source; pretrained RGB-D indoor segmentation is a candidate after verified RGB/depth pairing. Audit the exact checkpoint and label mapping. It may distinguish wall/floor/ceiling but cannot by itself provide room placement or precise doorway geometry. |
| Refine a selected opening/surface region | [SAM 2 Hiera Tiny](https://github.com/facebookresearch/sam2) | Apache-2.0 checkpoints and code. Optional box-prompted mask or video propagation after another component finds the feature. It does not classify an opening or measure it. Adopt only if boundaries improve the final plan within CPU budget. |
| Metric point-cloud registration and planes | [Open3D](https://github.com/isl-org/Open3D) | Geometry library, not an AI model. Candidate for verified alignment, plane fitting, and fusion; compare with current fit on held-out measurements. |

The current quantized SegFormer pilot has evaluation-only terms; it remains
outside a commercial live path. Do not choose [DUSt3R](https://github.com/naver/dust3r)
as the default live reconstruction path because its released license is
noncommercial. [VGGT](https://github.com/facebookresearch/vggt) has a
separate commercially usable checkpoint with access conditions, while the
original checkpoint remains noncommercial; its 1B-parameter size also makes
it an unsuitable first CPU baseline. These may be research comparisons only
after exact terms and hardware needs are checked.

## First implementation slice

1. Freeze annotated hall photo/video/scan-RGB doorway correspondences and
   false-opening negatives, with source IDs. Keep the owner-confirmed
   connections out of model input.
2. Compare the current feature matcher with ALIKED + LightGlue on those same
   views; pass verified matches into a sparse camera/room graph. Use
   COLMAP/pycolmap only if enough nondegenerate view overlap survives.
3. Run existing OWLv2 on selected hall views; compare Florence-2 Base only
   if reviewed labels show a relevant detection gap. Group repeated doorway
   proposals and carry unresolved alternatives.
4. Register the hall visual graph to the scan using matched scan RGB and
   measured wall/gap geometry. Record failure reasons and keep the graph
   unscaled if this match cannot be verified.
5. Produce one fused hall plan and one visual-only result, compare both with
   the current model-off and mixed hall runs, then extend to the other rooms
   when their visual connections and metric coverage justify it.

No new component in this table is adopted merely because its model card
lists a free license or a benchmark on another dataset. The deciding result
is whether it improves RoomProof's labelled candidate and final-plan
accuracy within the local CPU and memory budget.

## First kitchen implementation checkpoint

The new single-room root-photo reader accepts `kitchen/` with the explicit
`--room-id room-kitchen`; the standalone video and ZIP remain separate
captures. `link-captures` produces source-linked 2D correspondence hypotheses
and a visual observation graph from completed photo, video, and LiDAR runs.
It attaches any existing image-model opening proposals but does not infer
adjacency or a cross-capture metric transform. The kitchen pilot and exact
run IDs are in `reports/kitchen_pipeline_pilot.md`.

The initial patch matcher found video-to-scan RGB overlap but no passing photo
links. A later learned-matcher run improved 2D correspondence coverage.
Kitchen LiDAR yielded a provisional room fit and
one unverified gap. The owner later supplied independent spans 2.36 and
2.30 m, height 2.80 m, and hall-facing passage width 2.26 m. The provisional
span errors are +0.1309 and +0.0777 m and the height error is −0.0219 m;
the opening remains unidentified and unmeasured. The photo OWLv2
pilot generated many unreviewed boxes and took about 6.6 minutes for eight
photos on CPU, so candidate quality and runtime remain adoption gates.
The scan RGB OWLv2 pilot produced 171 boxes but no confirmed structural
opening. The patch-model graph retained five video/scan-RGB 2D matches
without a metric transform or inferred adjacency. Kitchen is development
evidence for changes made after receiving its reference values; evaluate
those changes on a different untouched capture.

## Kitchen mixed-pipeline implementation pass

The video reader now analyzes the full decoded sequence before choosing its
bounded high-resolution windows, reserving windows near strong appearance
changes when present. The kitchen video had no strong appearance-change
candidate, so its 24 detailed samples still cover the timeline. OWLv2 is
available for photo, video, and selected scan RGB candidate generation.

`link-captures --match-backend aliked-lightglue` now uses pinned local
ALIKED/LightGlue weights. It keeps the original patch-matcher result for the
same pairs, checks learned correspondences with a fundamental-matrix RANSAC,
and records source pixels and model hashes. A separate registration report
uses confident paired scan depth to probe camera poses and checks
reprojection on held-out points and agreement across separated scan views.
Unknown intrinsics of the independent photo/video camera and uncalibrated
scan RGB/depth extrinsics keep these poses provisional. Model opening boxes
are linked across views only when local matched keypoints fall inside both
regions; this is a candidate identity, not an accepted opening or adjacency.

The combined command now writes an observation graph, registration and
opening-correspondence reports, and a schema-validated fused property plan.
Only LiDAR-supported surfaces carry metric values. A depth gap without
independent structural confirmation has unknown opening type and width in
the plan; its raw width hypothesis remains in `lidar_geometry.json`. Rooms
without verified metric placement remain unresolved. This implements the
conservative data flow for the kitchen pilot; labelled doorway identity,
calibrated cross-capture registration, general multiroom placement, and
held-out accuracy/runtimes are still required before the intended result
is achieved.

On the final kitchen pilot, the three model-on source runs and the learned
linker produced 148 supported 2D view pairs from 336 tests, versus five for
the patch matcher on the same source runs. The linker retained 52 local
opening-region links in 19 unverified groups and three cross-view-consistent
pose hypotheses under assumed focal lengths. It accepted no metric
registration, no room adjacency, and no confirmed opening width. The
LiDAR-derived 2.4909 × 2.3777 × 2.7781 m kitchen fit is provisional, while
the hall-facing 2.26 m reference opening remains a miss. The full serial
model-on pass took about 18 minutes on this CPU, above the 15-minute target.
See `reports/kitchen_pipeline_pilot.md` for exact run IDs and evidence.
