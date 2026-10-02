# RoomProof

Status: foundation only. The repository does **not** yet reconstruct plans or pass the benchmark gates. See [SPEC.md](SPEC.md), [TASK.md](TASK.md), and [COMPLIANCE.md](COMPLIANCE.md).

Ubuntu 24.04 with Python 3.12.3 is the tested platform. The pinned [requirements.txt](requirements.txt) now includes a free HEVC decoder for Stray Scanner export validation. Its Linux x86-64 wheel is about 29.5 MB. Set up a local environment and print the CLI version:

```bash
bash scripts/setup.sh
.venv/bin/python -m roomproof --version
```

The earlier foundation-only setup took 3.07 seconds, used a 16 MB virtual environment, and downloaded 0 bytes. A new temporary-directory setup with the pinned decoder took **14.65 seconds** and used a **92 MB** virtual environment with the wheel cached. The Linux x86-64 wheel is 29.5 MB to download when uncached. These measurements exclude capture transfer and property-plan processing.

The CLI currently imports and verifies original capture files in a reproducible [local bundle](repro/README.md). It writes a run manifest for each import/verification attempt, including failures. The future `photo`, `video`, and `lidar` processing command, JSON/plan outputs, and evaluation remain open tasks.

Run **every** project Python or CLI command through `.venv/bin/python` after setup. The setup script uses system `python3` only to create that virtual environment. Progress is recorded in [TASK.md](TASK.md) and a root-level journal for each numbered phase, beginning with [Journal-0.md](Journal-0.md).

Working choices are in [docs/decisions.md](docs/decisions.md); stable IDs and manifests are in [docs/ids_and_manifests.md](docs/ids_and_manifests.md). The Phase 1 capture card, [device matrix](docs/device_matrix.md), [format audit](reports/device_format_dummy_room.md), and [component/license record](docs/dependencies.md) document the stock route. Raw starter data and local environments are ignored by Git. Preserve raw interiors outside public Git until the owner chooses a submission destination and access level.
