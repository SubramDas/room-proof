# RoomProof execution tasks

**Deadline:** 4 October 2026, 10:00 a.m. Asia/Kolkata. **Status:** input quality checks exist; geometry reconstruction and scored outputs are not implemented. This checklist implements [SPEC.md](SPEC.md). It is a work tracker, not evidence that a requirement has passed. Tick an item only after its stated output exists and has been checked.

**People:** `Agent` = work I can do in this repository; `Owner` = phone capture, physical measurement, or account/device access that you provide; `Both` = coordinated work. The owner may send captures while agent work continues. **P0** items unlock a fresh capture at each tier; **P1** items satisfy the benchmark and scored gates; **P2** items package and defend the result. Every requirement remains mandatory even where a priority marks execution order.

**Execution and journal rule:** After setup, run every project Python command through `.venv/bin/python`; system `python3` is used only to create the environment. Maintain a root-level `Journal-<phase number>.md` for each numbered section below. Record evidence as work lands and update the journal when that phase completes, including remaining failures and run IDs. [Journal-0.md](Journal-0.md) records the foundation work so far; Phase 0 remains open while T02 and T08 are unchecked.

**Current evidence:** `SPEC.md` and project schema v0.1.0 exist. The three starter LiDAR-style exports and one owner Stray Scanner 1.4 test scan are in an ignored SHA-256 bundle; the owner ZIP and extracted copy represent the same physical recording. The owner scan has a machine-readable format report and a one-frame RGB/depth count mismatch. It does not supply matched photo/video/home benchmark, tape truth, or comparator exports. Do not present planning artifacts, synthetic example numbers, or byte-verification runs as benchmark results.

## Critical path and dependency map

1. **Immediately:** freeze the working interface and capture guide; validate the supplied LiDAR format; establish one-command runs, logging, and schema/rendered outputs.
2. **In parallel with code work:** capture the home at all three tiers and measure it independently. The benchmark, calibration, head-to-head, and fix loop cannot finish until these files exist.
3. **Before choosing a fix:** run every tier on the same benchmark, freeze gate definitions and the failing baseline, then write the one-page prediction.
4. **Before submission:** ship the fix, reproduce before/after, complete the comparator, and rehearse a genuinely new capture from a clean environment.

The deadline makes **early home capture and tape truth** the largest scheduling dependency. Do not postpone them until the pipeline is polished. Preserve a truthful partial/failing status wherever a gate remains unmet.

## 0. Repository, decisions, and reproducibility foundation — P0

- [x] **T00 [Agent]** Review `SPEC.md`, schema, and this tracker for conflicting assumptions; resolve the working choices in one decision log. **Done when:** `docs/decisions.md` records Route 2, all-tier contract, proposed 90% interval target, scorer assumptions, and known information limits.
- [x] **T01 [Agent]** Commit the discovery milestone (`SPEC.md`, `.gitignore`, schema, example, `TASK.md`) with a message that states the current status. **Done when:** Git history shows this work after the initial spec commit, with no raw dataset committed.
- [ ] **T02 [Agent]** Define stable property, room, surface, opening, damage, capture, and run IDs. **Done when:** a small manifest format and naming rules are documented and reused by outputs/evaluation. Naming rules and capture/run manifests exist; property-plan outputs and evaluator must still reuse the physical IDs.
- [x] **T03 [Agent]** Create `COMPLIANCE.md` from every contract row and deliverable, with requirement → real path → evidence artifact/run ID → status. **Done when:** missing items are explicitly `not started` or `failing`, never silently omitted.
- [x] **T04 [Agent]** Choose the zero-cost implementation stack, pin dependency versions, and write setup scripts for Ubuntu 24.04/i7-1265U without a dedicated GPU. **Done when:** a clean environment can install and print a working CLI version; record disk/download cost. Python 3.12.3 plus hash-pinned imageio-ffmpeg 0.6.0 for HEVC audit; new cached-wheel setup measured 14.65 s and 92 MB. Future geometry dependencies must be pinned when added.
- [x] **T05 [Agent]** Create immutable raw-data import rules: SHA-256 hashes, source metadata, no in-place editing, and separate derived outputs. **Done when:** a capture manifest links every imported file and its checksum. Three starter scans imported with 33,434 file records; device/app fields remain unknown.
- [x] **T06 [Agent]** Choose a reproducible large-file delivery method (content-addressed local bundle or DVC with a supplied volume). **Done when:** a second clean directory can obtain exact raw files by documented steps and verify checksums. Do not rely on `.gitignore` as data delivery. All three starter manifests verified in a separate copy; final submission volume remains to be chosen.
- [x] **T07 [Agent]** Define run logging: command/config, code and data revision, model/API version, seed, stage times, status/warnings, metrics, and artifact hashes. **Done when:** every command, including a failed one, writes a diagnosable run manifest. Current CLI commands checked; later pipeline commands must use the same wrapper.
- [ ] **T08 [Agent]** Keep meaningful commits as each verified milestone lands; preserve unsuccessful experiments and the before/after fix revisions. **Done when:** history reflects actual work, with no fabricated or squashed fix-loop evidence. Foundation is committed at `dd30e38`; this stays open until the later baseline, failed experiments, fix declaration, fix implementation, and before/after evidence are preserved.

## 1. Route 2 capture and device validation — P0

- [x] **T09 [Agent]** Draft a **one-page** stock-capture protocol for Camera photos, Camera video, and Stray Scanner LiDAR. State install/permissions, exact settings, room labels, 2–8 photos per room, full wall/floor/ceiling/opening/damage coverage, doorway views from both sides, walk path, recapture triggers, export, and handoff. **Done when:** `protocols/stock_capture.md` can be followed literally without technical interpretation. Draft exists; T12 may require revisions.
- [x] **T10 [Owner]** Install Stray Scanner on the iPhone 15 Pro Max (iOS 26.5), report its installed version, and export one short unedited test scan. **Done when:** original files and app/version/settings are available to inspect. Owner supplied `dummy_room.zip`, Stray Scanner 1.4, default settings, and extracted `dummy_room/`; iOS 26.5 is from the earlier owner report.
- [x] **T11 [Agent]** Validate the owner scan against the existing importer assumptions: RGB/depth frame correspondence, depth unit, intrinsics, pose convention, timestamp alignment, confidence, and transfer completeness. **Done when:** a machine-readable format report names every field and any mismatch. `reports/device_format_dummy_room.json` records one missing RGB frame and unverified coordinate/scale assumptions.
- [ ] **T12 [Both]** Try the protocol with a non-engineer using only the one-page instructions; record install/capture/export/transfer duration and points of confusion. **Done when:** the protocol is revised from observed errors and successfully repeated. Owner reports a trial under five minutes; timing breakdown, help needed, and repeat evidence are pending.
- [x] **T13 [Agent]** Publish `docs/device_matrix.md`: photos/video on any iPhone 15+, LiDAR only on LiDAR-capable Pro devices, minimum iOS for the chosen app, and measured rather than invented per-tier accuracy. **Done when:** device and unsupported-sensor handling are clear. Matrix explicitly states that no accuracy has been measured yet.
- [x] **T14 [Agent]** If Stray Scanner's actual free export fails, test the named free fallback (Scan4D), update the importer/protocol, and record why. **Done when:** one free Route 2 LiDAR workflow is validated end to end, or the failure is explicitly reported. Actual Stray Scanner 1.4 capture → ZIP share → transfer → extraction → SHA-256 comparison → format audit succeeded. The one-frame RGB mismatch is explicitly documented; Scan4D fallback was not triggered. Importer handling remains in Phase 2.

