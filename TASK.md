# RoomProof execution tasks

**Deadline:** 4 October 2026, 10:00 a.m. Asia/Kolkata. **Status:** planning and schema draft; no processing pipeline exists yet. This checklist implements [SPEC.md](SPEC.md). It is a work tracker, not evidence that a requirement has passed. Tick an item only after its stated output exists and has been checked.

**People:** `Agent` = work I can do in this repository; `Owner` = phone capture, physical measurement, or account/device access that you provide; `Both` = coordinated work. The owner may send captures while agent work continues. **P0** items unlock a fresh capture at each tier; **P1** items satisfy the benchmark and scored gates; **P2** items package and defend the result. Every requirement remains mandatory even where a priority marks execution order.

**Current evidence:** `SPEC.md` exists; `schema/property_plan.schema.json` version 0.1.0 and a validating synthetic example exist. The three ignored local LiDAR-style exports have been copied into a SHA-256 bundle and verified in a second directory, but their media alignment, units, geometry, and device metadata remain unaudited. They do not supply the required matched photo/video/home benchmark, ground truth, or comparator exports. Git has the initial spec and discovery commits; a foundation milestone is being prepared. Do not present planning artifacts, synthetic example numbers, or byte-verification runs as benchmark results.

## Critical path and dependency map

1. **Immediately:** freeze the working interface and capture guide; validate the supplied LiDAR format; establish one-command runs, logging, and schema/rendered outputs.
2. **In parallel with code work:** capture the home at all three tiers and measure it independently. The benchmark, calibration, head-to-head, and fix loop cannot finish until these files exist.
3. **Before choosing a fix:** run every tier on the same benchmark, freeze gate definitions and the failing baseline, then write the one-page prediction.
4. **Before submission:** ship the fix, reproduce before/after, complete the comparator, and rehearse a genuinely new capture from a clean environment.

The deadline makes **early home capture and tape truth** the largest scheduling dependency. Do not postpone them until the pipeline is polished. Preserve a truthful partial/failing status wherever a gate remains unmet.

## 0. Repository, decisions, and reproducibility foundation — P0

- [x] **T00 [Agent]** Review `SPEC.md`, schema, and this tracker for conflicting assumptions; resolve the working choices in one decision log. **Done when:** `docs/decisions.md` records Route 2, all-tier contract, proposed 90% interval target, scorer assumptions, and known information limits.
- [x] **T01 [Agent]** Commit the discovery milestone (`SPEC.md`, `.gitignore`, schema, example, `TASK.md`) with a message that states the current status. **Done when:** Git history shows this work after the initial spec commit, with no raw dataset committed.
- [ ] **T02 [Agent]** Define stable property, room, surface, opening, damage, capture, and run IDs. **Done when:** a small manifest format and naming rules are documented and reused by outputs/evaluation.
- [x] **T03 [Agent]** Create `COMPLIANCE.md` from every contract row and deliverable, with requirement → real path → evidence artifact/run ID → status. **Done when:** missing items are explicitly `not started` or `failing`, never silently omitted.
- [x] **T04 [Agent]** Choose the zero-cost implementation stack, pin dependency versions, and write setup scripts for Ubuntu 24.04/i7-1265U without a dedicated GPU. **Done when:** a clean environment can install and print a working CLI version; record disk/download cost. Foundation stack: Python 3.12.3 standard library, no external dependencies yet; future vision dependencies must be pinned when added.
- [x] **T05 [Agent]** Create immutable raw-data import rules: SHA-256 hashes, source metadata, no in-place editing, and separate derived outputs. **Done when:** a capture manifest links every imported file and its checksum. Three starter scans imported with 33,434 file records; device/app fields remain unknown.
- [x] **T06 [Agent]** Choose a reproducible large-file delivery method (content-addressed local bundle or DVC with a supplied volume). **Done when:** a second clean directory can obtain exact raw files by documented steps and verify checksums. Do not rely on `.gitignore` as data delivery. All three starter manifests verified in a separate copy; final submission volume remains to be chosen.
- [x] **T07 [Agent]** Define run logging: command/config, code and data revision, model/API version, seed, stage times, status/warnings, metrics, and artifact hashes. **Done when:** every command, including a failed one, writes a diagnosable run manifest. Current CLI commands checked; later pipeline commands must use the same wrapper.
- [ ] **T08 [Agent]** Keep meaningful commits as each verified milestone lands; preserve unsuccessful experiments and the before/after fix revisions. **Done when:** history reflects actual work, with no fabricated or squashed fix-loop evidence.

