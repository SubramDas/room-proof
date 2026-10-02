# Starter LiDAR input audit

**Status:** format and reader audit, not a geometry-accuracy result. Audits ran locally with `.venv/bin/python -m roomproof audit-stray` and the pinned imageio-ffmpeg 0.6.0 / FFmpeg 7.0.2 decoder. Original data remain in the ignored local bundle.

## Measured files and timing

| Starter scan | Decoded RGB | Pose / depth / confidence | IMU rows | Pose time span; median step | IMU median step | Largest translation step |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| `single_room/c00a170fe1` | 1,714 frames; 37.17 s; 1920×1440 HEVC; 46.12 fps average | 1,715 each; IDs 000000–001714 | 3,689 | 37.172 s; 0.0166693 s | 0.0100680 s | 0.0247 m |
| `single_scan_floor_only/1a8384c3f6` | 5,250 frames; 114.78 s; 1920×1440 HEVC; 45.75 fps average | 5,251 each; IDs 000000–005250 | 11,397 | 114.783 s; 0.0166691 s | 0.0100690 s | 0.3142 m |
| `single_scan_with_ceiling/c7d28f72c6` | 9,744 frames; 214.92 s; 1920×1440 HEVC; 45.34 fps average | 9,745 each; IDs 000000–009744 | 21,339 | 214.929 s; 0.0166690 s | 0.0100700 s | 0.0280 m |

Every RGB video decoded completely with original frame boundaries preserved (`-vsync 0`). Every depth/confidence PNG passed chunk CRC checks. All depth PNGs are 256×192, 16-bit grayscale; all confidence PNGs are 256×192, 8-bit grayscale. Five depth/confidence pairs per scan were pixel-decoded. Sampled depth values ranged 506–3,732, 240–1,945, and 311–4,480 respectively; the developer format describes depth values as millimetres, but no independent distance was measured. Sampled confidence values used codes 0, 1, and 2; this audit preserves the codes without assigning quality semantics.

The 3×3 `camera_matrix.csv` and per-pose `fx, fy, cx, cy` values parse. Quaternion norms stayed within about `1 ± 0.000001`; pose and IMU timestamps were strictly increasing. The largest pose translation step in the floor-only scan is about 31 cm and merits review in geometry processing; it is not independently confirmed as a tracking failure.

## Alignment and limits

All three scans have **one fewer decoded RGB frame** than pose/depth/confidence records. Depth and confidence frame IDs match the odometry frame IDs exactly. The reader in [roomproof/readers.py](../roomproof/readers.py) joins those three sources by ID and leaves `rgb_frame_index` null with `rgb_pairing_status: unresolved`; it does not assume the first or last RGB frame is missing. Variable-rate source videos also require `-vsync 0` during decoding: FFmpeg's default constant-rate output repeated frames in the first starter (2,230 yielded frames versus 1,714 original frames), so the reader and audit now preserve source frame boundaries.

The exports do not establish the precise RGB-to-depth timestamp offset, transform direction/axis convention, an independently measured metric scale, or an RGB-to-depth extrinsic/registered-pixel mapping. `camera_matrix.csv` and the per-pose intrinsics are retained, but calibration assumptions need physical checks before geometry or damage extents use them. These starter folders were not accompanied by original ZIPs for byte-transfer comparison, so their transfer completeness remains unverified. The owner scan's ZIP was separately verified byte-for-byte in [its device report](device_format_dummy_room.md).

## Reproduction runs

| Scan | Reader run | Detailed audit run |
| --- | --- | --- |
| `single_room/c00a170fe1` | `run-24eca40c59354f5b959c94af87ad19b8` | `run-e0ecb11d3d464ec8be938b97546ec2b0` |
| `single_scan_floor_only/1a8384c3f6` | `run-7f0a15c0d68643c2bb76792512274fdd` | `run-561bafe90427491eb0bcc993517baf76` |
| `single_scan_with_ceiling/c7d28f72c6` | `run-cdbeef8615ac4a42ac7ae43a7136a4ba` | `run-cb98c7452eef4d7d8f0acf895350c031` |

The detailed audit JSON is tracked as [single-room](input_audit_single_room.json), [floor-only](input_audit_floor_only.json), and [with-ceiling](input_audit_with_ceiling.json). Full run manifests and the three `lidar_frames.json` outputs remain under `/tmp/roomproof-runs/` for this workspace session; they are not added to Git with the raw scan data.
