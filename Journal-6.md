# Journal 6 — Uncertainty and evaluator

Status: partial. Added `roomproof.benchmark` with a separate reference-only
scorer for schema validity, measurement omissions/error, finite interval
coverage/width, openings with one-to-one wall/type/position matching, ceiling
accuracy, photo/video wall error, footprint area, and adjacency. It counts
phantom openings in the denominator. The benchmark manifest format is drafted
in `docs/benchmark_manifest.md`. Truth is not imported by the prediction path.

Still open: property-held-out calibration, repeatability, footprint shape
alignment, drift ablation, damage region metrics, final scoring definitions,
and a complete benchmark. No gate has been marked passing from absent truth.
