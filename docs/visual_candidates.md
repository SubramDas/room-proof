# Experimental visual candidate contract

`process-capture --visual-model on` writes `visual_candidates.json` after the
reader and before `build_plan`. Version `0.1.0` records proposals, not
verified geometry. The model is off by default. A failed or missing model
writes `status: unavailable`, empty `candidates`, and a reason; it leaves the
plan schema valid and unresolved where geometry is unsupported. LiDAR also
writes `rgb_pairing.json`, `rgb_frames.json`, and
`lidar_candidate_links.json` with timing and wall-link hypotheses.

Each proposal has `candidate_id`, `class`, `status`, `status_reason`, `frame_id`,
`source_ref`, `source_sha256`, optional `room_id` and `timestamp_seconds`, a
pixel `geometry` box, optional `mask_ref` and `mask_label_id`, `raw_model_score`, and
supporting/conflicting evidence arrays. The report records `capture_id`,
`tier`, exact model ID and weight hash, selection rule and selected frame IDs,
per-frame duration, warnings, and the candidate list. Candidate IDs are
deterministic for a given frame ID and predicted component. Consumers must
check `report_version` and frame references before use.

Boxes use `[left, top, right, bottom]` with the right and bottom edges
exclusive. For photos, `coordinate_space: source_photo` means the decoded
original photo dimensions. For video and LiDAR RGB, `coordinate_space: sampled_rgb_frame`
means the frame decoded by the existing reader at 640 pixels wide. The box
also carries that sampled size and the original video frame size. Multiply x
and y by `source_image_width / image_width` and
`source_image_height / image_height` to map to the original frame. The
`source_ref` identifies the original video frame; `sampled_sha256` identifies
the RGB sample. A semantic mask PNG has model output resolution and contains
ADE label IDs, so the candidate box, label ID, and mask must be used together.
The mask does not isolate one connected component when several share a label.

For SegFormer, `raw_model_score` is the mean winning-class softmax over
component pixels. For OWLv2, it is the detector's box score for the recorded
text prompt.
It is neither a calibrated probability that an opening is real nor a
measurement interval. No door/window candidate is added to
`property_plan.json` until its wall, repeated view, and geometry are checked.
Photo folder IDs identify source groups only. A model failure does not imply
that the capture is invalid or that an opening is absent.

For Stray LiDAR, `rgb_pairing.json` preserves decoded MP4 presentation times
and nearest relative odometry times, including residuals and unmatched
frames. It tests nearby integer depth-frame offsets with RGB image gradients
at measured depth discontinuities and shifted-pixel controls. A consistent
offset across early, middle, and late sampled frames can support a scan-wide
mapping; each sampled frame must also pass its own edge check to be marked
`registered_candidate`. Unsampled frames retain timing-only status. The hall
scan supported offset +1, leaving depth frame `000000` and two anomalous
frames unpaired. This checks image/depth registration; it does not establish
independent metric scale or prove every opening. `lidar_candidate_links.json`
casts image rays through recorded intrinsics and poses and compares their
nearest fitted-wall hits with depth-gap intervals. For each registered
candidate, it samples the paired depth and confidence at 12 interior pixels
and records at-wall, behind-wall, foreground, and missing returns separately.
The gap-support frames need not be the same frames selected for RGB inference;
the paired RGB frame supplies its own depth check. Missing returns alone never
support an opening. A box with at-wall depth at 10 or more of 12 samples and
no overlapping gap is rejected as a structural opening; it may still depict a
visible closed door. A repeated-view candidate must also span at least 1.5 m
of projected fitted-wall height and cover under half the frame; these are
conservative pilot gates, not calibrated accuracy guarantees. It records repeated-view
groups separately. A ray hit does not verify an opening, and unsupported
candidates cannot alter its status or dimensions. A depth-gap opening gains
RGB source references and `inferred` status only if registered candidates
from two independent camera positions agree on the same gap with measured
behind-wall depth. Its width and
offset still come from LiDAR and retain unbounded intervals.

## Model backends and pilot limits

The default `--visual-backend segformer` checkpoint is a small ADE20K semantic segmenter. It proposes
wall, floor, ceiling, door, and window regions; ADE classes do not distinguish
an entry door from a cabinet door or a passage, and the present pilot has
visible false positives and misses. The original SegFormer license permits
research and evaluation use; obtain a commercial license or replace the
checkpoint before any commercial deployment. Weight download and execution
remain local after provisioning. This checkpoint is experimental and has not
been adopted as an accuracy improving production model.

`--visual-backend owlv2 --visual-model-path PATH` selects a local OWLv2
checkpoint directory. It proposes doorway, door, open passage, window, and
cabinet-door boxes from fixed text prompts. OWLv2 produces no mask. Its box
and score remain proposals; paired depth and repeated wall-gap views decide
whether they can support an existing LiDAR opening. The checkpoint revision,
weights digest, package versions, and installation are recorded in
[dependencies](dependencies.md). This CPU backend is optional and off unless
`--visual-model on` is also supplied.

For a scan whose stored RGB is sideways, `--lidar-rgb-rotation 90` presents
frames clockwise to OWLv2 and maps every result back to raw sampled RGB
pixels before depth projection. Rotation is an explicit capture setting; it
does not rotate the depth, intrinsics, or world geometry. The hall RGB was
visually inspected and needs this 90° display rotation for the model view.

See [model candidate pilot](../reports/model_candidate_pilot.md) for recorded
run IDs, timing, and review findings. Human labels and an untouched capture
are required before deciding whether to adopt it.