## 1. Route 2 capture and device validation — P0

- [ ] **T09 [Agent]** Draft a **one-page** stock-capture protocol for Camera photos, Camera video, and Stray Scanner LiDAR. State install/permissions, exact settings, room labels, 2–8 photos per room, full wall/floor/ceiling/opening/damage coverage, doorway views from both sides, walk path, recapture triggers, export, and handoff. **Done when:** `protocols/stock_capture.md` can be followed literally without technical interpretation.
- [ ] **T10 [Owner]** Install Stray Scanner on the iPhone 15 Pro Max (iOS 26.5), report its installed version, and export one short unedited test scan. **Done when:** original files and app/version/settings are available to inspect. This is **not** a blocker for T15–T21 on existing files, but is required before final protocol claims.
- [ ] **T11 [Agent]** Validate the owner scan against the existing importer assumptions: RGB/depth frame correspondence, depth unit, intrinsics, pose convention, timestamp alignment, confidence, and transfer completeness. **Done when:** a machine-readable format report names every field and any mismatch.
- [ ] **T12 [Both]** Try the protocol with a non-engineer using only the one-page instructions; record install/capture/export/transfer duration and points of confusion. **Done when:** the protocol is revised from observed errors and successfully repeated.
- [ ] **T13 [Agent]** Publish `docs/device_matrix.md`: photos/video on any iPhone 15+, LiDAR only on LiDAR-capable Pro devices, minimum iOS for the chosen app, and measured rather than invented per-tier accuracy. **Done when:** device and unsupported-sensor handling are clear.
- [ ] **T14 [Agent]** If Stray Scanner's actual free export fails, test the named free fallback (Scan4D), update the importer/protocol, and record why. **Done when:** one free Route 2 LiDAR workflow is validated end to end, or the failure is explicitly reported.

## 2. Input contracts and one-command skeleton — P0

- [ ] **T15 [Agent]** Implement one documented CLI entry point taking a capture path and tier (`photo`, `video`, `lidar`) and creating a unique run directory. **Done when:** the same command shape works for each tier without hidden manual preprocessing.
- [ ] **T16 [Agent]** Accept/reject input explicitly: corrupt or duplicate media, missing photo folders, fewer than 2 or more than 8 photos per room, missing depth/pose samples, unsupported device/tier, and empty clips. **Done when:** a quality report distinguishes invalid input from a valid low-confidence result.
- [ ] **T17 [Agent]** Implement the photo-folder reader using stills alone; folder names are IDs, not secretly supplied adjacency. **Done when:** it emits usable frames and source references without reading LiDAR/video/tape truth.
- [ ] **T18 [Agent]** Implement an ordinary standalone MP4/MOV reader and bounded frame sampler. **Done when:** it handles a Camera walkthrough without sidecar depth or poses.
- [ ] **T19 [Agent]** Implement the existing Stray-style scan reader for `rgb.mp4`, `camera_matrix.csv`, `odometry.csv`, `imu.csv`, and depth/confidence PNGs. **Done when:** all three supplied scans load, align by frame ID, and preserve original units and missing-data warnings.
- [ ] **T20 [Agent]** Verify the three supplied scans beyond filename counts: decode video, sample depth/confidence values, inspect timestamps/pose continuity, and document camera-to-depth calibration assumptions. **Done when:** `reports/input_audit.md` states what was measured and what remains unverified.
- [ ] **T21 [Agent]** Implement the project JSON writer and schema validator for `schema/property_plan.schema.json`; add semantic checks for unique/cross-referenced IDs, positive/consistent measurements, interval containment of the point estimate, valid geometry, and room overlap. **Done when:** a generated run validates, and malformed references/intervals are rejected with clear errors.
- [ ] **T22 [Agent]** Implement a homeowner-readable rendered whole-property plan (SVG or PDF/PNG) from the same output data. **Done when:** rooms, connectors, walls, openings, dimensions, damage, and uncertainty/warnings are visible and consistent with the JSON.
- [ ] **T23 [Agent]** Make every tier emit the **full common contract**, with explicit `unknown`/unbounded fields when evidence is inadequate. **Done when:** photo, video, and LiDAR runs each write JSON, rendered plan, run log, and schema/semantic validation status from one command.

