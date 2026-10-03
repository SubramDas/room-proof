# Part 4 declaration index — retrospective

This is a navigation summary written after the runs, not a replacement or backdated fix declaration.

**Original documents:** declaration.md (early LiDAR subset); photo_declaration.md (first complete photo result). Both are preserved unchanged.

**Declared complete-tier failure:** photo whole-property reconstruction. The declaration highlighted corridor long extent error of 232.93% and no adjacency. Retrospective checking finds the true worst extent was the corridor short side: 4.44 m vs 0.81 m, 448.15% error. This declaration error is retained and disclosed.

**Original hypothesis:** focal/depth scale error, weak translation recovery in low-parallax images and incorrect gravity alignment. Evidence was inflated room dimensions and disconnected components.

**Original proposed fix:** depth-assisted PnP, surface-normal gravity alignment, and Apple Depth Pro for depth plus focal estimation. Prediction: worst extent error below 100%; at least one recovered connection if doorway overlap supports it.

**Measured outcome:** worst extent error becomes 176.54%; zero adjacency; prediction and required stitch gate fail. The highlighted long extent improves to 91.62% error; the short extent remains worst, improving 448.15% → 176.54%. See the post-mortem for all errors and source-recovery limitations.

**Separate supporting result:** standalone kitchen height error improves 1.62 → 0.79 cm, but this was not the declared worst-gate prediction and drift settings changed.