## 2. Input contracts and one-command skeleton — P0

- [x] **T15 [Agent]** Implement one documented CLI entry point taking a capture path and tier (`photo`, `video`, `lidar`) and creating a unique run directory. **Done when:** the same command shape works for each tier without hidden manual preprocessing. `process-capture PATH --tier ...` writes a unique run manifest and quality report for each tier.
- [x] **T16 [Agent]** Accept/reject input explicitly: corrupt or duplicate media, missing photo folders, fewer than 2 or more than 8 photos per room, missing depth/pose samples, unsupported device/tier, and empty clips. **Done when:** a quality report distinguishes invalid input from a valid low-confidence result. Checked per-room image counts/signatures and duplicate hashes, full video decode, LiDAR required files/frame IDs, unsupported LiDAR flag, and the owner scan's one-frame warning. Failures and low-confidence input produce distinct statuses.
- [x] **T17 [Agent]** Implement the photo-folder reader using stills alone; folder names are IDs, not secretly supplied adjacency. **Done when:** it emits usable frames and source references without reading LiDAR/video/tape truth. `frames.json` decodes/indexes each still by its `room-...` folder ID and source path/hash; it sets `adjacency_inferred: false`.
- [x] **T18 [Agent]** Implement an ordinary standalone MP4/MOV reader and bounded frame sampler. **Done when:** it handles a Camera walkthrough without sidecar depth or poses. `process-capture` samples at most 24 frames by default in evenly spaced short bursts, scales to 640 px wide, writes RGB24 bytes and source-frame/timestamp references; limit is configurable. Phase 4 changed the selection rule to support visual matching.
- [x] **T19 [Agent]** Implement the existing Stray-style scan reader for `rgb.mp4`, `camera_matrix.csv`, `odometry.csv`, `imu.csv`, and depth/confidence PNGs. **Done when:** all three supplied scans load, align by frame ID, and preserve original units and missing-data warnings. Three starter scans load; depth/confidence/pose join by frame ID; unit basis and RGB mismatch warnings are retained; RGB links remain unresolved.
- [x] **T20 [Agent]** Verify the three supplied scans beyond filename counts: decode video, sample depth/confidence values, inspect timestamps/pose continuity, and document camera-to-depth calibration assumptions. **Done when:** `reports/input_audit.md` states what was measured and what remains unverified. Detailed measurements and limits are in the report and linked machine-readable audits.
- [x] **T21 [Agent]** Implement the project JSON writer and schema validator for `schema/property_plan.schema.json`; add semantic checks for unique/cross-referenced IDs, positive/consistent measurements, interval containment of the point estimate, valid geometry, and room overlap. **Done when:** a generated run validates, and malformed references/intervals are rejected with clear errors. Generated photo plan validated; inverted interval, duplicate ID, and broken surface reference were rejected with specific errors. Remaining complex geometry checks belong to later phases.
- [x] **T22 [Agent]** Implement a homeowner-readable rendered whole-property plan (SVG or PDF/PNG) from the same output data. **Done when:** rooms, connectors, walls, openings, dimensions, damage, and uncertainty/warnings are visible and consistent with the JSON. SVG renders the current unresolved spaces and warnings, and draws measured boundaries/wall labels when available; geometry inference remains in later phases.
- [x] **T23 [Agent]** Make every tier emit the **full common contract**, with explicit `unknown`/unbounded fields when evidence is inadequate. **Done when:** photo, video, and LiDAR runs each write JSON, rendered plan, run log, and schema/semantic validation status from one command. Runs `run-fbd12f7b257c45b2b521df4271bec260`, `run-f23e9dc871964234965af823f7fe2302`, and `run-5d1ba3b94ecf4bdd81b99b2b174ea6c6` generated the required artifacts.

## 3. LiDAR geometry and drift — P0/P1

- [x] **T24 [Agent]** Convert aligned depth pixels, intrinsics, and camera poses to metric 3D points; downsample and filter low-confidence/outlier depth. **Done when:** point positions, axes, and units are checked against a known tape-measured distance, not inferred from appearance. Hall projection uses vision camera axes and was compared after inference with the owner's separate laser dimensions; its remaining error is recorded in `reports/hall_pilot.md`.
  - [x] Decode frame-matched depth and confidence, apply per-frame intrinsics and poses, and write a bounded point cloud with source-frame provenance. Owner and starter runs are recorded in `Journal-3.md`.
  - [x] Reject low-confidence, out-of-range, and discontinuous depth samples; record selection rules and rejection counts in `lidar_geometry.json`.
  - [x] Check the projection's axes, units, and distance against the owner's hall laser dimensions. The resulting plan remains explicitly provisional and uncalibrated.
- [x] **T25 [Agent]** Detect floor, ceiling, and wall planes despite furniture; estimate ceiling height, walls, corners, and floor area with per-surface provenance. **Done when:** one supplied room yields a consistent measured room plan and quality warnings. The 128-frame hall run produces four walls, floor, ceiling, area, source references, and low-confidence warnings; see `reports/hall_pilot.md`.
  - [x] Add source-linked horizontal and vertical patch bins plus a quality-aware bounded frame sampler. Flat-805 runs improve retained depth but do not yet identify validated room surfaces.
  - [x] Add a hall-only rectangular fit with source-linked four walls, floor, ceiling, dimensions, area, and a provisional SVG. Reference-error tuning is deferred while the pipeline is built.
- [ ] **T26 [Agent]** Find and size wall openings, including doors/windows, using depth gaps and RGB evidence; keep missed/uncertain detections visible. **Done when:** each opening has a stable wall link, width, height, and offset measurement.
  - [x] Carry depth-gap candidates into the plan with stable wall links, provisional width/offset, unknown height, and an explicit unverified status. RGB confirmation, windows, and complete sizing remain open.
