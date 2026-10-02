# Kitchen mixed-pipeline implementation and pilot — 3 October 2026

Input: the owner's initially unscored `kitchen/` folder contains eight root-level
photos, a standalone `kitchen.mp4`, and `kitchen.zip`. The ZIP holds a Stray
scan with depth/confidence PNGs, odometry, IMU, camera matrix, and the scan's
own `rgb.mp4`. The standalone video and scan RGB are independent recordings.
The ZIP was inspected for unsafe paths before extraction to
`/tmp/roomproof-kitchen-capture/03930c629e`. The first runs preceded the
owner's reference measurements. Later development runs did not read those
measurements as pipeline input.

## Initial runs

| Stage | Run | Result |
| --- | --- | --- |
| Photos, model off | `run-fb26604f96694ad988ca09d5b5ac6b6a` | All eight root stills indexed under the explicit `room-kitchen` label; visual overlap evidence; metric layout unresolved. |
| Standalone video, model off | `run-2b7b0fc2a90f4744939f37c881dbca3a` | All 1,270 frames contribute to the low-resolution timeline; 24 frames receive detailed matching; no strong scene-change candidate; metric layout unresolved. |
| LiDAR, model off | `run-1633d6ec31134175b694b7a9eb624c60` | Provisional rectangle **2.4909 × 2.3777 m**, height **2.7781 m**, area **5.9226 m²**, one unverified depth gap **0.697 m** wide. These values have unbounded accuracy intervals. |
| Photos, OWLv2 | `run-8da57c9fae7042f28ac3eba057cdae91` | 200 boxes over eight stills: 102 cabinet-door, 3 door, 24 doorway, 63 open-passage, 8 window. Inference stage **386.97 s** CPU. Boxes are unreviewed and do not alter the plan. |
| Video, SegFormer pilot | `run-d3da7cdec3b842a6b8869176d7fee9f8` | 106 regions over 24 selected frames: 35 wall, 24 floor, 24 ceiling, 7 door, 16 window. This checkpoint is evaluation-only; classes and regions are unreviewed. |
| LiDAR scan RGB, OWLv2 | `run-7572f09d631841899ef4e803b7fdf005` | 171 proposed boxes over 12 sampled scan RGB frames: 79 cabinet-door, 52 open-passage, 18 doorway, 16 door, 6 window. The 92 structural-class boxes yielded 49 projected-to-wall candidates and 36 visual/depth-gap coincidences, but **zero confirmed structural openings**. The provisional dimensions remain 2.4909 × 2.3777 × 2.7781 m. |
| Cross-capture observation graph | `run-0ea083407755415298c1df1d0b75cc96` | 336 photo/video/scan-RGB pairs inspected; **five** 2D overlaps supported, all video-to-scan RGB. No photo-to-video or photo-to-scan match passed the current matcher. The graph carries 98 photo, 23 video, and 92 scan RGB opening-like proposals on selected views. |

The scan RGB is sideways in storage; its 90° clockwise display rotation was
visually inspected before view matching. With 12 selected scan RGB views, the
RGB/depth pairing stage supported a +1 depth-frame offset on its sampled
views: 11 usable registration records, nine registered sampled frames, and
median edge/control contrast 3.836. This only aligns the scan's own RGB and
depth; it does not register the independent photos or walkthrough in 3D.

The initial `cross_capture_links.json` preserves each tested pair, match count, 2D
consensus, and source references. `visual_room_graph.json` preserves the
source room labels, model proposals on selected observations, and the five
image-overlap edges. It intentionally has no inferred adjacency or metric
cross-capture transform. A same-room label supplied to three capture runs is
not evidence that the algorithm found their shared geometry.

The initial patch matcher missed visually related kitchen views. The later
ALIKED/LightGlue comparison below addresses that miss at the 2D matching
stage, while metric placement and physical opening identity remain unresolved.
The model candidates also need owner-reviewed opening labels: cabinets,
sliding glass, and dark regions can all produce
false structural proposals. The LiDAR depth gap remains unverified until
paired RGB geometry and independent views support the same physical opening.

## Separately supplied kitchen reference

