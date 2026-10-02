# Benchmark manifest 0.1.0

The scorer reads this file **after** prediction. Never pass it to
`process-capture`. Paths to plan JSON files are relative to the manifest.

```json
{
  "schema_version": "0.1.0",
  "property_id": "prop-home",
  "captures": [
    {"capture_id": "cap-photo", "plan_path": "runs/photo/property_plan.json"}
  ],
  "truth": {
    "measurements": [
      {"id": "ref-bed-height", "object_type": "room", "object_id": "room-bed", "quantity": "ceiling_height", "value": 2.70, "unit": "m"},
      {"id": "ref-bed-wall-1", "object_type": "surface", "object_id": "surf-bed-wall-1", "quantity": "length", "value": 3.20, "unit": "m"},
      {"id": "ref-floor-area", "object_type": "plan", "object_id": "property", "quantity": "floor_area", "value": 85.0, "unit": "m2"}
    ],
    "openings": [
      {"id": "ref-door-1", "room_id": "room-bed", "surface_id": "surf-bed-wall-1", "kind": "door", "offset_along_wall_m": 1.2, "width_m": 0.8}
    ],
    "adjacency": [["room-bed", "room-hall"]]
  }
}
```

Each reference row needs its original measurement method, date, operator,
instrument, and repeated readings in the final benchmark sheet. This draft
format scores only point truth; interval-valued truth and footprint outlines
remain to be added. IDs must represent the same physical feature across tiers.
Store the reference sheet in the separate reproduction bundle, not in the
prediction capture folder. A scorer report is never evidence that the
prediction itself had access to truth.