- [ ] **T27 [Agent]** Detect room transitions and assemble a single plan for a multiroom LiDAR scan, including its connector. **Done when:** every captured room is placed once with candidate adjacency and no hidden hand placement.
- [ ] **T28 [Agent]** Add accumulated-drift correction (for example loop closure/pose graph or shared-plane constraints) and an `on/off` switch. **Done when:** the same multiroom input produces two recorded stitched footprints and a quantitative ablation; poses used as-is alone are not the final method.
  - [x] Record bounded pose-return candidates from the Flat-805 trajectory; no similar-orientation closure was supported, so no correction or ablation is claimed.
  - [x] Add `--lidar-drift on|off`, a conservative same-view 3D overlap constraint, and paired occupied-depth footprint diagnostics. The earlier Flat-805 scan had no verified closure, so its on/off footprint was identical; this did not pass the stitched-footprint acceptance gate.
  - [x] The replacement Flat-805 scan supports one verified same-view constraint after reserving bounded revisit frames. On/off occupied-depth-cell areas are 34.23/34.29 m², respectively; these are still not stitched room/property footprints.
- [ ] **T29 [Agent]** Preserve failures around glass, mirrors, wet-look surfaces, low light, tracking loss, and unobserved ceilings as warnings and wider intervals. **Done when:** these cases are traceable in plan/run quality reports rather than silently treated as valid depth.
  - [x] Record large consecutive pose jumps and weak sampled depth coverage in the geometry report and plan warnings.
  - [x] Record per-frame depth rejection counts, weak-depth frame IDs, and weak lower/upper horizontal support warnings; preserve unbounded measurements when surface identity is unverified.
  - [x] Sample RGB frames independently for a scan-level low-light heuristic without assuming the unresolved RGB/depth time pairing. Flat-805 sampled 32 RGB frames and flagged none as dark; this does not validate light at each depth frame.
  - [ ] Diagnose glass, mirrors, wet-look surfaces, low light, and unobserved ceilings from capture evidence; widen affected measurement intervals.

## 4. Ordinary video and photo geometry — P0/P1

- [ ] **T30 [Agent]** For video, match sampled frames and estimate camera movement/scene structure using a CPU-feasible method; record frame rejection and tracking gaps. **Done when:** a standalone Camera clip produces a room/transition hypothesis without LiDAR data.
  - [x] Match nearby RGB frames without sidecars and record supported image motion, frame quality, sampling gaps, and tracking gaps. Run `run-4cbe8839016e46acb2936a45cca58e33` supports 14 of 18 within-burst transitions.
  - [x] Audit a one-frame-per-second appearance-change baseline on the real flat walkthrough. Run `run-08357569b6104024adcda7c6af3a1b88` flagged turns near 35, 103, and 108 seconds as false room-transition candidates; keep this baseline as a documented failure, not a room detector.
  - [ ] Infer a defensible room/transition hypothesis and scene structure from those tracks.
- [ ] **T31 [Agent]** For video, identify rooms, shared doorways, walls/openings, and a stitched property layout. **Done when:** a fresh multiroom walkthrough generates one connected plan with labelled dimensions and quality warnings.
- [x] **T32 [Agent]** Define and disclose any video scale prior or learned metric-depth aid; never feed reference tape measurements into inference. **Done when:** the output distinguishes observed from inferred scale and reports honest intervals. Current method uses no metric prior or depth aid; `visual_geometry.json` marks scale unidentifiable, and the common JSON keeps physical measurements null with unbounded 90% intervals. No tape values enter inference.
- [ ] **T33 [Agent]** For photos, extract wall/corner/doorway evidence from 2–8 unposed stills per room. **Done when:** each folder can yield a room hypothesis with full-wall coverage warnings.
  - [x] Decode stills, extract generic visual corners, compare image overlap within and across folders, and record source-linked quality. A derived two-still fixture yielded 17 mutual matches and 11 coherent inliers in run `run-cdb77082c2ed4ea1add472f30e34a4b3`.
  - [x] Record long vertical and horizontal edge candidates on the owner's four-room still set; `run-5a0fcbff2e0b4bf58b5c78f9c855b1a8` keeps them unclassified because furniture and curtains also produce lines.
  - [ ] Identify wall and doorway evidence and assess full-wall coverage from an independent camera-photo capture.
- [ ] **T34 [Agent]** Stitch photo rooms using shared doorway views, room boundaries, and geometry optimization; handle the connector and reject overlaps. **Done when:** the complete multiroom photo-folder set produces one property plan and an adjacency graph.
- [ ] **T35 [Agent]** Define and disclose any photo scale prior or small depth model; test its CPU/cloud latency and licensing before adoption. **Done when:** arbitrary photos still produce a contract-compliant result, with unbounded estimates where metric scale cannot be supported.
- [x] **T36 [Agent]** Record alternate/unresolved room placements when photos lack connection evidence; do not silently assert a unique layout. **Done when:** ambiguity appears in JSON and plan warnings while the one-property artifact still exists. Run `run-732ee29b93a24b508091137148c1f4fc` writes one four-room artifact with `placement_ambiguities` and an SVG unresolved-placement label; no adjacency or dimensions are invented.
- [ ] **T37 [Agent]** Limit frames/images/model calls to fit the no-GPU machine and log all selection rules. **Done when:** one fresh capture per tier is timed end to end and reduction choices are reproducible.
  - [x] Time the owner Flat-805 photo and video runs on the local CPU: 30 stills and 256 candidate pairs in 17.68 s (`run-732ee29b93a24b508091137148c1f4fc`); 24 motion frames plus a one-frame-per-second scene pass in 9.92 s (`run-08357569b6104024adcda7c6af3a1b88`). Selection rules are recorded in `frames.json` and `visual_geometry.json`.
  - [ ] Time and assess an end-to-end scored output before closing this gate.
  - [x] Matched Flat-805 LiDAR development run `run-0292663a46e44a7ba792dfcc5cbc72ee` took 26.78 s, selecting 32 of 3,302 depth frames; 20,730 diagnostic points. No scored output yet.

## 5. Damage, concealed flags, and scope — P0/P1

- [ ] **T38 [Both]** Freeze a first visible-damage vocabulary and pick the two benchmark classes from credible damage available or safely staged at home. **Done when:** `docs/damage_vocabulary.md` gives class definitions and ground-truth marking instructions before scoring.
- [ ] **T39 [Owner]** Capture and tape-measure the two damage regions in the furnished benchmark room; label exact room/surface/class and record staging method. **Done when:** independent reference polygons/extents and raw photos/video/LiDAR views exist.
- [ ] **T40 [Agent]** Compare a simple local image method with a free disclosed cloud vision model on labelled samples; measure class/region quality, cost/quota, latency, and data handling. **Done when:** a chosen live path is justified by measured evidence, with its exact model/API version logged.
- [ ] **T41 [Agent]** Find visible damage regions and map image pixels to the correct room surface; derive metric width/height/area (and crack length where applicable). **Done when:** each reported region has class, surface ID, evidence, and an interval on every extent.
- [ ] **T42 [Agent]** Implement versioned concealed-damage rules with exact trigger evidence and cautious wording. **Done when:** each fired flag names a rule and surface and asserts suspicion rather than unseen fact; non-fired rules are auditable.
  - [x] Add a versioned source-evidence-gated rule function; no live damage detector supplies it yet.
