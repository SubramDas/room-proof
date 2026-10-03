# Reproduction

Raw kitchen and three_room data are included in project/. Public model weights are fetched by scripts; no private API or credential is needed. Set up from this directory:

```bash
cd project
bash scripts/setup.sh --models
.venv/bin/python scripts/fetch_models.py --depth-pro
.venv/bin/python scripts/check_environment.py
cd ..
bash reproduce_pairs.sh
```

The script runs all three before/after pairs from separate source directories. The stored config controls frame budgets, semantic views and drift settings. Outputs go into reruns/, preserving submitted evidence. CPU photo inference can take a long time. Set up downloads require network access; no clean-install time guarantee is claimed.

**Historical-source limitation:** four photo-after source files have hashes that cannot be recovered from the recorded commits or current files. That snapshot falls back to the recorded revision for those files and is explicitly not an exact reconstruction of the historical source. See source_audit.json. The current source is also included under project/astra for future reruns, but a new current-source run must not be represented as an exact replay of the saved photo-after numbers.

Before LiDAR/photo runs were actually reproduced from original revision e3977de; outputs are included under 02_runs/original_reproduction_checks/. Their reported dimensions match the original before outputs. A future clean-machine rerun of all historical after snapshots has not been verified. No exact historical-source reproduction claim is made for the saved photo-after result. A supplemental current-source replay is included when its run is available.
