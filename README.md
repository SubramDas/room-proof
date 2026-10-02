# RoomProof

Status: input-validation foundation. The repository does **not** yet reconstruct plans or pass the benchmark gates. See [SPEC.md](SPEC.md), [TASK.md](TASK.md), and [COMPLIANCE.md](COMPLIANCE.md).

Ubuntu 24.04 with Python 3.12.3 is the tested platform. The pinned [requirements.txt](requirements.txt) now includes a free HEVC decoder for Stray Scanner export validation. Its Linux x86-64 wheel is about 29.5 MB. Set up a local environment and print the CLI version:

```bash
bash scripts/setup.sh
.venv/bin/python -m roomproof --version
```

The earlier foundation-only setup took 3.07 seconds, used a 16 MB virtual environment, and downloaded 0 bytes. A new temporary-directory setup with the pinned decoder took **14.65 seconds** and used a **92 MB** virtual environment with the wheel cached. The Linux x86-64 wheel is 29.5 MB to download when uncached. These measurements exclude capture transfer and property-plan processing.

The CLI imports and verifies original capture files in a reproducible [local bundle](repro/README.md). `process-capture` uses one command shape for `photo`, `video`, and `lidar`; it writes an input quality report and a run manifest, including for rejected inputs. Photo runs index decoded stills by the stable room-folder ID. Ordinary video runs decode up to 24 evenly spaced frames by default, downscale them to 640 pixels wide, and preserve source-video frame references; `--max-video-frames` changes that limit. Variable-rate video decoding preserves source frame boundaries. LiDAR runs preserve depth/confidence/pose joins by frame ID and leave RGB links unresolved where timing evidence is absent. The three starter exports' format findings are in [reports/input_audit.md](reports/input_audit.md). Geometry reconstruction, property-plan JSON, and rendered plan remain open tasks.

Example input check (replace the IDs with the project's stable IDs):

```bash
.venv/bin/python -m roomproof process-capture captures/my-scan --tier lidar \
  --property-id prop-home --capture-id cap-home-lidar
```

Run **every** project Python or CLI command through `.venv/bin/python` after setup. The setup script uses system `python3` only to create that virtual environment. Progress is recorded in [TASK.md](TASK.md) and a root-level journal for each numbered phase, beginning with [Journal-0.md](Journal-0.md).

Working choices are in [docs/decisions.md](docs/decisions.md); stable IDs and manifests are in [docs/ids_and_manifests.md](docs/ids_and_manifests.md). The Phase 1 capture card, [device matrix](docs/device_matrix.md), [format audit](reports/device_format_dummy_room.md), and [component/license record](docs/dependencies.md) document the stock route. Raw starter data and local environments are ignored by Git. Preserve raw interiors outside public Git until the owner chooses a submission destination and access level.