- [ ] **T43 [Agent]** Implement surface-keyed scope items with work type, quantity, and conditional inspection/repair logic. **Done when:** items reference real surfaces/damage IDs, do not invent hidden repair quantities, and remain empty when unsupported.
  - [x] Add conditional surface-linked items for supplied visible regions; live region input remains absent.

## 6. Uncertainty and evaluator — P1

- [x] **T44 [Agent]** Wrap every wall, ceiling, area, opening, and damage extent in the project measurement/interval representation; target proposed 90% coverage unless scorer instructions supersede it. **Done when:** no numeric physical measurement lacks units, bounds/method, status, and evidence references. `schema/property_plan.schema.json` and `roomproof/plan.py` enforce the representation, with unknown/unbounded values until calibrated.
- [ ] **T45 [Agent]** Split calibration and held-out evaluation by **property**, not by frames or walls from the same home; fit tier/quantity-specific error margins and quality-based widening. **Done when:** run metadata proves reference values were never read by prediction and the calibration procedure is repeatable.
- [ ] **T46 [Agent]** Report coverage, interval width, unbounded/unknown rate, sample counts, and point-estimate error for each tier and measurement type. **Done when:** an all-wide or all-unknown strategy cannot be presented as calibrated success.
- [ ] **T47 [Agent]** Build a benchmark manifest joining raw capture IDs, room/surface/opening/damage IDs, app versions, tape/laser truth, and repeated captures. **Done when:** every reported number traces to a raw file and independent reference row.
- [ ] **T48 [Agent]** Implement opening matching/scoring: one-to-one same-type/wall/position assignment, width ≤2 cm, missed and phantom counts, ≥85% denominator. **Done when:** the table lists every real, matched, over-tolerance, missed, and invented opening.
  - [x] Add one-to-one matching and full outcome rows in the reference-only scorer; real truth remains pending.
- [ ] **T49 [Agent]** Implement ceiling-height absolute error ≤1.5 cm **per room** and repeat spread ≤1 cm; distinguish biased from unrepeatable. **Done when:** both diagnostics appear for any repeat-captured room.
  - [x] Add per-room reference error and repeat spread; repeated room capture remains pending.
- [ ] **T50 [Agent]** Implement per-wall repeatability for two same-tier captures, reporting both interpretations of “1 cm or 0.5%” and the conservative working pass. **Done when:** all corresponding walls appear, not only an average.
  - [x] Add per-wall strict and permissive rows; repeated room capture remains pending.
- [ ] **T51 [Agent]** Implement photo/video wall-length gates (±8%/±3%), photo adjacency/no-overlap, and photo footprint area/shape checks. **Done when:** per-wall/room/property errors and the exact plan alignment are saved.
  - [x] Add wall error, footprint area, and adjacency comparison; outline alignment and overlap checks remain pending.
- [ ] **T52 [Agent]** Implement drift-ablation comparison, damage-class/surface/extent evaluation, schema/execution gate, and per-tier timing. **Done when:** a single benchmark command regenerates every gate table from frozen outputs and truth.
- [ ] **T53 [Agent]** Publish working scorer definitions before the baseline and never change them after seeing results without preserving both versions. **Done when:** scorer code revision and definitions are linked in the benchmark report.

## 7. Home benchmark capture and reference truth — P1; Owner critical path

- [ ] **T54 [Owner]** Choose and label a home area with **three or more rooms plus a connector**; note any stairs/floors and ensure all required spaces can be entered. **Done when:** a room map/ID list exists before scanning.
  - [x] Flat-805 has bed, kitchen, toilet, and confirmed hall connector; owner reference connections are bed–hall, hall–toilet, hall–kitchen. Stairs/floor note remains pending.
- [ ] **T55 [Owner]** Capture the **same complete property** at photo tier: one folder per room/connector, 2–8 stills each, every wall/corner/opening/ceiling/floor edge/damage region, doorways from both sides. **Done when:** original stills and transfer metadata are preserved.
- [ ] **T56 [Owner]** Capture a separate ordinary Camera walkthrough of the same property, continuous through connectors and all doors. **Done when:** an original standalone clip exists without depth/pose sidecars.
- [ ] **T57 [Owner]** Capture the same property in Stray Scanner LiDAR mode with revisit/loop-closure opportunity; preserve the complete export. **Done when:** RGB, depth, confidence, intrinsics, and pose data are transferred unmodified.
  - [x] Original Flat-805 Stray ZIP transferred; all 6,608 extracted files match the ZIP and the required streams decode. Room coverage/revisit still needs visual review.
- [ ] **T58 [Owner]** Independently capture at least one room **twice at the same tier**, following the same protocol and without selecting the better run. **Done when:** two separate capture IDs exist for repeatability.
- [ ] **T59 [Owner]** Tape-measure all scored wall lengths, openings, ceiling heights, damage extents, and footprint dimensions; record method, units, IDs, and repeated readings where practical. **Done when:** a ground-truth sheet links each value to a physical feature and stays separate from inference inputs.
  - [x] Owner supplied laser length, breadth, and ceiling height for all four rooms, stored outside prediction input; individual walls/openings, endpoints, repeats, and footprint remain pending.
  - [x] Owner supplied one door height 2.17 m and width 0.79 m; room/wall identity is pending, so it is not a scored opening reference yet.
- [ ] **T60 [Both]** Include documented mirror, glass, reflective/wet-look, and low-light examples and record any safe recapture conditions. **Done when:** raw evidence and failure/quality notes exist, not just a report claim.
- [ ] **T61 [Agent]** Import the home captures without altering originals, run all three tiers cold, and freeze raw outputs before reading tape truth for scoring. **Done when:** three linked run IDs and immutable raw outputs exist.
- [ ] **T62 [Agent]** Audit benchmark composition against the exact brief and capture missing material promptly. **Done when:** matched multiroom all-tier inputs, furnished two-class damage, repeat room, and reference truth are all present or explicitly marked missing.

## 8. Consumer-app head-to-head — P1

