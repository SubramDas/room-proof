# Fix declaration — room-local measurement support

Baseline revision: `e3977de`. Declared before shipping the fix.

## Failing result

The currently available **LiDAR geometry baseline** on `three_room/lidar`, 140 frames with drift correction, estimates the kitchen candidate (room_2 by trajectory order) at **2.75350 m** ceiling height versus **2.80000 m** laser truth: **4.65 cm error**, failing the **1.5 cm** gate. The hall is 2.76965 m (3.04 cm error). This is the worst height error in this currently measured LiDAR subset. The all-tier benchmark is not yet complete, so this is not claimed to be the worst gate of the final full benchmark.

The free-space partition also gives the kitchen only 1.84 m of horizontal extent, while visual inspection of the reconstructed cloud shows a continuous separating wall beyond the watershed split.

## Root-cause hypothesis and evidence

A global floor mode is used for all room heights despite pose/depth residuals differing by room. The free-space watershed also partitions a broad doorway geometrically between room centres, cutting through a room instead of following its observed separating plane. This contaminates local ceiling support and room boundaries. The cloud and plane histograms in `runs/three_room_lidar/geometry/geometry.npz` and `/tmp/astra_three_probe.png` motivated this diagnosis; the durable after/before report will include replacement figures.

## Proposed fix and prediction

Use the free-space seeds to select room-local structural planes; snap supported rectangular regions to enclosing wall planes using high wall observations, then fit the floor and ceiling locally inside that room. Keep the unsnapped method selectable and retain partial/nonrectangular fallback. Do not read reference measurements during inference.

Predicted kitchen height absolute error after correction: **≤2.0 cm** (improvement, but not a promised pass). Predicted hall height error: **≤2.0 cm**. Report misses and regressions. We will also report wall extents but there is no supplied official LiDAR wall threshold.

## Reproduction

Before: revision e3977de, `python -m astra run --tier lidar --input three_room/lidar --output runs/fix_before --capture-id three_room --max-frames 140 --semantic-views 12`.

After: new revision, same inputs/frame count/semantic budget with `--layout-method planes`. Also run new code with `--layout-method free-space` to isolate the algorithm change. Ground truth remains outside inference. The raw before/after outputs, stage-only comparison, code diff and evaluation must all be retained. No consumer-app result or independent repeatability result is available.
