# Hall mixed RGB and LiDAR pilot — 3 October 2026

Input: the unchanged Stray Scanner export from `Flat-805/room-hall/hall.zip`,
extracted at `/tmp/roomproof-hall-lidar/b41a75401a`. Its original ZIP SHA-256
is `a5909cacdccb25d0593f80cc4eac7e67c311670359f3ade24505ab7bdf8b24cb`.
The command used 128 selected depth frames and the exported poses. Reference
laser dimensions were not passed to inference. The hall RGB is sideways in
storage; its 90° clockwise display rotation was verified by visual inspection.
OWLv2 boxes were mapped back to stored RGB pixels before wall and depth checks.

| Run | RGB candidates | Opening evidence | Dimensions (m) | Total time |
| --- | --- | --- | --- | ---: |
| Model off: `run-41cb90bb93e94a829ee817498840bf5e` | none | one unresolved depth gap | 3.926 × 3.3958 × 2.7682 | 100.3 s |
| SegFormer pilot: `run-a2b2c4829c414b57b53ea4b700a1fb93` | 2 door boxes from 24 frames; both at fitted wall depth | gap unresolved | same | 155.4 s |
| OWLv2 upright view: `run-0f36bbf4e6c14b2ca908ad987d1d608e` | 147 boxes from 12 frames | one provisional open-passage inference from repeated RGB/depth support | same | 367.5 s |

In the OWLv2 run, 12 sampled RGB frames passed the sampled registration gate
with a +1 depth-frame offset. The linker considered 118 opening-like boxes:
109 projected to a fitted wall, 34 overlapped the one depth gap, 26 were
rejected as structural openings because at least 10/12 depth samples landed
on the fitted wall, and 7 boxes from multiple frames passed the current
height, box-size, behind-wall depth, and independent-view gates. Most other
boxes remain unresolved. The candidate report also includes 29 cabinet-door
proposals, which are not eligible to confirm a structural opening. The owner
had previously identified an open kitchen doorway connected to the hall;
that label was **not** passed to the model or geometry pipeline.

The plan's inferred opening is `opening-hall-candidate-1` on
`surf-hall-wall-1`, with a provisional **0.705 m** width and **2.919 m** wall
offset from the LiDAR depth-gap fit. Opening height is unknown. The opening
status is an evidence-supported hypothesis, not a independently checked
dimension. The fitted room area is **13.3319 m²**. Wall lengths and ceiling
height have unbounded intervals because calibration against a held-out
property set has not been completed.

Against the separate hall laser values of 3.90 m, 3.21 m, and 2.84 m, the
side and height errors remain **+0.026 m**, **+0.1858 m**, and **−0.0718 m**.
OWLv2 changed opening evidence; it did not improve metric wall or ceiling
measurements. No verified pose closure was found, so drift correction applied
no change. CPU inference across the 12 model frames took 242.1 s; the full
visual stage including RGB/depth pairing took 289.4 s. Peak process RSS was
about 2,304 MiB. This is too costly to assume the present 12-frame OWLv2 path
meets the live-run budget without further sampling or optimization.
The final qualified-view separation check was also replayed on this run's
recorded candidates and retained the same 7 supported proposals; its two
supporting groups have qualified camera separations of 0.231 m and 2.172 m.

An earlier unrotated OWLv2 run (`run-1db72a014c25467aa1843c405f787af1`)
incorrectly promoted the gap from broad, sideways boxes. Replaying its
candidate report through the new height and box-size gates yielded zero
supported proposals. It is retained as a diagnostic failure, not scored as
the current pipeline result. The upright run still produces many low-score,
overlapping proposals; owner-reviewed frame labels and a separate capture are
needed before selecting thresholds or claiming doorway precision/recall.

## Replay command

```bash
.venv/bin/python -m roomproof process-capture /tmp/roomproof-hall-lidar/b41a75401a --tier lidar --property-id prop-flat-805 --capture-id cap-flat-805-hall-owlv2-rotated --room-id room-hall --room-kind connector --max-lidar-frames 128 --visual-model on --visual-backend owlv2 --visual-model-path .room-proof/models/owlv2-base-patch16-ensemble --lidar-rgb-rotation 90 --max-model-frames 12 --runs-dir runs
```

The model is the pinned local
[OWLv2 Base checkpoint](https://huggingface.co/google/owlv2-base-patch16-ensemble)
with weights SHA-256
`e1e130b9e404cf91a75ad45644c1da9d7fa5284085eecc864266a6923efb99e7`.
The run artifacts are in ignored `runs/`, including `property_plan.json`,
`property_plan.svg`, `visual_candidates.json`, `rgb_pairing.json`, and
`lidar_candidate_links.json`.