After the first prediction runs, the owner supplied two wall
spans of 2.36 and 2.30 m, ceiling height 2.80 m, and a hall-facing open
passage width of 2.26 m. None of these values entered the predictions above.
The two reference spans were not assigned to physical wall IDs. Pairing them
by size gives current LiDAR errors of **+0.1309 m** (**5.5%**) and
**+0.0777 m** (**3.4%**); the ceiling error is **−0.0219 m** (**0.8%**).
These are provisional point-estimate errors, not calibrated accuracy claims.
The 0.697 m depth gap is not verified as the same feature as the owner's
2.26 m passage, so a numeric gap-width error would be misleading. The initial gap detector had
a 1.6 m width ceiling; a later general wide-passage candidate range up to
3.2 m still did not identify this passage in the kitchen scan. Record this
as a missed opening, not a successful doorway measurement. The owner later identified
`IMG_0004.jpeg` as showing both edges of that passage; this reference was
used for post-run evaluation only. Because these values are now known,
kitchen is development evidence for future rule changes; use a
different capture for an untouched evaluation of any changed thresholds.

## Mixed pipeline run after implementation

The photo, standalone-video, and scan-RGB candidate runs are respectively
`run-8da57c9fae7042f28ac3eba057cdae91`,
`run-9ba3b81942884ef6a5686ac3e84f7944`, and
`run-643ac8fb13c14f7f8443c3b175586121`. The standalone-video run
decoded all **1,270** frames for its coarse timeline, selected **24** for
detailed geometry, ran OWLv2 on **12**, and emitted **232** boxes. The LiDAR
run used **128** selected depth frames and emitted **171** scan-RGB boxes;
**zero** openings were structurally confirmed. It retained the same room
point estimates and a raw **0.697 m** depth-gap hypothesis. The exported
property plan gives that unverified opening an unknown type and **null,
unbounded width**, rather than assigning the raw gap width to the owner's
hall passage.

The patch matcher baseline on these **same three model-on source runs** is
`run-5b581e0c2192498db4e6fcbe5f5e7c14`: **336** view pairs, **five**
supported 2D overlaps, all video to scan RGB. The learned matcher run
`run-dc79cc91e51243fab3100e1018dfb6a3` inspected the same **336**
pairs and supported **148** 2D overlaps: 63 video/scan RGB, 48 photo/video,
and 37 photo/scan RGB. Its depth-backed registration diagnostic yielded 25
plausible camera-pose hypotheses under assumed focal lengths and three
cross-view-consistent hypotheses, but **no accepted metric registration**.
Independent camera intrinsics and scan RGB-to-depth extrinsics have not been
calibrated. The stricter local-keypoint opening association emitted **52**
image-region links in **19 unverified groups**. These counts show improved
image matching, not verified physical-opening recall or room adjacency.

In `IMG_0004.jpeg`, OWLv2 proposed several overlapping open-passage boxes.
One box (`candidate-d433f437ec34a33d`, source pixels
`[331, 1180, 1467, 3536]` in the 3024 × 4032 photo) roughly covers the
visible kitchen-to-hall passage. The learned linker connects nine region
pairs involving that photo, including some scan-RGB views. Boxes overlap
substantially and could represent the same passage or its surrounding
scene. There is no verified projection of its left and right jambs onto the
same measured LiDAR wall, so the **2.26 m width was not recovered**. The
photo filename and reference width were not passed to the model.

The fused [property plan](../runs/run-dc79cc91e51243fab3100e1018dfb6a3/property_plan.json)
contains one inferred kitchen room, provisional floor area **5.9226 m²**,
spans **2.4909 × 2.3777 m**, ceiling **2.7781 m**, one unresolved opening
with null width, and no inferred adjacency. Its intervals remain unbounded.
The linked [SVG](../runs/run-dc79cc91e51243fab3100e1018dfb6a3/property_plan.svg)
is a visualization of that provisional room fit. These `runs/` links are
local ignored artifacts; they will not resolve on GitHub.

The three model-on stages took 397.75, 243.25, and 307.66 seconds;
learned linking took 132.99 seconds. Their sequential total is **1,081.65 s
(18.0 min)** on this CPU, above the project's **15-minute** target even
before model provisioning. Memory peaks were approximately 2.3 GiB per
model stage. Candidate precision, physical-opening identity, and finite
measurement intervals remain unscored or unresolved. This is a functional
mixed-pipeline pilot, not a complete property reconstruction.

## Reproduction commands

