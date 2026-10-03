# Florence-2 Base versus OWLv2 on the kitchen — 3 October 2026

The Florence-2 adapter is available with `--visual-backend florence2` for
photo, standalone video, and LiDAR scan RGB. It emits the existing
`visual_candidates.json` contract; no model box directly measures an opening.
The checkpoint is `microsoft/Florence-2-base` at commit
`5ca5edf5bd017b9919c05d08aebef5e4c7ac3bac`, with pinned weight SHA-256
`03075d2d2d2bbd3e180b9ba0afae4aa8563226e2d32911656966e05b2f2ee060`.
Inference used CPU PyTorch, four threads, phrase grounding for doorway, door,
open passage, window, and cabinet door, greedy generation with no KV cache.
Florence does not supply a comparable per-box score in this path; the required
`raw_model_score` field is zero as a documented missing-score sentinel.

The two candidates saw the **same kitchen source files and selected frame
IDs**: eight photos, 12 ordinary-video frames, 12 scan-RGB views, and 128
selected LiDAR depth frames. Both linkers used ALIKED/LightGlue on 375 view
pairs. The independent video and scan RGB are separate recordings. No owner
tape value was used as model input. These are development captures and
reviewed doorway annotations for all frames are still unavailable.

| Stage | OWLv2 run, time, proposals | Florence run, time, proposals |
| --- | --- | --- |
| Photos | `run-8da57c9fae7042f28ac3eba057cdae91`; 397.75 s total, 386.97 s model; 200 boxes | `run-ab91e5bb4e2c4501b1d18e3cef62a5af`; 79.67 s total, 75.15 s model; 43 boxes |
| Ordinary video | `run-9ba3b81942884ef6a5686ac3e84f7944`; 243.25 s total, 230.50 s model; 232 boxes | `run-6762f49446074af1be06621ecccefb2a`; 109.67 s total, 101.57 s model; 53 boxes |
| LiDAR | `run-8bc96a7785874b168c202b0c681dee2a`; 290.27 s total, 230.82 s model; 171 boxes | `run-6d0de6e3f49c48299bf6209e65bc00a8`; 191.37 s total, 126.48 s model; 59 boxes |
| Learned link and fused plan | `run-dbe819d692074d83af4d698741ff5786`; 144.87 s; 69 region links, 26 unverified tracks | `run-d118b408d9ca46a1ade53e739e774969`; 136.22 s; 38 region links, 13 unverified tracks |

Sequential total: **1,076.13 s (17.9 min)** for OWLv2 versus **516.93 s
(8.6 min)** for Florence, on this CPU and these selected inputs. This excludes
weight provisioning and capture transfer. The Florence model itself is
smaller and faster here; proposal count alone does not measure precision.
Both linkers found the same **172 supported 2D view pairs of 375**, because
the image matcher is independent of candidate backend. OWLv2 had 36 visual
box/depth-gap coincidences and Florence 17, but neither accepted a structural
opening on the scan. Both plans retain the same provisional kitchen size
**2.4909 × 2.3777 × 2.7781 m**, one unresolved opening with null width, and
zero room adjacencies. Neither accepted calibrated registration.

The one owner-identified opening view is `kitchen/IMG_0004.jpeg`. On the
3024 × 4032 source image, OWLv2 proposed an open-passage box near the
visible kitchen-to-hall opening at approximately `[331, 1180, 1467, 3536]`.
Florence returned an `open_passage` box spanning almost the entire image,
`[1.51, 2.02, 3019.46, 4025.95]`, and its `doorway` box covered a narrow
left strip, `[1.51, 889.06, 521.64, 4025.95]`. Visual inspection does not
support treating either Florence box as both jambs of that passage. The
known 2.26 m passage height remains missed by the metric pipeline. A single
view does not establish full candidate precision or recall.

**Decision for now:** keep Florence optional. It is a clear CPU speed
improvement, but did not improve the kitchen plan and was worse on the one
reviewed passage localization. Do not replace OWLv2 until reviewed labels
across rooms show an acceptable opening recall and false-positive rate.

Reproduction commands, changing only the capture path/tier, IDs, and the
scan rotation as appropriate:

```bash
.venv/bin/python scripts/fetch_florence2_model.py
.venv/bin/python -m roomproof process-capture kitchen --tier photo \
  --property-id prop-kitchen --capture-id cap-kitchen-photo-florence2 \
  --room-id room-kitchen --visual-model on --visual-backend florence2 \
  --visual-model-path .room-proof/models/florence-2-base \
  --max-model-frames 8 --runs-dir runs
.venv/bin/python -m roomproof process-capture kitchen/kitchen.mp4 --tier video \
  --property-id prop-kitchen --capture-id cap-kitchen-video-florence2 \
  --room-id room-kitchen --visual-model on --visual-backend florence2 \
  --visual-model-path .room-proof/models/florence-2-base \
  --max-model-frames 12 --runs-dir runs
.venv/bin/python -m roomproof process-capture /tmp/roomproof-kitchen-capture/03930c629e \
  --tier lidar --property-id prop-kitchen --capture-id cap-kitchen-lidar-florence2 \
  --room-id room-kitchen --max-lidar-frames 128 --visual-model on \
  --visual-backend florence2 --visual-model-path .room-proof/models/florence-2-base \
  --max-model-frames 12 --lidar-rgb-rotation 90 --runs-dir runs
.venv/bin/python -m roomproof link-captures \
  --photo-run runs/run-ab91e5bb4e2c4501b1d18e3cef62a5af \
  --video-run runs/run-6762f49446074af1be06621ecccefb2a \
  --lidar-run runs/run-6d0de6e3f49c48299bf6209e65bc00a8 \
  --photo-source kitchen --lidar-source /tmp/roomproof-kitchen-capture/03930c629e \
  --max-views 12 --lidar-rgb-rotation 90 \
  --match-backend aliked-lightglue --runs-dir runs
```

Run directories and private capture media are local ignored artifacts; the
run IDs in this report will not resolve on GitHub.
