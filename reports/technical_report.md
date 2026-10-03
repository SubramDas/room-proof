# Technical report (six-page PDF companion)

## 1. Scope, architecture and output

Astra local property reconstruction — 3 October 2026. 12/16 declared runs have completed at report generation. This is a measured development submission; no blanket gate-pass claim is made.

Route 2 uses Stray Scanner 1.4 on iPhone 15 Pro Max. Laptop: Ubuntu 24, Intel i7-1265U, 64 GB RAM, no GPU. Photos/video are intended for iPhone 15 or newer; other physical devices have not been tested. Kaggle is optional and unvalidated.

LiDAR: validate samples/units -> backproject confident depth -> verified local/loop correction graph -> structural room planes. RGB: select frames/photos -> focal/depth prior -> feature matching and PnP/essential geometry -> relative pose graph -> approximate gravity -> structural layout.

All tiers: surface IDs -> opening/region candidates -> metric projection -> transparent inspection rules and scope -> provisional JSON, room/surface drawings and whole-property plan. Input and model hashes, source provenance, timing and dependency versions accompany each run.

Ground truth is read only by evaluation. The official Round 1 schema is missing; the supplied schema is explicitly provisional. Filtered point fusion and GrabCut replace the planned TSDF and SAM components.

## 2. Sensor handling, geometry and drift

Depth is millimetres; poses and output coordinates are metres. Per-frame intrinsics are resized to depth resolution. Stray camera-to-world xyzw poses use OpenCV camera coordinates, with world y up. The plan is x,z after a common yaw alignment.

MP4 sample times preserve variable timing. Decoding disables edit-list trimming to retain recorded HEVC sensor frames. Pose/RGB timing residuals are exported. IMU acceleration norms are near 1, so raw translation is not integrated under a false m/s² assumption.

Local and revisited cloud pairs create trimmed ICP factors only after overlap/residual/motion checks. A robust sparse small-angle correction graph anchors the first camera and penalizes implausible/non-smooth corrections. It is an approximation, not complete SLAM.

The actual 140-frame ablation accepted 41 factors including five loop factors, with maximum translation correction about 8.89 cm. Summed inferred room area changed from 20.8086 to 20.8020 m². The footprint overlay also exposes shape changes. A small area delta does not prove accuracy improvement.

Distance-watershed free-space basins seed structural-plane extraction. High wall observations reduce furniture confusion; local horizontal modes estimate height. Unobserved ceilings remain null. Low coverage, reflective/glass surfaces, cabinets, soffits and non-Manhattan walls can still bias boundaries.

## 3. RGB models, semantics and scope

The initial RGB depth prior is Depth Anything V2 Metric Hypersim Small. It executes on CPU but has severe scale bias in the supplied stills. Depth Pro estimates focal length and depth jointly; its actual after-run results are reported separately when complete. No API key or paid inference is used.

Full-precision Depth Pro took about 225.6 seconds including load in a concurrent CPU probe. Dynamic int8 took about 230.5 seconds and changed focal length from 236.6 to 462.2 px on the same input. That variant is excluded from the benchmark configuration; numerical equivalence is not assumed.

Depth-assisted PnP handles some low-parallax feature pairs that defeat essential triangulation. Remaining disconnected components are explicitly schematic. Overlap and adjacency diagnostics must pass before a physical whole-property stitch can be accepted.

Grounding DINO proposals and GrabCut masks are unverified visual evidence. LiDAR openings additionally require wall gaps plus transmitted depth rays and lintel support. Facing opening pairs support room adjacency; detected widths remain uncertain.

Black/brown staging props are assessed only in explicit staged mode. They are not natural damage training examples. Metric wall regions are clipped and unioned; generalized floor/ceiling damage is incomplete. Flags recommend inspection using named rules. Scope items are inspection quantities, not diagnoses or priced repair orders.

## 4. Benchmark, gates and uncertainty

