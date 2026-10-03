# Expanded three-room scan results

## What was run

The replacement whole-property LiDAR scan contains 8,023 paired frames over 152.893 seconds. The pipeline sampled 240 frames, reconstructed 1,234,031 points, and completed the automatic run in 241.8 seconds. All four photo folders are present (bedroom 8, kitchen 8, hall 8, connector 6); these outputs are LiDAR reconstructions, not new photo-only or video-only runs.

## Automatic result

The unchanged automatic pipeline returned three candidates: bedroom (3.047 × 2.904 m, height 2.767 m), connector (1.325 × 1.013 m, height 2.272 m), and a merged hall/kitchen region (bounding extents 4.560 × 6.400 m, area 21.510 m²). Thus the automatic run did not recover the required four spaces correctly.

Run folder: `runs/three_room_expanded_assisted`. Relative output links below are relative to that run folder.

Original outputs: `../three_room_expanded_lidar/result.json`, `plan.pdf`, and `report.html`.

## Assisted result

To provide separate room measurements, visually reviewed source-frame ranges were used to select bedroom, hall and kitchen geometry. The existing single-room layout fitter was applied to each selection in the original shared coordinate system. The connector retains the automatic candidate. No laser dimensions, declared connections, rescaling, or manual polygon coordinates were supplied to the geometry fitter. The frame ranges and source hashes are recorded in `segments.json` and `provenance.json`. This is explicitly an assisted result, not a successful fully automatic segmentation benchmark.

| Space | Short × long extent (m) | Height (m) | Area (m²) | Extent errors (cm) | Height error (cm) |
|---|---:|---:|---:|---:|---:|
| bedroom | 2.904 × 3.047 | 2.769 | 8.851 | 7.43, 7.75 | 0.05 |
| connector | 1.013 × 1.325 | 2.272 | 1.343 | 20.31, 34.48 | 1.19 |
| hall | 3.310 × 4.215 | 2.765 | 13.951 | 0.99, 1.50 | 3.53 |
| kitchen | 2.337 × 2.379 | 2.758 | 5.561 | 3.74, 1.91 | 4.19 |

Extent errors compare sorted rectangle dimensions; physical wall-by-wall correspondence has not been established. Laser references were used only after reconstruction for this comparison.

Inferred paired-opening connections: bedroom–connector, hall–connector, hall–kitchen. These match the supplied connection list, but doorway dimensions remain provisional.

## Limitations

- The connector boundaries are inaccurate: predicted 1.013 × 1.325 m versus the reference 0.810 × 1.670 m. Do not infer accuracy from its similar total area.
- Kitchen and hall height errors are approximately 4.19 cm and 3.53 cm. Bedroom height is close, but its horizontal extents are oversized.
- RGB presentation timing and pose timestamps differ by up to 12.326 seconds. Source-index pairing is used; visual projection and assisted frame selections require caution. LiDAR backprojection uses depth/pose frame IDs and per-frame intrinsics.
- The IMU acceleration magnitude is approximately 1 g; the pipeline does not integrate it as m/s² translation.
- Measurement intervals are uncalibrated. Opening proposals are not verified doorway measurements. Damage detection was not rerun for the assisted layout.
- Both result files passed the provisional schema and measurement-invariant validator; this does not establish geometric accuracy.

## Reproduce

From the project root:

```bash
.venv/bin/python -m astra run --tier lidar --input three_room/lidar --output runs/three_room_expanded_lidar --max-frames 240 --semantic-views 12 --capture-id three_room_expanded
.venv/bin/python scripts/refine_lidar_segments.py --source runs/three_room_expanded_lidar --segments configs/three_room_expanded_segments.json --output runs/three_room_expanded_assisted
```

Open `plan.pdf` or `plan.png` for the floor plan, `report.html` for measurements, and `dimensions_comparison.csv` for the reference comparison. Existing submission snapshots were not replaced by these new results.
