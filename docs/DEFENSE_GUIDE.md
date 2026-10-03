# Defense and demonstration guide

## Start with the actual status

This is an executable local pipeline with measured limitations. Do not say that all evaluator gates pass. Open `docs/COMPLIANCE.md` and `reports/benchmark.md`; distinguish a completed run, a valid JSON file, an accurate measurement, and a calibrated uncertainty interval.

The declared property is kitchen + hall + corridor. It is not the prescribed three rooms plus connector. Repeat scans were deferred; the second-app comparison is missing. State those omissions directly.

## Preparation

```bash
.venv/bin/python scripts/check_environment.py
.venv/bin/python -m pytest -q
```

Keep the pinned environment stable. No API key is required. Cached public weights are local. A completed benchmark replay can be fast; an unseen capture must use the live inference path. Full-precision Depth Pro is slow on this CPU, so disclose the observed latency rather than presenting cached timing as a cold run. GPU acceleration does not itself validate accuracy.

## Show the working LiDAR path

```bash
.venv/bin/python -m astra run --tier lidar --input three_room/lidar --output runs/defense_lidar_new --max-frames 140 --semantic-views 12
```

Open `report.html`, then `result.json`, `geometry/drift.json`, and the input/provenance manifests. Show the inferred hall–kitchen and hall–corridor opening pairs. Explain that widths remain provisional and do not pass the 2 cm gate merely because adjacency is plausible. The IDs are in camera-visit order; use the explicit evaluation mapping to match physical room names.

Show `runs/drift_ablation/footprint_comparison.svg`. It is the same raw scan with correction toggled, not two independent captures. The algorithm verifies ICP factors and optimizes a correction graph; it does not use poses unchanged.

## Show the two RGB paths

Use the README photo and video commands. The raw Stray RGB clip needs `--rotation 90`. Video gets the video file alone; photo processing excludes sensor folders. Neither path reads laser truth or LiDAR pose/depth sidecars. Show input manifests to substantiate that separation.

Explain metric ambiguity: image-only geometry obtains absolute scale from a learned depth prior, which can be systematically wrong. Feature/pose connectivity is separate from metric scale. A set of disconnected room estimates placed side by side is explicitly labelled schematic and fails the required physical whole-property stitch.

## Explain measurements and uncertainty

Depth is mm; poses/output are m. Resize each frame's intrinsics to the depth image before backprojection. Camera-to-world xyzw poses have world y up. Room polygons lie in x,z. Pixel masks intersect inferred wall planes, giving surface-local u,v measurements.

Current intervals are engineering ranges, not calibrated 95% coverage. A null height means unobserved, not zero. Calibration requires independent physical properties and reference measurements; duplicated stills or the same scan's RGB/LiDAR streams cannot form independent calibration/test sets.

## Explain damage honestly

The black and brown props are declared staging. Staged mode measures candidate prop regions and assigns the user-declared class. It does not demonstrate natural crack/flood recognition. Normal mode uses local open-vocabulary proposals and GrabCut, with unverified candidate status. Foreground-depth checks help reject furniture being projected onto walls, but do not establish detection accuracy.

Flags name the inspection rule and its inputs. They do not assert concealed damage. Scope quantities describe visible-region inspection, with surface IDs and intervals; they are not priced repair instructions.

## Walk through the fix loop

1. Open the declarations written before the changes.
2. Show the preserved before outputs and the actual measured failures.
3. Explain the structural-plane change and the separate photo pose/depth changes.
4. Open `fix_loop/changes.diff`, then the regenerated before/after tables.
5. State which predictions missed. Do not describe the height change as a pass.
6. Show the archived-source reproduction scripts and incremental Git bundle/history.

## Useful answers to likely questions

- **Why no IMU integration?** The observed acceleration norm suggests g units. Blind double integration would amplify bias. Poses/depth support this implementation; the unit discrepancy is exposed.
- **Why variable frame timing?** The source MP4 sample table is nonuniform. The adapter uses sample timestamps and preserves sensor frames hidden by presentation edit lists.
- **Why not use the laser numbers to fix scale?** They are evaluation truth. Fitting this test property would invalidate the reported accuracy and not solve the unseen walk-in test.
- **Why are there false openings or damage candidates?** Open-vocabulary detections and incomplete geometry are hypotheses. Their scores are not calibrated probabilities; evidence and candidate status remain visible.
- **What caused the interrupted video run?** A progress write hit a closed output pipe. Durable logging now tolerates that disconnection; the separate geometry failures remain reported.