## 3. LiDAR geometry and drift — P0/P1

- [ ] **T24 [Agent]** Convert aligned depth pixels, intrinsics, and camera poses to metric 3D points; downsample and filter low-confidence/outlier depth. **Done when:** point positions, axes, and units are checked against a known tape-measured distance, not inferred from appearance.
- [ ] **T25 [Agent]** Detect floor, ceiling, and wall planes despite furniture; estimate ceiling height, walls, corners, and floor area with per-surface provenance. **Done when:** one supplied room yields a consistent measured room plan and quality warnings.
- [ ] **T26 [Agent]** Find and size wall openings, including doors/windows, using depth gaps and RGB evidence; keep missed/uncertain detections visible. **Done when:** each opening has a stable wall link, width, height, and offset measurement.
- [ ] **T27 [Agent]** Detect room transitions and assemble a single plan for a multiroom LiDAR scan, including its connector. **Done when:** every captured room is placed once with candidate adjacency and no hidden hand placement.
- [ ] **T28 [Agent]** Add accumulated-drift correction (for example loop closure/pose graph or shared-plane constraints) and an `on/off` switch. **Done when:** the same multiroom input produces two recorded stitched footprints and a quantitative ablation; poses used as-is alone are not the final method.
- [ ] **T29 [Agent]** Preserve failures around glass, mirrors, wet-look surfaces, low light, tracking loss, and unobserved ceilings as warnings and wider intervals. **Done when:** these cases are traceable in plan/run quality reports rather than silently treated as valid depth.

## 4. Ordinary video and photo geometry — P0/P1

- [ ] **T30 [Agent]** For video, match sampled frames and estimate camera movement/scene structure using a CPU-feasible method; record frame rejection and tracking gaps. **Done when:** a standalone Camera clip produces a room/transition hypothesis without LiDAR data.
- [ ] **T31 [Agent]** For video, identify rooms, shared doorways, walls/openings, and a stitched property layout. **Done when:** a fresh multiroom walkthrough generates one connected plan with labelled dimensions and quality warnings.
- [ ] **T32 [Agent]** Define and disclose any video scale prior or learned metric-depth aid; never feed reference tape measurements into inference. **Done when:** the output distinguishes observed from inferred scale and reports honest intervals.
- [ ] **T33 [Agent]** For photos, extract wall/corner/doorway evidence from 2–8 unposed stills per room. **Done when:** each folder can yield a room hypothesis with full-wall coverage warnings.
- [ ] **T34 [Agent]** Stitch photo rooms using shared doorway views, room boundaries, and geometry optimization; handle the connector and reject overlaps. **Done when:** the complete multiroom photo-folder set produces one property plan and an adjacency graph.
- [ ] **T35 [Agent]** Define and disclose any photo scale prior or small depth model; test its CPU/cloud latency and licensing before adoption. **Done when:** arbitrary photos still produce a contract-compliant result, with unbounded estimates where metric scale cannot be supported.
- [ ] **T36 [Agent]** Record alternate/unresolved room placements when photos lack connection evidence; do not silently assert a unique layout. **Done when:** ambiguity appears in JSON and plan warnings while the one-property artifact still exists.
- [ ] **T37 [Agent]** Limit frames/images/model calls to fit the no-GPU machine and log all selection rules. **Done when:** one fresh capture per tier is timed end to end and reduction choices are reproducible.

