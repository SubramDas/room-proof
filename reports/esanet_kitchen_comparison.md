# ESANet RGB-D kitchen pilot — 3 October 2026

The optional `esanet` backend runs the official NYUv2 40-class ESANet-R34-NBt1D
checkpoint on scan RGB plus registered LiDAR depth. The source is pinned at
`820c5bb633e49e69dcd075d4330165bb540a0cc9`; checkpoint SHA-256 is
`eb1e5ee8b7c8f46f0d3014ac8684069b8ae6f52ddc24d655ef163be5ef962150`.
The checkpoint labels include wall, floor, ceiling, door, and window, but no
open passage. The model receives no independent tape measurements. Outputs
are masks and image-space region proposals, not a replacement for metric
LiDAR geometry.

Kitchen scan run: `run-fd3189133c2040f4af117c75e894c7fe`. The input was
the same extracted Stray scan as the OWLv2 and Florence kitchen comparisons,
with 128 sampled depth frames, 12 sampled scan RGB frames, and 90-degree
clockwise upright rotation. The registration gate admitted **9 of 12** RGB
samples for paired depth. ESANet ran on those nine only. Raw depth is in
millimetres; samples with low confidence or outside 0.25–6 m were masked.
Both RGB and depth were rotated, then resized to the model's 640 × 480 input.
This portrait-to-landscape resize is a domain mismatch and may affect masks.

| Result | ESANet | Florence-2 | OWLv2 |
| --- | ---: | ---: | ---: |
| Scan RGB frames inferred | 9 registered | 12 selected | 12 selected |
| Model stage on this CPU | 49.03 s | 126.48 s | 230.82 s |
| Full LiDAR capture run | 132.99 s | 191.37 s | 290.27 s |
| Structural-class proposals | 12 doors/windows | 45 doors/doorways/passages/windows | 92 doors/doorways/passages/windows |
| Visual proposal/depth-gap coincidences | 5 | 17 | 36 |
| Supported structural openings | 0 | 0 | 0 |

The time and proposal counts are **not a same-frame accuracy comparison**:
ESANet deliberately excludes the three selected RGB frames whose sampled
RGB/depth registration was not supported. Its 39 proposals comprise 15 wall,
7 floor, 5 ceiling, 6 door, and 6 window components. A contact-sheet review
of all nine paired views showed useful broad wall/floor/ceiling regions in
several views, but also a refrigerator region labeled as wall and some wall
patches labeled as window. A door label appeared over a glass partition.
These are qualitative observations, not precision/recall scores; reviewed
pixel labels and independently verified opening boundaries are unavailable.

The final single-room plan remains **2.4909 × 2.3777 × 2.7781 m**, area
**5.9226 m²**, with one unresolved opening of unknown width and zero verified
adjacencies. Against the owner's kitchen reference spans 2.36 m and 2.30 m,
the unordered side errors remain +0.1309 m (+5.5%) and +0.0777 m (+3.4%).
The height error against 2.80 m remains −0.0219 m (−0.8%). The hall-facing
opening height reference is 2.26 m, but no predicted opening height exists, so its height
error cannot be scored. Side references were matched by size because their
physical wall IDs were not supplied. These LiDAR fits have unbounded accuracy
intervals and remain provisional.

The end-to-end linker was also run as `run-e101f34aeec04abda5bc22b8988bc0d6`
using the existing Florence photo and ordinary-video runs plus the ESANet
LiDAR run. It inspected the same 375 image pairs and retained 172 supported
2D overlaps as the earlier Florence scan combination. It accepted no
metric registration, room crossing, opening width, or adjacency; the fused
plan retained the same dimensions and unknown hall passage. Link time was
196.65 s in this run versus 136.22 s previously; this is one CPU execution
with mixed visual backends, so it is not evidence that ESANet slows matching.

**Decision:** ESANet provides faster surface proposals on the registered
subset, but this pilot does not show improved plan quality or measurement
accuracy. Keep it optional. Surface masks currently enter the candidate
report and evidence trail; they do not change the LiDAR wall fit. Promoting
them into geometry would require verifying pixel alignment, class errors,
and a model-on/off measurement improvement on independent reference captures.

Reproduce with a local CPU virtual environment containing PyTorch,
torchvision, OpenCV, NumPy, matplotlib, pandas, and gdown:

```bash
.venv/bin/python scripts/fetch_esanet_model.py
.venv/bin/python -m roomproof process-capture /path/to/extracted/kitchen/scan \
  --tier lidar --property-id prop-kitchen --capture-id cap-kitchen-lidar-esanet \
  --room-id room-kitchen --max-lidar-frames 128 --visual-model on \
  --visual-backend esanet --visual-model-path .room-proof/models/ESANet \
  --max-model-frames 12 --lidar-rgb-rotation 90 --runs-dir runs
.venv/bin/python -m roomproof link-captures \
  --photo-run /path/to/completed/photo-run \
  --video-run /path/to/completed/video-run \
  --lidar-run /path/to/completed/esanet-scan-run \
  --photo-source /path/to/kitchen/photos \
  --lidar-source /path/to/extracted/kitchen/scan \
  --max-views 12 --lidar-rgb-rotation 90 \
  --match-backend aliked-lightglue --runs-dir runs
```

The local run files and the private kitchen capture are ignored artifacts;
the run ID in this report will not resolve on GitHub.
