# Astra: Local Property Reconstruction

CPU-first Python implementation.
It accepts LiDAR exports, RGB-only video, or unposed room photo folders and emits the same provisional JSON contract, a dimensioned plan, per-surface drawings, semantic evidence, and a browsable report.

See the [command and flag reference](#command-and-flag-reference) for all CLI options, accepted values and defaults.

## Start here on a new machine

The supported setup is **Ubuntu 24.04 on x86-64, Python 3.12, CPU**. Development runs used 64 GB RAM; a minimum RAM requirement has not been established. Native Windows and macOS installs have not been verified. Windows users can follow the Ubuntu commands in WSL2, but that environment has not been tested here. Allow several GB of free disk space for dependencies and models, plus space for raw captures and generated outputs. Internet is required for installation and model downloads; inference then runs locally without a paid API or API key.

### 1. Clone and install

The implementation is on the `final_implementation` branch. The repository must be public or shared with the reviewer for cloning to work.

```bash
sudo apt update
sudo apt install -y git python3.12 python3.12-venv

git clone --branch final_implementation https://github.com/SubramDas/room-proof.git
cd room-proof
bash scripts/setup.sh --models
.venv/bin/python -m pytest -q
```

Run all subsequent commands from the repository root. There is no separate application build or `pip install .` step: `.venv/bin/python -m astra` runs the source directly. Setup installs the pinned dependencies, downloads the default depth and detection models, and checks dependency compatibility. It may take longer than 15 minutes depending on download speed. If a download fails, restore connectivity and rerun setup; completed downloads are reused. Keep the pinned Torch/Torchvision pair together; xFormers is not required.

For a LiDAR geometry-only run, `bash scripts/setup.sh` installs the base dependencies without model downloads. In that case, use `--semantics off` in the LiDAR command below. Photo/video inference and LiDAR semantic detection require `--models` setup. The optional larger depth model can be downloaded later with `.venv/bin/python scripts/fetch_models.py --depth-pro`.

### 2. Supply a dataset

**Raw datasets and model binaries are excluded from Git. Cloning alone does not provide `three_room/`, `kitchen/`, or `Crack_water/`.** To run the supplied captures, obtain the separate Part 2 raw-data bundle from the project author and copy the desired capture into the repository root, for example `three_room/lidar/`.

Alternatively, put a compatible new dataset anywhere locally and pass its path to `--input`. Paths containing spaces must be quoted. A LiDAR scan must follow the Stray export contract below; an arbitrary point cloud or RGB folder is not a LiDAR export.

```text
my_capture/
  lidar/
    rgb.mp4
    odometry.csv
    imu.csv
    camera_matrix.csv
    depth/
      000000.png
      ...
    confidence/
      000000.png
      ...
```

- `odometry.csv`: columns `timestamp,frame,x,y,z,qx,qy,qz,qw`; strictly increasing timestamps, unique frame IDs, finite positions in metres, and normalized quaternions in xyzw order. Poses use the supplied camera-to-world convention (OpenCV camera axes, world Y up).
- Depth: single-channel PNGs with depth in millimetres (normally 16-bit). Confidence: matching single-channel PNGs with the same image dimensions and levels 0/1/2. Both folders must contain exactly the pose frame IDs, including leading zeros.
- Intrinsics: per-frame `fx,fy,cx,cy` columns in `odometry.csv`, or a numeric 3×3 comma-separated `camera_matrix.csv` using RGB pixel coordinates. Include `camera_matrix.csv` even with per-frame intrinsics because the run records it in the input manifest.
- `rgb.mp4`: one video sample per pose/depth frame, in the same source order. Preserve the original export; editing or trimming the video can invalidate pairing.
- `imu.csv`: a nonempty CSV containing numeric `a_x,a_y,a_z` columns; preserve the original export and its other columns.

Check the LiDAR structure before reconstruction:

```bash
.venv/bin/python -m astra audit \
  --input /path/to/my_capture/lidar \
  --output runs/my_capture_audit.json
```

The audit checks pose, intrinsics, frame pairing and video metadata, and records timing warnings. It does not check every image pixel or guarantee a usable reconstruction. Review warnings in the audit JSON.

For **photos**, use a folder containing 2–8 JPEG/PNG images, or one immediate subfolder per room with 2–8 images each. Convert HEIC images to JPEG/PNG first; HEIC decoding is not configured by this setup. For **video**, pass the MP4 file itself and choose `--rotation 0`, `90`, `180` or `270` to make its frames upright; the supplied Stray MP4 needs `90`.

### 3. Run a new dataset

Choose the command matching your input. Replace `/path/to/...` with the real local path, and use a fresh output directory for each run.

```bash
# LiDAR: add --single-room only if the capture contains one room.
.venv/bin/python -m astra run --tier lidar --input /path/to/my_capture/lidar --output runs/my_capture_lidar --max-frames 240 --semantic-views 12

# Photos: input is one room folder or a parent containing room folders.
.venv/bin/python -m astra run --tier photos --input /path/to/my_photos --output runs/my_capture_photos

# Video: set rotation for your particular recording.
.venv/bin/python -m astra run --tier video --input /path/to/my_video.mp4 --rotation 90 --max-frames 32 --output runs/my_capture_video
```

Open `report.html` in the chosen output folder after completion. `result.json`, `plan.pdf` and `plan.png` contain the structured result and floor plan. To explicitly check a LiDAR result:

```bash
.venv/bin/python -m astra validate runs/my_capture_lidar/result.json
```

A successful run can still report incomplete geometry, merged rooms, disconnected components or inaccurate dimensions. Validation checks the provisional output contract, not geometric accuracy. Do not apply `configs/three_room_expanded_segments.json` to a new capture: it contains frame selections specific to the supplied replacement scan.

### Troubleshooting

- **Missing input files:** datasets are separate from Git. Check extraction paths and use a specific scan folder with `odometry.csv` directly inside it.
- **Python/venv errors:** use Python 3.12 with `python3.12-venv` installed. If an existing `.venv` uses another version, rename it before running setup again.
- **Missing models or incompatible imports:** rerun `bash scripts/setup.sh --models`, then `.venv/bin/python scripts/check_environment.py`. Downloads require access to PyPI, the PyTorch CPU package index, GitHub, and Hugging Face.
- **Frame pairing errors:** use the complete, unmodified export; depth/confidence filenames must match pose IDs and the MP4 sample count must match the pose count.
- **`xFormers not available`:** this message from the depth model is expected on the CPU setup and does not indicate a failed run.
- **Long or interrupted run:** inspect `progress.log` and `run_status.json` in its output folder. See [Long CPU runs and recovery](#long-cpu-runs-and-recovery) below.

## Rerun the supplied replacement scan

After installation and placing the supplied dataset at `three_room/lidar/` (already present on the development laptop), check the environment and rerun with the latest documented LiDAR settings (240 sampled frames):

```bash
.venv/bin/python scripts/check_environment.py
.venv/bin/python -m astra run \
  --tier lidar \
  --input three_room/lidar \
  --output runs/three_room_rerun \
  --max-frames 240 \
  --semantic-views 12 \
  --capture-id three_room_expanded
```

Wait for the run to finish, then open `runs/three_room_rerun/report.html` in a browser. `result.json`, `plan.svg`, `plan.pdf`, `plan.png`, `rooms/`, `surfaces/`, semantic overlays, hashes and provenance are alongside it. Inference does not read `measurements.txt`. Use a fresh output directory for each experiment; if the example directory already exists, choose another name and update the following commands to match.

### Optional: reproduce the assisted four-space plan

The automatic run above is sufficient to rerun the pipeline. On this capture, automatic segmentation merges hall and kitchen. To reproduce the documented separate bedroom, connector, hall and kitchen plan, run this step **after the automatic run completes**:

```bash
.venv/bin/python scripts/refine_lidar_segments.py \
  --source runs/three_room_rerun \
  --segments configs/three_room_expanded_segments.json \
  --output runs/three_room_rerun_assisted
```

`--source` points to the completed automatic run, including `result.json` and `geometry/geometry.npz`. `--segments` supplies manually reviewed source-frame ranges for bedroom, hall and kitchen; the connector keeps its automatic geometry. The script reconstructs those selected spaces and writes a separate result to `--output`, preserving the automatic run. It does not use laser reference dimensions to fit the rooms, and it does not rerun damage detection.

**These frame selections apply only to the existing replacement scan in `three_room/lidar`.** Review and update the selections for a newly captured dataset. This is assisted reconstruction, and the connector geometry remains inaccurate. See [expanded scan results](docs/THREE_ROOM_EXPANDED_RESULTS.md) for measured limitations.

Open `runs/three_room_rerun_assisted/report.html` for the assisted measurements, or `plan.pdf` / `plan.png` in that folder for the floor plan.

### Optional: validate the output

```bash
.venv/bin/python -m astra validate \
  runs/three_room_rerun_assisted/result.json
```

This checks the JSON against the project's provisional schema and measurement consistency rules. It does **not** establish that room dimensions are accurate. The refinement script already validates internally, so this command is an optional explicit recheck. If you skipped refinement, use `runs/three_room_rerun/result.json` instead.

### Other input examples

```bash
# Single furnished room
.venv/bin/python -m astra run --tier lidar --input kitchen/lidar --output runs/kitchen --single-room

# RGB-only video: pass the MP4 itself. Sensor sidecars are not read.
.venv/bin/python -m astra run --tier video --input three_room/lidar/rgb.mp4 --rotation 90 --max-frames 32 --output runs/video

# Photos: named room folders, each with 2–8 images
.venv/bin/python -m astra run --tier photos --input three_room --output runs/photos

# Explicit demonstration of user-declared black/brown staging props
.venv/bin/python -m astra run --tier lidar --input Crack_water/lidar --output runs/damage --single-room --staged-damage

```

For a separate comparison with laser references, `astra evaluate` requires an explicit JSON mapping from reference-room IDs to prediction-room IDs. Check this mapping against the rendered plan and result for each capture: LiDAR room IDs are ordered by observed camera visits. The previous README mapping (`{"room_1":"room_2","room_2":"room_1","room_3":"room_3"}`) belonged to the earlier three-space scan and must not be reused for the current replacement scan. The automatic merged hall/kitchen region cannot provide separate measurements for both rooms. Evaluation mappings never enter inference.

`--depth-model depth-pro` selects the optional Apple model after downloading it. `--device cuda` selects a compatible GPU installation; CPU is the default. `--semantics off` runs geometry without the detector; it does not claim damage is absent. `--drift off` provides the LiDAR ablation. `--layout-method free-space` reproduces the earlier wall extraction method. `--schema path.json` additionally validates against an official schema if one becomes available. Use a new output directory for each experiment.

## Command and flag reference

This reference covers every option of `.venv/bin/python -m astra` and the setup/refinement helpers used above. Defaults below are the CLI defaults; example commands may override them. Flags marked **switch** take no value: write `--single-room`, not `--single-room true`. Omit a switch to leave it disabled. Tier-specific options have no effect on other tiers unless stated otherwise.

Use `-h` or `--help` on the main command or any subcommand to display its syntax without starting a run:

```bash
.venv/bin/python -m astra --help
.venv/bin/python -m astra run --help
.venv/bin/python -m astra evaluate --help
```

### `run`: reconstruct a dataset

```text
.venv/bin/python -m astra run --tier TIER --input PATH --output DIRECTORY [options]
```

| Flag | Accepted values / default | Meaning and applicability |
|---|---|---|
| `--tier` | **Required:** `lidar`, `photos`, `video` | Selects the input adapter and reconstruction pipeline. |
| `--input` | **Required:** local path | LiDAR scan directory (or parent containing exactly one scan), photo folder/parent of room folders, or MP4 file, according to tier. See the input contract above. |
| `--output` | **Required:** directory path | Destination for results, reports, geometry and progress logs. Use a new directory for a new experiment. |
| `--capture-id` | Text; default: input path's final component without its extension | Label recorded in the result. For an input ending in `/lidar`, the default is `lidar`; set an explicit name to distinguish captures. |
| `--max-frames` | Integer **≥ 2**; default `120` | Maximum evenly sampled frames for LiDAR/video, capped at available frames. More frames increase work. Photos use all supplied images (2–8 per room), so this does not limit photos. The value is still checked for every tier. |
| `--semantic-views` | Integer **≥ 0**; default `10` | Maximum sampled views examined for semantic/staged evidence. `0` processes no views, but does not itself disable loading the detector; use `--semantics off` to disable it. |
| `--semantics` | `on`, `off`; default `on` | Enables/disables the learned detector. `off` retains geometry and geometric opening proposals; it does not establish absence of damage. Explicit staged-marker processing can still run if requested. |
| `--device` | `cpu`, `cuda`; default `cpu` | Device for learned depth and detection models. Geometry remains on CPU. `cuda` requires a compatible NVIDIA GPU and CUDA-enabled Torch/Torchvision installation; the documented setup installs CPU builds. |
| `--layout-method` | `planes`, `free-space`; default `planes` | Wall/layout extraction method for all tiers. `planes` uses structural plane evidence; `free-space` selects the earlier extraction method for comparison. |
| `--single-room` | Switch; default disabled | Keeps the strongest room candidate when fitting LiDAR or each video component. Use for a single-room capture; it does not join disconnected video components. Photo folders already receive single-room fitting. |
| `--schema` | JSON schema file path; default none | Additionally validates the output against your supplied schema. The project's provisional schema and consistency checks always run. Does not transform output into a different contract. |
| `--staged-damage` | Switch; default disabled | Adds black/brown staging-prop candidates on sampled views. Use only for explicitly staged demonstrations such as `Crack_water`; this is not a natural-damage detector. |
| `--drift` | `on`, `off`; default `on` | **LiDAR:** enables/disables pose-graph drift correction. Use `off` for an ablation comparison. |
| `--min-confidence` | `1`, `2`; default `1` | **LiDAR:** minimum depth-confidence value retained. `1` accepts levels 1 and 2; `2` keeps only level 2, reducing available geometry. |
| `--gravity-lock` | Switch; default disabled | **LiDAR:** experimental restriction of drift-correction rotations to the world Y axis, suppressing roll/pitch corrections. Has no effect with `--drift off`. |
| `--rotation` | `0`, `90`, `180`, `270`; default `0` | **Photos/video:** clockwise image rotation before depth and feature extraction. `270` is equivalent to 90° counterclockwise. Does not rotate LiDAR inputs. |
| `--depth-model` | `small`, `depth-pro`, `depth-pro-int8`, `hybrid`; default `small` | **Photos/video:** selects learned depth estimation; see model choices below. LiDAR uses sensor depth. |
| `--rgb-scale-refinement` | Switch; default disabled | **Photos/video:** experimental refinement of relative per-view depth scales using matched image points. Does not calibrate against survey measurements. |
| `--rgb-geometry-bridges` | Switch; default disabled | **Video only:** tries weak depth-based links between consecutive frames when feature matching fails. Does not guarantee a connected or accurate reconstruction. |
| `-h`, `--help` | Switch | Prints command syntax and exits. |

Depth model choices:

| Value | Meaning | Required assets / restrictions |
|---|---|---|
| `small` | Depth Anything V2 Metric Hypersim Small; default depth model. | Installed by `bash scripts/setup.sh --models`. |
| `depth-pro` | Apple Depth Pro, including its learned focal estimate. | Also run `.venv/bin/python scripts/fetch_models.py --depth-pro`; larger memory/runtime cost. |
| `depth-pro-int8` | Experimental Depth Pro with dynamic int8 quantization of linear layers. | Same Depth Pro download; **CPU only**. Accuracy and speed must be checked for the capture. |
| `hybrid` | Experimental small-model depth rescaled from up to three Depth Pro anchor views, with a shared focal estimate. | Both small and Depth Pro assets are required. |

For ordinary runs, start with defaults plus the required input/output options. Experimental switches do not certify better results. `--semantics off` removes the detector requirement, but photos/video still require their depth model.

### `audit`: check a LiDAR export

| Argument | Accepted value / default | Meaning |
|---|---|---|
| `--input` | **Required:** scan directory or parent containing exactly one scan | Loads the LiDAR export and checks pairing, poses and metadata. |
| `--output` | **Required:** JSON **file** path | Writes the audit findings, e.g. `runs/my_capture_audit.json`. |

### `validate`: check a result

| Argument | Accepted value / default | Meaning |
|---|---|---|
| `result` | **Required positional argument:** result JSON file | File to validate; write the path directly after `validate`, without `--result`. |
| `--schema` | JSON schema file path; default none | Adds validation against this schema to the built-in provisional checks. |

### `evaluate`: compare with reference dimensions

All four options are required. Evaluation reads completed results and reference measurements; it does not rerun or adjust reconstruction.

| Flag | Accepted value | Meaning |
|---|---|---|
| `--result` | Result JSON file path | Reconstruction to score. |
| `--truth` | Measurements text file path | Reference room dimensions in metres, using the format of `measurements.txt`. Every mapped room needs `length`, `breadth` and `height`. |
| `--mapping` | Quoted JSON object | Maps **reference room ID → predicted room ID**; values must be checked against the actual result. This is inline JSON, not a mapping-file path. |
| `--output` | Directory path | Writes `metrics.json`, `metrics.csv` (when there are records), and `benchmark.md`. |

Example mapping syntax: `--mapping '{"room_1":"predicted_kitchen_id"}'`. Replace the example ID before running. The reference parser maps headings `Kitchen`, `Hall`, `connector`, `Bedroom` to IDs `room_1`, `room_2`, `room_3`, `bedroom`, respectively. Only mapped reference rooms are scored. Extents are compared in sorted short/long order; this is not a physical wall-by-wall or doorway score.

### `repeat`: compare two completed runs

| Flag | Accepted value | Meaning |
|---|---|---|
| `--first` | **Required:** result JSON file path | First reconstruction. |
| `--second` | **Required:** result JSON file path | Second reconstruction. |
| `--output` | **Required:** JSON **file** path | Destination for repeatability measurements. |

Rooms are matched by identical IDs; this command does not infer correspondence. Check that IDs represent the same physical rooms before interpreting differences. It compares extents and ceiling height, records missing rooms from the first result, and reports whether tiers match.

`audit`, `validate`, `evaluate` and `repeat` also accept `-h` / `--help`.

### Setup and assisted-refinement helpers

| Command / option | Accepted value / default | Meaning |
|---|---|---|
| `bash scripts/setup.sh` | No options | Installs base dependencies for LiDAR geometry with `--semantics off`. |
| `bash scripts/setup.sh --models` | Optional switch | Also installs model dependencies, downloads the default depth/detection models and checks the model environment. |
| `ASTRA_PYTHON` | Environment variable; default `python3.12` | Selects the Python 3.12 executable for setup, e.g. `ASTRA_PYTHON=/path/to/python3.12 bash scripts/setup.sh --models`. |
| `.venv/bin/python scripts/fetch_models.py` | No options | Downloads the default small depth model and its source. |
| `.venv/bin/python scripts/fetch_models.py --depth-pro` | Optional switch | Downloads optional Depth Pro and its source instead of the small model. |
| `.venv/bin/python scripts/fetch_semantic_models.py` | No options | Downloads Grounding DINO tiny for semantic detection. |
| `.venv/bin/python scripts/check_environment.py` | No options | Checks tested core/model package versions and model imports; it does not check dataset validity or load model weights. |

For `.venv/bin/python scripts/refine_lidar_segments.py`:

| Flag | Accepted value | Meaning |
|---|---|---|
| `--source` | **Required:** completed automatic LiDAR run directory | Must contain `result.json` and `geometry/geometry.npz`. |
| `--segments` | **Required:** segmentation JSON file | Contains `spaces`: each entry has a `name` and either an inclusive `source_frame_range_inclusive: [start, end]` or `retain_automatic_room` ID. Ranges refer to source-frame indices; each fitted range needs at least two sampled frames in the source run. |
| `--output` | **Required:** directory path | Must differ from `--source`; use a fresh folder for assisted outputs. |
| `-h`, `--help` | Switch | Prints the helper's syntax and exits. |

The supplied segments file is specific to the replacement scan. Review frame ranges and retained room IDs before using this helper with any other capture.

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


## Long CPU runs and recovery

Use the tested environment: `.venv/bin/python scripts/check_environment.py`. Installing xFormers independently changed PyTorch to an incompatible CUDA build during development; the CPU versions were restored. xFormers is not required. Keep the pinned Torch/Torchvision pair together.

The raw Stray walkthrough is sideways. A denser video run is:

```bash
.venv/bin/python -m astra run --tier video --input three_room/lidar/rgb.mp4 --output runs/video_dense_new --rotation 90 --depth-model small --max-frames 180 --semantic-views 8
```

Progress is written to `progress.log`, with state in `run_status.json`. A disconnected terminal output pipe no longer aborts computation. An explicit interrupt/termination is recorded separately. If an interrupted run has no completed result, rerun the same command to reuse its exact-image/model depth caches. Cached completion timings are not cold-run timings.

`--depth-model hybrid` is an experimental RGB-only mode using three Depth Pro anchors to estimate a shared focal length and rescale the faster depth model. `--rgb-scale-refinement` tests per-view depth-scale consistency from matched image points. `--rgb-geometry-bridges` tests weak depth-based temporal links. These options do not certify connectivity or accuracy; inspect each run's diagnostics. `--gravity-lock` and `--min-confidence 2` are LiDAR diagnostic alternatives; they were not improvements on the current three-room partition and are not default settings.