- [ ] **T63 [Owner]** Install magicplan, report installed version and whether its free account exports a dimensioned plan. **Done when:** an actual unedited free-tier export is available; if unavailable, select/test another free comparator and document the reason.
- [ ] **T64 [Both]** Preselect two distinct benchmark rooms and the eligible wall/opening/height dimensions **before** seeing comparison errors. **Done when:** the frozen list and reference IDs are recorded.
  - [x] Preselected bed and kitchen and all eligible wall/opening/height dimensions in `docs/flat805_comparator_preselection.md` before any app export; physical feature IDs remain pending.
- [ ] **T65 [Owner]** Scan the two rooms with magicplan on the same phone/site visit, with no manual truth-based correction; save original exports and actions taken. **Done when:** both app exports and versions are in the raw benchmark bundle.
- [ ] **T66 [Agent]** Build the dimension-by-dimension table with independent truth, our error, app error, win/tie/loss, omissions, and reported precision. **Done when:** both literal shared-only ≥70% score and the owner-requested expanded score (accurate ours-only dimensions may win) are reported separately.
  - [x] Add both scoring paths, explicit omissions, and per-dimension rows; app export/truth values remain pending.
- [x] **T67 [Agent]** Predeclare an absolute LiDAR wall-length accuracy limit for ours-only dimensions before the baseline; opening/height limits are already in the brief. **Done when:** the expanded score cannot select its tolerance after results are visible. Project working limit is 0.05 m absolute error in `roomproof/comparator.py`, frozen before benchmark results.

## 9. The scored fix loop — P1; must follow a complete baseline

- [ ] **T68 [Agent]** Run the complete benchmark with frozen evaluator/scorer code and save all results, including failed runs. **Done when:** before run IDs, source revision, data hashes, plans, and every gate value are immutable.
- [ ] **T69 [Agent]** Rank eligible failed gates by the predeclared relative-gap rule; if execution/schema fails, treat it as the blocking failure first. **Done when:** the single selected worst gate and its failing number can be independently recomputed.
  - [x] Add deterministic numeric-gate ranking; the complete baseline and execution/schema blocker check remain pending.
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

## 11. Model candidate pipeline and integration — P0/P1; execute before the scored baseline

**Goal:** Add a bounded model stage that proposes visible walls, wall/floor/ceiling boundaries, doors, windows, and shared-doorway evidence. Geometry and cross-view checks decide which proposals reach the existing property plan. Start with photo/video openings and wall cues because those paths currently have no room geometry; use LiDAR RGB only after its frame-to-depth relationship is established. Damage is a later extension once T38–T39 supply labelled classes and regions. This phase extends T26, T30–T37, T40–T41, and T44–T53; it does not replace their acceptance gates. Record work and remaining failures in `Journal-11.md` as it lands.

**Target mixed pipeline (LiDAR tier):** Read the original Stray RGB video, depth and confidence PNGs, per-frame camera intrinsics, odometry/poses, timestamps, and IMU data. VIO means visual **and inertial** odometry; the Stray export already contains estimated poses, so use and audit those first. Add independent VIO only if tracking/pose evidence shows it is needed and the capture supports it. Register RGB to depth/pose with a recorded offset and residual; reject unsupported frame pairs. Project confidence-filtered metric depth into 3D, fuse overlapping views, and fit floor, ceiling, walls, corners, and possible wall gaps. Detect visible openings in selected RGB frames, back-project their image regions using verified frame alignment, associate them with fitted wall surfaces and depth gaps, and merge repeated views of each physical opening. Correct drift with verified overlapping surfaces/loop constraints and compare correction on/off. Vectorize the supported geometry into room boundaries and opening extents, then write the existing source-linked `property_plan.json` and SVG with explicit unknowns and intervals. A fitted dimension is an estimate, never an exact value merely because it is expressed as a vector or box. Keep photo-only and standalone video tiers independent of LiDAR; combined LiDAR fusion applies only when that capture was provided as input.

**Intended free local models:** Pilot `google/owlv2-base-patch16-ensemble` (Apache-2.0 model card) first for text-conditioned RGB proposals such as doorway, door, window, and open passage; it supplies boxes/classes, not metric dimensions. Keep its selection conditional on owner-reviewed labels, CPU time/memory, false positives, and whether the *final plan* improves. Compare `TUI-NICR/ESANet` as the RGB-plus-depth semantic segmentation candidate once paired frames are verified; its source is Apache-2.0, but document the exact downloaded checkpoint's usage terms before any production adoption. Its pretrained indoor classes and sensor domain may differ from Stray/iPhone data, so evaluate rather than assume transfer. `facebookresearch/sam2` Hiera Tiny (Apache-2.0 checkpoints) is optional for masks after a class/box proposal; it is not a detector or measurement model. Open3D (MIT) is a geometry library, not an AI model. The current quantized SegFormer checkpoint is an evaluation-only pilot with noncommercial terms; do not silently ship it. Pin versions, checkpoint hashes, sources, dependencies, and license evidence for each adopted component. No paid API or GPU may be required for the baseline live path.

