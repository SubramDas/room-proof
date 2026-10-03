# Part 4 — The fix loop

Read `03_comparison/POSTMORTEM.md` first. This folder reports actual improvements, regressions, prediction misses and reproduction limitations.

- `01_original_declarations/`: original LiDAR and photo declarations, unchanged; retrospective one-page index is separately labelled.
- `02_runs/lidar_declared/{before,after}/`: targeted three-room LiDAR pair.
- `02_runs/photos_declared/{before,after}/`: original photo baseline and newly completed Depth Pro result.
- `02_runs/kitchen_supporting/{before,after}/`: same-capture standalone kitchen improvement; excludes kitchen_reproduce.
- `02_runs/original_reproduction_checks/`: original-code reruns verifying baseline dimensions.
- `03_comparison/`: all dimension errors, original laser reference, input-hash identity checks and post-mortem.
- `04_code_changes/`: readable diff and change summary.
- `05_reproduction/`: raw inputs, historical source snapshots, source-recovery audit, current source, setup/download scripts and rerun commands.

**Result:** measured photo worst extent error improves 448.15% → 176.54% (the original declaration misidentified the worst dimension as 232.93%), but target and stitch gate fail. Declared LiDAR kitchen height improves 4.65 → 4.09 cm and misses its prediction. Supporting standalone kitchen height improves 1.62 → 0.79 cm (local fail → pass), with drift settings also changed.

**Reproduction caveat:** the original before runs were reproduced, but four historical photo-after source hashes cannot be recovered. Its supplied snapshot is a labelled revision fallback, not an exact replay guarantee. A new source-frozen after run remains necessary for full reproducibility. Original declaration chronology is preserved, not rewritten to predict observed successes.

Model binaries are not embedded; public fetch scripts are included. There are no private API keys. Consumer-app comparison remains Part 3; complete development history is Part 5.
