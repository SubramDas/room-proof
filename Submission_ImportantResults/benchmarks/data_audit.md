# Supplied-data audit

| Dataset | Frames | Seconds | Variable video timing | Acceleration norm | Focal range px |
|---|---:|---:|---|---:|---|
| kitchen/lidar | 2298 | 52.30 | True | 0.999 | 1338.1–1363.1 |
| three_room/lidar | 5351 | 123.53 | True | 1.000 | 1338.1–1352.8 |
| Crack_water/lidar/04a0d041fc | 2338 | 39.29 | True | 0.999 | 1340.9–1348.2 |
| single_room/c00a170fe1 | 1715 | 37.17 | True | 1.003 | 1586.6–1617.8 |
| single_scan_floor_only/1a8384c3f6 | 5251 | 114.78 | True | 1.001 | 1588.8–1616.0 |
| single_scan_with_ceiling/c7d28f72c6 | 9745 | 214.93 | True | 1.003 | 1581.2–1614.6 |

## Findings

8 image hashes occur in multiple folders. These are not independent validation samples.

Variable timing, changing intrinsics and likely IMU units are handled by the adapter; no manual edits to sensor files are needed. Keep originals unchanged. A timing mismatch causes a warning rather than an invented frame association.

- Use per-frame K; static camera_matrix is only a fallback.
- Decode MP4 sample timing and preserve edit-list-hidden frames.
- Do not integrate IMU translation; acceleration norms suggest g units.
- Two rooms plus corridor retained per user instruction.
- Consumer-app comparison unavailable tonight; repeat scans deferred.
