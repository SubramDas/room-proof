# Evidence that is not established

| Requirement | Status / reason |
|---|---|
| Exhaustive opening score, including misses/phantoms | Room-level doorway values supplied, but no exhaustive opening IDs, counts, wall offsets or reference correspondences. Candidates are not scored as correct detections. |
| Per-wall ±8% photo / ±3% video accuracy | Current table uses sorted horizontal extent proxies, not corresponding physical walls. RGB geometry failures remain. |
| Repeatability ≤1 cm or 0.5% per wall | New kitchen LiDAR capture added; see kitchen_repeat/README.md for confirmation status, proxy differences and remaining wall correspondence requirement. |
| Repeated height spread ≤1 cm | New kitchen output height differs by 3.10 cm; see kitchen_repeat/README.md. Same physical kitchen and dimensions confirmed; source consistency still qualifies interpretation. |
| Empirical interval calibration at each tier | No independent calibration and test scenes; engineering intervals only. |
| Damage class and extent accuracy | Staged black/brown props; no independent measured masks/prop extents; natural damage recognition unvalidated. |
| Complete Round 1 contract / published schema | Not supplied; local provisional schema only. |
| Three rooms plus connector | Supplied property has kitchen, hall and corridor: two rooms plus connector. |
| Complete three-room and damage photo results | No final result files at snapshot time. |
| Full geometry/height truth for evaluator samples | Not supplied; execution evidence only. |

The one standalone kitchen LiDAR height result is within 1.5 cm of its reference; all three heights in the multi-room LiDAR result exceed 1.5 cm error. This is not an overall height-gate pass. The confirmed kitchen repeat shows 3.10 cm height variation and a 3.89 cm height error in the new output; source consistency must be checked before attributing variation solely to capture. No confidence-interval calibration, opening gate, or whole-property RGB gate is claimed as passed.

## Kitchen reproduction update

Added `02_outputs/kitchen_reproduce/lidar/` and its verified raw LiDAR input. See `03_evaluation/kitchen_repeat/README.md` for the updated repeat evidence. same kitchen and laser dimensions confirmed by operator. Earlier deferred-repeat statements describe the original snapshot and are superseded by this update. This supplemental run does not complete the two missing photo benchmarks.
