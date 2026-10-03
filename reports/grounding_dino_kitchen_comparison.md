# Grounding DINO Tiny kitchen comparison — 3 October 2026

`IDEA-Research/grounding-dino-tiny` is now an optional local detector backend
for photo, ordinary-video, and LiDAR scan-RGB candidates. It emits the same
`visual_candidates.json` contract as OWLv2 and Florence-2. The checkpoint is
pinned at revision `a2bb814dd30d776dcf7e30523b00659f4f141c71`, with
`model.safetensors` SHA-256
`1a2412ef99bd74bcd3c2a246fa1e48581f8889a1300c9051974741314fc042f3`.
Its text prompt is `doorway. door. open passage. window. cabinet door.`;
box and text thresholds are both 0.2, with a maximum of 30 boxes per frame.
The model card lists Apache 2.0. Boxes and scores are visual proposals only.

The kitchen comparison used the **same selected frame IDs** as earlier
Florence-2 and OWLv2 runs: eight photos, 12 standalone-video frames, and 12
scan RGB views; the LiDAR stage also fit 128 depth frames. The ordinary video
and scan RGB are independent recordings. Reference tape measurements were
used only for scoring, never for model input.

| Stage | Grounding DINO Tiny | Florence-2 Base | OWLv2 Base |
| --- | ---: | ---: | ---: |
| Photos | 113.01 s total; 107.66 s model; 94 boxes | 79.67 s; 75.15 s; 43 boxes | 397.75 s; 386.97 s; 200 boxes |
| Ordinary video | 184.28 s total; 171.61 s model; 140 boxes | 109.67 s; 101.57 s; 53 boxes | 243.25 s; 230.50 s; 232 boxes |
| LiDAR scan RGB | 245.96 s total; 181.65 s model; 106 boxes | 191.37 s; 126.48 s; 59 boxes | 290.27 s; 230.82 s; 171 boxes |
| Cross-capture linker | 147.09 s | 136.22 s | 144.87 s |
| Serial source plus linker time | **690.34 s (11.5 min)** | **516.93 s (8.6 min)** | **1,076.13 s (17.9 min)** |

The Grounding DINO scan produced 67 structural-class boxes (door, doorway,
open passage, window). Forty-eight projected to a fitted wall and 20
coincided with provisional LiDAR depth gaps, compared with 17 Florence and
36 OWLv2 gap coincidences. **Zero** passed the registered, measured-depth,
repeated-view criteria for a supported structural opening. Eight boxes were
rejected as structural openings by the at-wall depth check. More boxes or
coincidences are not a precision or recall score.

On the owner-identified `kitchen/IMG_0004.jpeg`, Grounding DINO proposed
three `open_passage` boxes in approximately `[453,2283,1406,3437]`,
`[378,1471,1412,3428]`, and `[212,1076,1476,3987]` source pixels. Visual
inspection found that these cover parts of the hall-facing opening, with
duplicate/broad extents. The same image has a curtained area proposed as a
window and a wall strip proposed as a door. OWLv2 also had an opening box
near this region; Florence's `open_passage` box covered nearly the whole
image. This one reviewed view does not establish whole-set accuracy.

The learned linker again supported **172 of 375** 2D image pairs. Grounding
DINO produced 106 image-region links, versus 38 Florence and 69 OWLv2, but
zero calibrated metric registrations, verified room crossings, measured
hall-passage widths, or room adjacencies. Its fused kitchen plan is unchanged:
**2.4909 × 2.3777 × 2.7781 m**, floor area **5.9226 m²**, with one unresolved
opening of unknown width. Against the owner's unordered 2.36 and 2.30 m
side references, errors remain +0.1309 m (+5.5%) and +0.0777 m (+3.4%);
height is −0.0219 m (−0.8%) versus 2.80 m. The 2.26 m hall opening height has no
accepted prediction, so height error cannot be calculated. The dimension fit is
provisional and its intervals remain unbounded.

**Decision:** keep Grounding DINO optional. It is faster than OWLv2 and its
passage proposals on one known view are more localized than Florence's, but
it is slower than Florence and did not improve the final kitchen structure
or measurements. Reviewed labels across frames and independent capture
scoring are needed before choosing a default detector.

Reproduction commands:

```bash
.venv/bin/python scripts/fetch_grounding_dino_model.py
.venv/bin/python -m roomproof process-capture kitchen --tier photo \
  --property-id prop-kitchen --capture-id cap-kitchen-photo-grounding-dino \
  --room-id room-kitchen --visual-model on --visual-backend grounding-dino \
  --visual-model-path .room-proof/models/grounding-dino-tiny \
  --max-model-frames 8 --runs-dir runs
.venv/bin/python -m roomproof process-capture kitchen/kitchen.mp4 --tier video \
  --property-id prop-kitchen --capture-id cap-kitchen-video-grounding-dino \
  --room-id room-kitchen --visual-model on --visual-backend grounding-dino \
  --visual-model-path .room-proof/models/grounding-dino-tiny \
  --max-model-frames 12 --runs-dir runs
.venv/bin/python -m roomproof process-capture /path/to/extracted/kitchen/scan \
  --tier lidar --property-id prop-kitchen --capture-id cap-kitchen-lidar-grounding-dino \
  --room-id room-kitchen --max-lidar-frames 128 --visual-model on \
  --visual-backend grounding-dino \
  --visual-model-path .room-proof/models/grounding-dino-tiny \
  --max-model-frames 12 --lidar-rgb-rotation 90 --runs-dir runs
.venv/bin/python -m roomproof link-captures \
  --photo-run /path/to/completed/photo-run \
  --video-run /path/to/completed/video-run \
  --lidar-run /path/to/completed/grounding-dino-scan-run \
  --photo-source kitchen --lidar-source /path/to/extracted/kitchen/scan \
  --max-views 12 --lidar-rgb-rotation 90 \
  --match-backend aliked-lightglue --runs-dir runs
```

Local ignored run IDs: photo `run-130ca0aa92074c058559638eb4fb5976`,
video `run-6d457520b13a467c86767396774b39d7`, LiDAR
`run-a89de626979e4ec08c33f48a20ce813d`, and linker
`run-2807cabe99ae48c0b0dfdcb6709549d1`. Private capture media and run
artifacts are not committed.