## 5. Damage, concealed flags, and scope — P0/P1

- [ ] **T38 [Both]** Freeze a first visible-damage vocabulary and pick the two benchmark classes from credible damage available or safely staged at home. **Done when:** `docs/damage_vocabulary.md` gives class definitions and ground-truth marking instructions before scoring.
- [ ] **T39 [Owner]** Capture and tape-measure the two damage regions in the furnished benchmark room; label exact room/surface/class and record staging method. **Done when:** independent reference polygons/extents and raw photos/video/LiDAR views exist.
- [ ] **T40 [Agent]** Compare a simple local image method with a free disclosed cloud vision model on labelled samples; measure class/region quality, cost/quota, latency, and data handling. **Done when:** a chosen live path is justified by measured evidence, with its exact model/API version logged.
- [ ] **T41 [Agent]** Find visible damage regions and map image pixels to the correct room surface; derive metric width/height/area (and crack length where applicable). **Done when:** each reported region has class, surface ID, evidence, and an interval on every extent.
- [ ] **T42 [Agent]** Implement versioned concealed-damage rules with exact trigger evidence and cautious wording. **Done when:** each fired flag names a rule and surface and asserts suspicion rather than unseen fact; non-fired rules are auditable.
- [ ] **T43 [Agent]** Implement surface-keyed scope items with work type, quantity, and conditional inspection/repair logic. **Done when:** items reference real surfaces/damage IDs, do not invent hidden repair quantities, and remain empty when unsupported.

## 6. Uncertainty and evaluator — P1

- [ ] **T44 [Agent]** Wrap every wall, ceiling, area, opening, and damage extent in the project measurement/interval representation; target proposed 90% coverage unless scorer instructions supersede it. **Done when:** no numeric physical measurement lacks units, bounds/method, status, and evidence references.
- [ ] **T45 [Agent]** Split calibration and held-out evaluation by **property**, not by frames or walls from the same home; fit tier/quantity-specific error margins and quality-based widening. **Done when:** run metadata proves reference values were never read by prediction and the calibration procedure is repeatable.
- [ ] **T46 [Agent]** Report coverage, interval width, unbounded/unknown rate, sample counts, and point-estimate error for each tier and measurement type. **Done when:** an all-wide or all-unknown strategy cannot be presented as calibrated success.
- [ ] **T47 [Agent]** Build a benchmark manifest joining raw capture IDs, room/surface/opening/damage IDs, app versions, tape/laser truth, and repeated captures. **Done when:** every reported number traces to a raw file and independent reference row.
- [ ] **T48 [Agent]** Implement opening matching/scoring: one-to-one same-type/wall/position assignment, width ≤2 cm, missed and phantom counts, ≥85% denominator. **Done when:** the table lists every real, matched, over-tolerance, missed, and invented opening.
- [ ] **T49 [Agent]** Implement ceiling-height absolute error ≤1.5 cm **per room** and repeat spread ≤1 cm; distinguish biased from unrepeatable. **Done when:** both diagnostics appear for any repeat-captured room.
- [ ] **T50 [Agent]** Implement per-wall repeatability for two same-tier captures, reporting both interpretations of “1 cm or 0.5%” and the conservative working pass. **Done when:** all corresponding walls appear, not only an average.
- [ ] **T51 [Agent]** Implement photo/video wall-length gates (±8%/±3%), photo adjacency/no-overlap, and photo footprint area/shape checks. **Done when:** per-wall/room/property errors and the exact plan alignment are saved.
- [ ] **T52 [Agent]** Implement drift-ablation comparison, damage-class/surface/extent evaluation, schema/execution gate, and per-tier timing. **Done when:** a single benchmark command regenerates every gate table from frozen outputs and truth.
- [ ] **T53 [Agent]** Publish working scorer definitions before the baseline and never change them after seeing results without preserving both versions. **Done when:** scorer code revision and definitions are linked in the benchmark report.

## 7. Home benchmark capture and reference truth — P1; Owner critical path

