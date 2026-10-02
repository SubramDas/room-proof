# LiDAR RGB candidate integration, hall scan

On 3 October 2026, the hall-only Stray export was rerun with
`--visual-model on --max-lidar-frames 128 --max-model-frames 24`. Completed run:
`runs/run-d421e1bc9d614527af63cfb6703dbfde/`. The input was the existing
audited extraction of `Flat-805/room-hall/hall.zip`; the raw archive was not
modified. Full processing took 127.95 s; the RGB selection, timestamp,
model, and linkage stage took 49.03 s. Input quality was
`valid_low_confidence`; plan schema and semantic checks passed.

The [Stray data specification](https://raw.githubusercontent.com/strayrobots/scanner/main/docs/format.md)
describes depth, confidence, and odometry by frame ID, but this export has
3,164 decoded RGB frames and 3,165 depth/pose frames. `rgb_pairing.json`
records actual RGB MP4 presentation timestamps, relative odometry times, and
per-frame candidate links. Timestamp agreement alone initially suggested
same-numbered frames (p95 residual 3.54 ms). Cross-modal image evidence then
favored **RGB frame i → depth frame i+1**: 18 of 23 usable sampled frames
preferred offset +1, four preferred 0, one preferred −1. The median RGB
gradient at the selected depth boundary was **3.86×** the shifted-pixel
control. The offset was supported in early, middle, and late samples; 20 of
24 selected RGB frames passed an individual registration check. Depth frame
`000000` and two local timing anomalies remain unpaired. This is a sampled
registration result, not verification of all frames or metric scale. The
absolute first-frame clock-origin assumption remains unverified; the integer
offset is supported by image/depth content.

The model produced 38 RGB proposals from 24 selected frames: 24 wall, 7
floor, 5 ceiling, and 2 door regions. The door proposals came from RGB frames
1087 and 1512, associated with depth frames 1088 and 1513 after offset
correction. `lidar_candidate_links.json` projects their image rays to the
fitted hall wall. All six sampled rays per proposal hit wall index 0, at
median offsets 0.377 m and 2.290 m along
that wall. The only provisional depth gap spans 2.919–3.624 m on the same
wall, so **neither visual proposal coincides with the gap**. There is no
repeated-view group supporting it. The model proposals remain unresolved and
the plan retains one unverified 0.705 m doorway candidate from depth alone.

The final LiDAR plan still reports 3.926 × 3.3958 m wall sides, 13.3319 m²
floor area, and 2.7682 m ceiling height, with unbounded intervals pending
held-out calibration. RGB registration did not change these numbers. The
owner's separately held 3.90 × 3.21 × 2.84 m values were not inference input.
This run demonstrates source-linked RGB inference and a detectable one-frame
offset; it does not establish that the chosen semantic checkpoint finds the
actual hall doorway or that the provisional depth gap is a door.

```bash
.venv/bin/python -m roomproof process-capture /tmp/roomproof-hall-lidar/b41a75401a --tier lidar --property-id prop-flat-805 --capture-id cap-flat-805-hall-rgb-linked-final --room-id room-hall --room-kind connector --max-lidar-frames 128 --visual-model on --max-model-frames 24 --runs-dir runs
```
