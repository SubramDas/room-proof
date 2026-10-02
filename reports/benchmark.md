# Benchmark report — pending matched capture and reference truth

No all-tier benchmark result is reported yet. Current Flat-805 photo/video
plans have unresolved geometry and cannot satisfy the plan or accuracy gates.
The owner has supplied a matched LiDAR export and room-level laser dimensions.
Individual wall/opening reference rows, repeat capture, two labelled damage
classes, and comparator exports are still
required. Do not interpret the presence of this report as a passing gate.

The optional local model pilot has paired photo/video model-on and model-off
runs in [model_candidate_pilot.md](model_candidate_pilot.md). Both final plans
remain unresolved. Candidate counts and timing are recorded, but no labelled
precision/recall or metric plan improvement can yet be scored. LiDAR RGB
proposals remain separate from metric openings until registration and
wall-gap correspondence are supported.

The later [hall LiDAR RGB integration](lidar_rgb_candidate_integration.md)
established a sampled one-frame RGB/depth offset and ran the local visual
model on 24 RGB frames. Two door proposals failed the depth-gap location
check; the final hall plan and its unverified opening were unchanged. This
is not a scored model-on improvement.

## Evidence ledger to complete

| Tier | Capture ID | Run ID | Raw manifest SHA-256 | Plan SHA-256 | Status |
| --- | --- | --- | --- | --- | --- |
| Photo | pending | pending | pending | pending | pending |
| Video | pending | pending | pending | pending | pending |
| LiDAR | pending | pending | pending | pending | pending |

## Required tables

Record execution/schema, room and property geometry, every reference opening
and wall, ceiling bias and repeat spread, photo/video wall error, footprint
area and aligned shape, adjacency and room overlap, drift on/off, both visible
damage classes and surface match, interval coverage/width/unknown rate by tier
and quantity, head-to-head shared/expanded scores, challenging surfaces,
stage/setup/transfer/processing time, and the before/after fix comparison.

Every row must link raw capture ID, reference ID, plan/run ID, scorer revision,
and relevant model/API version. Publish both successful and failed rows.
