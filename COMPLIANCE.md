# Requirement and evidence matrix

Status as of 2 October 2026. `Complete` means the named evidence exists and has been checked; `partial` means only part exists; `not started` means no qualifying artifact exists; `failing` means an attempted gate has evidence of failure. A path under "planned" is not evidence. Run IDs will be added when prediction and scoring exist. See [SPEC.md](SPEC.md) for the exact brief and [TASK.md](TASK.md) for tasks.

| Requirement / gate | Real path or planned artifact | Evidence / run ID | Status |
| --- | --- | --- | --- |
| Chosen Route 2 and supported devices | [protocols/stock_capture.md](protocols/stock_capture.md), [docs/device_matrix.md](docs/device_matrix.md) | Owner Stray 1.4 ZIP tested; non-engineer timing breakdown/repeat pending | partial |
| Photo input: 2–8 stills per room, no hidden depth/poses | Planned photo reader and home capture | None | not started |
| Ordinary standalone video input | Planned video reader and home capture | None | not started |
| LiDAR RGB/depth/confidence/poses/intrinsics input | Starter directories and `dummy_room.zip`; [device audit](reports/device_format_dummy_room.md) | 569 RGB vs 570 pose/depth/confidence; ZIP bytes verified; metric accuracy untested | partial |
| Explicit input rejection and capture quality report | Planned pipeline quality report | None | not started |
| Common three-tier property-plan JSON contract | [schema/property_plan.schema.json](schema/property_plan.schema.json), [schema/example_property.json](schema/example_property.json) | Synthetic example only; no generated capture output | partial |
| Whole-property plan, rooms, surfaces, openings, adjacency, dimensions | Planned `runs/<id>/property_plan.json` | None | not started |
| Rendered homeowner-readable dimensioned plan | Planned `runs/<id>/plan.svg` | None | not started |
| Visible damage regions on correct surfaces and metric extent | Planned prediction and benchmark labels | None | not started |
| Concealed-damage flags with rule and triggering evidence | Planned rule engine | None | not started |
| Surface-keyed scope line items | Planned rule engine | None | not started |
| Intervals for all physical measurements and calibration | Schema measurement/interval definition; planned scorer | Structure exists; no calibrated outputs | partial |
| Provenance, warnings, status, unresolved topology | Schema fields; [docs/decisions.md](docs/decisions.md) | Synthetic example only | partial |
| One fresh-capture command per tier, schema-valid JSON and plan | Planned pipeline command | None | not started |
| Multiroom geometry and correct adjacency at all tiers | Planned benchmark outputs | None | not started |
| Opening width ≤2 cm on ≥85%, with missed/phantom accounting | Planned scorer | None | not started |
| Ceiling height absolute error ≤1.5 cm per room | Planned scorer | None | not started |
| Ceiling height repeat spread ≤1 cm | Planned repeated capture and scorer | None | not started |
| Wall repeatability within 1 cm or 0.5% per wall | Planned repeated capture and scorer | None | not started |
| LiDAR drift correction and on/off stitched footprints | Planned geometry module and ablation report | None | not started |
| Photo adjacency/no overlap/footprint ±8% | Planned scorer and matched home capture | None | not started |
| Photo wall lengths ±8% | Planned scorer and truth | None | not started |
| Video wall lengths ±3% | Planned scorer and truth | None | not started |
| Two damage classes in a furnished room | Planned home benchmark | None | not started |
| 90% proposed interval coverage, width and unknown-rate report | [docs/decisions.md](docs/decisions.md); planned benchmark report | Policy only; no empirical calibration | partial |
| At least three rooms plus connector, all three tiers, one repeat, tape/laser truth | Planned `benchmark/` bundle | Starter scans do not qualify | not started |
| Two-room consumer-app comparison and ≥70% shared-dimension wins/ties | Planned magicplan exports and comparison table | None | not started |
| Frozen baseline, one-page predicted fix, implementation, rerun and diff | Planned `fix_loop/` | None | not started |
| New walk-in capture processed without property setup | Planned cold rehearsal | None | not started |
| No specialist rig, no reference truth as inference input | [docs/decisions.md](docs/decisions.md) | Design rule; no pipeline to test | partial |
| Challenging surfaces and low light reported | Planned home benchmark and quality report | None | not started |
| CPU/no-GPU local path, free dependencies, disclosed external components | [README.md](README.md), [docs/decisions.md](docs/decisions.md), [scripts/setup.sh](scripts/setup.sh) | Foundation CLI only | partial |

## Eight required deliverables