- [x] **T84 [Agent]** Define a versioned intermediate `visual_candidates.json` contract and the stage boundary. Each candidate must carry a stable candidate ID, capture/tier, source frame or photo ID and timestamp where available, proposed class, image-space line/box/polygon or mask, raw model score if supplied, model/preprocessing version, and `proposed`/`rejected`/`verified` status with reason and supporting or conflicting evidence. Record pixel coordinates in the decoded image's dimensions and preserve the original file reference and hash. Do not place a model's unverified dimension, adjacency, or score directly into `property_plan.json`. **Done when:** candidate files can be validated, traced to original pixels, and consumed without relying on a model-specific response format.
- [ ] **T85 [Both]** Prepare a small labelled development set from the existing Flat-805/hall photos and bounded video frames: visible wall boundaries and door/window regions, the wall containing each opening, matching doorway views across rooms where visible, occluded/ambiguous cases, and furniture or dark gaps as negatives. Have the owner review ambiguous labels. Record capture IDs, selected frame IDs, annotation instructions, and scene/property splits; keep independent laser dimensions and benchmark reference values outside inference. Identify missing two-sided doorway coverage before claiming topology recall. **Done when:** labels and splits are reproducible, omissions are explicit, and no frame from a held-out property was used to choose model settings.
- [ ] **T86 [Agent]** Freeze a no-model baseline on the same labelled captures using current `visual_geometry.json`, LiDAR depth-gap candidates, and full `property_plan.json`. Record wall/door candidate precision and recall, false openings, correct wall links, shared-doorway matches, final adjacency/geometry coverage, stage time, and run/code/data IDs; distinguish absent labels from model misses. **Done when:** a later model run can be compared against immutable source files and the same scoring definitions, including failures and unknown outputs.
- [ ] **T87 [Agent]** Pilot OWLv2 Base as the first free local visual candidate model for visible doors, doorways, windows, open passages, and wall-related cues, alongside the no-model baseline and the existing SegFormer pilot. Measure per-frame and end-to-end CPU time, peak memory, model/weight download and disk size, candidate precision/recall, false openings, and misses on the owner-reviewed labelled set. Record prompt wording, image selection, preprocessing, thresholds, exact weights hash, package versions, license/terms, deterministic settings, and source. A generic segmenter can refine a mask only after a class proposal. Do not select a model from one attractive example or its raw confidence score. **Done when:** a recorded comparison justifies adopting or rejecting OWLv2 against the frozen baseline and the live-run budget in T37/T75; the current research-only checkpoint is not promoted as a production dependency.
- [ ] **T88 [Agent]** Insert the adopted candidate stage into `process-capture` after the existing photo/video frame readers and before `build_plan`, with a bounded frame/image selection rule and one documented command per tier. Reuse original `frames.json` IDs and source references; log model stage timing, warnings, candidate artifact hash, model version, and selected frames in `run.json`/quality output. Photo inference may read only its room-folder stills; ordinary video inference may read only its standalone clip. Missing weights, model failure, or unsupported image quality must produce a diagnosable status and schema-valid unresolved output when the input itself remains valid. **Done when:** fresh photo and video captures run through the stage automatically, without hidden manual preprocessing or another tier's depth/poses.
- [ ] **T89 [Agent]** Gate LiDAR RGB use on verified RGB/depth/pose frame correspondence. Audit the one-frame mismatch and timing/offset evidence in each Stray export; attach visual candidates to metric planes only when the paired frame and projection are supported. Otherwise retain the depth-gap candidate as unverified with its original source references and no invented RGB confirmation. **Done when:** a LiDAR opening's visual evidence can be replayed to the source pixels and 3D wall, or the output explicitly records why pairing is unresolved.
- [ ] **T90 [Agent]** Connect candidates to the geometry and plan stages: associate image boundaries/openings with fitted walls, merge repeated views of one physical opening, test doorway agreement across rooms and capture sequence, and optimize placements subject to wall geometry, adjacency, and no-overlap constraints. Reject conflicting proposals and preserve multiple placements or unknown links when evidence is insufficient. Derive metric opening size/offset from supported geometry or a disclosed visual scale prior, never from model pixels alone. Update stable surface/opening/adjacency IDs, provenance, warnings, `property_plan.json`, and the SVG together through `roomproof/plan.py`. **Done when:** the same command produces a source-linked plan with traceable accepted/rejected candidates and no duplicate doorway or unsupported metric claim.
- [ ] **T91 [Both]** After T38–T39, extend the candidate contract to visible damage class and mask/polygon proposals, compare a simple local method with the selected model/cloud candidate as required by T40, and map accepted regions to a verified room/surface. Derive physical extent only from supported surface geometry, then feed the existing concealed-flag and scope rules; absence of a detection must not assert absence of damage. **Done when:** both labelled damage classes have per-region class, surface, geometry, source evidence, misses/false positives, latency, and interval accounting under T41–T43.
- [ ] **T92 [Agent]** Propagate candidate rejection, weak coverage, image/depth misalignment, tracking gaps, occlusion, and scale ambiguity into plan status and measurement intervals. Keep model scores separate from 90% prediction intervals; fit finite tier/quantity-specific intervals only with independent property-held-out calibration under T45, while retaining unknown/unbounded values where scale or surface identity cannot be established. **Done when:** every accepted physical number passes schema/semantic validation and the benchmark reports point error, interval coverage/width, and unknown rate without treating model confidence as calibrated accuracy.
- [ ] **T93 [Agent]** Run model-on/model-off comparisons through the complete `process-capture` and benchmark paths on real Stray, Camera photo, and standalone Camera video inputs, then repeat on an untouched capture. Score candidate detection and the final plan gates separately, including openings, wall/ceiling measurements, adjacency, damage when labelled, runtime, and schema validity. Record regressions as well as gains; retain raw artifacts, model hashes, run IDs, and exact commands. Update `docs/dependencies.md`, `README.md`, `COMPLIANCE.md`, `reports/benchmark.md`, and the clean-machine provisioning instructions for any adopted model. **Done when:** a reviewer can reproduce the model-on/off outputs from original captures, verify whether the final plan improved, and run the selected path within the documented hardware and time budget.
- [ ] **T94 [Agent]** Audit exported Stray trajectory quality using timestamp continuity, tracking/IMU signals when available, pose jumps, return-to-place views, and independent surface overlap. Preserve original exported poses and frame IDs. Implement a repeatable raw-pose versus verified pose-graph/shared-plane correction comparison, including an on/off switch; introduce a separate visual-inertial estimator only if exported poses fail documented checks and sufficient RGB/IMU data exists. **Done when:** the same hall and later multiroom capture produce two traceable trajectories/footprints, accepted constraints have replayable 3D evidence, rejected loops are logged, and changes in geometric error and runtime are reported without using tape measurements during inference.
- [ ] **T95 [Agent]** Extend depth projection to a bounded, confidence-weighted, multi-view metric fusion and surface stage. Verify depth units, camera axes, intrinsics, RGB-to-depth image transform and selected frame correspondence; mark holes, reflective/transparent surfaces, furniture occlusion, and tracking gaps. Fit supported floor, ceiling, wall planes and corner intersections, preserving per-surface frames/points and competing fits rather than forcing a rectangle on every room. Use Open3D where its CPU implementation helps, with pinned version and provenance. **Done when:** the hall's walls/height and at least one later non-rectangular or multiroom capture can be reproduced from source frames, and each reported boundary has support, residuals, warnings, and a corresponding `property_plan.json` reference.
- [ ] **T96 [Agent]** Integrate OWLv2 proposals into the existing `visual_candidates.json` adapter for photo, video, and verified LiDAR RGB samples. For LiDAR only, project candidate boxes/rays into depth and fitted walls; seek agreement with wall gaps, vertical sides, lintels, floor contact, and repeat views. Distinguish a door leaf, cabinet door, doorway, window, and open passage; reject occlusions/dark furniture as openings where evidence conflicts. Do not turn a detector box or light discontinuity alone into a measured opening. **Done when:** model-on/off runs record every proposed, accepted, rejected, and unresolved opening with source pixels, wall/pose/depth support, stable IDs, false-positive/miss counts, and any metric width/height/offset derived from 3D geometry.
- [ ] **T97 [Agent]** After T89/T95 establish reliable RGB-depth alignment, compare ESANet's downloaded indoor RGB-D checkpoint against OWLv2 plus geometry and the no-model baseline on the same labelled hall frames. Map its semantic classes to the RoomProof candidate vocabulary without inventing door/window labels it cannot represent. Measure CPU runtime/memory and effect on wall/opening association and final plan accuracy; record depth preprocessing/domain mismatch, exact checkpoint terms/hash, and unsupported classes. Try SAM 2 Hiera Tiny only if box-level boundaries materially limit opening measurements, with the same CPU and final-plan comparison. **Done when:** adopt/reject decisions for ESANet and optional SAM are backed by licence review, candidate metrics, independent hall measurement error, coverage, and runtime; no untested model is required in the live path.
- [ ] **T98 [Agent]** Vectorize fitted 3D surfaces and verified openings into wall segments, room footprints, floor area, ceiling height, and opening width/height/offset, retaining raw observations and fit residuals. Compare the hall's long side, short side, and height with the owner's separately held laser values (3.90 m, 3.21 m, 2.84 m); current provisional errors are +0.026 m, +0.1858 m, and -0.0718 m respectively. Score metric change, omissions, phantom openings, and runtime for raw poses/model off, pose correction/model off, and pose correction/model on. Keep reference values out of prediction inputs and any interval calibration separate under T45/T92. **Done when:** the same original capture generates a schema-valid dimensioned plan and a reproducible ablation table, and improvements or regressions are stated against independent measurements rather than visual plausibility.

