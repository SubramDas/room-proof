# Project specification

Status: discovery draft covering Parts 1–5, deliverables, the walk-in test, scoring, and final constraints. The execution checklist is `TASK.md`. A project-owned output schema draft is now published at `schema/property_plan.schema.json` (version 0.1.0); an illustrative output is at `schema/example_property.json`. Later decisions may refine the schema, damage rules, accuracy goals, and acceptance tests. Proposed choices are marked **Proposed**. No capture or reconstruction implementation exists yet. Capture-route and comparator-app research was checked against developer-authored App Store listings and help pages on 2 October 2026; exported files have not yet been tested on a device.

## Part 1 — Capture ownership and input tiers

### Device matrix (starting point)

| Device / submitted input | Photos: 2–8 stills per room | Video: handheld walkthrough | LiDAR: depth + poses + intrinsics | Honest accuracy statement before validation |
| --- | --- | --- | --- | --- |
| iPhone 15/15 Plus, 16/16 Plus, 16e, 17, and any newer non-LiDAR iPhone | Required | Required | Unavailable | Photos and ordinary video do **not** establish absolute metric scale by themselves. A result can show room shapes and candidate connections, but a finite metric error bound cannot be promised for arbitrary inputs. Video usually gives stronger overlap and ordering than stills; neither guarantees a correct property layout. |
| iPhone 15 Pro/Pro Max, 16 Pro/Pro Max, 17 Pro/Pro Max, and newer models **when a LiDAR Scanner is present** | Required | Required | Required | LiDAR provides measured scene depth and tracked camera geometry, so metric room dimensions can be estimated. The actual error distribution and interval coverage remain **unmeasured** until a device-and-property benchmark; no centimetre claim is made here. |

The capture workflow must check sensor support rather than infer it from a model name. A Pro device may still be used for the photo or video tier. The matrix is a hardware capability statement, not a validated performance claim. Apple's [RoomPlan support flag](https://developer.apple.com/documentation/RoomPlan/RoomCaptureSession/isSupported) and [ARKit scene-depth support check](https://developer.apple.com/documentation/arkit/arconfiguration/framesemantics-swift.struct/scenedepth) explain the relevant runtime gates. Apple lists LiDAR on the [iPhone 15 Pro](https://support.apple.com/en-in/111829), [iPhone 16 Pro](https://support.apple.com/en-au/121031), and [iPhone 17 Pro](https://www.apple.com/ie/iphone-17-pro/specs/).

### Capture route and existing tools