| # | Deliverable | Real path or planned artifact | Evidence / run ID | Status |
| --- | --- | --- | --- | --- |
| 1 | Compliance matrix | [COMPLIANCE.md](COMPLIANCE.md) | This audited matrix; update as runs exist | complete |
| 2 | Tested capture guide and device matrix | [protocols/stock_capture.md](protocols/stock_capture.md), [docs/device_matrix.md](docs/device_matrix.md) | Owner app export validated; non-engineer timing/repeat incomplete | partial |
| 3 | Runnable repository under 15 minutes, one command per capture | [README.md](README.md), [scripts/setup.sh](scripts/setup.sh); `process-capture` input checks | Setup and tier-aware input checks run; geometry processing and end-to-end timing absent | partial |
| 4 | Reproduction bundle: exact raw files, references, code/models/settings | [repro/README.md](repro/README.md), local `repro/bundle/`; planned benchmark bundle | All three starter scans imported and clean-copy verified; home data, truth, models, replay absent | partial |
| 5 | All-tier benchmark and gate report | Planned `reports/benchmark.md` | None | not started |
| 6 | Fix-loop declaration, before/after and diff | Planned `fix_loop/` | None | not started |
| 7 | Technical report of at most six pages | Planned `reports/technical_report.pdf` | None | not started |
| 8 | Original benchmark data, truth and app exports | Planned `benchmark/` bundle | Starter scans plus one owner Stray test export; still lacks matched photo/video home capture, truth, and comparator exports | partial |

## Foundation task evidence

| Task | Evidence / run ID | Status |
| --- | --- | --- |
| T00 decisions and conflicts | [docs/decisions.md](docs/decisions.md) | complete |
| T01 discovery commit | Git `59b1a58` | complete |
| T02 IDs and manifests | [docs/ids_and_manifests.md](docs/ids_and_manifests.md); [roomproof/cli.py](roomproof/cli.py) | partial until output/evaluation reuse IDs |
| T03 compliance coverage | This file | complete |
| T04 zero-cost setup | [scripts/setup.sh](scripts/setup.sh), [requirements.txt](requirements.txt), [README.md](README.md) | complete for current CLI; cached-wheel setup 14.65 s, 92 MB; full pipeline not built |
| T05 immutable raw import | [roomproof/cli.py](roomproof/cli.py), [repro/README.md](repro/README.md) | complete for all three starter scans; 33,434 file hashes |
| T06 second-copy reproducibility | [repro/README.md](repro/README.md), [repro/manifest.json](repro/manifest.json) | complete for starter scans; clean committed-code run `run-ea1cf72ec4da4ae9885726059699bf1b` |
| T07 run logging, including failure | [roomproof/cli.py](roomproof/cli.py), [docs/ids_and_manifests.md](docs/ids_and_manifests.md) | complete for current commands; failure run `run-93e41cf1501a4b2eb618771b50abf40c` |
| T08 milestone history | Git `95510f2`, `59b1a58`, `dd30e38` | partial; fix-loop history cannot exist yet |

## Phase 1 task evidence

| Task | Evidence / run ID | Status |
| --- | --- | --- |
| T09 one-page guide | [protocols/stock_capture.md](protocols/stock_capture.md) | complete draft; revise from T12 feedback |
| T10 owner app/export | Ignored `dummy_room.zip`; [device audit](reports/device_format_dummy_room.md) | complete: Stray Scanner 1.4 default settings, original ZIP supplied |
| T11 format validation | [JSON audit](reports/device_format_dummy_room.json), [readable audit](reports/device_format_dummy_room.md), run `run-62dd712f6c2f485e82d9a12bd8eac037` | complete report; one-frame RGB mismatch remains a pipeline issue |
| T12 non-engineer rehearsal | Owner reports total under five minutes | partial: breakdown, observed confusion, and repeat evidence pending |
| T13 device matrix | [docs/device_matrix.md](docs/device_matrix.md) | complete; accuracy explicitly unmeasured |
| T14 fallback decision | [Capture route guide](protocols/stock_capture.md), [format report](reports/device_format_dummy_room.md) | complete for free Stray capture/share/transfer/audit; mismatch explicitly documented, Scan4D fallback not triggered |

## Phase 2 task evidence

| Task | Evidence / run ID | Status |
| --- | --- | --- |
| T15 one-command capture entry point | [roomproof/capture.py](roomproof/capture.py), [README command](README.md) | photo `run-98c54ba0d00049e5a4015f22828b2468`, video `run-093977fb719c47bc8ee692c7f92bc0e4`, LiDAR `run-cb3603c144de470ab6b34c3aabd5809c`; all unique run reports under `/tmp/roomproof-runs/` |
| T16 input rejection and low-confidence distinction | [roomproof/capture.py](roomproof/capture.py) | empty/missing folders `run-62a963c23a2d4f469cb23f9d9c8c21fb`, corrupt image `run-b2c25bd0192944b29c0f1eb405032ffa`, duplicate photo `run-aa4a1b1be38f4c29828c1c2d21e079c6`, empty clip `run-63bd26df1027415c977eebb689d70fc0`, unsupported LiDAR `run-2efbc50a6cca4fb0ac4dc6e5a39f0525`, missing LiDAR files `run-a76fc94ac2334894a1e8e807a5a23a6e`; owner frame mismatch is `valid_low_confidence` in `run-cb3603c144de470ab6b34c3aabd5809c` |
| T17 photo reader | [roomproof/readers.py](roomproof/readers.py) | Photo index run `run-7e8bf730e89d4a92ac1186ef0b0474db`; `frames.json` records room-folder IDs and source hashes without inferring adjacency |
| T18 standalone video reader | [roomproof/readers.py](roomproof/readers.py) | Video run `run-8ac85e840a9d491caccfa1520b0ff608`; six requested evenly spaced frames from the standalone owner MP4 were decoded and indexed with source frame references |
