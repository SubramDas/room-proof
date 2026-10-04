# Technical Report Summary

## 1. Scope, Hardware and Outputs

* **Hardware:**
  * **Capture Device:** iPhone 15 Pro Max running Stray Scanner 1.4.
  * **Processing Computer:** Intel i7-1265U laptop with $64\text{ GB}$ RAM, running Ubuntu 24 **without a GPU**.
* **Pipeline Breakdown:**
  * **LiDAR:** Checks inputs $\rightarrow$ projects depth points $\rightarrow$ applies loop-correction graphs $\rightarrow$ extracts structural room planes.
  * **RGB (Photos/Video):** Selects frames $\rightarrow$ estimates focal/depth $\rightarrow$ matches visual features $\rightarrow$ estimates camera poses and gravity $\rightarrow$ generates room layout.
* **Outputs Produced:** Room JSON files, floor plans, wall opening/doorway detection, metric surface projections, and full run-provenance metadata.
* **Provisional Components:** Replaced planned TSDF and SAM models with point-fusion and GrabCut filters.

## 2. Sensor Geometry and Drift Correction

* **Units & Coordinates:** Depth is stored in millimeters; final camera poses and room dimensions are output in meters (OpenCV coordinate system, Y-axis up).
* **Timing & Acceleration:** Frame timing from MP4 files is explicitly preserved without edit-list trimming. Raw IMU accelerations are not naively integrated to prevent false velocity drift.
* **Drift Correction (SLAM-lite):** Uses sparse loop-closure constraints to fix drift. On a $140$-frame test:
  * $41$ alignment factors were accepted ($5$ loop-closures).
  * Maximum position adjustment was $8.89\text{ cm}$.
  * Estimated floor area adjusted slightly from $20.81\text{ m}^2$ to $20.80\text{ m}^2$.
* **Room Plane Extraction:** Free-space basins and horizontal mode filters isolate walls and ceilings. Ceiling heights are left blank if unobserved.
* **Noise Sources:** Glass, reflective surfaces, cabinets, soffits, and non-rectangular (non-Manhattan) walls can introduce layout biases.

## 3. RGB Processing, Depth Models and Detection

* **Primary Models Used:**
  * **Depth Anything V2 (Hypersim Small):** Runs on CPU but exhibits significant scale bias on still photos.
  * **Depth Pro:** Estimates depth and focal length simultaneously directly on CPU ($\approx 225.6\text{ s}$ processing time).
* **Quantization Warning:** Quantized Int8 Depth Pro alters calculated focal length dramatically ($236.6\text{ px}$ vs. $462.2\text{ px}$) and is excluded from official benchmarks.
* **Room Alignment & Stitching:** Disconnected rooms remain schematic. Multi-room physical floor plans require valid overlap and adjacency checks.
* **Doorway & Object Detection:**
  * Grounding DINO + GrabCut provide visual masks.
  * LiDAR requires physical wall gaps, depth rays, and lintel supports to confirm doorways.
* **Inspection Flags:** Staged props and potential wall/ceiling damage are flagged using rules, providing inspection prompts rather than priced repair estimates.

## 4. Benchmark Results and Gate Failures

* **Dataset Scope:** Scanning dataset includes a bedroom, kitchen, hall, and corridor.
* **Stitching Failures:**
  * **Photos:** $4$ disconnected rooms with $4.14\text{ m}^2$ of invalid overlap.
  * **RGB Video:** Fragmented into $22$ separate pieces.
* **Ground Truth Constraints:** Reference laser data contains only room lengths, widths, heights, and door entry dimensions.
* **Accuracy Gate Failures:**
  * **LiDAR Height Gate:** (Pipeline vs truth) Hall: $2.77\text{ m}$ vs. $2.80\text{ m}$, Kitchen: $2.76\text{ m}$ vs $2.80\text{ m}$, Corridor: $2.19\text{ m}$ vs. $2.26\text{ m}$
  * **Standalone Kitchen LiDAR:** $3.10\text{ cm}$ height spread.
  * **App Comparison (Magicplan):** All under 1 m of error.
## 5. Engineering Fix Loop & Post-Mortem

* **LiDAR Plane Fix:**
  * **Goal:** Correct a $4.65\text{ cm}$ kitchen height error by improving room boundary separation.
  * **Result:** Improved physical room boundary definitions and adjacency links.
* **Photo Scale & Pose Fix:**
  * **Goal:** Fix extreme photo scale errors using Depth Pro, updated poses, and gravity estimation.
  * **Result:** Worst-case room extent error decreased from $448.15\%$ to $176.54\%$ (a $271.60$ percentage point reduction).
* **Kitchen-Only Improvement (Supporting Evidence):**
  * Kitchen height error decreased from $1.62\text{ cm}$ to $0.79\text{ cm}$.
  * Kitchen floor area error dropped from $24.9\%$ to $9.3\%$.
* **Code Repository:** Saved history using `.history` due to read-only Git mounts; exported full working history via standard Git bundle.

## 6. Reproduction Setup and Known Risks

* **Execution:** Runs via simple commands per tier/capture. Weights are downloaded via scripts, allowing fully offline processing afterwards.
* **Bottlenecks:** Fresh setup speed ($<15\text{ minutes}$) is unverified due to large weight downloads and CPU-heavy Depth Pro inference times.
* **Known Failure Cases:**
  * Mirrors and glass.
  * Highly reflective or wet-looking surfaces.
  * Motion blur and low-light environments.
  * Scans lacking doorway parallax or looping pathways.
* **Summary Verdict:** LiDAR provides useful overall geometry, but tight centimeter-level precision gates are not met. RGB scale estimation and multi-room stitching remain unresolved.