**Chosen route: Route 2, a stock capture protocol, subject to a real-device export test.** Use Apple's Camera app for the mandatory plain-photo and plain-video tiers. The user's available device is an iPhone 15 Pro Max, which has LiDAR. For its LiDAR tier, first try [Stray Scanner](https://apps.apple.com/in/app/stray-scanner/id1557051662): its India App Store listing says **Free** and requires iOS 18.6 or later. The developer's [published data format](https://github.com/strayrobots/scanner/blob/main/docs/format.md) specifies an RGB video, per-frame millimetre depth PNGs, confidence PNGs, and a CSV containing matching camera poses and intrinsics. The listing says scans can be accessed through Files and shared using the iOS share menu. This is a strong candidate for the user's free-only constraint, but the actual export must still be tested.

Free alternative: [Scan4D](https://apps.apple.com/in/app/scan4d/id6760872918), whose listing describes RAW image/depth/camera-data export and requires iOS 18; confirm that its exported intrinsics are available before using it. [Record3D](https://apps.apple.com/in/app/record3d-3d-videos/id1477716895) is now a paid fallback: the listing gives only three free trial recordings before purchase. Its developer [confirms camera poses in `.r3d` metadata](https://github.com/marek-simonik/record3d/issues/59), and a published `.r3d` example includes [camera intrinsics, RGB, depth and confidence](https://github.com/marek-simonik/record3d/issues/76). [LiDARDataCapture](https://apps.apple.com/us/app/lidardatacapture/id6762121558) also advertises the required fields but is paid and requires iOS 26+. A listing alone is not proof that an exported file matches our loader.

**Route 2 validation gate:** Check that the iPhone 15 Pro Max runs iOS 18.6 or later. Install Stray Scanner, capture a multiroom walkthrough, transfer the complete scan folder, and inspect the actual files. Confirm readable RGB frames, metric depth, frame correspondence, intrinsics, camera poses, coordinate conventions, and a clean transfer into the pipeline. Repeat the entire process with a non-engineer following a one-page protocol literally; revise ambiguous steps and retest. Then freeze the app version, export setting, file handoff, and supported iOS/device matrix. A store listing alone cannot satisfy this gate. If this free tool fails, test Scan4D before considering paid tools or Route 1.

The chosen route avoids building a capture app; it does **not** supply the property-plan pipeline. We must still build ingestion, reconstruction, room stitching, uncertainty reporting, visualization, and evaluation for all three tiers. Apple's ARKit documentation describes why [depth](https://developer.apple.com/documentation/arkit/arframe/scenedepth) and [camera geometry](https://developer.apple.com/documentation/arkit/arcamera) matter for the LiDAR tier.

### Mandatory inputs and capture behavior

1. **Photos:** Accept a property directory with one folder per room and 2–8 unposed, depth-free still images per folder from any iPhone 15 or newer. The floor tier must run without LiDAR, ARKit poses, video, manually measured dimensions, or a known-size marker. A room folder's name is an identifier, not ground-truth adjacency. The pipeline must attempt a stitched whole-property plan and emit the common output contract even when placement is ambiguous.
2. **Video:** Accept an ordinary handheld walkthrough clip from any iPhone 15 or newer. It must work without LiDAR or a pose sidecar. Derive usable frames, visual motion, room transitions, and quality indicators from the clip. If a capture tool records optional motion or pose data, label that as extra evidence; validation of the mandatory video tier must also use an ordinary clip alone.
3. **LiDAR:** On a supported Pro-class device, record color frames with aligned depth, depth confidence when available, timestamps, camera poses, intrinsics, image resolution, and tracking quality. Preserve coordinate conventions and frame-to-depth alignment in a machine-readable manifest. If depth or tracking is missing for some frames, record the gap and carry it into uncertainty.

For every tier, input ingestion must report accepted files, rejected files, duplicate/corrupt media, device metadata when available, and missing rooms or coverage. A pipeline failure must be distinguishable from a low-confidence but valid result.

### Shared property-plan contract (proposed minimum)

The downstream outputs in later parts may add fields, but each tier must produce the **same schema and renderer**: property identifier; source tier and device metadata; a whole-property 2D plan in a declared coordinate system; rooms with polygons or a declared unresolved boundary; door/opening candidates; room-adjacency graph; room placement and orientation; estimates for available lengths, widths, perimeters, areas, and total area; and uncertainty for every estimated quantity and connection. Each feature must include evidence provenance and a status such as observed, inferred, or unresolved. The contract must support multiple floors if later parts require them; floor assignment can be unresolved.

**Uncertainty representation:** Report intervals with a named coverage level and method, plus separate confidence for discrete choices such as adjacency. Permit `unknown`/unbounded intervals where the evidence cannot establish a finite bound. Never turn an unconstrained scale into a precise-looking metre value by silently assuming a standard door, ceiling, or object size. Optional calibrated priors may narrow intervals only when disclosed in the result.

**Stitching rule:** Produce one property-level artifact for every valid input set. When room placement cannot be uniquely inferred, show a best hypothesis and explicit competing placements or unresolved links. A single drawing is an output format, not proof that the geometric arrangement is correct. Separate room photo folders with no overlap, shared doors, sequence, or known dimensions can admit many equally consistent layouts; this is a genuine information limit.

The scale limitation for ordinary monocular video is a standard structure-from-motion ambiguity; resolving it requires additional information such as known geometry, inertial capture, or depth. See this [research paper on scale recovery](https://www.sciencedirect.com/science/article/abs/pii/S003039921830224X).

### Capture guidance for the one-page Route 2 protocol

- Give each room a stable name. Capture halls, stairs, and landings as spaces if they are needed to connect rooms.
- For stills, take **2–8 photos per room that together show all four sides (or every wall in a non-rectangular room)**. From one or more corners, include the full wall from floor to ceiling where possible. Show the floor–wall and wall–ceiling edges, all corners, every doorway and window, and any damaged patch. Photograph shared doorways from both rooms so the connection is visible.
- For video, walk continuously and slowly through doors. In each room, turn far enough to show every wall, the floor–wall and wall–ceiling edges, corners, openings, and damage; keep the wall–floor junction in frame during movement. Retrace a shared doorway when practical.
- For LiDAR, sweep every wall, floor/ceiling junction, doorway, window, and damaged area at a steady pace. Revisit a known area for tracking closure, and warn on lost tracking or weak depth.
- Flag mirrors, glass, blank walls, motion blur, occlusion by furniture, dark areas, and missed rooms as quality risks. A non-engineer must be able to recognize when recapture is needed.

These are guidance for better results. They must not become hidden prerequisites for the mandatory photo and ordinary-video input tiers. The final one-page protocol must give exact install, capture, duration/coverage, export, and file-handoff steps, verified against the chosen app version and device.

### Accuracy and evidence plan

Accuracy means **measured performance of the complete pipeline**, not Apple's sensor precision or an attractive sample rendering. Before claiming numeric accuracy, collect consented properties with independent reference measurements and capture the **same properties** in all three tiers. Include small/large rooms, multiroom layouts, weak texture, glass/mirrors, occlusion, and different compatible iPhones. Keep a held-out evaluation set.

Report by tier and device class: successful-output rate; room detection/coverage; adjacency precision and recall; absolute error in room dimensions and total area where scale is identifiable; layout alignment error; interval coverage at the named confidence level; and interval width. Break out failures and high-uncertainty cases. An interval is acceptable only if its stated coverage is calibrated on held-out properties. Compare tiers on matched properties and expect intervals to widen as evidence weakens; exceptions must be explained by measured capture quality. Publish the evaluated population and protocol with every accuracy claim.

**Current accuracy matrix:** Photos: metric scale unidentifiable in the worst case; no universal finite bound. Ordinary video: metric scale unidentifiable in the worst case; no universal finite bound, though overlap may improve topology. LiDAR: finite metric estimates are feasible with valid depth/tracking, but actual error and calibrated interval width are to be established by the benchmark. These are limits and commitments to measurement, not invented performance figures.

### Acceptance criteria for Part 1

- A non-engineer can install the named App Store tool, follow the one-page capture protocol literally, and transfer a usable recording without developer intervention; the process has been rehearsed on the evaluator's device class.
- Each of the three tiers independently ingests a valid capture and emits the same property-plan schema and visual artifact.
- The photo tier accepts 2–8 stills per room in separate folders with no depth or pose sidecars; the video tier accepts an ordinary standalone clip.
- A LiDAR session exports readable depth, pose, and intrinsics data with frame correspondence, and missing/low-quality samples are reported.
- Every output states its source tier, coverage, coordinate/scale status, uncertainty, provenance, and unresolved topology. Unidentifiable metric dimensions are not represented as calibrated narrow intervals.
- A device matrix and empirical accuracy report are delivered before any numeric accuracy claim is used at the defense.

### Open decisions for later parts

- The benchmark's detailed reference-measurement method, sample size beyond the stated minimum, interval coverage level, and unspecified pass thresholds still need to be set before implementation is judged. Part 2 supplies several explicit numeric gates below.
- Clarify whether optional user-supplied scale/adjacency hints are allowed during evaluation. This draft treats the mandatory photo and video tiers as operating without them.

## Part 2 — Output contract and gates

Here, a **gate** means a pass/fail acceptance check with a defined metric and threshold. For example, the opening gate passes only if enough openings are detected and their widths are close enough to reference measurements. The brief does not define a separate “Round 1” document in the material received. **Working assumption:** the supplied requirements and gates are the complete actionable set; no clarification is required to proceed. If an additional Round 1 document appears later, reconcile it with this specification then.

### What one capture must produce

For each capture at **each** input tier, one command must run the full pipeline and write both (1) JSON that validates against the **published project schema** and (2) a rendered, homeowner-readable whole-property plan. No evaluator schema has been supplied, so we have published our own draft at `schema/property_plan.schema.json`; its format must be mapped if an official schema appears. The plan is the main product: every room appears in one property layout, placed and connected to the correct neighbors, with dimensions. Polycam's [2D floor plan](https://learn.poly.cam/hc/en-us/articles/36655587097620-How-to-Use-Space-Mode-LiDAR-Devices) and magicplan's [dimensioned plan exports](https://help.magicplan.app/customize-your-exports) are visual references, not data dependencies.

The required content is:

| Output | Minimum meaning |
| --- | --- |
| Dimensioned room plans | Each room's boundary and walls, ceiling height, floor area, and doors/windows/other openings with location and dimensions. |
| Stitched property plan | One whole-property layout with all rooms, a connector space where present, correct adjacency, consistent room placement, and labelled dimensions. Room plans must agree with the property plan. |
| Damage map | Damage regions attached to a specific wall, ceiling, or floor surface; each region has a class, location, and metric extent (dimensions and/or area as the published schema requires). |
| Concealed-damage flags | A surface-specific warning for possible hidden damage, with the exact rule identifier and input evidence that triggered it. A flag is a suspicion, not proof of hidden damage. |
| Scope line items | Proposed work items linked by stable ID to the affected room, surface, and, where relevant, damage region. The exact item vocabulary and costing rules are pending later parts. |
| Measurement intervals | A confidence interval for **every** numeric measurement, including room dimensions, ceiling height, floor area, opening sizes, and damage extent. Each interval needs units and a declared confidence level. Unidentifiable quantities must be explicitly marked unknown/unbounded under the schema. |
| Deliverables | Schema-valid JSON and a rendered property plan, generated together by one command from one capture. Preserve source tier, provenance, warnings, and processing status. |

**Proposed command contract:** A single documented invocation takes the capture path and tier (or detects the tier without ambiguity), then writes a run directory with the JSON, rendered plan, and a machine-readable execution/quality report. It must work without manual editing, hidden measurements, or tier-specific command chains. Exact command syntax and artifact filenames remain to be finalized with the published schema.

### Benchmark set we must build

The original brief says no evaluation captures are provided; the owner later reported that a **test dataset is provided** and can use their **home** for additional testing. Until the provided dataset is inspected, treat it as supplementary material. We must still create and submit our own benchmark with **at least**:

1. A property capture containing **three or more rooms plus a connector** such as a hall or landing.
2. A **furnished** room with deliberately staged, documented damage from **two distinct damage classes**.
3. The **same rooms**, including the complete multiroom property, captured at all three tiers. For photos, supply one folder per room with 2–8 stills and demonstrate that those folders produce a single stitched property plan.
4. At least one room captured **twice independently at the same tier** to measure repeatability.
5. Laser or tape reference measurements for all scored geometry and damage extents, plus the original unmodified sensor files and a record of how reference measurements were taken. Reference values must be kept out of model input during evaluation.

The benchmark manifest must map each property, room, surface, damage region, capture tier, repeated capture, and reference measurement to stable IDs. Include capture device/iOS/app version and the Route 2 protocol used. The same evaluation code must compare outputs from all tiers with the reference. Report coverage and error separately by tier, and compare the two repeated captures for room geometry, damage findings, and final line items. Do not select only the better run.

### Gates and unresolved definitions

- **Execution gate:** One command per capture finishes and produces both required artifacts; JSON validates against the published schema. A command that only outputs intermediate scans fails this gate.
- **Plan gate:** All rooms in the multiroom benchmark appear in one recognizable plan with correct adjacency and labelled dimensions at every tier, including photo folders.
- **Inspection gate:** The furnished-room output identifies both staged damage classes on the right surfaces, records metric regions, reports any concealed-damage rule that fires, and links scope items to surfaces.
- **Uncertainty gate:** Every measurement has an interval; evaluate whether stated intervals cover independent reference values and how wide they are. The required interval confidence level and calibration pass threshold have not yet been supplied.
- **Repeatability gate:** Two independent captures of the same room at one tier yield comparable results; the tolerance and exact scoring rule are pending.
- **Submission gate:** Deliver all raw captures, reference measurements, benchmark manifest, outputs, and the command needed to reproduce each run.

**Critical feasibility issue:** The contract asks for *correct* adjacency and metric dimensions from arbitrary separate-room photos. When photos contain no shared doorway, sequence, known scale, or other linking clue, multiple property layouts can fit them equally well. An uncertainty flag cannot by itself pass a strict correct-adjacency gate. The benchmark can be captured with overlapping doorway evidence and still honor the 2–8-photo format, but this does not establish success for every arbitrary set of room photos. We must clarify whether the strict gate applies to the defined benchmark only, or whether a capture protocol may require visible connection cues. Reference measurements cannot be secretly fed into photo inference to resolve this.

The supplied text does not yet define the damage-class list, concealed-damage rules, scope-item vocabulary, published JSON schema, interval coverage level, or whether surface damage hidden by furniture is expected to be found. Additional numeric gates are specified below; their remaining scoring ambiguities are listed there.

### Proposed damage vocabulary for discussion (not yet an evaluator requirement)

Keep the first version focused on **visible appearance**, because photos/video/LiDAR cannot confirm a cause or see inside a closed wall. Distinguish the observed class from a possible hidden condition. A region is tied to one room and one wall, floor, or ceiling surface, with a local polygon and metric width, height, and area intervals in the project schema. Multiple classes may overlap if evidence warrants it.

| Candidate visible class | What the image can show | Typical first scope item |
| --- | --- | --- |
| `discoloration_or_water_stain` | A bounded stain, tide mark, or changed color; water cause remains a hypothesis. | Inspect moisture source and affected finish. |
| `crack` | A visible line or split in paint, plaster, drywall, tile, or flooring. Record line length and affected bounding region. | Inspect crack and underlying surface before patching. |
| `coating_failure` | Peeling, flaking, blistering, or lifting paint/wall covering. | Assess substrate and prepare/refinish the affected area after the cause is checked. |
| `surface_breakage` | Hole, chipped plaster/tile, broken board, or missing surface material. | Assess/patch or replace the damaged finish after material review. |
| `floor_finish_damage` | Scratched, lifted, stained, or visibly damaged floor finish. | Inspect and repair/replace the affected finish area. |

An optional `suspected_microbial_growth` label should describe appearance only and require a separate review path; do not assert that a photograph proves mold. EPA notes that stains can resemble mold and that hidden growth may occur behind finishes after moisture problems. See [EPA mold/moisture guidance](https://www.epa.gov/mold/brief-guide-mold-moisture-and-your-home) and [EPA inspection guidance](https://www.epa.gov/mold/mold-course-chapter-3). The final two benchmark classes should be chosen before capture and marked with independent reference regions; a practical candidate pair is `crack` plus `coating_failure` or `discoloration_or_water_stain` plus `surface_breakage`, depending on what can be safely and credibly staged or found at the benchmark property.

**Candidate concealed-damage rules:**

| Rule ID | Visible trigger | Flag, not diagnosis | Initial scope item |
| --- | --- | --- | --- |
| `R-WATER-CEILING-01` | Stain or blistered coating on a ceiling or at a wall–ceiling junction | Possible moisture above/behind the finish. | Locate/check the moisture source and inspect affected material. |
| `R-WATER-OPENING-02` | Stain or peeling around a window/door opening | Possible moisture intrusion behind the adjacent finish. | Inspect opening seal and nearby substrate. |
| `R-WATER-FLOOR-03` | Stain or lifted finish at a wall–floor edge | Possible moisture below/behind the finish. | Check moisture and substrate before repair. |
| `R-CRACK-REVIEW-01` | Crack spans a corner, opening, or wall/ceiling transition, or several aligned cracks are seen | Possible underlying movement or joint failure. | Recommend qualified inspection before cosmetic patching. |

Each fired flag must record its exact rule ID, affected surface, triggering region/evidence, and a plain-language reason. No flag may claim confirmed hidden moisture, mold, structural failure, or a precise hidden-damage area from the phone capture alone. The repair/scope vocabulary should begin with `inspect`, `test_moisture`, `identify_source`, `prepare_surface`, `patch`, `refinish`, and `replace_finish`; each item names its surface and measured quantity where appropriate. A diagnosis-dependent repair is conditional until inspection. Pricing is outside this proposed first version unless the evaluator requires it. EPA's guidance supports investigating moisture sources and hidden areas; the [Gypsum Association](https://gypsum.org/2019/05/moisture-in-gypsum-panel-products/) advises assessing wet gypsum before deciding whether to keep or replace it.

### Additional Round 1 gates supplied with Part 2

These gates apply in addition to the output and benchmark requirements above. Evaluate predictions against independent tape/laser reference measurements; do not use those measurements as inference input.

| Gate | Required pass condition | How it must be checked |
| --- | --- | --- |
| Opening metric and detection | Width error **≤ 2 cm** on **≥ 85%** of openings. A missing real opening and an invented opening each count as a miss. | Match predicted doors/windows/openings one-to-one to reference openings by room, surface, and position before scoring width. Report correct, missed, invented, and over-tolerance openings. |
| Ceiling height accuracy | Absolute height error **≤ 1.5 cm per room**. | Compare every room's predicted height with independent reference height. Do not let a small repeat-capture spread hide a consistent offset from truth. |
| Ceiling height repeatability | If a room is captured more than once, predicted-height spread **≤ 1 cm** across captures. | Report both reference error (bias) and between-capture spread. State explicitly whether a failure is biased, unrepeatable, or both. |
| Wall repeatability | Two independent captures of the same room at the same tier agree **within 1 cm or 0.5% per wall**. | Match corresponding walls and compare each wall's predicted length across the two runs. Report all wall differences, not just the average. |
| Drift accountability | State the method that corrects accumulated error across a multiroom capture, and show the stitched footprint with correction **on and off**. | Run the same capture through both settings and show the two footprints plus quantitative effect. Using input camera poses unchanged, without a correction method, fails this row. |
| Photo whole-property stitching | Per-room photo folders yield **one** plan with correct adjacency, **no room overlaps**, and footprint **within ±8%**, with calibrated uncertainty intervals. | Compare the connected floor plan and footprint with reference; a photo pipeline that handles only separate rooms fails. |
| Photo wall lengths | Wall lengths **within ±8%**, with calibrated intervals. | Score against each reference wall, reporting error and interval coverage. |
| Video wall lengths | Wall lengths **within ±3%**, with calibrated intervals. | Score against each reference wall, reporting error and interval coverage. |

Calibration is scored at **every** tier. Narrow intervals that miss the reference values are a major failure even when a plan looks plausible. Report interval coverage and width alongside point-estimate accuracy. The supplied text does not give the required interval confidence level or the overall score cap formula.

### Proposed interval scoring and calibration policy (pending evaluator rules)

Use a **90% target coverage** for each physical measurement if the evaluator supplies no level. This means that, across comparable unseen captures, approximately nine of ten independent reference values should lie between the reported lower and upper bounds. These are intervals for each individual wall, opening, height, area, or damage extent; they are not confidence intervals for a population average. The number `0.90` is a project choice, not a stated brief requirement. The project JSON schema records this fraction in every interval.

Score intervals on two axes, separately for photo, video, and LiDAR and for each measurement type:

1. **Coverage:** `number of matched reference measurements inside the interval / number of eligible matched measurements`. List misses and the size/direction of each miss. Do not hide omitted predictions; report an additional missing-output rate.
2. **Usefulness:** report median interval width in metres or square metres, relative width against the point estimate where meaningful, and the fraction of unbounded/unknown intervals. An all-encompassing or unbounded interval may cover truth but is not a useful metric estimate.

Also report point-estimate error against the explicit wall/opening/height/footprint gates. A wide interval does **not** turn a failing point estimate into a pass. Use separate training/calibration and held-out evaluation **properties**, so repeated walls from one home do not masquerade as many independent tests. Fit tier- and quantity-specific error margins from calibration data; widen them for weak coverage, occlusion, low light, poor tracking, and other recorded quality indicators. Test calibration on untouched properties. With only the three currently supplied LiDAR scans, reliable calibration for unseen properties is not established; report the limited sample rather than claiming 90% performance. See [NIST on prediction intervals for individual new measurements](https://itl.nist.gov/div898/handbook/pmd/section1/pmd132.htm) and the [original conformal prediction framework](https://arxiv.org/abs/1604.04173).

The brief gives no numeric coverage pass threshold, width penalty, or rule for unbounded intervals. Publish coverage, width, unknown rate, and sample counts transparently; if the evaluator later supplies a formula, use it without changing the underlying outputs after seeing results.

### Working scoring rules for ambiguous gates (ours, not evaluator-issued)

Freeze these rules **before** a benchmark baseline and publish both aggregate and per-room results. If the evaluator supplies different rules, report both calculations without changing predictions after seeing reference values.

| Ambiguity | Working rule | Why |
| --- | --- | --- |
| Missed and invented openings in the ≥85% gate | Match each predicted opening to **at most one** real opening of the same type on the same physical wall, with center position within 0.30 m after rigid plan alignment. An opening is a success only if matched **and** width error is ≤0.02 m. Score = successes / (number of real openings + unmatched predicted openings). | Every missed real opening stays in the denominator; every invented opening adds a failure. A width-correct opening in the wrong place does not receive credit. The 0.30 m matching radius is a project choice, not supplied by the brief. |
| “Within 1 cm or 0.5%” repeatability | Report both tolerances. For our own conservative pass, each corresponding wall must differ by no more than **the smaller** of 0.01 m and 0.005 × the mean of the two predicted lengths. Also show whether the more permissive “either tolerance” interpretation would pass. | The wording may mean the larger tolerance is enough; using the smaller one prevents a favorable interpretation from hiding a shaky result. |
| Photo footprint “within ±8%” | Compare total stitched footprint **area** with ground truth: absolute relative area error ≤8%. Separately align the outline by translation/rotation **without rescaling** and report symmetric-difference area divided by true footprint area. Our internal stretch pass requires this shape error ≤8% too, plus correct adjacency and no room-interior overlap. | Equal areas can conceal the wrong shape. The brief does not say whether the evaluator applies 8% to outline error, so report the area result separately as the literal candidate gate. |
| Per-room versus pooled scoring | Treat “per room” and “per wall” wording literally: ceiling-height and wall-repeatability conditions must hold for **each** eligible room/wall. Pool opening successes and failures for the stated ≥85% rate, but also show each room/capture so a bad room is visible. | Avoid averages that conceal a failing room where the brief explicitly requires each one. |

For opening matching, record every real, matched, missed, width-over-tolerance, and phantom opening by ID. For the footprint, publish both aligned geometry and the transform used. The evaluator's exact opening-matching distance, repeatability interpretation, footprint-shape metric, and aggregation method remain unknown; none of the working choices above is claimed as official scoring.

**Feasibility consequence:** The photo tier has strict numeric and adjacency gates despite having no sensor scale or room poses. Capture guidance should maximize shared-doorway evidence, and the method must explicitly disclose any scale prior. A calibrated interval does not replace the required point-estimate thresholds. Benchmark ground truth must be withheld from the predictor.

## Part 3 — Consumer-app LiDAR comparison

### Required comparison

Pick **two distinct rooms** from our benchmark and capture each at the **LiDAR tier** with our Route 2 capture workflow. Independently scan the **same physical rooms** with one consumer scanning app on the same iPhone 15 Pro Max. Preserve its unedited export, name the app and **installed version**, and submit that export with our LiDAR inputs, outputs, and tape/laser reference measurements. Use one dimension-by-dimension comparison table covering both rooms.

**Proposed comparator: [magicplan](https://apps.apple.com/in/app/magicplan/id427424432).** Its [free Starter plan](https://help.magicplan.app/using-magicplan-for-free) supports two projects and sketch exports; its [LiDAR Auto-Scan guide](https://help.magicplan.app/auto-scan-your-floor-plan) supports iPhone Pro devices, and its [export settings](https://help.magicplan.app/customize-your-exports) can include wall, opening, and room dimensions in a PDF. Record the actual installed app version on test day and verify that a dimensioned export is available on the free account before fixing the comparator. This app is the **baseline we compare against**, not the raw-data capture tool for our pipeline. Polycam is a recognizable option, but its [current free export policy](https://learn.poly.cam/hc/en-us/articles/27756102599572-What-File-Types-Can-Polycam-Export) limits exports to GLTF and excludes dimensioned floorplan export, so magicplan is a better free candidate for this gate.

### Fair measurement and report procedure

1. Preselect two distinct benchmark rooms before seeing results; preferably include the furnished damaged room and another room from the multiroom property. Record room IDs and every reference wall/opening/height dimension eligible for comparison.
2. Scan each room separately with our LiDAR capture route and magicplan on the same phone, during the same site visit and without changing the room. Follow each app's ordinary scan instructions. Do not type tape/laser measurements, redraw walls to match truth, or otherwise correct either output manually. Record any allowed in-app review action.
3. Export magicplan's dimensioned plan/report for each room and preserve the original files. Keep our raw Stray Scanner capture, one-command result, app versions, iOS version, scan date, and reference sheet.
4. Match corresponding physical dimensions by room and surface/opening ID. Include every dimension both systems report and the independent reference value. Report dimensions either system omitted separately so the shared set cannot be chosen after seeing errors.
5. For each shared dimension, compute absolute error for our result and magicplan in the same units. Count a win or tie when our error is **≤** its error. Pass if wins plus ties are **≥ 70%** of shared dimensions across the two rooms. Show the counts and denominator. Proposed anti-omission rule: a predeclared eligible dimension missing from our output but present in magicplan counts as a loss; this requires confirmation against the external scorer's definition of “shared.”

| Room | Dimension ID and type | Tape/laser truth | Our estimate | Our absolute error | magicplan estimate | magicplan absolute error | Win/tie/loss |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| room ID | wall/opening/ceiling ID | value + unit | value + unit | value + unit | value + unit | value + unit | result |

### Working head-to-head accounting rule (ours, not evaluator-issued)

Before either app's results are inspected, freeze two room IDs and the list of eligible **linear dimensions**: each independently measured wall length, opening width, and ceiling height. Report floor area in a separate table because it is an area rather than a linear dimension; include it in the ≥70% score only if the evaluator explicitly defines it as a shared dimension. Compare matching physical features one-to-one, using the original unedited app exports and the same reference values.

- When **both** systems report an eligible dimension, count a win/tie if our absolute error is no larger than the consumer app's; otherwise count a loss. Use the finest common reported precision and show the raw exports so rounding cannot be hidden.
- When the consumer app reports an eligible dimension and **we omit it**, count a loss in our expanded internal score.
- When **we report it but the consumer app omits it**, count a win in the expanded score **only if our absolute error meets that dimension type's predeclared accuracy limit**; otherwise count a loss. The supplied brief gives ≤2 cm for opening widths and ≤1.5 cm for ceiling heights. It does **not** give an absolute LiDAR wall-length accuracy limit in the excerpts received; define and publish a project limit before the baseline rather than borrowing the repeatability limit or choosing one after seeing results.
- When **both omit** an eligible dimension, count a loss in the expanded score and report the shared omission.
- Publish **two scores**: (1) the literal brief's ≥70% win/tie rate on dimensions both systems report; and (2) the expanded score above over all predeclared eligible dimensions, which gives credit for an accurate ours-only result and penalizes omissions. Keep the scores and denominators visibly separate so an ours-only win is not presented as a “shared dimension” under the brief. Publish eligible, shared, omitted, won, tied, and lost counts for each room and in total. Do not change the two rooms or eligible list after seeing errors.

The supplied gate does not define missing-value treatment, exported rounding, or area inclusion; these are working choices, not official scorer instructions. The app version and baseline export are required evidence; a verbal claim of beating another app is insufficient.

## Part 4 — Fix loop (25% of score)

### Required sequence

1. Run the complete benchmark and identify the **single worst-performing gate** in our own results. Record its measured score, required threshold, and the specific captures or dimensions that failed. Choose it using a stated rule before looking for a convenient fix; publish results for every gate so the choice can be checked.
2. Write a **one-page fix declaration before making the fix**. It must state: (a) the selected gate and failing number, (b) a root-cause hypothesis with concrete supporting evidence, and (c) the intended code/process fix and a numeric prediction for that gate after the fix. Date and preserve the declaration so the prediction cannot be rewritten after seeing the result.
3. Implement and ship the declared fix. A diagnosis or plan alone earns zero on this part.
4. Rerun the same benchmark with the same reference measurements, gate definition, and evaluator. For a software/model fix, use the same raw captures. If the fix changes the capture protocol, use controlled before/after captures of the same spaces and submit both raw sets. Deliver the before and after outputs, each reproducible by the evaluator, plus a human-readable diff of the changed code or protocol, results, and rendered plans where relevant.
5. Compare the observed after score with the predicted score. Explain any gap, including an overoptimistic or underoptimistic prediction, and state whether the gate passed. Preserve failures; do not silently drop hard captures or change reference values.

### Reproducibility package

The final submission must include the one-page declaration; before and after source revisions or immutable code snapshots; exact commands and configuration; dependency and model versions; input-file and reference-file identifiers/checksums; machine-readable benchmark results for both runs; the corresponding JSON and rendered plans; and a readable before/after diff. Record any nondeterminism and random seeds. A reviewer must be able to regenerate both runs from the supplied raw data and verify the same gate calculation. For a capture-protocol fix, explain the paired-capture design and any input differences so they are not mistaken for an algorithmic improvement.

### Scoring interpretation from the supplied brief

| Result | Credit described in the brief |
| --- | --- |
| Correct root cause, fix shipped, selected gate changes from fail to pass | Full marks for Part 4. |
| Correct root cause, fix shipped, meaningful improvement but still fails | Majority marks if the report explains the shortfall. |
| Numeric prediction badly wrong in either direction | Post-mortem honesty can earn credit; prediction itself earns none. |
| Analysis without a shipped fix | Zero, regardless of analysis quality. |
| Fix without regenerable before and after runs | Zero. |

### Working fix-selection and improvement rule (ours, not evaluator-issued)

1. Freeze the benchmark manifest, gate definitions, evaluation code, and all baseline results before choosing a fix. If a capture fails to produce valid output, repair that execution/schema blocker first and record it as the selected failure; otherwise consider the failed **numeric benchmark gates** in Part 2, not head-to-head, process, or the later walk-in test.
2. Rank failed gates by **relative gap from the pass threshold**, so unlike units can be compared. For a minimum target `T` and observed score `S`, gap is `(T - S) / T`. For a maximum error target `T` and observed error `E`, gap is `(E - T) / T`. For a gate requiring every room/wall to pass, use its largest individual relative gap. Select the largest gap; break a tie by the number of affected rooms/features, then alphabetically by gate ID. Publish the ranking and raw measurements. This is a transparent choice rule, not proof that all gates have equal real-world importance.
3. In the one-page declaration, predict **one numeric after value in the gate's own units** (for example, opening pass rate from 68% to 87%). After the fix, compare observed with both prediction and threshold; report change in percentage points or centimetres, absolute prediction error, and whether the gate passed. Do not move the threshold or drop hard captures.
4. If the gate still fails, call movement **meaningful for our internal report** only when at least 25% of the original gap to the threshold is closed on the same benchmark; disclose any other gate that regresses from pass to fail. The brief does not define “meaningful” or a tolerated prediction error, so this project rule does not promise evaluator credit. Report under- and over-prediction honestly even if the fix passes.

If an external scorer later specifies different ranking or improvement rules, publish both calculations while preserving the original declaration and before/after runs.

### Proposed capture and run logging

**Recommended free setup:** Use Git for code revisions and [DVC](https://dvc.org/doc/user-guide/pipelines) for original captures, benchmark references, pipeline stages, parameters, results, and reproducibility. DVC records pipeline inputs and outputs in a [`dvc.lock` file](https://dvc.org/doc/user-guide/project-structure/dvcyaml-files) and can store large files on a [local drive or other remote](https://dvc.org/doc/user-guide/data-management/remote-storage). An optional local [MLflow Tracking](https://mlflow.org/docs/latest/ml/tracking/) UI can make run metrics and artifacts easier to browse; it is not required for the first reproducible version and does not replace versioning the raw captures. No paid hosted service is required.

At import, retain the original phone export unchanged. Create a **capture manifest** with capture ID, property/room IDs, tier, date, device model, iOS version, capture-app name/version and settings, protocol version, original filenames and checksums, and transfer method. Keep independent tape/laser truth separately identified so it is never read by inference.

Each one-command pipeline invocation creates a unique **run ID** and records: capture IDs and checksums; Git revision; DVC data revision; exact command, configuration, dependency/model versions and model-file checksum; random seed; start/end time and completion status; stage timings, warnings and logs; every gate metric; and paths/checksums for JSON, rendered plan, and evaluation reports. A run must link back to the immutable source capture, and artifacts must link forward to the run that produced them. The before and after fix runs reference the one-page declaration and can be compared by run ID.

Stray Scanner's role is to **record and export sensor data on the phone**. It does not automatically log our downstream commands, code, metrics, or plans. The import step is the handoff into DVC. A website or dashboard is useful for inspection, but complete reproducibility depends on the versioned files, pinned environment, and exact commands actually being submitted. During implementation, establish a real Git repository and storage location before creating benchmark captures; the current workspace is still a discovery draft, not an initialized pipeline.

## Part 5 — Process evidence

The repository history is itself assessed. Commit **as work happens**, with small, meaningful milestones that show the real path from requirements through capture validation, benchmark creation, pipeline stages, tests, failures, diagnosis, fixes, and final report. A repository created nearly complete in one or two deadline commits scores zero for this part and weakens the credibility of its narrative report. There is no target number of commits per day; the history must reflect actual development.

**Working practice during implementation:** Initialize the Git repository before implementation and commit the discovery spec as the starting state. Make authentic commits when a coherent change is working or an experiment yields a useful result. Use messages that say what changed and why. Preserve failed experiments and fix-loop before/after revisions; link relevant DVC capture/data versions and run IDs to the commit or report. Do not fabricate timestamps, backfill a staged history, or squash away the evidence needed to understand the fix loop. Keep large raw captures in the versioned data store rather than embedding them in Git.

**Commit rhythm (proposed):** A person or coding agent reviews and commits each coherent milestone: capture protocol validated; a tier importer working; property-plan output working; each gate/evaluator implemented; benchmark baseline frozen; fix declaration; fix implementation; and after-run evidence. A tiny edit can be folded into its milestone, while a large feature should be split into independently understandable steps. Do not automatically make a Git commit after every file edit, test, or pipeline run. Automatically log **every run** through the run manifest/DVC experiment record, including failures; promote important runs to named, durable Git/DVC revisions. DVC's [`exp run`](https://dvc.org/doc/command-reference/exp/run) tracks experiments without cluttering the main commit history, but only Git- or DVC-tracked files are saved, so capture import/versioning must precede runs. Before Part 4 changes, freeze a named failing baseline revision; after the fix, commit the changed code and preserve the corresponding passing or improved run ID.

AI coding tools are allowed and expected. The final defense tests whether the builder can explain the design and results live **with tools closed**: why each capture route, model/algorithm, metric, uncertainty method, correction, and fix was chosen; what evidence supports it; and where it fails. Maintain concise decision notes alongside meaningful commits so the work is understandable without an AI assistant during the defense. Tool use does not replace ownership of those decisions.

## Final deliverables

The following paths are a **proposed repository layout**, not claims that the files already exist. Create each artifact during implementation and keep the compliance matrix current with its true status.

| # | Required deliverable | Proposed location | What the submitted artifact must prove |
| --- | --- | --- | --- |
| 1 | Compliance matrix | `COMPLIANCE.md` | Every requirement maps to a real file path, a specific artifact or command, and a truthful status such as complete, partial, or failing. Include evidence links/run IDs; do not mark a requirement complete merely because code exists. |
| 2 | Capture route and device matrix | `protocols/stock_capture.md`, `docs/device_matrix.md` | A tested **one-page** Route 2 guide states exact app versions, installation, how to capture photos/video/LiDAR, duration/coverage, what to avoid, and how to deliver all original files. The matrix lists supported devices, available tiers, and validated accuracy. If the first stock tool fails its real-device validation gate, test another free stock tool and reassess the route with the evidence. |
| 3 | Runnable repository | `README.md`, pipeline command/entry point | A reviewer on a clean machine can set up and process a fresh capture in **under 15 minutes**, with **one documented command per capture**. State required hardware, OS, packages, model downloads, environment variables, input layout, output paths, and an example. Test the instructions from a clean environment and record elapsed setup and run times. |
| 4 | Reproduction bundle | `repro/manifest.json`, lockfiles, DVC metadata/storage, `repro/README.md` | All code, exact inputs, references, model versions/weights or permitted caches, settings, seeds, and commands needed to regenerate **every reported number**. A cache is allowed only if replay is deterministic and the **live** processing path also runs on a new walk-in capture. Verify hashes and replay before submission. |
| 5 | Benchmark report | `reports/benchmark.md`, machine-readable metrics/tables | Gate results for photo, video, and LiDAR tiers; opening/height/wall/footprint/calibration results; repeatability table; two-room consumer-app head-to-head table; failures; and setup/capture/processing timing. Every table points to raw captures, reference measurements, and run IDs. |
| 6 | Fix-loop bundle | `fix_loop/declaration.md`, before/after run manifests, diffs | The one-page declaration written before the fix, failing number and predicted after number, root-cause evidence, shipped change, regenerable before and after runs, and readable code/result/plan diff. |
| 7 | Technical report, **maximum six pages** | `reports/technical_report.pdf` | Concise architecture; design for all three tiers and device matrix; multiroom drift correction; error budget; interval calibration; fix-loop story; and known failure modes. Use the benchmark report for detailed tables rather than exceeding the page cap. |
| 8 | Raw benchmark data | `benchmark/raw/` tracked through DVC or an included data bundle; `benchmark/ground_truth/`; `benchmark/comparator/` | Original photo folders, video, Stray Scanner sensor logs, independent tape/laser measurements, consumer-app exports and app versions, and capture manifests. Preserve originals unchanged; document any derived files separately. |

### Submission checks

- Run the documented fresh-capture command on a clean machine or clean environment and confirm setup plus execution meet the 15-minute requirement as interpreted by the evaluator. Record actual hardware, download size, network use, and timing; do not hide manual preprocessing steps.
- Run the reproduction command for **every** result cited in the benchmark and technical reports, and compare regenerated metrics with the submitted tables.
- Check that cache replay is deterministic, then separately run at least one new capture through the live path; keep both results and timings.
- Check that all eight items have valid paths in the compliance matrix, and that `partial`/`failing` entries remain visible rather than being omitted.

**Open delivery details:** We have published a project-owned JSON schema because none was supplied by the evaluator. The exact packaging/upload destination remains unspecified. The 15-minute wording does not explicitly separate installation time from processing time, so the README and report should measure and disclose both. Confirm any external scorer's interpretation rather than silently excluding setup or model downloads.

### Working final-bundle and timing plan (until evaluator instructions arrive)

**Delivery:** Provide (1) the GitHub repository with code, schema, README, capture protocol, lockfiles, scripts, reports, compliance matrix, and small examples; and (2) a separate, versioned reproduction data bundle containing **all** raw benchmark captures, laser/tape truth, comparator-app exports, required model files or pinned fetch instructions, and deterministic caches where used. The three supplied LiDAR directories are ignored by Git to avoid committing large files, but ignoring them does **not** waive the raw-data submission requirement. A manifest lists every file path, size, and SHA-256 checksum, links capture/run IDs to reported numbers, and describes how to place or mount the bundle. The exact upload location, accepted archive format, size limits, and whether an evaluator provides a storage volume are pending external instructions; preserve a local complete copy meanwhile. Never place cloud API secrets in the repo or bundle.

**Conservative internal 15-minute clock:** Start when a reviewer has a clean permitted computer, repository/data access, and a fresh capture ready to hand over. Count clone/unpack, dependency installation, data transfer into the expected input path, weight download or volume mounting, any cloud credential setup required by the documented command, preprocessing, cloud upload/inference if selected, reconstruction, JSON/schema checks, and plan rendering. Stop only when the JSON and rendered plan are ready to inspect. The actual phone walkthrough is timed and reported separately for capture-route quality. This end-to-end definition is stricter than the possibly narrower phrase “README to running”; it prevents a quick pipeline command from hiding a long setup.

Record **setup time, input-transfer time, per-capture processing time, total time, download bytes, computer/OS/CPU/RAM, network conditions, and any preprovisioned resources**. Repeat from a clean environment and with an unseen capture at every tier. If the total exceeds 15 minutes, report the measured miss and optimize; do not claim compliance from an untimed development machine. One documented command processes each capture after setup and writes the complete output contract. The evaluator may later clarify a different clock; publish both measurements if so.

## Walk-in defense test

At the defense, evaluators choose an **unseen space** and one of the three mandatory tiers on the day, using **their own iPhone 15 or newer**. They follow our Route 2 one-page protocol **literally**, hand over the resulting original files, and watch our pipeline run on that fresh input. While it runs, they independently measure the space with a laser. The output is scored against those measurements immediately. We must be ready to do the same for photos, ordinary video, and LiDAR; preparing only the tier we expect them to choose is insufficient.

**Operational readiness requirements:**

1. The stock-capture guide must give unambiguous install, permission, capture, export, and file-handoff steps for a non-engineer. It must account for their phone and iOS version, available storage, transfer method, and the time to finish a valid capture. Test it with someone unfamiliar with the system before the defense.
2. The pipeline must accept a genuinely new input with no property-specific setup, hand-corrected plan, reference dimension, or cached output keyed to that space. General pretrained models and reusable caches are allowed only if the live path can process the new capture. Preserve the new raw files and create a new capture/run ID automatically.
3. One documented command per capture must produce schema-valid JSON and a rendered whole-property plan, damage/scope outputs, intervals, and machine-readable timing/quality logs, or an explicit diagnosable failure. The live test cannot depend on unmentioned preprocessing steps.
4. Keep evaluators' laser measurements separate from the prediction path until the output is frozen. Then compute the same gate metrics with the same scoring code used for our benchmark; record both the raw live output and the scored report.
5. Rehearse **all three** tier paths on properties outside the development benchmark, including a photo-folder multiroom handoff, a standalone video, and a LiDAR export from the selected stock app. Record end-to-end duration and failure recovery steps.

**Device-availability clarification:** Photo and ordinary-video tiers run on any stated iPhone 15+ device. The LiDAR tier requires an iPhone with a LiDAR Scanner (such as the user's iPhone 15 Pro Max); an ordinary iPhone 15 cannot provide LiDAR readings. The evaluator's statement that it may choose any tier using its own iPhone 15+ must be read together with this hardware prerequisite. Confirm that a LiDAR-capable evaluator phone will be available if they choose LiDAR. The Route 2 tool's iOS minimum must also be checked on that device; if it is below Stray Scanner's iOS 18.6 minimum, a tested compatible free tool is needed before the defense.

## Scoring weights and engineering priority

The supplied weights sum to **100%**. The failure-mode descriptions explain why each item exists; a polished report cannot substitute for a live-working system or a shipped fix.

| Weight | Scored component | Failure mode the gate is designed to catch |
| ---: | --- | --- |
| **30%** | Walk-in test: cold run on evaluator capture, scored against laser measurements taken in that space | System works only on its author's data. |
| **25%** | Fix-loop improvement | Diagnosis is delivered instead of an implemented repair. |
| **15%** | Verified benchmark accuracy at all three tiers | Accuracy claims disappear when results are reproduced. |
| **10%** | Compliance-matrix coverage | A different product is built from the specified one. |
| **10%** | Two-room head-to-head with a consumer app such as magicplan or Polycam | Comparison with an incumbent is avoided. |
| **5%** | Capture-route quality: install time, guide clarity, and non-engineer experience | The pipeline has no practical route into a user's hands. |
| **5%** | Process evidence in repository history | Work arrives as an unauditable single-commit repository. |

**Execution priority implied by the weights:** Establish a live, one-command vertical slice that accepts fresh input for every tier and produces the complete required output. Then build and freeze the benchmark/evaluator so the worst gate can be identified and repaired with a regenerable before/after. Keep the Route 2 protocol, compliance matrix, and authentic commits current throughout. This is an ordering of work, not permission to omit lower-weight requirements: the walk-in test can select any tier, and the compliance matrix exposes missing outputs.

## Final constraints

- **Consumer handheld capture only.** The predictor must work from an ordinary person holding an iPhone and following the published capture protocol. Do not depend on a tripod, specialist scanner, calibration rig, hidden markers, or tape/laser dimensions as model input. The evaluator's laser/tape measurements are independent reference data used only after prediction for scoring.
- **External components are allowed with disclosure.** Record the name, version, source, license/terms, intended role, and any data-sharing behavior of every pretrained model, dataset, or API used. State which reported results depend on each component. The final system must run without calling infrastructure operated by us; avoid a hidden server dependency. Any third-party API used must be disclosed and must be available under the defense conditions. Prefer a locally runnable path for the walk-in test, and verify it from a clean machine.
- **Large files are delivered reproducibly.** Do not bury model weights or other large binaries in ordinary Git commits. Supply a scripted, version-pinned fetch with checksums and a documented local-volume alternative. The README must state download size, storage needs, expected time, and how the reviewer supplies the volume or runs the fetch; include these steps in the clean-machine rehearsal. The live path must run after the weights are provisioned.
- **Challenging real surfaces and lighting must appear in the submission.** Include captures or documented test cases with mirrors, glass, wet-look/reflective surfaces, and low light. Report how these affect photo, video, and LiDAR outputs, interval width, and failure rates; provide the raw evidence and identify limitations in the technical report. The capture protocol should explain practical ways to cover or flag such areas without silently excluding them from scoring.

**Open interpretation:** “Any API with disclosure” and “without calling your infrastructure” permit at least non-proprietary local processing and may permit a third-party API. Since availability and privacy may differ on defense day, the primary walk-in path should not require an external service unless that dependency is explicitly accepted by the evaluator. No separate capture accessory is assumed.

## Open questions and decisions

These questions are grouped by owner. **No unanswered clarification currently blocks a design prototype.** The supplied brief already answers the three required tiers, Route 2 choice, core outputs, numerical thresholds, benchmark minimum, and scoring weights; those are not choices to revisit. The remaining practical information is needed before the full benchmark, live timing claim, or final submission. Where the brief is silent, use the working assumptions elsewhere in this file and show them openly.

### Questions for the project owner before implementation

1. **Deadline and resources:** The owner reports a **4 October 2026, 10:00 a.m. Asia/Kolkata** deadline. Development computer: **Ubuntu 24.04, Intel Core i7-1265U (12th generation), 64 GB RAM, 512 GB SSD, no dedicated GPU**. The owner wants a **zero-budget** approach unless evidence shows a required capability cannot be delivered for free. End-to-end timing and the remaining engineering time must be planned against this deadline.
2. **Phone and app validation:** The owner's iPhone 15 Pro Max runs **iOS 26.5** (owner-reported), meeting Stray Scanner's listed iOS minimum. The owner will provide installed Stray Scanner and magicplan versions/exports later. Those are **not prerequisites for starting** the schema, evaluation, or importer against the supplied local LiDAR files, but a real-device export test is required before freezing the final capture protocol, app comparator, or defense claims.
3. **Benchmark access:** The owner says a **test dataset is provided** and will capture their **home with the same iPhone 15 Pro Max**, using tape for independent measurements. The original brief said no captures would be provided, so treat the current local scans as supplementary starter data. The home capture still must be checked against the self-built benchmark requirements: at least three rooms plus a connector, all three tiers on the same rooms, a furnished room with two staged damage classes, repeat capture, and reference measurements for every scored dimension. The owner has confirmed willingness to make these captures; exact room coverage/damage setup remains to be documented.
4. **Data rights and storage:** The owner confirms the datasets **may be submitted and sent to a third-party cloud model**. Permission for public GitHub publication of raw interiors is not assumed; keep large raw files in a separate submission bundle. The storage and handoff location for raw captures and model weights remains to be chosen.
5. **Defense environment:** The owner asks us to **assume the necessary phone, computer, internet, installation access, and time will be available**. This is a planning assumption, not a confirmed evaluator rule. The evaluator's exact device/iOS, preprovisioned weights permission, and interpretation of the under-15-minute requirement still need external confirmation.
6. **Scope and product conventions:** Is this restricted to single-floor interiors, or must stairs and multiple floors be geometrically linked? What units and property/room naming conventions should the output use if the published schema does not decide them?

### Questions to send to the brief owner or evaluator

1. **Canonical requirements:** No evaluator JSON schema was supplied; we have defined `schema/property_plan.schema.json` version 0.1.0 as our published project schema. If the evaluator later provides another required schema or additional damage, scope, or safety rules, reconcile them before final submission. The “Round 1” wording alone does not block implementation.
2. **Photo/video information limit:** May the capture protocol require views through shared doorways or a room traversal order? May the user provide a room adjacency list, one measured scale, a known-size marker, or other hints? If not, is an unresolved or unbounded estimate acceptable when photos/video do not identify scale or layout, or does the strict numeric/adjacency gate still apply to every valid input?
3. **Damage output:** Which damage classes must be recognized? What counts as a valid damage region and metric extent? Must damage hidden behind furniture be inferred? Which concealed-damage rules and scope-item categories are expected, and is pricing part of scope?
4. **Intervals:** What confidence level is required (for example, 90% or 95%)? How is calibration scored, at what sample level, and what is the penalty for wide or unbounded intervals? Are intervals required for discrete room adjacency/opening presence, or only measurements?
5. **Gate mechanics:** For openings, how are real and phantom detections matched, and what is the denominator for the 85% pass rate? Does wall repeatability use the larger of 1 cm and 0.5%, the smaller, or another rule? Is the photo footprint ±8% gate about area, aligned outline, or both? Are gate scores per room/capture or pooled, and how are absent walls/rooms counted?
6. **Comparison and fix scoring:** Which measurements count as “shared dimensions” against the consumer app (walls, openings, heights, area), and what happens when only one system reports one? How is the single worst gate selected across different metrics, and what counts as meaningful improvement or an acceptable prediction error?
7. **Delivery and defense:** What are the exact submission destination and size limits? Is the 15-minute clean-machine requirement measured from installation start through output, or only execution after dependencies and weights are present? Can a third-party API be used live, or must all inference run locally/offline? Will the LiDAR test use a Pro-class phone with a compatible iOS version?

### Decisions the team can make and validate without waiting

- Choose exact command syntax, repository layout, renderer, processing methods, and a stated interval method once the canonical schema is known.
- Rehearse the free stock-app export, select the working app/version, and turn the actual steps into the one-page protocol.
- Select and document the comparator, benchmark rooms, reference measurement method, opening matching rule, and fix-gate ranking method when the evaluator has not prescribed them; publish assumptions before scoring rather than choosing after seeing results.
- Test capture transfer, clean setup, runtime, repeatability, and difficult surfaces; report measured failures and uncertainty honestly.

### Supplied local dataset inspection (2 October 2026)

Three ignored local directories are present: `single_room/`, `single_scan_floor_only/`, and `single_scan_with_ceiling/` (about 914 MB total). Each contains one RGB MP4, `camera_matrix.csv`, `odometry.csv`, `imu.csv`, and matching 256 × 192 depth/confidence PNG sequences. The three scans have respectively 1,715, 5,251, and 9,745 depth frames; each has exactly one pose row and one confidence image per frame, with contiguous IDs starting at zero. This is a promising LiDAR input set and supports importer development. Full video/depth quality, metric unit convention, timing alignment, and geometry accuracy have not yet been checked.

These directories do **not** contain independent photo-tier folders, separately captured ordinary video, laser/tape reference measurements, damage labels/regions, consumer-app exports, capture manifests/app versions, or a declared multiroom property. The names suggest single-room/scan tests, but actual room coverage requires visual review. They are therefore useful starter data, not evidence that the mandatory all-tier multiroom benchmark or head-to-head gates are already satisfied. Keep their original files unchanged; record source, permission, device/app version, and checksums when importing them into the reproducible benchmark store.

### Model and computation strategy under the current hardware limit

**Status: candidates to test, not selected dependencies or accuracy claims.** Prefer small, local, free components and geometry algorithms before adding large neural networks. The live path must be timed on the actual CPU against the defense constraint.

| Required task | First candidate | Why / limitation |
| --- | --- | --- |
| LiDAR room geometry, dimensions, and drift | Use exported metric depth/poses with Open3D plane fitting and multiway pose-graph correction; extract a 2D footprint and openings from the corrected geometry. | Sensor data provides scale. This is primarily geometric processing, but glass, mirrors, missing depth, clutter, and drift need checks. |
| Video geometry and room links | Sample a bounded number of frames; use CPU feature matching and sparse reconstruction with COLMAP or OpenCV, plus doorway/sequence evidence. | CPU reconstruction is possible but may be slow. Ordinary monocular video has no guaranteed absolute scale. |
| Photo room geometry and property links | Use 2–8 views per room, feature/line matching, visible doorways, and an optional small indoor depth model such as Depth Anything V2 Small; optimize room placement with stated priors. | Predicted depth is an estimate, not a measured scale or proof of adjacency. The strict photo gate remains a feasibility risk. |
| Damage detection and extent | Define the required classes first, collect labeled staged examples, then compare simple image features with a small classifier/segmenter. SAM 2 Tiny is only a candidate to segment proposed regions. | A generic mask model does not identify damage class or hidden damage by itself. Metric extent depends on a calibrated surface geometry estimate. |
| Concealed-damage flags and scope items | Explicit, versioned rules keyed to recognized damage, surface, and measured region. | This needs a defined damage vocabulary and rule set; a large language model is not inherently required. |
| Measurement intervals | Fit and check uncertainty against independent benchmark truth per tier and capture quality. | A model's confidence score is not automatically a calibrated interval. |

Keep model weights out of Git and provision them by pinned download or local volume. Test image downsampling, frame selection, CPU thread limits, model size, and end-to-end runtime before selecting a stack. Do not promise a 15-minute live run or centimetre accuracy before measurement. Candidate source documentation: [Open3D plane fitting](https://www.open3d.org/docs/latest/tutorial/t_geometry/pointcloud.html), [Open3D pose-graph optimization](https://open3d.org/docs/latest/tutorial/pipelines/multiway_registration.html), [COLMAP CPU support and caveats](https://github.com/colmap/colmap/blob/main/doc/faq.rst), [Depth Anything V2 Small and licenses](https://github.com/DepthAnything/Depth-Anything-V2), and [SAM 2 Small/Tiny checkpoints and license](https://github.com/facebookresearch/sam2).

### Free third-party cloud inference candidates

The brief bans dependence on **our own** infrastructure, not clearly on all third-party APIs. A disclosed third-party API may be eligible, subject to evaluator confirmation, network availability, property-data consent, quota, and live timing. The owner is **willing to use free cloud models if they help the project work**; no provider or model is selected yet. Prices, model availability, limits, and terms must be rechecked when chosen.

- **Gemini API:** As checked on 2 October 2026, Google's [pricing page](https://ai.google.dev/gemini-api/docs/pricing) lists free text/image/video input and output for `gemini-2.5-flash-lite` and `gemini-2.5-flash`, subject to [account-specific rate limits](https://ai.google.dev/gemini-api/docs/rate-limits). Its [video guide](https://ai.google.dev/gemini-api/docs/video-understanding) lists a 2 GB free-tier File API limit. Candidate uses: label visible damage, identify doors/rooms, and propose topology for local checking. The pricing page says free-tier input may be used to improve Google's products; obtain suitable property-data permission before upload.
- **GroqCloud vision:** Its [vision documentation](https://console.groq.com/docs/vision) lists an image-capable Qwen model and a three-images-per-request limit; its [rate-limit page](https://console.groq.com/docs/rate-limits) publishes free-plan quotas. Candidate for selected stills and damage descriptions, not full raw-video/point-cloud reconstruction.
- **Hugging Face Inference Providers:** [Free accounts currently receive $0.10/month in credits](https://huggingface.co/docs/inference-providers/pricing), subject to change. Useful for a small experiment, but this allowance is too small to assume it will support every benchmark replay and live walk-in run.

No general image/video language model is known here to return verified centimetre-level whole-property geometry, stable damage extents, and calibrated intervals from all three tiers. Test cloud help on a labeled sample, compare it with a local method, and record exact model/version, request/response, latency, failure/rate-limit behavior, and whether the service processed private interiors. Geometry, schema validation, interval calibration, and reproducibility remain our pipeline's responsibility. A local route avoids depending on free quota and connectivity during the defense, unless the evaluator explicitly confirms cloud reliance is acceptable.
