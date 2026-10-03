# Fix-loop post-mortem

Declarations: `declaration.md` (early LiDAR subset), then `photo_declaration.md` (first complete photo run). Both preceded their proposed fixes. The early LiDAR declaration was not the single worst gate across a complete all-tier benchmark, so it does not fully satisfy that aspect of the rubric.

The structural-plane change improves wall partitioning and supports both expected LiDAR connections. It does not establish the height gate. Full before/after numbers are in `evaluation/metrics.csv`; the actual original outputs remain in `runs/three_room_lidar` and `runs/three_room_photos`.

The kitchen height prediction of ≤2 cm error was not met in the initial structural-plane after run; the corridor height regressed when the inferred room boundary selected a different dominant horizontal surface. The hypothesis explained a wall-partition error but did not explain all height bias. No reference-derived scale correction was applied.

Photo changes address focal/depth priors, low-parallax pose estimation and gravity alignment. The initial small-model pose-only change did not resolve the whole-property stitch. The Depth Pro after result is included only when an actual completed result exists. The prediction in `photo_declaration.md` must be judged against that result, including connectivity rather than dimensions alone.

See `reproduce.sh` for commands and `changes.diff` for the shipped source changes. Cached inference outputs are permitted for exact replay; the live path remains in the same code.