**Phase 11 progress (3 October 2026):** T84 is implemented. The optional
SegFormer pilot still runs on photo/video/LiDAR RGB, but its checkpoint is
evaluation-only. A pinned local OWLv2 CPU adapter now proposes doors,
doorways, windows, passages, and cabinet doors through the same intermediate
contract. For LiDAR, the hall's stored RGB is explicitly rotated 90° for
model inference, then boxes are mapped back to raw pixels. Sampled RGB/depth
registration supports a +1 frame offset. The linker now checks candidate rays
against fitted walls and depth gaps, samples paired depth/confidence, records
at-wall/behind-wall/occluded/missing evidence, rejects strong wall-only
conflicts, and requires qualified independent views before an opening can be
inferred. This advances T87–T90 and T96 but does not complete their labelled
accuracy gates. See `reports/hall_mixed_pipeline.md` and `Journal-11.md`.

The hall model-off and OWLv2 runs both estimate 3.926 × 3.3958 m sides and
2.7682 m height. The OWLv2 run provisionally supports one open passage with a
0.705 m depth-gap width; it does **not** improve metric accuracy. Against
separate laser values the errors remain +0.026, +0.1858, and -0.0718 m.
Its 12-frame CPU run took 367.5 s and about 2.3 GiB peak process memory, with
many unverified boxes. The scan found no verified pose closure. Thus T85–T87
still need reviewed labels and fair same-frame scoring; T94–T95 need trajectory
and metric surface improvements; T97 needs a justified model comparison; T98
needs measured ablations and residuals. T90/T92/T93 remain incomplete for
multiroom placement, calibrated intervals, and an untouched capture. T91
still needs visible damage examples. Keep model scores out of measurement
intervals and independent tape dimensions out of inference.

**Measurement continuation (3 October 2026):** `lidar_pose_audit.json` now
records exported pose and IMU timing continuity, motion steps, and closure
status. `lidar_surface_diagnostics.json` records confidence-weighted
within-frame point estimates, frame-balanced wall/floor/ceiling alternatives,
surface residuals, and support frames. The hall has one unstable wall on its
short-side axis. The alternative short side (3.4133 m) is worse against the
separate 3.21 m laser value, so the plan remains at 3.3958 m with a warning.
See `reports/hall_measurement_diagnostics.md`. These artifacts advance the
audit portions of T94–T95 and the comparison in T98; they do not complete
pose-graph correction, competing surface selection, calibration, or the
non-rectangular/multiroom acceptance cases.

**Standalone video correction (3 October 2026):** The ordinary video clip is
independent of the Stray scan's `rgb.mp4`. `visual_geometry.json` now includes
a low-resolution appearance/lighting timeline for every decoded source frame,
with source frame indices and possible scene-change times. The bounded
640-pixel feature matcher and optional model still inspect selected frames;
their limits and selections remain explicit. This full sequence pass is an
evidence index, not a metric reconstruction. Remaining video work: use the
complete sequence to choose trackable keyframes and candidate transition
windows, run the local model on those windows, estimate and verify camera
motion/geometry where possible, and feed only supported room structure into
the plan. Photo and LiDAR RGB-D model proposals likewise still need verified
surface and topology integration; no model currently consumes the structured
LiDAR stream directly to produce a building layout.
The first replay on `Flat-805/IMG_0031.mp4` processed all 3,328 source frames,
found one strong appearance-change candidate at frame 1848 (nominal 61.6 s),
and kept the plan unresolved. See `Journal-11.md` for run ID and limits.

**Kitchen multi-capture checkpoint (3 October 2026):** Added explicit
single-room root-photo input support and the `link-captures` command. It
uses completed independent photo/video/LiDAR runs to emit
`cross_capture_links.json` and `visual_room_graph.json`, carrying source
frames, bounded 2D matches, and optional model opening proposals. It does
not infer a metric cross-capture transform or room adjacency from 2D overlap.
The initial patch-matcher kitchen run matched five video/scan-RGB view pairs, zero photo pairs,
and supported a +1 sampled scan RGB/depth offset. The provisional LiDAR
kitchen fit is 2.4909 × 2.3777 m, 2.7781 m high, with a 0.697 m unverified
gap. OWLv2 generated 200 unreviewed boxes on eight photos in 386.97 s;
SegFormer generated 106 unreviewed regions on 24 video samples. See
`reports/kitchen_pipeline_pilot.md`. T85–T90/T93–T98 remain open for
reviewed labels, robust learned matching, verified 3D registration, full
structure assembly, metric calibration, and end-to-end runtime.
The later scan RGB OWLv2 pass proposed 171 boxes but confirmed no structural
opening. The initial combined graph linked five video/scan RGB image pairs and no
photos, with no metric registration or adjacency. Owner-supplied kitchen
reference is 2.36 × 2.30 m, 2.80 m high, and a 2.26 m hall-facing passage height.
The provisional LiDAR fit differs by +0.1309 and +0.0777 m on sorted spans
and −0.0219 m in height. The 0.697 m gap is not identified as that passage;
the prior 1.6 m width ceiling prevented its proposal; the wider generic
candidate range still did not identify it in the kitchen scan. Kitchen reference is
now development data, not an untouched score set for later changes.

**Kitchen learned-matching and fused-plan pass:** The reader now selects
detailed video windows after a full-frame lightweight scan. Added optional
pinned ALIKED/LightGlue matching with epipolar verification and the patch
baseline on the same selected pairs. Added depth-backed PnP probes with
held-out reprojection and separated-scan-view consistency checks, plus
unverified cross-view opening-region links. `link-captures` now emits a
schema-validated fused `property_plan.json`/SVG alongside correspondence,
registration, opening, and visual-room-graph reports. Unsupported gap width
and kind remain unknown in the plan. This is an implementation advance on
T85–T90/T93–T98; none of their final done criteria are claimed without
reviewed physical opening labels, calibrated registration, multiroom
placement, untouched evaluation, and the end-to-end time gate.

