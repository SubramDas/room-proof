# Photo-guided Grounding DINO kitchen passage review — 3 October 2026

The new `review-dino-openings` stage reuses the completed Grounding DINO photo,
scan-RGB, LiDAR, and ALIKED/LightGlue linker reports. It performs **no new
model inference**. Future Grounding DINO `link-captures` runs also write the
same `photo_guided_openings.json` report automatically. The review compares
matched feature points inside opening proposals, groups overlapping photo
boxes, probes timed scan depth around the matched scan boxes, and records
whether metric registration and repeated 3D edges are available.

Development run: `runs/run-f433fdf99c2d440ab28a555bed4bf807`, using
`runs/run-2807cabe99ae48c0b0dfdcb6709549d1` and the previously completed
Grounding DINO source runs. The `--photo-name IMG_0004.jpeg` option selected
the owner's identified view for inspection. The supplied 2.26 m reference
was not used by the stage.

**Visual result:** One grouped passage hypothesis combines three overlapping
photo boxes. Its representative box `candidate-2c2b801bfa78cf02` shares
103 matched feature pairs with scan frame 2279's `open_passage` box and 83
with scan frame 1830's. The two scan camera positions are only 0.1166 m
apart. The side-by-side review PNG shows that these views depict the same
opening-looking part of the kitchen. This is visual correspondence, not a
verified structural jamb pair.

**Depth result:** Both scan frames have only `timing_offset_candidate`
RGB/depth links. Their local RGB-edge/depth-edge contrast ratios are 1.980
and 1.053 respectively, below the sampled-frame gate of 2.0. Applying the
timed depth hypothesis to frame 2279 finds three similar wall/behind-wall/
wall row spans, with median raw span 0.793 m. Frame 1830 does not show both
flanks in the targeted rows. These are diagnostic pixels, not calibrated
doorway edges. The existing room fit has an unverified 0.697 m depth gap;
the new stage does not equate it with the owner's hall passage. The 0.793 m
span is a **width** hypothesis and must not be compared with the owner's
2.26 m **height** reference.

**Provisional height check:** With DINO's scan-box top provisionally treated
as the structural lintel and the fitted LiDAR floor as the doorway floor,
the representative scan boxes yield 1.788 m (frame 2279) and 1.751 m
(frame 1830); median 1.769 m. This is 0.491 m below the owner's 2.26 m
doorway height. The first DINO box stops about 0.435 m above the fitted
floor, and the RGB/depth pairs are timing-only. The detector box may follow
the curtain rather than the actual lintel. This is a diagnostic estimate,
not a measured doorway height. The calculation is in the later saved review
run `runs/run-06762596e3d146c9aae5598907c11a28`.
Treating the DINO box sides as wall edges in the same projection gives
provisional widths of 0.782 m and 0.676 m across those two views. The owner
has not supplied an independent passage width, and these side projections
are not yet calibrated measurements.

**Plan result:** No accepted photo camera pose, independently repeated
scan edge pair, measured hall-passage width or height, or kitchen–hall adjacency.
The fused plan stays unchanged. The new stage does establish a useful
reviewable visual association, while clearly rejecting a metric claim.

To reproduce from saved runs without rerunning Grounding DINO:

```bash
.venv/bin/python -m roomproof review-dino-openings \
  --linked-run runs/run-2807cabe99ae48c0b0dfdcb6709549d1 \
  --photo-name IMG_0004.jpeg --runs-dir runs
```

The report is `photo_guided_openings.json`, and its `passages[].review_png`
points to the matching photo and scan views. Omitting `--photo-name` reviews
all existing Grounding DINO photo candidates. The stage sees only the scan
frames processed by the earlier Grounding DINO run; searching new frames
would require additional scan image processing. The next geometry work is
independent RGB/depth pixel calibration for these matched views and repeated
3D edge fitting across sufficiently separated camera positions.
