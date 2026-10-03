# Fix-loop results and post-mortem

## 1. Declared LiDAR subset fix

Kitchen height in the three-room scan: before 2.75350 m, after 2.75915 m, laser 2.80000 m. Absolute error improved **4.65 → 4.09 cm** (0.56 cm reduction). Prediction: ≤2 cm. Actual gate: ≤1.5 cm. **Prediction missed; gate still fails.** Hall error increased slightly, about 3.04 → 3.13 cm. Corridor error regressed from 1.46 → 6.72 cm. The boundary change helps extents but does not resolve ceiling bias and can select the wrong horizontal surface.

This early declaration used a LiDAR subset and was not the worst gate across the complete benchmark. The saved targeted after run has no recovered adjacency; later connectivity improvements are separate and must not be attributed to this particular artifact.

## 2. Declared photo reconstruction fix

The original declaration incorrectly identified corridor long extent 5.56 m vs 1.67 m (232.93%) as the worst. Rechecking all six extents shows the true baseline worst is corridor short extent 4.44 m vs 0.81 m, **448.15%**. The original declaration is preserved with this error disclosed. After Depth Pro plus pose/gravity changes, the worst of all six room extents is the corridor short extent 2.24 m vs 0.81 m, **176.54%**. This is a reduction of **271.60 percentage points**, but the below-100% prediction is missed and the ±8% gate still fails.

The originally highlighted corridor long extent improves to 3.20 m, **91.62% error**. Reporting only this dimension would omit the actual worst dimension both before and after. Kitchen long extent improves 7.60 → 2.772 m; hall short extent remains 7.28 m vs 3.30 m. The after output has **zero adjacency links**, three disconnected room components and a reported room overlap of approximately **7.004 m²**. There is no valid stitched whole-property result. The conditional connectivity prediction is not achieved on this capture.

Depth/focal and pose changes address some scale inflation, but sparse overlap, residual scale error and pose failures remain. No surveyed dimensions are fed back into inference. Intervals remain uncalibrated. The historical photo-after source hash gap means exact replay of these numbers is not established.

## 3. Supporting standalone kitchen improvement

Same original kitchen capture; kitchen_reproduce is excluded. Height changes 2.783779 → 2.792080 m against 2.80 m truth: error **1.62 → 0.79 cm**, crossing the 1.5 cm threshold. Floor-area error decreases approximately **24.9% → 9.3%**. This pair combines code changes and drift off → on. It is supporting evidence, not a retroactively declared worst-gate prediction and not proof that the general height gate is solved.

## Rubric assessment

Shipped changes and measured movement are supplied. The original LiDAR/photo before results were rerun successfully. Both declared predictions missed; photo stitching still fails. Full exact historical after-source regeneration is not demonstrated, especially for the original photo after run. No full-mark or fail-to-pass claim is made for the originally declared worst gate. A supplemental source-frozen replay is reported separately; it does not restore unavailable historical source bytes.

## Supplemental source-frozen photo after run

A later photo after run on the same original capture is included under `02_runs/photos_current_source_replay/`. Its exact source files are included under `05_reproduction/snapshots/photos_current_source_replay/`, and all recorded source hashes match the snapshot. The horizontal extents and heights match the earlier saved after output to displayed precision, including the 176.54% worst extent error. It still has zero adjacency links and an approximately 6.782 m² room overlap; the physical stitch fails. This supplements the historically unrecoverable photo-after source; it does not rewrite the original declaration or prove the earlier saved after source can be recovered exactly.
