# Part 2 requirements → evidence → status

Source: Applied_AI_Case_Study.pdf, Part 2, printed pages 1–2. Later consumer-app comparison and fix-loop requirements belong to Parts 3 and 4.

| Required submission | Included evidence | Status |
|---|---|---|
| Per-room dimensioned walls, ceiling height, floor area, openings | `02_outputs/<dataset>/<tier>/result.json`, `rooms/`, `plan.pdf`, `report.html` | Present for completed runs; incomplete observations and inaccurate candidates remain. |
| Stitched property with correct adjacency, every tier | Results' adjacency/layout_quality and whole-property plans | Three-room LiDAR connected; RGB physical stitching unresolved. No all-tier pass. |
| Per-surface damage classes and metric extent | Result damage arrays, `surfaces/`, `semantics/overlays/` | Staged demonstration; false positives, extent and assignment accuracy unvalidated; general nonwall association incomplete. |
| Concealed flags and fired rules | Result concealed_damage_flags | Implemented inspection rules; staged results have no concealed flags. Not proof of absent hidden damage. |
| Scope lines keyed to surfaces | Result scope_items | Provisional inspection scope. Official Round 1 scope unknown. |
| Confidence interval for every measurement | Measurement interval objects in JSON | Engineering ranges, not empirically calibrated. Unobserved values are null. |
| Published-schema JSON | `05_reproduction/project/schemas/result.schema.json`; validation table | Provisional local schema passes for packaged results; official schema unavailable. |
| One command per capture and rendered plan | `05_reproduction/COMMANDS.md`; each completed output folder | Included. Missing-run entries have status documents only. |
| ≥3 rooms plus connector | Raw `three_room/`, earlier `three_room_original/`, expanded LiDAR outputs | Raw composition now present; automatic segmentation merges hall and kitchen. Assisted four-space output supplied. |
| Furnished room, staged damage in two classes | Raw `Crack_water/` and outputs | Black crack/brown waterlogging staging supplied; recognition accuracy unvalidated. |
| Same spaces at all three tiers | Raw folders and execution.csv | Earlier benchmark and replacement four-space runs completed at all tiers. Replacement photo/video physical stitching fails. |
| Independent repeats and laser/tape ground truth on everything | `01_reference/measurements.txt`; kitchen_repeat; unavailable-evidence table | Independent kitchen repeat supplied. Partial laser room/doorway measurements; exhaustive surface/opening/damage truth absent. |
| Openings ≤2 cm on ≥85%, misses/phantoms included | Candidate outputs; unavailable-evidence table | Not established; false candidates remain and exhaustive truth absent. |
| Height ≤1.5 cm; repeated spread ≤1 cm | `03_evaluation/measured_scores/`; kitchen_repeat | Multi-room LiDAR height gate failed; kitchen repeat height spread 3.10 cm fails. |
| Repeat wall agreement ≤1 cm or 0.5% | kitchen_repeat; unavailable-evidence table | Extent proxy long side fails; full physical wall matching unavailable. |
| Actual drift correction and on/off footprint | `04_drift_ablation/` | Executed and supplied; accuracy improvement not demonstrated. |
| Photo footprint ±8%, correct adjacency, no overlaps | Plans/layout diagnostics | Not established. |
| Photo walls ±8%; video walls ±3%; calibrated intervals | Proxy measurement table and raw results | Full gates not established; interval calibration incomplete. |

Successful execution or JSON validation is not a geometry-accuracy pass. No missing result is replaced by a fabricated output.
