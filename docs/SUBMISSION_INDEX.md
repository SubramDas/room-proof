# Submission evidence in this repository

The development source, model-download scripts, reference measurements, consumer-app PDFs and selected small submission reports are tracked in Git. Large raw captures, model weights, run caches and full submission ZIPs are excluded by .gitignore. Obtain the accompanying archives for raw-input reproduction. `submission/Astra_Final_Submission.zip` is the combined handoff and `submission/FINAL_MANIFEST.json` lists its files.

- [Part 1 protocol](submission/part_1/Capture_Protocol.pdf)
- [Part 2 requirement status](submission/part_2/00_REQUIREMENTS_AND_STATUS.md)
- [Kitchen independent repeat comparison](submission/part_2/03_evaluation/kitchen_repeat/README.md)
- [Part 3 kitchen and hall comparison](submission/part_3/04_comparison/REPORT.md)
- [Part 4 fix-loop post-mortem](submission/part_4/03_comparison/POSTMORTEM.md)
- [Part 5 process evidence](PART_5_PROCESS_EVIDENCE.md)

The files under docs/submission are selected evidence excerpts, not standalone reproductions of the full submission directories. Some relative links inside them refer to larger accompanying archive contents. The packaging scripts use the original workspace data/run folders; cloning Git alone does not supply those raw inputs.

## Snapshot chronology

Part 2 now contains all 12 completed declared runs, the independent kitchen repeat, the earlier raw three-space scan under `three_room_original/`, and the replacement 8,023-frame bedroom/kitchen/hall/connector scan under `three_room/`. The replacement scan has separate automatic and visually assisted LiDAR plans. Automatic extraction merges hall and kitchen; assisted room selection is disclosed. The resulting plans are supplemental evidence, not a retroactive replacement for earlier benchmark numbers.

Part 3 contains both magicplan exports (2026.38.0, automatic dimensions) and scores 2/6 shared linear dimensions in the pipeline's favour. Part 4 includes the completed earlier three-room Depth Pro output and corrects the baseline worst extent error to 448.15%, improving to 176.54%. Independent kitchen repeat evidence fails the longer-extent proxy and 1 cm height-spread gate. No overall gate pass is claimed.

Original declarations are unchanged. Four historical photo-after source files cannot be recovered exactly; the Part 4 source audit records that reproduction limitation. The original baseline LiDAR/photo dimensions were reproduced from archived code.
