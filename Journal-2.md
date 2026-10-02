# Journal 2 — Input contracts and one-command skeleton

**Status:** In progress on 2 October 2026. T15 and T16 are checked in [TASK.md](TASK.md); T17–T23 remain open. This journal will be updated when Phase 2 is complete.

## Work and evidence

| Task | Progress | Evidence |
| --- | --- | --- |
| T15 | Added `process-capture PATH --tier {photo,video,lidar}` with required stable property/capture IDs, optional device metadata, unique run directory, `run.json`, and `quality_report.json`. Source file hashes are recorded in the quality report and combined into the run's data revision. README documents the invocation. | [roomproof/capture.py](roomproof/capture.py), [README.md](README.md); photo run `run-98c54ba0d00049e5a4015f22828b2468`, video run `run-093977fb719c47bc8ee692c7f92bc0e4`, LiDAR run `run-cb3603c144de470ab6b34c3aabd5809c` |
| T16 | Added explicit `invalid`, `valid_low_confidence`, and `valid` classifications. Photo checks room folders, 2–8 stills, PNG/JPEG/HEIC signatures, PNG integrity, and duplicate hashes; video files are fully decoded; LiDAR checks required files, pose/depth/confidence frame IDs, every PNG's CRC/layout, decodable RGB, and device sensor declaration. | Owner LiDAR run `run-cb3603c144de470ab6b34c3aabd5809c` correctly reports 569 RGB frames vs 570 metadata frames as valid-low-confidence. Negative runs checked empty photo root (`run-62a963c23a2d4f469cb23f9d9c8c21fb`), corrupt image (`run-b2c25bd0192944b29c0f1eb405032ffa`), duplicate photo (`run-aa4a1b1be38f4c29828c1c2d21e079c6`), empty video (`run-63bd26df1027415c977eebb689d70fc0`), unsupported LiDAR device (`run-2efbc50a6cca4fb0ac4dc6e5a39f0525`), and missing LiDAR files (`run-a76fc94ac2334894a1e8e807a5a23a6e`). |

## Limits and next work

The command validates inputs and logs provenance; `next_stage` is `not_implemented`. It does not yet decode photo pixels into a geometry reader, sample ordinary video for inference, reconstruct LiDAR geometry, validate the property-plan schema, or render a plan. The photo smoke fixture used distinct PNG files to exercise container/count handling, not real camera photos or a geometry pipeline. Continue with T17–T23 and keep T02 open until property-plan output and evaluation reuse stable physical IDs.