```bash
.venv/bin/python -m roomproof process-capture kitchen --tier photo \
  --property-id prop-kitchen --capture-id cap-kitchen-photo \
  --room-id room-kitchen --runs-dir runs
.venv/bin/python -m roomproof process-capture kitchen/kitchen.mp4 --tier video \
  --property-id prop-kitchen --capture-id cap-kitchen-video \
  --room-id room-kitchen --runs-dir runs
.venv/bin/python -m roomproof process-capture /tmp/roomproof-kitchen-capture/03930c629e \
  --tier lidar --property-id prop-kitchen --capture-id cap-kitchen-lidar \
  --room-id room-kitchen --max-lidar-frames 128 --runs-dir runs
.venv/bin/python -m roomproof link-captures \
  --photo-run runs/run-8da57c9fae7042f28ac3eba057cdae91 \
  --video-run runs/run-9ba3b81942884ef6a5686ac3e84f7944 \
  --lidar-run runs/run-643ac8fb13c14f7f8443c3b175586121 \
  --photo-source kitchen --lidar-source /tmp/roomproof-kitchen-capture/03930c629e \
  --max-views 12 --lidar-rgb-rotation 90 \
  --match-backend aliked-lightglue --runs-dir runs
```

These run IDs refer to local ignored artifacts; raw kitchen media and model
weights are not stored in Git.

## Stages 2–6 integrated kitchen run

After the earlier pilot, the updated LiDAR run
`run-8bc96a7785874b168c202b0c681dee2a` processed 128 selected depth
frames with OWLv2 on 12 scan-RGB views. Its repeated-plane irregular
alternative found 12 candidate wall planes but rejected the resulting
polygon because one edge lacked sufficient repeated wall support. The
original rectangle stayed **2.4909 × 2.3777 m**, height **2.7781 m**. The
depth stage still found only a separate **0.697 m** unverified gap; the new
3D edge record shows both flanking wall sides in 17 sampled frames and
behind-wall returns in five, but these do not identify it as the owner's
2.26 m hall passage. The final plan keeps its width null.

The final learned linker `run-dbe819d692074d83af4d698741ff5786` used
the same eight photo and 12 model-video frames as the earlier pilot, added
adjacent selected video pairs and within-photo pairs, and compared **375**
view pairs. **172** passed 2D matching: 63 video/scan RGB, 48 photo/video,
37 photo/scan RGB, 16 photo/photo, and 8 video/video. Its 69 matched
image-region links formed 26 unverified opening tracks. It decoded **all
1,270 standalone-video frames** for low-resolution optical flow, recording
seven candidate-region continuity segments. Sparse video geometry supported
seven ordered motion edges, all with **arbitrary scale and assumed
intrinsics**. It recorded eight possible opening-transition tracks; none
passed a calibrated wall-crossing test. Twenty-five assumed-focal camera
poses appeared plausible and three agreed across separated scan views,
but **no metric registration was accepted**. The kitchen had no calibration
file for its independent camera or scan RGB-to-depth pixel mapping.

The linked [property plan](../runs/run-dbe819d692074d83af4d698741ff5786/property_plan.json)
is schema-valid: one provisional kitchen, **5.9226 m²** floor area,
**2.7781 m** ceiling, one unresolved opening with null width, and **zero**
adjacencies. The [visual room graph](../runs/run-dbe819d692074d83af4d698741ff5786/visual_room_graph.json),
[LiDAR geometry](../runs/run-8bc96a7785874b168c202b0c681dee2a/lidar_geometry.json),
and [placement report](../runs/run-dbe819d692074d83af4d698741ff5786/room_placement.json)
retain the rejected or unresolved evidence. These links are local ignored
artifacts and will not resolve on GitHub.

The updated LiDAR and linker stages took **290.27 s** and **144.87 s**.
With the prior photo and video model-on stages, the serial kitchen total is
**1,076.13 s (17.9 minutes)**, still above the 15-minute target. The
calibrated PnP path was exercised with controlled synthetic 3D landmarks:
two separated scan views produced one accepted camera pose. Synthetic
ordinary-image jamb rays also matched a supported one-metre scan gap and
the calibrated video crossing gate identified a wall crossing. These
checks exercise code paths; they are **not** measured accuracy on a real
property. The
multiroom placement path was exercised separately with a synthetic
two-room, shared-opening fixture: one verified connection yielded two
nonoverlapping placements and one adjacency in a schema-valid plan. This
does not demonstrate accuracy on a real second scan. Without a real
calibrated connection, `assemble-property` must leave the second room
unplaced. Kitchen reference measurements are development evidence, not an
untouched score for the new rules.
