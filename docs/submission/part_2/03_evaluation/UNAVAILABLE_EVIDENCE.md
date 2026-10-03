# Evidence that is not established

| Requirement | Status / reason |
|---|---|
| Exhaustive opening score, including misses/phantoms | Room-level doorway values supplied, but no exhaustive opening IDs, counts, wall offsets or reference correspondences. Candidates are not scored as correct detections. |
| Per-wall ±8% photo / ±3% video accuracy | Current table uses sorted horizontal extent proxies, not corresponding physical walls. RGB geometry failures remain. |
| Repeatability ≤1 cm or 0.5% per wall | Independent kitchen repeat supplied and extent proxies scored; physical wall correspondence is missing and the long extent proxy fails. |
| Repeated height spread ≤1 cm | Kitchen repeat spread is 3.10 cm, so this gate fails. |
| Empirical interval calibration at each tier | No independent calibration and test scenes; engineering intervals only. |
| Damage class and extent accuracy | Staged black/brown props; no independent measured masks/prop extents; natural damage recognition unvalidated. |
| Complete Round 1 contract / published schema | Not supplied; local provisional schema only. |
| Three rooms plus connector | The newer raw scan contains bedroom, kitchen, hall and connector; automatic LiDAR extraction merged hall and kitchen. A visually assisted four-space output is supplied separately. |
| Complete three-room and damage photo results | Earlier capture and replacement photo runs complete, but physical multi-room stitching fails. The replacement photo result has four disconnected spaces and a 4.139 m² overlap. |
| Full geometry/height truth for evaluator samples | Not supplied; execution evidence only. |

The one standalone kitchen LiDAR height result is within 1.5 cm of its reference; all three heights in the earlier multi-room LiDAR result exceed 1.5 cm error. This is not an overall height-gate pass. No confidence-interval calibration, opening gate, or whole-property RGB gate is claimed as passed.
