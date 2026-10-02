# Hall-only pipeline pilot

Scope: one hall, processed independently from hall-only inputs. No multiroom stitching or reference measurements are fed to inference. The owner has already supplied hall reference dimensions separately: length 3.21 m, breadth 3.90 m, and ceiling height 2.84 m in `repro/bundle/benchmark_truth/flat_805_owner_dimensions.json`. These are available for validation once the software reports corresponding hall measurements; no new measurement is required for the current hall pilot.

| Tier | Input | Run | Result |
| --- | --- | --- | --- |
| Photos | `hall_photos/room-hall/`, 8 JPEGs | `run-3ed0a17855f140ff8000078192297ca6` | Input accepted; schema-valid JSON and SVG; one unresolved hall; no metric walls/openings. 8.30 s. |
| Video | `hall_video/IMG_0009.mp4`, 24 sampled frames | `run-a0e4461d405d48329d2233f6615d7b90` | Input accepted; schema-valid JSON and SVG; one unresolved room; no metric walls/openings. 12.34 s. Three of 18 sampled transitions lacked supported feature overlap. |
| LiDAR | `Flat-805/room-hall/hall.zip`, 3,165 depth/pose frames | `run-e36d1c3019d94640b77f890eaaa466f9` | Input accepted; schema-valid JSON and SVG; provisional four-wall hall and one unverified doorway candidate. 89.28 s. |

All three completed runs are under `/tmp/roomproof-hall-pilot/`. The LiDAR run now completes a provisional hall plan. Photo and video geometry remain unresolved. The separately supplied `flat_805.zip` was not used for this hall-only pilot.

The hall ZIP SHA-256 is `a5909cacdccb25d0593f80cc4eac7e67c311670359f3ade24505ab7bdf8b24cb`. ZIP integrity and extracted-file byte comparison passed. Audit run `run-42e956c81f754280a61eda57dec8f473` found 3,165 matching depth/confidence/pose frames, 3,164 decoded RGB frames, and closely matched 52.77 s video and 52.77 s pose durations. The one missing RGB frame keeps exact pairing unresolved.

The first 32-frame LiDAR run used the wrong camera-axis convention and left the hall unresolved. The corrected projection uses positive camera Z as forward and camera Y as down before applying the exported camera-to-world pose, consistent with the Stray visualizer's depth projection. The completed 128-frame run retained 366,019 filtered points and inferred a 3.926 m × 3.3958 m rectangle, 13.3319 m² floor area, and 2.7682 m ceiling height. Its wall, floor, and ceiling entries cite supporting depth/pose frames. One possible doorway gap on wall 1 has a provisional 0.705 m width and 2.919 m offset; its height is unknown and its status is unresolved until RGB/occlusion evidence confirms it. No verified hall revisit was found, so drift correction changed nothing here.

The separate owner laser values are 3.90 m × 3.21 m and 2.84 m high. The run's long side is +0.026 m, short side +0.1858 m, and ceiling −0.0718 m against those values. These comparisons are a post-run diagnostic, not inference inputs; accuracy tuning is deferred while the pipeline is built. All numeric plan measurements have unbounded intervals because no held-out calibration exists. The run quality is `valid_low_confidence`, and both schema and semantic checks pass. This is a working **single-hall** pipeline, not yet a verified multiroom plan, confirmed door/window schedule, or completed Phase 3.
