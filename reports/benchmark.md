# Measured benchmark results

These results compare predictions with supplied laser dimensions. Extent comparisons are proxies, not full per-wall scores.

| Capture / tier | Reference | Quantity | Truth m | Predicted m | Error cm | Gate |
|---|---|---|---:|---:|---:|---|
| three_room_lidar_final / lidar | room_1 | short_extent | 2.300 | 2.374 | 7.38 | not specified |
| three_room_lidar_final / lidar | room_1 | long_extent | 2.360 | 2.389 | 2.93 | not specified |
| three_room_lidar_final / lidar | room_1 | ceiling_height | 2.800 | 2.759 | 4.09 | FAIL |
| three_room_lidar_final / lidar | room_2 | short_extent | 3.300 | 3.253 | 4.66 | not specified |
| three_room_lidar_final / lidar | room_2 | long_extent | 4.200 | 4.235 | 3.51 | not specified |
| three_room_lidar_final / lidar | room_2 | ceiling_height | 2.800 | 2.769 | 3.13 | FAIL |
| three_room_lidar_final / lidar | room_3 | short_extent | 0.810 | 0.808 | 0.24 | not specified |
| three_room_lidar_final / lidar | room_3 | long_extent | 1.670 | 1.674 | 0.39 | not specified |
| three_room_lidar_final / lidar | room_3 | ceiling_height | 2.260 | 2.193 | 6.72 | FAIL |
| kitchen_lidar_final / lidar | room_1 | short_extent | 2.300 | 2.377 | 7.70 | not specified |
| kitchen_lidar_final / lidar | room_1 | long_extent | 2.360 | 2.495 | 13.54 | not specified |
| kitchen_lidar_final / lidar | room_1 | ceiling_height | 2.800 | 2.792 | 0.79 | pass |
| three_room_video_final / video | room_1 | short_extent | 2.300 | missing | missing | FAIL |
| three_room_video_final / video | room_1 | long_extent | 2.360 | missing | missing | FAIL |
| three_room_video_final / video | room_1 | ceiling_height | 2.800 | missing | missing | FAIL |
| three_room_video_final / video | room_2 | short_extent | 3.300 | missing | missing | FAIL |
| three_room_video_final / video | room_2 | long_extent | 4.200 | missing | missing | FAIL |
| three_room_video_final / video | room_2 | ceiling_height | 2.800 | missing | missing | FAIL |
| three_room_video_final / video | room_3 | short_extent | 0.810 | missing | missing | FAIL |
| three_room_video_final / video | room_3 | long_extent | 1.670 | missing | missing | FAIL |
| three_room_video_final / video | room_3 | ceiling_height | 2.260 | missing | missing | FAIL |
| kitchen_video_final / video | room_1 | short_extent | 2.300 | missing | missing | FAIL |
| kitchen_video_final / video | room_1 | long_extent | 2.360 | missing | missing | FAIL |
| kitchen_video_final / video | room_1 | ceiling_height | 2.800 | missing | missing | FAIL |

## Incomplete benchmark evidence

Repeat scans are deferred by the user. Consumer-app exports, independent damage extents, official schema/round-one gates and independent calibration scenes were not supplied. The property contains two rooms plus a corridor, not the prescribed three rooms plus a connector. These omissions are not counted as passed gates.

## Execution and topology

| Run | Execution | Rooms | Opening candidates | Damage regions | Layout status |
|---|---|---:|---:|---:|---|
| three_room_lidar_final | executed | 3 | 18 | 8 | provisional_connected_layout |
| kitchen_lidar_final | executed | 1 | 8 | 2 | provisional_connected_layout |
| damage_lidar_final | executed | 1 | 15 | 4 | provisional_connected_layout |
| three_room_photos_final | not_completed | 0 | 0 | 0 | not available |
| kitchen_photos_final | not_completed | 0 | 0 | 0 | not available |
| damage_photos_final | not_completed | 0 | 0 | 0 | not available |
| three_room_video_final | executed | 16 | 4 | 5 | unresolved_physical_stitch |
| kitchen_video_final | executed | 5 | 5 | 2 | unresolved_physical_stitch |
| damage_video_final | executed | 3 | 0 | 4 | unresolved_physical_stitch |
| evaluator_single_room | executed | 1 | 0 | 0 | provisional_connected_layout |
| evaluator_floor_only | executed | 3 | 0 | 0 | unresolved_physical_stitch |
| evaluator_with_ceiling | executed | 5 | 7 | 0 | unresolved_physical_stitch |

Video rows with missing predictions indicate unresolved physical room correspondence, not zero-sized rooms. Candidate-room outputs remain available in each run. No dimension-based best-match assignment is used.

## CPU timing

Measured wall time includes the selected reconstruction and rendering stages. Some runs shared the laptop concurrently; cache reuse and changing source revisions are disclosed in provenance. These are not isolated hardware speed benchmarks.

| Run | Seconds | Peak process RSS MB | Device |
|---|---:|---:|---|
| three_room_lidar_final | 460.6 | 2395 | cpu |
| kitchen_lidar_final | 281.7 | 2363 | cpu |
| damage_lidar_final | 327.5 | 2370 | cpu |
| three_room_video_final | 647.8 | 2870 | cpu |
| kitchen_video_final | 387.8 | 2708 | cpu |
| damage_video_final | 219.7 | 2694 | cpu |
| evaluator_single_room | 13.8 | 255 | cpu |
| evaluator_floor_only | 11.2 | 265 | cpu |
| evaluator_with_ceiling | 29.0 | 308 | cpu |

## Required tables with unavailable evidence

| Gate | Evidence | Status |
|---|---|---|
| Wall repeatability | Independent repeat scans deferred by user | Not measured |
| Repeated ceiling spread | Independent repeat scans deferred | Not measured |
| Consumer app, two rooms, 70% beat/tie | Exports unavailable tonight | Incomplete |
| Calibrated intervals | No independent calibration/test properties | Not established |
| Full opening detection and width | Missing unique reference opening IDs and exhaustive counts | Not scoreable completely |
| Damage metric extents | No measured reference masks/prop dimensions | Not established |
| Photo footprint + adjacency | Inspect layout quality and partial extent scores | No full gate pass claimed |
