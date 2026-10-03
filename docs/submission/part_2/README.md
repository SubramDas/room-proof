# Part 2 — Output contract and accuracy gates

This is an evidence snapshot, not a claim that all Part 2 gates passed.

## Start here

1. Read `00_REQUIREMENTS_AND_STATUS.md` for the PDF requirements and artifact locations.
2. Open `02_outputs/three_room/lidar/report.html` and `plan.pdf` for the multi-room result.
3. Open `02_outputs/Crack_water/lidar_later_candidate/report.html` for the later staged-damage example; the declared benchmark is separately preserved in `lidar/`.
4. Read `03_evaluation/measured_scores/benchmark.md`, `execution.csv` and `UNAVAILABLE_EVIDENCE.md`.
5. View `04_drift_ablation/footprint_comparison.png` and its README.
6. Use `05_reproduction/COMMANDS.md` to set up and rerun captures.

## Folder contents

- `01_reference/`: original laser measurements, room mapping, input audit and dataset discrepancies.
- `02_outputs/`: per-dataset/per-tier saved JSON, plans, room/surface renders, image overlays, diagnostic data, logs and provenance. Incomplete runs have explicit status files.
- `03_evaluation/`: refreshed measurements, execution inventory, dimensions/damage CSVs, schema validation and missing evidence.
- `04_drift_ablation/`: drift on/off layouts and footprint comparison.
- `05_reproduction/project/`: original raw captures, runnable current source, schema, configs and public model-download scripts.
- `MANIFEST_SHA256.csv`: path, byte size and SHA-256 for every other file in this folder.

**Completed declared benchmark outputs:** 10/12. A separate later damage LiDAR run is supplemental. Incomplete photo results remain incomplete even if their historical status file says running. The evaluator sample scans are extra execution evidence, not independently measured benchmark passes.

**Known limits:** RGB stitching and scale errors; multi-room ceiling errors; opening false positives; unverified damage extents; uncalibrated intervals; missing official schema; failed kitchen repeat proxies and incomplete wall correspondence; dataset composition shortfall. See the checklist for details.

This section includes raw inputs, but downloadable weights are not embedded. Full historical regeneration, fix-loop history, consumer-app comparison and the final six-page technical report belong in the corresponding project deliverables. No keys, tokens or local virtual environment are included.

Snapshot time (UTC): 2026-10-03T13:14:48.993510+00:00

## Kitchen reproduction update

Added `02_outputs/kitchen_reproduce/lidar/` and its verified raw LiDAR input. See `03_evaluation/kitchen_repeat/README.md` for the updated repeat evidence. same kitchen and laser dimensions confirmed by operator. Earlier deferred-repeat statements describe the original snapshot and are superseded by this update. This supplemental run does not complete the two missing photo benchmarks.
