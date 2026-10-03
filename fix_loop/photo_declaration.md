# Fix declaration after the first complete photo run

Recorded before implementing depth-assisted PnP or testing Depth Pro. Initial LiDAR-only declaration is retained in `declaration.md`; it was not based on a complete all-tier benchmark.

Worst observed complete-tier gate: photo whole-property reconstruction. On the first run (`runs/three_room_photos/result.json`), the kitchen's longer extent is 7.60 m against 2.36 m laser reference: **222.0% error** against the 8% gate. The corridor's longer extent is 5.56 m against 1.67 m: **232.9% error**. There are six disconnected view components and no recovered adjacency. Therefore the required stitched plan fails regardless of extent error.

Hypothesis: incorrect focal/metric-depth scale, weak essential-matrix translation in low-parallax views, and the assumption that the first camera is level. Evidence: inflated extents and ceiling heights across all three rooms, multiple disconnected components, learned depth scale with guessed intrinsics, and no absolute gravity input in this tier. Laser dimensions have not been used to fit the reconstruction.

Fix: test a model that jointly estimates focal length and metric depth (Apple Depth Pro), use depth-assisted PnP for rotation/translation where feature matches support it, and estimate gravity orientation from dominant surface normals. Keep disconnected components explicit; never synthesize the declared hall connections as observed geometry.

Prediction: worst extent relative error falls below **100%** on the supplied three-room photo set; at least one of the two expected room connections becomes observable if overlapping doorway views exist. This remains well short of the 8% gate and will be reported as such. The connectivity prediction can fail if the capture has no shared visual coverage.

Reproduction: the before revision is `e3977de` with the original small depth model (recorded output preserved). After commands and measured delta will be added after the actual run; a missing download will not count as a shipped successful model comparison.
