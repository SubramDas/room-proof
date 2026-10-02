# RoomProof

Status: partial reconstruction pipeline. A labelled single-room LiDAR scan can produce a provisional plan; photo and video plans remain unresolved, and benchmark gates are not met. See [SPEC.md](SPEC.md), [PLAN.md](PLAN.md) for the visual structure and LiDAR fusion order, [TASK.md](TASK.md), and [COMPLIANCE.md](COMPLIANCE.md).

Phase journals are [Journal-0.md](Journal-0.md) through [Journal-11.md](Journal-11.md). Phase 5 adds evidence-gated damage rules but no detector. The separate reference evaluator is invoked after prediction, once independent truth exists:

An optional single-image [Gemini vision probe](roomproof/cloud_vision.py) is available with `GEMINI_API_KEY` set: `.venv/bin/python -m roomproof probe-vision PHOTO.jpeg`. It sends the original image to Google's API, stores model/response/usage/latency in an ignored run directory, and does not modify the property plan. Google's [pricing page](https://ai.google.dev/gemini-api/docs/pricing) currently lists a free tier for `gemini-3.5-flash-lite`; [image input documentation](https://ai.google.dev/gemini-api/docs/image-understanding) explains inline image transfer. Account quota and free availability must be rechecked at use time. No labelled cloud-versus-local accuracy result exists yet.

```bash
.venv/bin/python -m roomproof score-benchmark /path/to/benchmark_manifest.json
```

The manifest format is in [docs/benchmark_manifest.md](docs/benchmark_manifest.md). Keep this reference file outside the capture input tree; `process-capture` never reads it. The scorer currently covers measurement omissions/error and finite interval coverage, openings, ceiling accuracy, photo/video wall error, footprint area, adjacency, repeat spread, and damage class/surface omissions. Shape alignment, drift ablation, and damage polygon accuracy remain unfinished. [reports/benchmark.md](reports/benchmark.md) records the outstanding evidence.

Ubuntu 24.04 with Python 3.12.3 is the tested platform. The pinned [requirements.txt](requirements.txt) now includes a free HEVC decoder for Stray Scanner export validation. Its Linux x86-64 wheel is about 29.5 MB. Set up a local environment and print the CLI version:

```bash
bash scripts/setup.sh
.venv/bin/python -m roomproof --version
```

The earlier foundation-only setup took 3.07 seconds, used a 16 MB virtual environment, and downloaded 0 bytes. A new temporary-directory setup with the pinned decoder took **14.65 seconds** and used a **92 MB** virtual environment with the wheel cached. The Linux x86-64 wheel is 29.5 MB to download when uncached. These measurements exclude capture transfer and property-plan processing.

The CLI imports and verifies original capture files in a reproducible [local bundle](repro/README.md). `process-capture` uses one command shape for `photo`, `video`, and `lidar`; it writes an input quality report and a run manifest, including for rejected inputs. Valid inputs also write `property_plan.json` and `property_plan.svg` from one common contract. Photo and video still leave geometry unresolved. An explicitly labelled single-room LiDAR capture can now produce a provisional rectangle, wall/floor/ceiling surfaces, and unverified doorway gap candidates; an unlabelled or multiroom LiDAR capture remains unresolved. Dimensions have unbounded intervals until calibrated. Photo runs index decoded stills by the stable room-folder ID. Ordinary standalone video runs analyze **every decoded frame** at 64×48 for an ordered brightness and appearance-change timeline in `visual_geometry.json`; nominal-FPS timestamps are estimates. The more expensive corner matching uses up to 24 frames by default in evenly spaced short bursts at 640 pixels wide; `--max-video-frames` changes that limit. The optional visual model also has a separate `--max-model-frames` limit. Variable-rate video decoding preserves source frame boundaries. Photo and video runs write `visual_geometry.json` with source-linked visual corners, overlap, image motion, full-video appearance changes, and quality warnings. These are visual evidence, not metric poses or a stitched layout. The standalone video is separate from a LiDAR scan's `rgb.mp4`; the latter is used only within the LiDAR path for optional RGB/depth candidate linkage. LiDAR runs preserve depth/confidence/pose joins by frame ID and leave RGB links unresolved where timing evidence is absent. The three starter exports' format findings are in [reports/input_audit.md](reports/input_audit.md).

LiDAR runs also write a filtered diagnostic point cloud (`lidar_points.ply`) and `lidar_geometry.json`. The default sampler uses at most 32 frames: it reserves up to six slots for pose-near revisit views and fills the rest from evenly spaced time windows with strong raw depth/confidence coverage. `--max-lidar-frames` changes the bound. The report records the selection probes, horizontal height bins, and wall-like vertical-plane bins. These coordinates use documented camera and calibration assumptions and have not passed a tape-measured scale check. See [Journal-3.md](Journal-3.md) for current evidence and limits.

Use `--lidar-drift on` (the default) or `--lidar-drift off` to compare a geometrically verified revisit correction with exported poses. Both modes record raw and resulting occupied-depth-cell footprints in `lidar_geometry.json` and write `lidar_points_after_drift.ply`. If no same-view 3D closure passes the checks, the two point clouds and footprints remain identical. Occupied depth cells are a diagnostic, not a stitched room or property footprint.
The geometry report also samples RGB brightness across the scan and records weak-depth frames. RGB frame times are not paired to depth in this export, so a bright RGB sample does not certify a particular depth frame or surface.

A property folder may contain `room-...` photo subfolders and one top-level video file. Run `process-capture PROPERTY_FOLDER --tier photo ...` and `process-capture PROPERTY_FOLDER --tier video ...` separately. The photo run indexes only stills inside room folders; the video run selects the sole top-level clip. If there are multiple top-level clips, pass the intended video file path explicitly.
For a folder containing the stills of just one room at its root, pass
`--room-id room-...` to the photo command. Root-level video and ZIP files are
not treated as photos.

Example input check (replace the IDs with the project's stable IDs):

```bash
.venv/bin/python -m roomproof process-capture captures/my-scan --tier lidar \
  --property-id prop-home --capture-id cap-home-lidar
```

For a scan known to contain only the hall, add `--room-id room-hall --room-kind connector --max-lidar-frames 128`. The label declares the capture scope; it does not supply geometry. The resulting rectangle and any doorway gaps are provisional. See [reports/hall_pilot.md](reports/hall_pilot.md) for the supplied hall run.

For the supplied mixed `Flat-805/` folder, use a separate stable capture ID
for each independently interpreted tier:

```bash
.venv/bin/python -m roomproof process-capture Flat-805 --tier photo \
  --property-id prop-flat-805 --capture-id cap-flat-805-photo
.venv/bin/python -m roomproof process-capture Flat-805 --tier video \
  --property-id prop-flat-805 --capture-id cap-flat-805-video
```

Each invocation prints a `runs/run-.../run.json` path. Successful input
processing also writes `quality_report.json`, `property_plan.json`, and
`property_plan.svg` in that run directory; photo/video runs add
`visual_geometry.json`, and LiDAR adds `lidar_geometry.json` and sampled
`lidar_points.ply`. Check `run.json` for completion and warnings. A rejected
input still gets a failed run record. An accepted capture can produce an
*unresolved* plan; this means the geometry gate remains unsatisfied.

An experimental local semantic candidate stage is available for photo and
standalone video. It is off by default. Install its optional pinned Python
dependencies and fetch the hash-checked checkpoint, then use the same
`process-capture` command with `--visual-model on`:

```bash
.venv/bin/python -m pip install --require-hashes -r requirements-model.txt
.venv/bin/python scripts/fetch_visual_model.py
.venv/bin/python -m roomproof process-capture captures/my-photos --tier photo \
  --property-id prop-home --capture-id cap-home-photo --visual-model on
.venv/bin/python -m roomproof process-capture captures/my-video.mp4 --tier video \
  --property-id prop-home --capture-id cap-home-video --visual-model on
.venv/bin/python -m roomproof process-capture captures/my-extracted-stray --tier lidar \
  --property-id prop-home --capture-id cap-home-lidar --room-id room-hall \
  --room-kind connector --visual-model on
```

The stage writes `visual_candidates.json` and source-linked mask PNGs before
the plan stage. `--max-model-frames` bounds inference (default 24). Missing
weights or inference failure writes a diagnosable `unavailable` report and
keeps the plan unresolved. For LiDAR, the same flag produces independent RGB
proposals plus `rgb_pairing.json` and `lidar_candidate_links.json`. The pairing
stage compares nearby depth frames using RGB/depth boundaries; only sampled
frames that pass this check receive registered candidate links. Door proposals
must still match a supported depth gap and repeated views before affecting
an opening. Proposals do not establish metric dimensions or room
adjacency. The [candidate contract](docs/visual_candidates.md),
[pilot results](reports/model_candidate_pilot.md), and
[owner review sheet](docs/model_label_review.md) record current evidence.
The checkpoint is research/evaluation licensed and has not been adopted for
commercial production.

To compare independently processed photo, standalone-video, and LiDAR RGB
captures, use `link-captures` with their completed run directories and the
original photo folder and extracted Stray folder. It writes
`cross_capture_links.json`, `cross_capture_registration.json`,
`opening_correspondences.json`, `visual_room_graph.json`, a conservative
fused `property_plan.json`/SVG, and RGB pairing evidence.
At least nine scan RGB views are required for its registration gate. The
default patch matcher records 2D visual overlaps and opening proposals.
`--match-backend aliked-lightglue` enables the optional local learned matcher
after [provisioning](docs/dependencies.md); it also probes LiDAR-backed PnP
poses with held-out reprojection checks. Unknown independent-camera
calibration keeps those poses as hypotheses. The fused plan retains only
LiDAR-supported dimensions, carries unresolved rooms and openings, and does
not infer adjacency merely from image matches.

```bash
.venv/bin/python -m roomproof link-captures \
  --photo-run runs/PHOTO_RUN --video-run runs/VIDEO_RUN \
  --lidar-run runs/LIDAR_RUN --photo-source kitchen \
  --lidar-source /path/to/extracted/stray/scan \
  --max-views 12 --lidar-rgb-rotation 90
```

Add `--match-backend aliked-lightglue` to compare the learned matcher with
the patch baseline on the same selected view pairs.

The optional cloud probe needs `GEMINI_API_KEY` in the environment and explicit
approval before uploading any private interior photo. Its output is separate
from `process-capture`. Keep raw captures and reference truth in the separate
versioned bundle described in [repro/README.md](repro/README.md).

If setup fails, confirm Ubuntu/Python version, network access to the pinned
wheel, and free disk space (the current environment was about 92 MB). If a
capture fails, inspect its run's error and `quality_report.json`; keep the
original files intact and recapture missing coverage rather than editing the
source folder. If input processing succeeds but dimensions are null, that is
the current geometry limitation, not a setup failure.

Run **every** project Python or CLI command through `.venv/bin/python` after setup. The setup script uses system `python3` only to create that virtual environment. Progress is recorded in [TASK.md](TASK.md) and a root-level journal for each numbered phase, beginning with [Journal-0.md](Journal-0.md).

Working choices are in [docs/decisions.md](docs/decisions.md); stable IDs and manifests are in [docs/ids_and_manifests.md](docs/ids_and_manifests.md). The Phase 1 capture card, [device matrix](docs/device_matrix.md), [format audit](reports/device_format_dummy_room.md), and [component/license record](docs/dependencies.md) document the stock route. Raw starter data and local environments are ignored by Git. Preserve raw interiors outside public Git until the owner chooses a submission destination and access level.
