# Experimental visual candidate contract

`process-capture --visual-model on` writes `visual_candidates.json` after the
photo/video reader and before `build_plan`. Version `0.1.0` records proposals,
not verified geometry. The model is off by default. A failed or missing model
writes `status: unavailable`; LiDAR writes
`status: skipped_rgb_pairing_unresolved` until RGB/depth/pose correspondence is
established. Both contain empty `candidates` and a reason, and leave the plan
schema valid and unresolved wherever geometry is unsupported.

Each proposal has `candidate_id`, `class`, `status`, `status_reason`, `frame_id`,
`source_ref`, `source_sha256`, optional `room_id` and `timestamp_seconds`, a
pixel `geometry` box, a `mask_ref` and `mask_label_id`, `raw_model_score`, and
supporting/conflicting evidence arrays. The report records `capture_id`,
`tier`, exact model ID and weight hash, selection rule and selected frame IDs,
per-frame duration, warnings, and the candidate list. Candidate IDs are
deterministic for a given frame ID and predicted component. Consumers must
check `report_version` and frame references before use.

Boxes use `[left, top, right, bottom]` with the right and bottom edges
exclusive. For photos, `coordinate_space: source_photo` means the decoded
original photo dimensions. For video, `coordinate_space: sampled_rgb_frame`
means the frame decoded by the existing reader at 640 pixels wide. The box
also carries that sampled size and the original video frame size. Multiply x
and y by `source_image_width / image_width` and
`source_image_height / image_height` to map to the original frame. The
`source_ref` identifies the original video frame; `sampled_sha256` identifies
the RGB sample. A semantic mask PNG has model output resolution and contains
ADE label IDs, so the candidate box, label ID, and mask must be used together.
The mask does not isolate one connected component when several share a label.

`raw_model_score` is the mean winning-class softmax over component pixels.
It is neither a calibrated probability that an opening is real nor a
measurement interval. No door/window candidate is added to
`property_plan.json` until its wall, repeated view, and geometry are checked.
Photo folder IDs identify source groups only. A model failure does not imply
that the capture is invalid or that an opening is absent.

## Current pilot limits

The selected checkpoint is a small ADE20K semantic segmenter. It proposes
wall, floor, ceiling, door, and window regions; ADE classes do not distinguish
an entry door from a cabinet door or a passage, and the present pilot has
visible false positives and misses. The original SegFormer license permits
research and evaluation use; obtain a commercial license or replace the
checkpoint before any commercial deployment. Weight download and execution
remain local after provisioning. This checkpoint is experimental and has not
been adopted as an accuracy improving production model.

See [model candidate pilot](../reports/model_candidate_pilot.md) for recorded
run IDs, timing, and review findings. Human labels and an untouched capture
are required before deciding whether to adopt it.
