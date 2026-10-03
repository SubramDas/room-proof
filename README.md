# Astra: local property reconstruction

CPU-first Python implementation for the supplied Applied AI case study. It accepts LiDAR exports, RGB-only video, or unposed room photo folders and emits the same provisional JSON contract, a dimensioned plan, per-surface drawings, semantic evidence, and a browsable report.

**Current status: development benchmark, not a claim that evaluator gates pass.** See `reports/benchmark.md` and `docs/COMPLIANCE.md` for measured failures and missing evidence. The official Round 1 schema has not been supplied; `schemas/result.schema.json` is explicitly provisional. Learned depth has systematic scale error; room stitching can remain unresolved. All measurement ranges are labelled as uncalibrated.

## Run on this laptop

The environment and local weights are already installed. From this directory:

```bash
.venv/bin/python -m astra run --tier lidar --input three_room/lidar --output runs/demo --max-frames 140 --semantic-views 12
```

Open `runs/demo/report.html` in a browser. `result.json`, `plan.svg`, `plan.pdf`, `plan.png`, `rooms/`, `surfaces/`, semantic overlays, hashes and provenance are alongside it. Inference does not read `measurements.txt`.

```bash
# Single furnished room
.venv/bin/python -m astra run --tier lidar --input kitchen/lidar --output runs/kitchen --single-room

# RGB-only video: pass the MP4 itself. Sensor sidecars are not read.
.venv/bin/python -m astra run --tier video --input three_room/lidar/rgb.mp4 --rotation 90 --max-frames 32 --output runs/video

# Photos: folders room_1, room_2, room_3, each with 2–8 images
.venv/bin/python -m astra run --tier photos --input three_room --output runs/photos

# Explicit demonstration of user-declared black/brown staging props
.venv/bin/python -m astra run --tier lidar --input Crack_water/lidar --output runs/damage --single-room --staged-damage

# Validate and separately compare with the laser reference
.venv/bin/python -m astra validate runs/demo/result.json
.venv/bin/python -m astra evaluate --result runs/demo/result.json --truth measurements.txt --mapping '{"room_1":"room_2","room_2":"room_1","room_3":"room_3"}' --output runs/demo/evaluation
```

LiDAR room IDs are ordered by observed camera visits, so mapping must be checked against the rendered plan for each capture. The example maps this supplied multi-room scan's kitchen to predicted room_2 and hall to predicted room_1. It is not used during inference.

`--depth-model depth-pro` selects the optional Apple model after downloading it. `--device cuda` selects a compatible GPU installation; CPU is the default. `--semantics off` runs geometry without the detector; it does not claim damage is absent. `--drift off` provides the LiDAR ablation. `--layout-method free-space` reproduces the earlier wall extraction method. `--schema path.json` additionally validates against an official schema if one becomes available. Use a new output directory for each experiment.

## Clean Ubuntu installation

Python 3.12 with venv support is required. Internet is needed only to install public packages and download weights, then inference runs offline.

```bash
bash scripts/setup.sh --models
# Optional larger depth/focal model
.venv/bin/python scripts/fetch_models.py --depth-pro
.venv/bin/python -m pytest -q
```

A fresh install in under 15 minutes is a target, **not yet verified**; download speed dominates. No paid API or Kaggle key is required. Models are kept outside Git. The local run uses no hosted inference. See `models/README.md` for model sources and disclosures. GPU/Kaggle setup is optional; credentials are not included or read by this project.

## Project map

- `astra/io.py`: timestamped MP4 decoding, Stray validation, strict tier input adapters.
- `astra/geometry.py`, `lidar.py`, `rgb.py`, `layout.py`: geometry, drift graph, matching, depth, structural room extraction.
- `astra/semantics.py`, `openings.py`: candidate regions, metric projection, opening evidence, scope rules.
- `astra/evaluate.py`: laser scoring independent from reconstruction.
- `scripts/`: setup, downloads, benchmark and bundle helpers.
- `docs/`: capture protocol, device matrix, limitations and compliance.
- `fix_loop/`: declarations, preserved intermediate evidence and regenerable comparison.
- `reports/`: measured benchmarks and technical report.
- `IMPLEMENTATION_PLAN.md`: original detailed plan; actual implementation differences are disclosed in the report.

## Capture and evidence limitations

The current benchmark has two rooms and a corridor, rather than the specified three rooms plus a connector. Consumer-app captures are unavailable tonight; repeat scans are deferred at the user's request. The kitchen stills duplicate the multi-room kitchen stills and are not an independent test set. The damage marks are staged props. Do not use the candidate flags as a diagnosis of concealed damage or automatically price repairs.

## Development history

This session mounts `.git` read-only. Development commits are recorded in independent metadata `.history`:

```bash
git --git-dir=.history --work-tree=. log --oneline
```

The reproduction bundle includes a standard Git bundle export so another machine can inspect and clone the history. This is actual incremental implementation history, not reconstructed historical timestamps.