- [ ] **T54 [Owner]** Choose and label a home area with **three or more rooms plus a connector**; note any stairs/floors and ensure all required spaces can be entered. **Done when:** a room map/ID list exists before scanning.
- [ ] **T55 [Owner]** Capture the **same complete property** at photo tier: one folder per room/connector, 2–8 stills each, every wall/corner/opening/ceiling/floor edge/damage region, doorways from both sides. **Done when:** original stills and transfer metadata are preserved.
- [ ] **T56 [Owner]** Capture a separate ordinary Camera walkthrough of the same property, continuous through connectors and all doors. **Done when:** an original standalone clip exists without depth/pose sidecars.
- [ ] **T57 [Owner]** Capture the same property in Stray Scanner LiDAR mode with revisit/loop-closure opportunity; preserve the complete export. **Done when:** RGB, depth, confidence, intrinsics, and pose data are transferred unmodified.
- [ ] **T58 [Owner]** Independently capture at least one room **twice at the same tier**, following the same protocol and without selecting the better run. **Done when:** two separate capture IDs exist for repeatability.
- [ ] **T59 [Owner]** Tape-measure all scored wall lengths, openings, ceiling heights, damage extents, and footprint dimensions; record method, units, IDs, and repeated readings where practical. **Done when:** a ground-truth sheet links each value to a physical feature and stays separate from inference inputs.
- [ ] **T60 [Both]** Include documented mirror, glass, reflective/wet-look, and low-light examples and record any safe recapture conditions. **Done when:** raw evidence and failure/quality notes exist, not just a report claim.
- [ ] **T61 [Agent]** Import the home captures without altering originals, run all three tiers cold, and freeze raw outputs before reading tape truth for scoring. **Done when:** three linked run IDs and immutable raw outputs exist.
- [ ] **T62 [Agent]** Audit benchmark composition against the exact brief and capture missing material promptly. **Done when:** matched multiroom all-tier inputs, furnished two-class damage, repeat room, and reference truth are all present or explicitly marked missing.

## 8. Consumer-app head-to-head — P1

- [ ] **T63 [Owner]** Install magicplan, report installed version and whether its free account exports a dimensioned plan. **Done when:** an actual unedited free-tier export is available; if unavailable, select/test another free comparator and document the reason.
- [ ] **T64 [Both]** Preselect two distinct benchmark rooms and the eligible wall/opening/height dimensions **before** seeing comparison errors. **Done when:** the frozen list and reference IDs are recorded.
- [ ] **T65 [Owner]** Scan the two rooms with magicplan on the same phone/site visit, with no manual truth-based correction; save original exports and actions taken. **Done when:** both app exports and versions are in the raw benchmark bundle.
- [ ] **T66 [Agent]** Build the dimension-by-dimension table with independent truth, our error, app error, win/tie/loss, omissions, and reported precision. **Done when:** both literal shared-only ≥70% score and the owner-requested expanded score (accurate ours-only dimensions may win) are reported separately.
- [ ] **T67 [Agent]** Predeclare an absolute LiDAR wall-length accuracy limit for ours-only dimensions before the baseline; opening/height limits are already in the brief. **Done when:** the expanded score cannot select its tolerance after results are visible.

## 9. The scored fix loop — P1; must follow a complete baseline

- [ ] **T68 [Agent]** Run the complete benchmark with frozen evaluator/scorer code and save all results, including failed runs. **Done when:** before run IDs, source revision, data hashes, plans, and every gate value are immutable.
- [ ] **T69 [Agent]** Rank eligible failed gates by the predeclared relative-gap rule; if execution/schema fails, treat it as the blocking failure first. **Done when:** the single selected worst gate and its failing number can be independently recomputed.
- [ ] **T70 [Agent]** Write and commit the **one-page fix declaration before editing the fix**: gate/failing number, root-cause hypothesis with evidence, intended fix, and one numeric after prediction. **Done when:** a dated source revision preserves the original prediction.
- [ ] **T71 [Agent]** Implement the declared fix and commit it as a coherent milestone. **Done when:** code or capture protocol genuinely changes the identified failure path; diagnosis alone is insufficient.
- [ ] **T72 [Agent]** Rerun the same raw inputs and truth with the same evaluator (or controlled paired recaptures for a protocol fix). **Done when:** after outputs, plans, timings, and metrics regenerate from documented commands.
- [ ] **T73 [Agent]** Produce a readable code/protocol and result/plan diff; compare observed with predicted score, threshold, other-gate regressions, and remaining error. **Done when:** `fix_loop/` contains declaration, before/after manifests, diff, and honest post-mortem.

