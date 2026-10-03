# Submission review guide

Start with `submission/Astra_Final_Submission.zip` and its matching
`Astra_Final_Submission.zip.sha256`. The top-level ZIP contains the five numbered
part ZIPs, the six-page technical report, benchmark report and compliance matrix.
The part ZIPs remain available separately if the upload service has a size limit.

| Part | Open first | What to verify |
|---|---|---|
| 1 — capture | `Part_1_Capture_Routes_and_Input_Tiers/Capture_Protocol.pdf` | Exactly one A4 page; Stray Scanner 1.4; kitchen → hall → connector → bedroom → return; file handoff and all three input tiers. |
| 2 — contract/benchmark | `part_2/00_REQUIREMENTS_AND_STATUS.md`, `03_evaluation/execution.csv`, `02_outputs/three_room_expanded/` | All 12 declared runs completed. The replacement scan has automatic LiDAR, visually assisted LiDAR, photo and RGB-only video outputs. Earlier and replacement raw scans have distinct names; `05_reproduction/input_identity_audit.json` checks their manifests. |
| 3 — app comparison | `part_3/04_comparison/REPORT.md` | Original Magicplan kitchen and hall PDFs, version 2026.38.0, and reproducible arithmetic. The pipeline wins/ties on 2/6 shared linear dimensions (33.3%); the 70% gate fails. |
| 4 — fix loop | `part_4/03_comparison/POSTMORTEM.md`, `05_reproduction/current_photo_replay_audit.json` | Original declarations unchanged; before/after, input identity, code diff and post-mortem. A later source-frozen photo run reproduces the result from an independent snapshot check after input-path normalization. Four historical source hashes of the earlier after run remain unrecoverable. |
| 5 — process | `part_5/commit_history.txt`, `bundle_verification.json`, `remote_verification.json` | Incremental history, offline bundle clone/fsck and remote branch head after final push. |

## Measured limits to disclose

- The new automatic LiDAR plan merged hall and kitchen. The four-space plan uses
  visually reviewed frame ranges and retains an inaccurate connector boundary.
- The new photo run produced four named but disconnected rooms, with a 4.139 m²
  connector/hall overlap and no accepted adjacency. New RGB-only video produced
  22 fragments and no accepted adjacency. Neither is a physical property stitch.
- The independent kitchen repeat has 3.10 cm height spread, above the 1 cm gate.
  Full physical wall correspondence has not been measured.
- The two-room consumer-app score is below 70%. The photo/video wall and
  footprint gates are not passed, and measurement intervals are not calibrated.
- The official Round 1 JSON schema, exhaustive opening/wall/damage ground truth,
  a verified clean installation under 15 minutes and the evaluator's unseen
  live capture are not available. The local schema is `astra.provisional.v1`.

The model weights are public and fetched by the supplied scripts. No API key or
Kaggle credential is needed for the included CPU runs. Read the provenance in
each run before treating a cached run time as a cold CPU benchmark.
