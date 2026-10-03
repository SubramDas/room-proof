# Submission evidence in this repository

The development source, model-download scripts, reference measurements, consumer-app PDFs and selected small submission reports are tracked in Git. Large raw captures, model weights, run caches and full submission ZIPs are deliberately excluded by .gitignore. Obtain the accompanying submission archives for raw-input reproduction.

- [Part 1 protocol](submission/part_1/Capture_Protocol.pdf)
- [Part 2 requirement status](submission/part_2/00_REQUIREMENTS_AND_STATUS.md)
- [Kitchen independent repeat comparison](submission/part_2/03_evaluation/kitchen_repeat/README.md)
- [Part 3 kitchen and hall comparison](submission/part_3/04_comparison/REPORT.md)
- [Part 4 fix-loop post-mortem](submission/part_4/03_comparison/POSTMORTEM.md)
- [Part 5 process evidence](PART_5_PROCESS_EVIDENCE.md)

The files under docs/submission are selected evidence excerpts, not standalone reproductions of the full submission directories. Some relative links inside them refer to larger accompanying archive contents. The packaging scripts use the original workspace data/run folders; cloning Git alone does not supply those raw inputs.

## Snapshot chronology

Reports in reports/ and the original Part 2 package were generated before later consumer-app exports and some photo jobs finished. They remain historical snapshots, not the latest status for every gate. Part 3 contains both magicplan exports (2026.38.0, automatic dimensions). Part 4 includes the completed three-room Depth Pro output and corrects the baseline worst extent error to 448.15%, improving to 176.54%. Independent kitchen repeat evidence is supplied, with failed longer-extent and height-spread comparisons. No overall gate pass is claimed.

Original declarations are unchanged. Four historical photo-after source files cannot be recovered exactly; the Part 4 source audit records that reproduction limitation. The original baseline LiDAR/photo dimensions were reproduced from archived code.
