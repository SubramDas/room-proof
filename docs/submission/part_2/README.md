# Part 2 — Output contract and accuracy gates

This is an evidence snapshot, not a claim that all Part 2 gates passed.

## Start here

1. Read `00_REQUIREMENTS_AND_STATUS.md` for the PDF requirements and artifact locations.
2. Open `02_outputs/three_room_expanded/lidar_automatic/plan.pdf` and `lidar_assisted/plan.pdf` for the new four-space capture. `02_outputs/three_room/lidar/` is the earlier scan.
3. Open `02_outputs/Crack_water/lidar_later_candidate/report.html` for the later staged-damage example; the declared benchmark is separately preserved in `lidar/`.
4. Read `03_evaluation/measured_scores/benchmark.md`, `execution.csv` and `UNAVAILABLE_EVIDENCE.md`.
5. View `04_drift_ablation/footprint_comparison.png` and its README.
6. Use `05_reproduction/COMMANDS.md` and `INPUT_VERSIONS.md` to set up and rerun the matching capture.

## Folder contents

- `01_reference/`: updated laser measurements, room mapping, input audit and dataset discrepancies.
- `02_outputs/`: per-dataset/per-tier saved JSON, plans, room/surface renders, image overlays, diagnostic data, logs and provenance. Incomplete runs have explicit status files.
- `03_evaluation/`: refreshed measurements, execution inventory, dimensions/damage CSVs, schema validation and missing evidence.
- `04_drift_ablation/`: drift on/off layouts and footprint comparison.
- `05_reproduction/project/`: earlier raw `three_room_original/`, replacement raw `three_room/`, other original captures, runnable current source, schema, configs and public model-download scripts.
- `MANIFEST_SHA256.csv`: path, byte size and SHA-256 for every other file in this folder.

**Completed declared benchmark outputs:** 12/16. A separate later damage LiDAR run and the new bedroom scan are supplemental. The earlier and replacement scan raw files are kept under distinct names. The evaluator sample scans are extra execution evidence, not independently measured benchmark passes.

**Known limits:** RGB stitching and scale errors; multi-room ceiling errors; opening false positives; unverified damage extents; uncalibrated intervals; missing official schema; failed kitchen height repeatability; automatic room merge on the new scan. See the checklist for details.

This section includes raw inputs, but downloadable weights are not embedded. Full historical regeneration, fix-loop history, consumer-app comparison and the final six-page technical report belong in the corresponding project deliverables. No keys, tokens or local virtual environment are included.

Snapshot time (UTC): 2026-10-03T15:51:58.119951+00:00
