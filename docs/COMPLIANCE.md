# Compliance matrix

Implementation and successful execution do not imply accuracy-gate compliance. Missing evidence is explicit.

| Requirement | File path | Artifact | Status |
|---|---|---|---|
| Route 2 stock capture protocol | docs/CAPTURE_PROTOCOL.md | One-page operator instructions | Written; not independently followed by evaluator |
| Device matrix | docs/DEVICE_MATRIX.md | Hardware/tier table | Written; actual tests limited to supplied device |
| Photos, video, LiDAR input | astra/__main__.py; configs/benchmark.json | Common CLI and declared benchmark runs | Implemented; execution listed in benchmark |
| Full Round 1 JSON | schemas/result.schema.json | Provisional contract and optional official validation | Blocked: official schema/instructions absent |
| Room dimensions/plans | astra/layout.py; runs/*/result.json | Walls, area, height, room/whole-plan exports | Implemented; measured errors and unobserved fields remain |
| Correct stitched property from every tier | astra/quality.py; runs/*/layout_quality | Overlap, connectivity and component diagnostics | Partial: RGB physical stitch can fail |
| Openings ≤2 cm on ≥85%, with misses/phantoms | astra/openings.py; semantics/candidates.json | Ray-supported and visual candidates | Not passed; exhaustive opening truth unavailable |
| Height ≤1.5 cm | reports/metrics.csv | Laser comparison | Failed on current measured rooms |
| Repeatability and repeated height spread | submission/part_2/03_evaluation/kitchen_repeat/ | Independent kitchen capture and laser comparison | Height spread 3.10 cm fails; long extent proxy fails; physical walls unmatched |
| Drift correction and ablation | runs/drift_ablation/ablation.json; footprint_comparison.svg | Verified ICP graph and actual on/off footprint | Implemented and executed |
| Photo ±8% / video ±3% wall accuracy | reports/benchmark.md | Extent proxy scores and unmapped failures | Not established; full per-wall correspondence absent |
| Calibrated intervals at every tier | docs/ARCHITECTURE.md; result.json | Explicit provisional ranges and coverage rows | Incomplete: no independent empirical calibration |
| Surface damage classes and metric extent | astra/semantics.py; runs/damage_* | Wall-projected candidates, staging demo | Partial: natural recognition and extent accuracy unvalidated; generalized nonwall association incomplete |
| Concealed flags with rules | astra/semantics.py; result.json | Visible-evidence inspection flags | Implemented as inspection rules; no hidden-damage diagnosis |
| Scope lines keyed to surfaces | astra/semantics.py; result.json | Inspection quantity and rule IDs | Implemented inspection scope; full Round 1 contract unknown |
| Three rooms plus connector benchmark | three_room/; runs/three_room_expanded_assisted/ | Bedroom, kitchen, hall, connector raw; automatic and assisted plans | Raw composition met; automatic hall/kitchen merge; assisted result marked |
| Same spaces in all tiers | configs/benchmark.json; runs/three_room_expanded_* | Original and replacement photo/video/LiDAR outputs | Executed; replacement RGB physical stitching fails; video is Stray RGB export |
| Two-room consumer app comparison | submission/part_3/04_comparison/REPORT.md | Magicplan 2026.38.0 kitchen and hall PDF exports; scored table | 2/6 linear dimensions, 33.3%; below 70% |
| Fix declaration, before/after, diff | fix_loop/ | Measured declarations and reproduction | Shipped fixes; predictions and shortcomings reported |
| Incremental process history | .history; submission/part_5/ | Actual development commits and portable bundle | Recorded; bundle refreshed at final packaging |
| Clean install under 15 minutes | scripts/setup.sh; README.md | Pinned environment and downloads | Not verified on clean machine; network-dependent |
| Reproduction bundle | submission/part_2/05_reproduction/; submission/part_4/05_reproduction/ | Raw captures, source and historic snapshots; public model fetch | Prepared; clean-machine and exact photo-after replay not verified |
| Technical report ≤6 pages | reports/technical_report.pdf | Six-page PDF | Generated from actual available evidence |
| Unseen live walk-in | README.md; docs/CAPTURE_PROTOCOL.md | Same live CLI | Not tested on evaluator capture |
