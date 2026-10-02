# Working scorer definitions, revision 0.1.0

These are project choices made before the first complete benchmark baseline.
The evaluator's rules take precedence if later supplied; preserve results
under both versions if definitions change after a baseline. This file and
`roomproof.benchmark.SCORER_VERSION` must be tied to a Git revision in each
benchmark report.

| Quantity | Working calculation | Threshold |
| --- | --- | --- |
| Opening detection/width | One-to-one same room, wall, type; center within 0.30 m. Greedy nearest center, then stable ID. Success needs width error ≤0.02 m. Denominator is real count plus unmatched predictions. | At least 85% successes |
| Ceiling height | Absolute point error for every independently measured room. Missing output fails. | ≤0.015 m each |
| Ceiling repeat spread | Absolute difference between two independent same-tier estimates for each room. | ≤0.01 m each |
| Wall repeat spread | Absolute difference on corresponding wall IDs. Report both min and max of 0.01 m and 0.005 × mean predicted length. | Working strict pass uses min |
| Photo/video wall | Absolute relative point error against independent reference length. Missing output fails. | Photo ≤8%; video ≤3% |
| Photo footprint area | Absolute relative error in whole-property area. | ≤8%; shape and overlap are separate and pending |
| Adjacency | Equality of undirected room-pair sets. | Exact on the benchmark |
| Intervals | Finite bound coverage, median finite width, missing and unbounded fractions by quantity and tier; unbounded values are not counted as calibrated finite successes. | 90% target, no supplied pass threshold |
| Damage | Stable-ID presence, visible class, room/surface match, phantom count. | No supplied numeric pass threshold; region overlap pending |

The scorer never feeds reference values to `process-capture`. A matching stable
ID is established from the benchmark map before predictions are scored. The
current scorer is incomplete for footprint shape alignment, room-overlap
geometry, damage polygon overlap, drift ablation, and execution timing; these
rows cannot be called passing yet. The first full benchmark must freeze the
completed scorer and save its code revision before any fix declaration.