## 10. Final submission and live-defense rehearsal — P2

- [ ] **T74 [Agent]** Write a clean-machine `README.md` with setup, weight/data provisioning, optional cloud key handling, exact one-command capture invocation, inputs, outputs, and troubleshooting. **Done when:** a new Ubuntu 24.04 environment follows it without undocumented steps.
- [ ] **T75 [Agent]** Time the conservative 15-minute path from clean repo/data access through install, transfer, model provisioning/cloud calls, processing, validation, and rendered output; separately report capture time. **Done when:** measured setup, transfer, processing, total, download bytes, and hardware are in the benchmark report for each tier.
- [ ] **T76 [Agent]** Reproduce **every reported benchmark number** from original raw captures, truth, frozen code/model/API records, and cache where permitted; separately run live on a fresh unseen capture. **Done when:** rerun tables match and the live path has its own run ID.
- [ ] **T77 [Agent]** Package raw captures, reference sheet, app exports, model weights/fetch scripts, deterministic caches, SHA-256 manifest, and unpack instructions outside ordinary Git. **Done when:** a clean copy can verify hashes and regenerate results without our infrastructure.
- [ ] **T78 [Agent]** Write `reports/benchmark.md` with all three tiers, every gate, interval calibration/width, repeatability, drift on/off, head-to-head, difficult surfaces, failures, and timing. **Done when:** each table points to raw IDs, reference IDs, and run IDs.
- [ ] **T79 [Agent]** Write a technical report of **at most six pages**: architecture, tier/device design, drift, error budget, calibration, fix-loop story, and known failure modes. **Done when:** a rendered PDF meets the page cap and matches benchmark evidence.
- [ ] **T80 [Agent]** Update `COMPLIANCE.md` with the final real artifact paths and truthful complete/partial/failing statuses; audit all eight deliverables and every scored component. **Done when:** no requirement is left without a file/artifact/status entry.
- [ ] **T81 [Both]** Have someone unfamiliar with the system follow the one-page protocol and run a **new** photo, video, or LiDAR capture; repeat until all three tier paths have been rehearsed cold. **Done when:** no author-specific knowledge or hidden manual correction is needed to get JSON and a recognizable plan.
- [ ] **T82 [Agent]** Check source/model/API licenses and disclosures, third-party data transfer, no use of our infrastructure, no committed secrets, and all large-file paths. **Done when:** the final reports name every external component and the live path runs under documented conditions.
- [ ] **T83 [Agent]** Freeze the final Git revision and submission bundle; rerun schema validation, semantic checks, compliance audit, and checksum verification. **Done when:** a reviewer can map the submitted revision to every reported run and reproduce the final numbers.

## Stop conditions and honest reporting

- If an input tier cannot produce the complete schema and rendered whole-property plan, mark its execution gate **failing**. A local cache or hand-edited plan does not satisfy a fresh walk-in run.
- If photo/video evidence cannot establish true scale or adjacency, preserve the best hypothesis and uncertainty; do not feed tape truth into inference or claim a calibrated finite interval without evidence. The strict scorer may still mark it failing.
- If 90% intervals are based on too few independent properties, report the sample count and observed coverage; do not call them calibrated merely because they contain the development home's measurements.
- If the free cloud path or stock app is unavailable, record the failure, use a tested free alternative if possible, and keep raw/request/response or local model provenance sufficient for reproduction.
- The benchmark cannot substitute for the live walk-in test; the before/after fix cannot substitute for a runnable final pipeline; a polished report cannot substitute for either.
