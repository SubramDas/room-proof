# Visible damage vocabulary, draft 0.1.0

The detector may emit only source-linked visible regions. This vocabulary does
not diagnose hidden material or cause. Benchmark classes remain to be selected
with the owner before scoring; this draft does not mark T38 complete.

| Class | Visible marking rule | Exclude |
| --- | --- | --- |
| `discoloration_or_water_stain` | Polygon around bounded discoloration or tide mark | An inferred leak without visible change |
| `crack` | Polyline length and bounding polygon around a visible split | Decorative seams and unverified shadows |
| `coating_failure` | Polygon around peeling, flaking, blistering, or lifting finish | Intact patterned paint |
| `surface_breakage` | Polygon around chipped, missing, or broken surface material | Loose objects in front of a surface |
| `floor_finish_damage` | Polygon around visibly damaged floor finish | Furniture shadows and reflections |

For each marked region record property, room, surface, class, raw-file ID,
image-frame reference, polygon in image pixels, and independently measured
surface-local polygon/width/height/area in the reference sheet. Record crack
length where applicable. Keep image labels and tape/laser measurements separate
from the inference input. Mark obscured regions as unassessable, not clean.

Use `roomproof.damage_rules` only after a region has been identified and tied
to a known surface. Its positional tags must come from observed geometry, not
from a guessed damage cause. Fired flags say *possible* hidden conditions and
work items are conditional inspections. No price or hidden repair area is inferred.
