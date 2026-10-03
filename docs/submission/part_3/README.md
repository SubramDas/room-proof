# Part 3 — Two-room comparison against magicplan

Both required consumer-app room exports are now included: kitchen and hall. App version is 2026.38.0; operator reports automatically measured dimensions.

## Contents

- `01_magicplan/`: original PDFs, extracted text and metadata.
- `02_pipeline/`: original kitchen LiDAR output and three-room LiDAR output containing the hall, with JSON, plans, diagnostics and provenance.
- `03_reference/`: supplied laser measurements.
- `04_comparison/REPORT.md`, `comparison.csv`, `score.json`, `comparison.pdf`: combined dimension-by-dimension comparison, scoring and limitations.
- `05_reproduce_comparison.py`: verifies source-derived values and recomputes errors/counts.

**Result:** 2/6 shared linear measurements beat/tie (33.3%). Including derived area/perimeter, 4/10 (40%). Neither reaches 70%. The kitchen height and hall longer extent are the two linear wins. Physical wall/opening correspondences remain incomplete, so these are provisional extent/height scores rather than the exhaustive gate.

The hall room area is 13.99 m² in its room summary, but the property summary says 13.98 m². The per-room comparison uses 13.99 m² and discloses this discrepancy.

## Remaining work

Match physical wall/opening IDs across app, pipeline and laser; obtain missing opening widths/heights and segment references where necessary. Optional capture-mode/device details can complete the provenance record. Both PDFs and the app version are already available. Improving the score requires genuine pipeline accuracy improvements; no favourable run substitution is performed.

Raw inputs and pipeline rerun commands are in Part 2. Run `python3 05_reproduce_comparison.py` in this folder to verify the submitted comparison arithmetic.
