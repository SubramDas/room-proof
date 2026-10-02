# RoomProof

Status: foundation only. The repository does **not** yet reconstruct plans or pass the benchmark gates. See [SPEC.md](SPEC.md), [TASK.md](TASK.md), and [COMPLIANCE.md](COMPLIANCE.md).

Ubuntu 24.04 with Python 3.12.3 is the tested foundation platform. There are no third-party Python dependencies at this stage, so the pinned external dependency set is empty. Set up a local environment and print the CLI version:

```bash
bash scripts/setup.sh
.venv/bin/python -m roomproof --version
```

A fresh temporary-directory setup on the development machine took 3.07 seconds, used a 16 MB virtual environment, and downloaded 0 bytes. This measures only the foundation CLI, not future model setup or capture processing.

The CLI currently imports and verifies original capture files in a reproducible [local bundle](repro/README.md). It writes a run manifest for each import/verification attempt, including failures. The future `photo`, `video`, and `lidar` processing command, JSON/plan outputs, and evaluation remain open tasks.

Working choices are in [docs/decisions.md](docs/decisions.md); stable IDs and manifests are in [docs/ids_and_manifests.md](docs/ids_and_manifests.md). Raw starter data and local environments are ignored by Git. Preserve raw interiors outside public Git until the owner chooses a submission destination and access level.