The newer scan contains bedroom, kitchen, hall and connector; raw data meets the composition requirement. Automatic LiDAR merges hall and kitchen. The visually assisted four-space plan is labelled. Its photo result has four disconnected rooms and a 4.139 m² overlap; RGB-only video has 22 fragments. Both fail physical stitching.

Laser truth contains room length/breadth/height and room-level doorway entries. Wall identities, exhaustive opening IDs, global outline and damage reference extents are absent. Sorted extents are therefore proxies, not full per-wall scores. Video physical correspondence can remain unresolved and is not chosen to minimize error.

See benchmark.md and metrics.csv for every measured row, including missing predictions. The early LiDAR after run estimated hall height 2.7687 m, kitchen 2.7591 m and corridor 2.1928 m against 2.8, 2.8 and 2.26 m. All miss the 1.5 cm gate. Later results are tabulated separately.

Every measurement includes a nominal 95% engineering interval, explicitly marked uncalibrated. Unknown values and intervals are null. Detector scores and sensor confidence are not calibrated geometric intervals. Nominal coverage on this small correlated set is descriptive only.

The independent kitchen LiDAR repeat has height spread 3.10 cm and fails the 1 cm gate; the long horizontal extent proxy also fails. Magicplan 2026.38.0 exports exist for kitchen and hall; the pipeline wins/ties on 2/6 linear dimensions (33.3%), below 70%. Calibrated intervals still require a held-out set.

## 5. Fix loop and engineering evidence

The first declaration targeted the worst measured LiDAR height error available at that time: kitchen error 4.65 cm. It hypothesized that global floor support and free-space partitioning contaminated room measurements. It predicted at most 2 cm kitchen/hall error after local structural-plane extraction.

The shipped plane change substantially improves the kitchen/corridor boundaries and enables ray-supported adjacency. It misses the predicted height improvement; corridor height regresses. This supports the wall-partition diagnosis but leaves sensor/pose/surface-selection height bias unresolved. No laser scale fitting was used.

The photo declaration identified corridor long extent error 232.9% but missed the actual worst short extent error of 448.15%. The fix changes focal/depth, pose and gravity. The actual worst after error is 176.54%; prediction below 100% and one connection both fail. The original declaration remains unchanged.

Part 4 retains original declarations, before/after outputs, input hashes, original-code before reruns and a readable diff. Four historical photo-after source hashes are unrecoverable. A supplemental source-frozen photo after run completes in 101 s with cached depth and matching dimensions, but no adjacency. Supporting standalone kitchen height improves 1.62 to 0.79 cm with multiple settings changed.

Development commits use .history because this coding session mounts .git read-only. A standard Git bundle exports the actual incremental history. Unit/integration checks cover projection units, rigid alignment, gravity, masks, doorway evidence, topology and reference validation. Accuracy still requires physical benchmark evidence.

## 6. Reproduction, defense and remaining risks

README supplies one command per tier/capture. setup.sh installs pinned packages and fetch scripts download public models; inference then runs offline. A fresh-machine setup under 15 minutes has not been measured. Download bandwidth and Depth Pro CPU inference are substantial costs.

The Part 2 and 4 bundles contain source, declarations, old and new raw scans, measurements, outputs, manifests and historical evidence. Public model weights are fetched by script; credentials and virtual environments are excluded. Old and replacement scans have separate names to preserve input identity.

The stock capture page asks for slow overlapping views of floor/ceiling junctions, both sides of doorways and a return loop. The photos need parallax and shared doorway detail. Mirrors/glass, glossy or wet-looking finishes, motion blur and low light remain known failure modes, rather than solved claims.

Remaining external evidence: official contract/schema, exhaustive physical wall/opening/damage correspondences, held-out interval calibration, and an unseen evaluator capture. The two-room app exports and an independent kitchen repeat are now present; their gates are not passed. Clean setup under 15 minutes remains unverified.

The delivered output must be read with its warnings: LiDAR geometry is useful but centimetre gates fail; RGB scale/stitching may fail; staged masks do not validate natural damage; concealed flags are inspection prompts. docs/COMPLIANCE.md maps every requirement to its artifact and actual status.

