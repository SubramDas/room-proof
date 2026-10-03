# Measured benchmark results

These results compare predictions with supplied laser dimensions. Extent comparisons are proxies, not full per-wall scores.

| Capture / tier | Reference | Quantity | Truth m | Predicted m | Error cm | Gate |
|---|---|---|---:|---:|---:|---|
| three_room_lidar / lidar | room_1 | short_extent | 2.300 | 1.841 | 45.95 | not specified |
| three_room_lidar / lidar | room_1 | long_extent | 2.360 | 2.540 | 18.00 | not specified |
| three_room_lidar / lidar | room_1 | ceiling_height | 2.800 | 2.753 | 4.65 | FAIL |
| three_room_lidar / lidar | room_2 | short_extent | 3.300 | 4.360 | 106.00 | not specified |
| three_room_lidar / lidar | room_2 | long_extent | 4.200 | 4.680 | 48.00 | not specified |
| three_room_lidar / lidar | room_2 | ceiling_height | 2.800 | 2.770 | 3.04 | FAIL |
| three_room_lidar / lidar | room_3 | short_extent | 0.810 | 1.031 | 22.06 | not specified |
| three_room_lidar / lidar | room_3 | long_extent | 1.670 | 1.326 | 34.36 | not specified |
| three_room_lidar / lidar | room_3 | ceiling_height | 2.260 | 2.275 | 1.46 | pass |
| three_room_lidar_after / lidar | room_1 | short_extent | 2.300 | 2.374 | 7.38 | not specified |
| three_room_lidar_after / lidar | room_1 | long_extent | 2.360 | 2.389 | 2.93 | not specified |
| three_room_lidar_after / lidar | room_1 | ceiling_height | 2.800 | 2.759 | 4.09 | FAIL |
| three_room_lidar_after / lidar | room_2 | short_extent | 3.300 | 3.253 | 4.66 | not specified |
| three_room_lidar_after / lidar | room_2 | long_extent | 4.200 | 4.235 | 3.51 | not specified |
| three_room_lidar_after / lidar | room_2 | ceiling_height | 2.800 | 2.769 | 3.13 | FAIL |
| three_room_lidar_after / lidar | room_3 | short_extent | 0.810 | 0.808 | 0.24 | not specified |
| three_room_lidar_after / lidar | room_3 | long_extent | 1.670 | 1.674 | 0.39 | not specified |
| three_room_lidar_after / lidar | room_3 | ceiling_height | 2.260 | 2.193 | 6.72 | FAIL |
| three_room_photos / photos | room_1 | short_extent | 2.300 | 6.600 | 430.00 | FAIL |
| three_room_photos / photos | room_1 | long_extent | 2.360 | 7.600 | 524.00 | FAIL |
| three_room_photos / photos | room_1 | ceiling_height | 2.800 | 4.115 | 131.55 | FAIL |
| three_room_photos / photos | room_2 | short_extent | 3.300 | 8.680 | 538.00 | FAIL |
| three_room_photos / photos | room_2 | long_extent | 4.200 | 9.400 | 520.00 | FAIL |
| three_room_photos / photos | room_2 | ceiling_height | 2.800 | 7.795 | 499.45 | FAIL |
| three_room_photos / photos | room_3 | short_extent | 0.810 | 4.440 | 363.00 | FAIL |
| three_room_photos / photos | room_3 | long_extent | 1.670 | 5.560 | 389.00 | FAIL |
| three_room_photos / photos | room_3 | ceiling_height | 2.260 | 4.711 | 245.08 | FAIL |
| three_room_photos_posefix / photos | room_1 | short_extent | 2.300 | 3.048 | 74.76 | FAIL |
| three_room_photos_posefix / photos | room_1 | long_extent | 2.360 | 7.470 | 510.97 | FAIL |
| three_room_photos_posefix / photos | room_1 | ceiling_height | 2.800 | 4.375 | 157.53 | FAIL |
| three_room_photos_posefix / photos | room_2 | short_extent | 3.300 | 7.680 | 438.00 | FAIL |
| three_room_photos_posefix / photos | room_2 | long_extent | 4.200 | 9.280 | 508.00 | FAIL |
| three_room_photos_posefix / photos | room_2 | ceiling_height | 2.800 | 7.118 | 431.77 | FAIL |
| three_room_photos_posefix / photos | room_3 | short_extent | 0.810 | 3.720 | 291.00 | FAIL |
| three_room_photos_posefix / photos | room_3 | long_extent | 1.670 | 5.440 | 377.00 | FAIL |
| three_room_photos_posefix / photos | room_3 | ceiling_height | 2.260 | 6.383 | 412.34 | FAIL |
| three_room_photos_final / photos | room_1 | short_extent | 2.300 | 2.604 | 30.38 | FAIL |
| three_room_photos_final / photos | room_1 | long_extent | 2.360 | 2.772 | 41.23 | FAIL |
| three_room_photos_final / photos | room_1 | ceiling_height | 2.800 | 3.407 | 60.74 | FAIL |
| three_room_photos_final / photos | room_2 | short_extent | 3.300 | 7.280 | 398.00 | FAIL |
| three_room_photos_final / photos | room_2 | long_extent | 4.200 | 7.600 | 340.00 | FAIL |
| three_room_photos_final / photos | room_2 | ceiling_height | 2.800 | 5.747 | 294.70 | FAIL |
| three_room_photos_final / photos | room_3 | short_extent | 0.810 | 2.240 | 143.00 | FAIL |
| three_room_photos_final / photos | room_3 | long_extent | 1.670 | 3.200 | 153.00 | FAIL |
| three_room_photos_final / photos | room_3 | ceiling_height | 2.260 | 3.216 | 95.58 | FAIL |

## Incomplete benchmark evidence

An independent kitchen repeat and two Magicplan room exports are supplied separately. Full wall correspondence, independent damage extents, official schema/round-one gates and independent interval calibration remain unavailable. The expanded capture has three rooms plus a connector; its automatic segmentation merges hall and kitchen, and the assisted correction is labelled separately. These gaps are not counted as passed gates.
