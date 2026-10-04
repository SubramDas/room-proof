# Expanded Three-Room Scan Results

## What Was Run

The new whole-property LiDAR scan contains **8,023 paired frames** recorded over **152.893 seconds**.

The pipeline:

- Used **240 sampled frames**
- Reconstructed **1,234,031 3D points**
- Finished in **241.8 seconds**

Four room photo folders were also available:

- Bedroom: 8 photos
- Kitchen: 8 photos
- Hall: 8 photos
- Connector: 6 photos

LiDAR, photo, and RGB-only video results were tested separately.

---

## Automatic LiDAR Result

The automatic pipeline detected only three spaces:

- **Bedroom:** 3.047 × 2.904 m, height 2.767 m
- **Connector:** 1.325 × 1.013 m, height 2.272 m
- **Hall + Kitchen:** incorrectly merged into one region measuring approximately 4.560 × 6.400 m, with an area of 21.510 m²

The automatic pipeline therefore **failed to correctly detect all four spaces**.

Run folder:

`runs/three_room_expanded_assisted`

Original outputs:

- `../three_room_expanded_lidar/result.json`
- `plan.pdf`
- `report.html`

---

## Assisted LiDAR Result

Because the automatic pipeline merged the hall and kitchen, the source frames were visually reviewed.

Frame ranges corresponding to the **bedroom, hall, and kitchen** were selected manually. The existing room-layout algorithm was then applied separately to these selected frames.

The connector was kept from the automatic result.

No laser measurements, room dimensions, manual polygons, scaling factors, or room connections were given to the geometry-fitting algorithm.

The selected frame ranges and source information are stored in:

- `segments.json`
- `provenance.json`

Therefore, these results should be considered **assisted results**, not a successful fully automatic room-segmentation result.

| Space | Short × long extent (m) | Height (m) | Area (m²) | Extent errors (%) | Height error (%) |
|---|---:|---:|---:|---:|---:|
| bedroom | 2.904 × 3.047 | 2.769 | 8.851 | 2.63, 2.61 | 0.02 |
| connector | 1.013 × 1.325 | 2.272 | 1.343 | 25.07, 20.65 | 0.53 |
| hall | 3.310 × 4.215 | 2.765 | 13.951 | 0.30, 0.36 | 1.26 |
| kitchen | 2.337 × 2.379 | 2.758 | 5.561 | 1.63, 0.81 | 1.50 |

The extent errors compare the two rectangle dimensions after sorting them by size. Each percentage is the absolute error divided by the corresponding laser reference measurement from `../measurements.txt`, multiplied by 100.

The laser measurements were used **only after reconstruction** to calculate the errors. They were not provided to the reconstruction algorithm.

The system inferred these room connections:

- Bedroom ↔ Connector
- Hall ↔ Connector
- Hall ↔ Kitchen

These connections match the provided reference connections. However, the doorway measurements are still provisional and should not be treated as accurate measurements.

---

## Main Limitations

The **connector dimensions are inaccurate**. The pipeline predicted:

`1.013 × 1.325 m`

while the reference measurement was:

`0.810 × 1.670 m`

The total areas may look similar, but this does not mean the connector geometry is accurate.

The height errors for the larger rooms were also noticeable:

- Hall: approximately **1.26%**
- Kitchen: approximately **1.50%**

The bedroom height was very close to the reference, but its horizontal dimensions were oversized.

There is also a timing difference between RGB frames and pose timestamps of up to **12.326 seconds**. The pipeline therefore uses source-index pairing. Visual projections and manually selected frame ranges should be interpreted carefully.

LiDAR reconstruction uses depth/pose frame IDs together with the intrinsics stored for each frame.

The IMU acceleration magnitude is approximately **1 g**. The pipeline does not incorrectly integrate this value directly as translation in m/s².

Other important limitations:

- Measurement confidence intervals are not yet calibrated.
- Damage detection was not rerun using the assisted layout.
- Both result files passed the provisional schema and measurement-invariant validator, but passing these checks **does not prove that the geometry is accurate**.

---

## Reproducing the LiDAR Results

Run the following commands from the project root:

```bash
.venv/bin/python -m astra run --tier lidar --input three_room/lidar --output runs/three_room_expanded_lidar --max-frames 240 --semantic-views 12 --capture-id three_room_expanded

.venv/bin/python scripts/refine_lidar_segments.py --source runs/three_room_expanded_lidar --segments configs/three_room_expanded_segments.json --output runs/three_room_expanded_assisted
```

Useful output files:

- `plan.pdf` or `plan.png` — generated floor plan
- `report.html` — measurements and results
- `dimensions_comparison.csv` — comparison against reference measurements

Existing submission snapshots were **not replaced** by these new results.

---

# Photo and RGB-Only Video Results

The replacement scan was also tested without LiDAR using the photo and video pipelines.

These results are independent from the LiDAR-assisted results.

## Photo Results

The photo dataset contains:

- Bedroom: 8 images
- Connector: 6 images
- Hall: 8 images
- Kitchen: 8 images

The photo pipeline used **Apple Depth Pro on CPU**.

It produced four named room polygons, but it failed to correctly combine them into a whole-property floor plan.

The output had:

- **0 room adjacency links**
- **4 disconnected components**
- **4.139 m² overlap between the connector and hall**

Therefore, the photo result is **not a valid physical whole-property stitch**.

| Space | Photo short × long extent (m) | Photo height (m) | Laser short × long / height (m) |
|---|---:|---:|---:|
| Bedroom | 4.160 × 5.600 | 3.378 | 2.830 × 2.970 / 2.770 |
| Connector | 3.280 × 4.000 | 2.922 | 0.810 × 1.670 / 2.260 |
| Hall | 4.920 × 8.640 | 3.003 | 3.300 × 4.200 / 2.800 |
| Kitchen | 2.615 × 2.769 | 3.375 | 2.300 × 2.360 / 2.800 |

The photo measurements differ significantly from the reference measurements for several rooms, especially the bedroom, connector, and hall.

---

## RGB-Only Video Results

The RGB-only MP4 pipeline also completed successfully from a software-execution perspective, but its geometric result was not usable as a whole-property floor plan.

It produced:

- **22 disconnected room candidates**
- **0 accepted adjacency links**

Because the fragments could not be reliably matched to the actual physical rooms, there is **no reliable one-to-one room measurement comparison** for the video result.

Therefore, both the **photo and RGB-only video tiers failed the required whole-property stitching task**.

---

## RGB Output Files

Photo results are stored in:

`runs/three_room_expanded_photos/`

Video results are stored in:

`runs/three_room_expanded_video/`

Each folder contains:

- `result.json`
- `plan.pdf`
- `report.html`
- Input manifest
- Source manifest
- Provenance information

The assisted LiDAR measurements must **not** be copied or used as the results of the photo or video pipelines.

---

## Overall Result

The **LiDAR pipeline produced useful room geometry**, but the fully automatic system did not correctly separate all four spaces because it merged the hall and kitchen.

After manually selecting relevant frame ranges, the assisted LiDAR pipeline produced separate measurements for the bedroom, connector, hall, and kitchen. Hall and kitchen horizontal dimensions were relatively close to the reference measurements, while the connector and bedroom showed larger errors.

The **photo pipeline detected four room regions but failed to correctly connect them into a whole-property floor plan**.

The **RGB-only video pipeline produced many disconnected fragments and also failed to create a usable whole-property floor plan**.

Therefore, the current results show that the pipeline can reconstruct useful geometry from LiDAR, but **fully automatic multi-room segmentation and whole-property stitching still need improvement**, particularly for the photo and video tiers.
