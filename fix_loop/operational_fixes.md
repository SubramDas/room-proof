# Operational and diagnostic follow-ups

## Video progress pipe

The dense video job computed all 180 depth frames and began semantics, then recorded `BrokenPipeError: [Errno 32] Broken pipe`. The execution tool reported exit 143. A closed output pipe caused a progress write to abort the computation; this was separate from disconnected RGB geometry.

Shipped fix: `astra/runtime.py` tees progress to a durable file and tolerates a disconnected output stream. Explicit SIGTERM/SIGINT is still respected and recorded as interrupted. A regression test exercises a closed writer followed by continued progress. The dense run completed after the fix. This operational fix is additional evidence, not a substitute for the declared accuracy fix loop.

## Environment recovery

A user package installation changed project PyTorch from 2.8 CPU to 2.14 CUDA while Torchvision remained 0.23 CPU. The detector import failed. The tested CPU package was restored from an already available local installation; changed packages were retained in `.cache/environment_recovery` and excluded from submission. `scripts/check_environment.py` validates the pinned versions and model imports. Existing valid depth caches were retained.

## LiDAR height diagnostics

`reports/height_diagnostics.json` records confidence=2 and gravity-preserving alternatives. These configurations merged the kitchen/hall in the current free-space extraction and did not solve the height error. They are not promoted as defaults or gate passes. This exposed segmentation sensitivity rather than a successful height calibration.

## Video diagnostic branches

Denser sampling uses 180 views; it still has disconnected components. Weak depth-geometry links accepted only one extra temporal factor in the initial test, reducing component count from 28 to 27 without solving room layout. This is not a meaningful gate success. Hybrid depth anchors and relative scale consistency are separate experiments; only completed, measured results count as evidence.
