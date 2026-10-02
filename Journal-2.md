# Journal 2 — Input contracts and one-command skeleton

**Status:** In progress on 2 October 2026. T15 and T16 are checked in [TASK.md](TASK.md); T17–T23 remain open. This journal will be updated when Phase 2 is complete.

## Work and evidence

| Task | Progress | Evidence |
| --- | --- | --- |
| T15 | Added `process-capture PATH --tier {photo,video,lidar}` with required stable property/capture IDs, optional device metadata, unique run directory, `run.json`, and `quality_report.json`. Source file hashes are recorded in the quality report and combined into the run's data revision. README documents the invocation. | [roomproof/capture.py](roomproof/capture.py), [README.md](README.md); photo run `run-98c54ba0d00049e5a4015f22828b2468`, video run `run-093977fb719c47bc8ee692c7f92bc0e4`, LiDAR run `run-cb3603c144de470ab6b34c3aabd5809c` |
| T16 | Added explicit `invalid`, `valid_low_confidence`, and `valid` classifications. Photo checks room folders, 2–8 stills, PNG/JPEG/HEIC signatures, PNG integrity, and duplicate hashes; video files are fully decoded; LiDAR checks required files, pose/depth/confidence frame IDs, every PNG's CRC/layout, decodable RGB, and device sensor declaration. | Owner LiDAR run `run-cb3603c144de470ab6b34c3aabd5809c` correctly reports 569 RGB frames vs 570 metadata frames as valid-low-confidence. Negative runs checked empty photo root (`run-62a963c23a2d4f469cb23f9d9c8c21fb`), corrupt image (`run-b2c25bd0192944b29c0f1eb405032ffa`), duplicate photo (`run-aa4a1b1be38f4c29828c1c2d21e079c6`), empty video (`run-63bd26df1027415c977eebb689d70fc0`), unsupported LiDAR device (`run-2efbc50a6cca4fb0ac4dc6e5a39f0525`), and missing LiDAR files (`run-a76fc94ac2334894a1e8e807a5a23a6e`). |
| T17 | Added a photo-folder reader that decodes/indexes stills and keys each frame to the stable `room-...` folder ID. It reports no inferred adjacency and records original path/hash references. | [roomproof/readers.py](roomproof/readers.py); photo reader run `run-7e8bf730e89d4a92ac1186ef0b0474db` |
| T18 | Added a standalone video reader with an evenly spaced bounded sample, downscaling to 640 px wide and writing RGB24 sample files plus source frame/timestamp references. Default maximum is 24; the CLI can set another positive limit. | [roomproof/readers.py](roomproof/readers.py); standalone video run `run-8ac85e840a9d491caccfa1520b0ff608` wrote six samples from the 569-frame input at the requested limit |

## Limits and next work

The command validates all tiers and indexes photo/video frames; `next_stage` remains `not_implemented` for LiDAR. The photo smoke fixture used distinct valid PNG files to exercise decoding and source references, not real camera photos or geometry inference. The video sample came from a standalone MP4 without sidecars. LiDAR frame joining, property-plan schema validation, semantic checks, plan rendering, and common-contract output remain open. Continue with T19–T23 and keep T02 open until property-plan output and evaluation reuse stable physical IDs.
