# Device matrix and observed limitations

| Tier | Capture hardware/tool | Input to pipeline | Tested status |
|---|---|---|---|
| Photos | iPhone 15 or newer; native Camera | 2–8 JPEG/PNG images per named room; no depth or poses | Supplied iPhone 15 Pro Max photos tested; other devices not physically tested. HEIC requires JPEG conversion. |
| Video | iPhone 15 or newer; native Camera | One continuous clip; no depth, poses or IMU | Supplied Stray Scanner RGB MP4 exports tested. Native Camera MOV compatibility requires a decoder check. |
| LiDAR | LiDAR-equipped iPhone; Stray Scanner 1.4 | Original export with RGB, depth, confidence, poses, calibration and IMU | Supplied iPhone 15 Pro Max exports tested; other devices not physically tested. |

Processing uses an Ubuntu 24 laptop, Intel i7-1265U, 64 GB RAM, with no GPU. Local model inference needs no paid API key. Kaggle GPU execution is optional and has not been validated in these reported runs.

## What the current pipeline actually delivers

These are saved-run observations, not a general accuracy guarantee for the device or app. Reference dimensions are independent laser measurements.

| Run | Estimated horizontal extents | Estimated height | Laser reference |
|---|---|---|---|
| Kitchen, LiDAR | 2.495 × 2.377 m | 2.792 m | 2.300 × 2.360 m; height 2.800 m |
| Kitchen, photos | 3.360 × 4.080 m | 3.509 m | 2.300 × 2.360 m; height 2.800 m |
| Kitchen, video | Five room fragments; no accepted single-room estimate | Unreliable | One physical kitchen |
| Three-room LiDAR: kitchen | 2.389 × 2.374 m | 2.759 m | 2.300 × 2.360 m; height 2.800 m |
| Three-room LiDAR: hall | 3.253 × 4.235 m | 2.769 m | 3.300 × 4.200 m; height 2.800 m |
| Three-room LiDAR: corridor | 0.808 × 1.674 m | 2.193 m | 0.810 × 1.670 m; height 2.260 m |

Horizontal axes are not explicitly matched to reference length/breadth labels. Three-room LiDAR height errors are approximately 4.1, 3.1 and 6.7 cm, respectively, exceeding the 1.5 cm gate. RGB physical stitching remains unresolved. The photo ±8% and video ±3% requirements have not been established. Intervals are provisional engineering ranges, not empirically calibrated confidence intervals. Missing ceiling observations must remain unavailable.

Source run IDs: `kitchen_lidar_final`, `kitchen_photos_final`, `kitchen_video_final`, `three_room_lidar_final`; values read from each run's `result.json`. This is a documentation snapshot; later validated runs may supersede it.

The replacement four-space LiDAR scan is separately documented under Part 2. Its automatic layout merges hall and kitchen; its named four-space plan uses visually reviewed frame ranges. This is a reconstruction limitation, not an input-tier or device-compatibility pass.
