# Kitchen photo and LiDAR refresh — 3 October 2026

## Inputs and commands

The current `kitchen/` has eight root-level JPEGs and `kitchen/lidar/` with
`rgb.mp4`, `camera_matrix.csv`, `odometry.csv`, `imu.csv`, and 2,298 each of
depth and confidence PNGs. There is no standalone walkthrough video. The
photo reader indexed only the eight JPEGs; it did not ingest LiDAR PNGs as
photos. Source files were not edited.

```bash
.venv/bin/python -m roomproof process-capture kitchen --tier photo \
  --property-id prop-kitchen-refresh --capture-id cap-kitchen-refresh-photo \
  --room-id room-kitchen --visual-model on --visual-backend grounding-dino \
  --visual-model-path .room-proof/models/grounding-dino-tiny --max-model-frames 8

.venv/bin/python -m roomproof process-capture kitchen/lidar --tier lidar \
  --property-id prop-kitchen-refresh --capture-id cap-kitchen-refresh-lidar \
  --room-id room-kitchen --max-lidar-frames 64 --visual-model on \
  --visual-backend grounding-dino \
  --visual-model-path .room-proof/models/grounding-dino-tiny \
  --lidar-rgb-rotation 90 --max-model-frames 12

.venv/bin/python -m roomproof link-captures \
  --photo-run runs/run-30c5ffd2434c490e8af3a34c39ccffe2 \
  --lidar-run runs/run-e483f104c3604e98b25fcb415b8e9839 \
  --photo-source kitchen --lidar-source kitchen/lidar \
  --max-views 12 --lidar-rgb-rotation 90 \
  --match-backend aliked-lightglue
```

| Stage | Run ID | Result |
| --- | --- | --- |
| Photo + DINO | `run-30c5ffd2434c490e8af3a34c39ccffe2` | Complete, valid with low confidence; 94 proposals on eight photos. |
| LiDAR RGB-D + DINO | `run-e483f104c3604e98b25fcb415b8e9839` | Complete, valid with low confidence; 113 RGB proposals on 12 selected frames. |
| Photo-to-scan link and fused plan | `run-d574837b396542358576e5182adba76d` | Complete; schema-valid JSON and rendered SVG. |

## RGB/depth check

The replacement `rgb.mp4` decodes to 2,297 frames over about 52.28 s; the
depth, confidence, and pose streams have 2,298 matching frame IDs over about
52.30 s. The count differs by one because the export includes an initial
depth/pose frame before the RGB sequence. Sampled image-boundary evidence
favored a **+1 depth-frame offset** in 8 of 10 usable probes, with support
across the scan. The full-sequence index map then paired RGB frames 0–2296
to depth frames 000001–002297. All 2,297 mapped pairs pass the 7.5 ms timing
gate after clock-offset correction; maximum residual is about 1.9 ms.
Eight of the 12 selected RGB frames also passed the local pixel-registration
check. The median boundary contrast ratio against shifted controls was
3.268. The previous nearest-time implementation incorrectly left 840 frames
unpaired because it assumed the first RGB and depth frames shared an origin.
The corrected pairing is supported for the full sequence by timestamps and
index order; pixel alignment has only been checked on selected frames. This
does not calibrate an RGB-to-depth pixel transform or validate every opening.
See the LiDAR run's `rgb_pairing.json`.

## Plan result and limits

The fused plan contains one provisional kitchen room at **2.4946 × 2.3737 m**,
ceiling height **2.7782 m**. Its 0.698 m LiDAR depth gap remains an unverified
opening candidate with unknown plan width and height. The linker found 54
supported 2D image overlaps among 124 tested pairs and 34 opening-region
links. It accepted zero calibrated photo poses, zero structural openings, and
zero room connections. DINO's `IMG_0004.jpeg` passage match has one scan view
in this selected set; the provisional box-top-to-floor estimate is 1.787 m,
and is not a plan measurement. The absence of an ordinary video is explicit
in `video_motion_profile.json` and `room_transitions.json`.

The dataset now **runs through the photo, LiDAR, DINO, and fusion pipeline**
without a standalone video. It does not yet establish a measured passage or
complete property layout. The fused plan and review artifacts are in
`runs/run-d574837b396542358576e5182adba76d/`.
