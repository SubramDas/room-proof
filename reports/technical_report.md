# Technical report — working draft

**Status:** Architecture notes only; no final six-page PDF exists.

## Architecture

One `process-capture` command accepts each tier and records source hashes,
quality warnings, run metadata, JSON, and SVG. Photo/video paths currently
extract bounded image-space evidence; LiDAR samples provisional metric points.
The output schema represents unknown dimensions explicitly. These are current
implementation facts, not a claim of a reconstructed floor plan.

## Tier and device design

The stock route uses iPhone Camera photos, an ordinary Camera walkthrough,
and Stray Scanner depth/pose export when hardware supports LiDAR. Photo/video
monocular scale is unidentifiable in the worst case. LiDAR metric scale and
RGB/depth alignment require a measured validation target.

## Known failure modes

The Flat-805 appearance-change heuristic confused camera turns with room
transitions. Sparse photo overlap leaves room placements ambiguous. Contrast
lines also arise from curtains and furniture. Current outputs leave rooms,
openings, damage, and calibrated metric intervals unresolved.

## Sections awaiting evidence

Drift correction and ablation; property-level error budget; held-out interval
calibration; all-tier benchmark; consumer-app comparison; scored fix loop;
clean-machine timing and live unseen-capture rehearsal. The final rendered
PDF must contain no more than six pages and cite the frozen evidence IDs.