**Earlier kitchen pilot outcome:** Using the same three model-on source runs,
the learned linker `run-dc79cc91e51243fab3100e1018dfb6a3` supported
148 of 336 2D view pairs, versus five for the patch baseline. Its 52
opening-region links formed 19 unverified groups. Three pose hypotheses
agreed across separated scan views only under assumed focal lengths; no
metric registration or adjacency was accepted. `IMG_0004.jpeg`, later
identified by the owner as showing the hall-facing passage, has a roughly
covering model box, but no verified same-wall jamb measurements. The fused
plan retains a provisional 2.4909 × 2.3777 × 2.7781 m kitchen and a null,
unbounded opening width. The full serial model-on run took 1,081.65 s
(18.0 min), above the 15-minute target. The 2.26 m passage height is a miss.
Open gates remain: reviewed physical-opening labels, calibrated independent
camera-to-scan registration, multiroom placement, candidate precision and
recall, runtime reduction, and evaluation on a separate untouched capture.

**Stages 2–6 code pass:** Added full-decoded-video low-resolution optical
flow, model-opening temporal tracks, sparse arbitrary-scale video odometry,
and evidence-only room-transition hypotheses. Added repeated-plane convex
irregular LiDAR fitting and explicit 3D depth-gap side evidence. Optional
calibration gates independent-image PnP with held-out points and separated
scan views; a registered ordinary-image opening must agree with a LiDAR gap
before its width can enter the plan. Added `assemble-property` for separate
metric room runs, with verified shared-opening constraints, overlap and cycle
checks, alternatives, and unresolved placement. Connected rooms can still be
placed if another room has no verified link. The kitchen run remains a
single provisional room with no accepted metric registration or passage
width. These implementations advance T90/T94–T96/T98; their real-world
accuracy gates and unscanned/concave room cases remain open.

The integrated kitchen runs are `run-8bc96a7785874b168c202b0c681dee2a`
for LiDAR and `run-dbe819d692074d83af4d698741ff5786` for linking. All
1,270 video frames contributed motion diagnostics; 172 of 375 image pairs
passed 2D matching, seven opening-track segments and seven arbitrary-scale
video motion edges survived, but zero calibrated camera poses, verified
crossings, metric passage widths, or room connections passed. The irregular
polygon failed repeated wall support; the rectangular fit remained. A
synthetic two-room assembly fixture validated the accepted-connection path,
but is not a real multiroom accuracy result. The serial kitchen model-on
time is still 17.9 minutes.

**Florence-2 Base alternative:** A pinned local phrase-grounding backend now
feeds photo, video, and LiDAR RGB candidates through the same schema. On
identical selected kitchen frames it reduced serial source-plus-link time
from 17.9 to 8.6 minutes, but it did not verify the hall passage, accept a
metric camera registration, or change the plan dimensions or adjacency.
Its box on the owner-identified passage photo was too broad to locate both
jambs. Keep it optional until reviewed candidate labels establish whether
its faster path preserves acceptable recall and false-positive rates. See
`reports/florence2_kitchen_comparison.md`.

**ESANet RGB-D pilot:** A pinned NYUv2 checkpoint and upstream source now
feed wall, floor, ceiling, door, and window masks into the LiDAR-tier candidate
contract for registered RGB/depth samples only. On the kitchen, 9 of 12
selected pairs passed the gate; the model stage took 49.03 s and emitted
39 components. Five door/window proposals coincided with fitted depth gaps,
but none became a supported opening. Room dimensions, the unmeasured hall
passage height (2.26 m reference), and plan status were unchanged. The masks are currently
diagnostic evidence; review semantic errors and independent measurement
results before using them to alter metric geometry. See
`reports/esanet_kitchen_comparison.md`.
The photo/video/ESANet scan linker also retained the same unresolved
single-room plan despite 172 supported 2D view pairs.

**Grounding DINO Tiny alternative:** A pinned local text-conditioned detector
now provides photo, video, and scan-RGB boxes through the existing contract.
The kitchen run used identical selected frames to Florence/OWLv2, took
690.34 s serially, and linked 106 image regions. On the owner-identified
passage photo, it proposed localized but duplicated passage boxes and some
false window/door labels. The scan had 20 box/depth-gap coincidences but
zero supported structural openings. The final dimensions and unresolved
hall passage did not improve. Keep it optional pending reviewed labels and
independent plan-level measurement comparison. See
`reports/grounding_dino_kitchen_comparison.md`.

**Grounding DINO photo-guided opening follow-up:** Added `review-dino-openings`
to reuse a completed DINO linked run without new model inference. The stage
matches DINO passage boxes using saved ALIKED/LightGlue feature pairs,
groups overlapping photo boxes, inspects timed scan depth near the matched
region, and emits a source-linked report and review PNG. On the owner's
`IMG_0004.jpeg`, two scan views show the same opening-looking region, but
neither has accepted RGB/depth pixel registration; only one shows both 3D
flanks in the targeted probe. Its 0.793 m raw span is unverified and does
not measure the 2.26 m hall-passage height reference. The width, height, camera pose, and
adjacency remain unresolved. See `reports/dino_photo_guided_kitchen.md`.

Owner clarification: the 2.26 m hall-passage reference is **height**, not
width. The saved DINO review now reports an explicitly provisional
box-top-to-fitted-floor height. Two matched scan views yield 1.788 m and
1.751 m (median 1.769 m, error −0.491 m). This does not satisfy the
opening-height task: the scan RGB/depth pairs are timing-only, and the box
edge may be the curtain rather than the structural lintel. Keep the plan
height unknown until the lintel and floor are supported in calibrated 3D.

## Stop conditions and honest reporting

- If an input tier cannot produce the complete schema and rendered whole-property plan, mark its execution gate **failing**. A local cache or hand-edited plan does not satisfy a fresh walk-in run.
- If photo/video evidence cannot establish true scale or adjacency, preserve the best hypothesis and uncertainty; do not feed tape truth into inference or claim a calibrated finite interval without evidence. The strict scorer may still mark it failing.
- If 90% intervals are based on too few independent properties, report the sample count and observed coverage; do not call them calibrated merely because they contain the development home's measurements.
- If the free cloud path or stock app is unavailable, record the failure, use a tested free alternative if possible, and keep raw/request/response or local model provenance sufficient for reproduction.
- The benchmark cannot substitute for the live walk-in test; the before/after fix cannot substitute for a runnable final pipeline; a polished report cannot substitute for either.
