# Hall-only model pipeline output — 2 October 2026

All three commands used the current `model_pipeline` branch at commit
`860a439` with `--visual-model on` and wrote to ignored local `runs/`.
The hall photos are the seven JPEGs from `Flat-805/room-hall`, copied without
edits into `/tmp/roomproof-hall-model-input/room-hall` because the same source
folder also contains a video and ZIP. The standalone input was
`Flat-805/room-hall/hall.mp4`. The scan was the already audited extraction of
`Flat-805/room-hall/hall.zip` at `/tmp/roomproof-hall-lidar/b41a75401a`;
the ZIP SHA-256 is
`a5909cacdccb25d0593f80cc4eac7e67c311670359f3ade24505ab7bdf8b24cb`.
The original inputs were not modified.

| Tier | Run ID | Input quality / output validity | Model result | Plan result | Total time |
| --- | --- | --- | --- | --- | ---: |
| Photo | `run-59be7bfcd5914cf08995480341a1450a` | valid_low_confidence; schema and semantic valid | 29 proposals from 7 photos; 3 door proposals | one hall, geometry and openings unresolved | 11.69 s |
| Video | `run-d0f644563dcc4b6ab5f9b19c058fecc2` | valid_low_confidence; schema and semantic valid | 67 proposals from 24 sampled frames; 3 door proposals | one hall, geometry and openings unresolved | 29.40 s |
| LiDAR | `run-ef17462877d5424c995f8db6f0f1ae19` | valid_low_confidence; schema and semantic valid | RGB model skipped: 3,164 RGB versus 3,165 depth/pose frames, exact pairing unresolved | provisional four-wall hall and one unverified depth-gap doorway | 165.31 s |

The photo and video candidate reports retain source IDs, model weights hash,
pixel boxes, mask references, raw scores, and stage timing. Neither report
verifies which door is physical or joins an opening to a LiDAR wall. Their
plans contain no metric walls, areas, heights, or openings. The local model
stage took 7.75 s for photos and 16.90 s for video; these are part of the
total times above.

The LiDAR plan estimated wall sides of **3.926 m and 3.3958 m**, floor area
**13.3319 m²**, and ceiling height **2.7682 m**. Its single possible door is
on `surf-hall-wall-1`, with provisional width **0.705 m** and unknown height.
The opening remains `unresolved`. All numeric intervals have unknown bounds;
the pipeline has no held-out calibration. The owner-provided reference sides
of 3.90 m and 3.21 m and height 2.84 m were held out from inference. Post-run
errors are +0.026 m, +0.1858 m, and −0.0718 m respectively. This output does
not meet the project's opening or ceiling measurement accuracy gates.

The owner confirmed bedroom–hall, toilet–hall, and kitchen–hall doorway
relationships, including that bedroom and toilet doorways face each other.
Those labels are recorded in [model label review](../docs/model_label_review.md)
and were **not** passed into these three commands. A hall-only capture cannot
establish those full room connections from its current automated outputs.

## Exact commands

```bash
.venv/bin/python -m roomproof process-capture /tmp/roomproof-hall-model-input --tier photo --property-id prop-flat-805 --capture-id cap-flat-805-hall-photo-model --visual-model on --max-model-frames 7 --runs-dir runs
.venv/bin/python -m roomproof process-capture Flat-805/room-hall/hall.mp4 --tier video --property-id prop-flat-805 --capture-id cap-flat-805-hall-video-model --room-id room-hall --room-kind connector --visual-model on --max-model-frames 24 --runs-dir runs
.venv/bin/python -m roomproof process-capture /tmp/roomproof-hall-lidar/b41a75401a --tier lidar --property-id prop-flat-805 --capture-id cap-flat-805-hall-lidar-model --room-id room-hall --room-kind connector --max-lidar-frames 128 --visual-model on --runs-dir runs
```

An initial LiDAR call passed `hall.zip` directly and was rejected because the
CLI accepts an extracted Stray folder; its failure manifest is
`run-d079fc298d774cc08f5591b8b2f5d02e`. The corrected run above used the
verified existing extraction. The original ZIP remains unchanged.
