# Fresh Grounding DINO kitchen run — 3 October 2026

This run processed the eight kitchen photos, the independent kitchen video,
and the extracted `kitchen.zip` LiDAR capture from scratch with Grounding DINO
Tiny. The video timeline processed all frames for motion diagnostics; DINO ran
on 12 selected video frames. DINO also ran on eight photos and 12 selected
scan RGB frames. ALIKED/LightGlue linked the three completed captures.

| Stage | Run ID |
|---|---|
| Photos | `run-660a456e06e34803acd2981015665495` |
| Video | `run-ee795828774a4535bcf980daf378cad9` |
| LiDAR | `run-c321542398504e67818cd75641af0ed1` |
| Linked plan and doorway review | `run-ee1d54ac41ad4fdbacf7083fc53ee981` |

The linked `property_plan.json` contains one inferred kitchen room. Its
provisional LiDAR dimensions are **2.4909 × 2.3777 m**, ceiling height
**2.7781 m**, and floor area **5.9226 m²**. Against the separately supplied
2.36 × 2.30 × 2.80 m reference, the unordered horizontal errors are
+0.1309 and +0.0777 m; the ceiling-height error is −0.0219 m. These
reference measurements were not model inputs.

The plan includes one unresolved opening candidate. Its `width.value` and
`height.value` are both `null`; the scan-only 0.697 m depth gap remains
unverified. The photo-guided DINO report links the passage in
`IMG_0004.jpeg` with scan frames 2279 and 1830. If the DINO box top and
sides are provisionally treated as structural edges, their projections
against the fitted scan wall/floor give heights **1.788 m** and **1.751 m**
(median **1.769 m**) and widths **0.782 m** and **0.676 m**. The height
estimate is **0.491 m below** the owner's 2.26 m doorway-height reference.
No doorway-width reference was supplied.

These doorway figures are diagnostics, not plan measurements: the box top
may be the curtain rather than the lintel, the two scan RGB/depth pairs are
timing-only, and no independent photo-to-scan metric pose was accepted.
The linked run accepted zero measured openings and zero room adjacencies.
Its review image is
`runs/run-ee1d54ac41ad4fdbacf7083fc53ee981/photo_guided_reviews/passage-hypothesis-1.png`.
