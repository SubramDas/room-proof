# Kitchen and hall: pipeline vs magicplan

magicplan 2026.38.0; automatically measured dimensions per operator. Original exports preserved. Kitchen uses kitchen_lidar_final; hall uses room_1 of three_room_lidar_final (laser reference room_2). This retains the original kitchen comparison and does not substitute the repeat scan after seeing app performance.

| Room | Measurement | Unit | Laser reference | Pipeline | Magicplan | Pipeline error | Magicplan error | Beat/tie? |
|---|---|---|---:|---:|---:|---:|---:|---|
| kitchen | short_extent | m | 2.3000 | 2.3770 | 2.3700 | 0.0770 | 0.0700 | No |
| kitchen | long_extent | m | 2.3600 | 2.4954 | 2.4000 | 0.1354 | 0.0400 | No |
| kitchen | ceiling_height | m | 2.8000 | 2.7921 | 2.7900 | 0.0079 | 0.0100 | Yes |
| kitchen | floor_area | m2 | 5.4280 | 5.9318 | 5.6900 | 0.5038 | 0.2620 | No |
| kitchen | perimeter | m | 9.3200 | 9.7450 | 9.5400 | 0.4250 | 0.2200 | No |
| hall | short_extent | m | 3.3000 | 3.2534 | 3.3000 | 0.0466 | 0.0000 | No |
| hall | long_extent | m | 4.2000 | 4.2351 | 4.2400 | 0.0351 | 0.0400 | Yes |
| hall | ceiling_height | m | 2.8000 | 2.7687 | 2.8300 | 0.0313 | 0.0300 | No |
| hall | floor_area | m2 | 13.8600 | 13.7784 | 13.9900 | 0.0816 | 0.1300 | Yes |
| hall | perimeter | m | 15.0000 | 14.9770 | 15.0800 | 0.0230 | 0.0800 | Yes |

**Linear room measurements: 2/6 = 33.3% beat/tie. Including area and perimeter: 4/10 = 40.0%.** Both are below 70%. Both required room exports are now supplied; this remains a provisional extent/height comparison, not a complete matched-wall/opening score.

## Scoring and correspondence

- Absolute error is |estimate − laser reference|. Beat/tie uses pipeline error ≤ app error with 1e-9 numerical tolerance only.
- Horizontal dimensions are sorted short/long because physical wall IDs are absent in the laser notes. This is an extent proxy, not proof of physical wall correspondence.
- Height is compared directly. Area and perimeter references assume rectangular rooms and are derived from the supplied laser extents; they are reported separately to avoid padding the primary linear denominator.
- App values are rounded to 0.01 m / 0.01 m²; hidden precision and laser instrument uncertainty are unknown. In particular the height win/loss differences are smaller than app display resolution. Scores are point-estimate comparisons at exported precision, not statistical significance claims.
- In the three-room pipeline output room_1 is hall, room_2 is kitchen, room_3 is corridor. This physical mapping was recorded before app comparison.
- No app measurements or laser dimensions are used to calibrate pipeline inference.

## Hall export discrepancy

The cover and property header show 13.98 m², while the Hall room label and page-3 room summary show 13.99 m². Use **13.99 m²** for the per-room comparison and retain the discrepancy. Using 13.98 m² also gives a hall area win for our pipeline, so the aggregate count is unchanged. Do not silently replace either value.

## Remaining unscored dimensions

| Quantity | App evidence | Required correspondence/evidence |
|---|---|---|
| Kitchen opening width | 0.87 m left-wall opening | Match a specific pipeline candidate to the physical laser doorway (0.88 m). |
| Hall openings | Plan labels include 0.85 m, 0.84 m and 0.95 m openings | Identify each physical opening, its connected room and laser width; one room-level 0.88 m entry is insufficient. |
| Doorway heights | Not in either PDF | App detail export and matched pipeline opening. |
| Wall segments / window spans | Kitchen 1.53/1.64/0.69 m and hall 1.63/0.70/1.37/2.04 m labels | Separate full walls from openings/segments and supply matching reference measurements. |

All candidates remain in the submitted pipeline JSON. No closest-dimension matching is used to pick a favourable opening. The 70% full comparison target is not claimed passed.
