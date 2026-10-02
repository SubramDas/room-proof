# Requirement and evidence matrix

Status as of 2 October 2026. `Complete` means the named evidence exists and has been checked; `partial` means only part exists; `not started` means no qualifying artifact exists; `failing` means an attempted gate has evidence of failure. A path under "planned" is not evidence. Run IDs will be added when prediction and scoring exist. See [SPEC.md](SPEC.md) for the exact brief and [TASK.md](TASK.md) for tasks.

| Requirement / gate | Real path or planned artifact | Evidence / run ID | Status |
| --- | --- | --- | --- |
| Chosen Route 2 and supported devices | [docs/decisions.md](docs/decisions.md); planned `protocols/stock_capture.md`, `docs/device_matrix.md` | Decision documented; phone export and non-engineer test absent | partial |
| Photo input: 2–8 stills per room, no hidden depth/poses | Planned photo reader and home capture | None | not started |
| Ordinary standalone video input | Planned video reader and home capture | None | not started |
| LiDAR RGB/depth/confidence/poses/intrinsics input | Starter directories `single_room/`, `single_scan_floor_only/`, `single_scan_with_ceiling/`; planned importer audit | Raw files present; alignment/units not validated | partial |
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
| 2 | Tested capture guide and device matrix | Planned `protocols/stock_capture.md`, `docs/device_matrix.md` | Decision only; actual app export missing | not started |
| 3 | Runnable repository under 15 minutes, one command per capture | [README.md](README.md), [scripts/setup.sh](scripts/setup.sh); planned pipeline command | Foundation CLI runs; capture processing and timing absent | partial |
| 4 | Reproduction bundle: exact raw files, references, code/models/settings | [repro/README.md](repro/README.md), local `repro/bundle/`; planned benchmark bundle | All three starter scans imported and clean-copy verified; home data, truth, models, replay absent | partial |
| 5 | All-tier benchmark and gate report | Planned `reports/benchmark.md` | None | not started |
| 6 | Fix-loop declaration, before/after and diff | Planned `fix_loop/` | None | not started |
| 7 | Technical report of at most six pages | Planned `reports/technical_report.pdf` | None | not started |
| 8 | Original benchmark data, truth and app exports | Planned `benchmark/` bundle | Three starter scans only, lacking benchmark requirements | partial |

## Foundation task evidence

| Task | Evidence / run ID | Status |
| --- | --- | --- |
| T00 decisions and conflicts | [docs/decisions.md](docs/decisions.md) | complete |
| T01 discovery commit | Git `59b1a58` | complete |
| T02 IDs and manifests | [docs/ids_and_manifests.md](docs/ids_and_manifests.md); [roomproof/cli.py](roomproof/cli.py) | partial until output/evaluation reuse IDs |
| T03 compliance coverage | This file | complete |
| T04 zero-cost setup | [scripts/setup.sh](scripts/setup.sh), [README.md](README.md) | complete for foundation CLI; 3.07 s, 16 MB, 0 download in fresh temp directory |
| T05 immutable raw import | [roomproof/cli.py](roomproof/cli.py), [repro/README.md](repro/README.md) | complete for all three starter scans; 33,434 file hashes |
| T06 second-copy reproducibility | [repro/README.md](repro/README.md), [repro/manifest.json](repro/manifest.json) | complete for starter scans; clean committed-code run `run-ea1cf72ec4da4ae9885726059699bf1b` |
| T07 run logging, including failure | [roomproof/cli.py](roomproof/cli.py), [docs/ids_and_manifests.md](docs/ids_and_manifests.md) | complete for current commands; failure run `run-93e41cf1501a4b2eb618771b50abf40c` |
| T08 milestone history | Git `95510f2`, `59b1a58`, `dd30e38` | partial; fix-loop history cannot exist yet |
