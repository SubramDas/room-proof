# RoomProof

Status: input-validation foundation. The repository does **not** yet reconstruct plans or pass the benchmark gates. See [SPEC.md](SPEC.md), [TASK.md](TASK.md), and [COMPLIANCE.md](COMPLIANCE.md).

Phase journals are [Journal-0.md](Journal-0.md) through [Journal-10.md](Journal-10.md). Phase 5 adds evidence-gated damage rules but no detector. The separate reference evaluator is invoked after prediction, once independent truth exists:

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

The CLI imports and verifies original capture files in a reproducible [local bundle](repro/README.md). `process-capture` uses one command shape for `photo`, `video`, and `lidar`; it writes an input quality report and a run manifest, including for rejected inputs. Valid inputs also write `property_plan.json` and `property_plan.svg` from one common contract. The current plan shows indexed photo rooms and explicit unknown geometry, scale, openings, damage, and connections; video and LiDAR use one unresolved room placeholder until room segmentation is implemented. These files are a contract skeleton, not a measured property plan. Photo runs index decoded stills by the stable room-folder ID. Ordinary video runs decode up to 24 frames by default in evenly spaced short bursts, downscale them to 640 pixels wide, and preserve source-video frame references; `--max-video-frames` changes that limit. Variable-rate video decoding preserves source frame boundaries. Photo and video runs write `visual_geometry.json` with source-linked visual corners, overlap, image motion, and quality warnings. These are visual evidence, not metric poses or a stitched layout. LiDAR runs preserve depth/confidence/pose joins by frame ID and leave RGB links unresolved where timing evidence is absent. The three starter exports' format findings are in [reports/input_audit.md](reports/input_audit.md).

LiDAR runs also write a filtered diagnostic point cloud (`lidar_points.ply`) and `lidar_geometry.json`. The default sampler uses at most 32 depth frames; `--max-lidar-frames` changes the bound. These coordinates use documented camera and calibration assumptions and have not passed a tape-measured scale check. See [Journal-3.md](Journal-3.md) for current evidence and limits.

A property folder may contain `room-...` photo subfolders and one top-level video file. Run `process-capture PROPERTY_FOLDER --tier photo ...` and `process-capture PROPERTY_FOLDER --tier video ...` separately. The photo run indexes only stills inside room folders; the video run selects the sole top-level clip. If there are multiple top-level clips, pass the intended video file path explicitly.

Example input check (replace the IDs with the project's stable IDs):

```bash
.venv/bin/python -m roomproof process-capture captures/my-scan --tier lidar \
  --property-id prop-home --capture-id cap-home-lidar
```

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

No neural-network weights are required for the current local processing path.
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
