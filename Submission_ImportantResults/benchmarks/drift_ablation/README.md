# Drift accountability

The pipeline adds accepted local and loop ICP constraints to a pose correction graph; it does not use all recorded poses unchanged. `ablation.json` records accepted constraints and corrections. `footprint_comparison.png` / `.svg` overlay the same scan with correction off and on. `off/` and `on/` contain layouts, point clouds, correction diagnostics and input QA.

Observed summed room area: off 20.808618 m², on 20.802035 m² (change −0.006583 m²). Maximum translation correction was approximately 8.89 cm. Summed room area is not necessarily the property union footprint. This ablation shows the algorithm changes the reconstruction; it does not prove improved ground-truth accuracy and is not a repeatability test.

Rerun instructions are in `../05_reproduction/COMMANDS.md`.
