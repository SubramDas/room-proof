# Property-plan JSON contract (project version 0.1.0)

The machine-readable schema is [property_plan.schema.json](property_plan.schema.json). We publish this project-owned contract because the supplied brief did not include an evaluator schema. It is a design draft until the capture and scoring rules are finalized. The same contract applies to photos, ordinary video, and LiDAR.

[example_property.json](example_property.json) is a synthetic example that validates against the schema. Its dimensions, damage, and rule are illustrative only; it is not a benchmark result. To validate it locally with Python's `jsonschema` package:

```bash
python3 -m jsonschema -i schema/example_property.json schema/property_plan.schema.json
```

## What the fields mean

- `capture` identifies the source tier, device, app, and files. `run_id` identifies one pipeline execution.
- `coordinate_system` fixes the drawing convention: metres in a capture-local 2D plan, x right and y up. Plan coordinates describe placement; they are not separate measurements with their own intervals.
- `plan` names the rendered plan and holds the whole-property footprint and floor area.
- `rooms` holds each room or connector. Each has a boundary, floor area, ceiling height, wall/floor/ceiling surfaces, and openings. A wall has a 2D line and measured length. Openings are tied to wall surface IDs and have width, height, and distance along the wall from its first endpoint.
- `adjacency` lists room-to-room connections separately from room geometry. Its `confidence` is a probability for a discrete connection, not a measurement interval.
- `damage_regions` are tied to surfaces. Their 2D region uses surface-local metres: for walls, horizontal distance from the wall line's first endpoint and vertical height above the floor. Floor and ceiling region coordinates use a local surface frame fixed by the pipeline and documented in each run manifest. Width, height, and area are measurements; `length` is optional for cracks or other line-like damage.
- `concealed_damage_flags` identify the specific rule and evidence for a suspected hidden problem. `scope_items` identify proposed work and quantities by room and surface. Empty arrays are allowed when no credible finding exists.
- `warnings` records capture, geometry, or inference limitations.

Every physical quantity uses a `measurement` object with `value`, `unit`, `interval`, `status`, and `source_refs`. `interval` has lower/upper bounds, a named numerical coverage fraction, and a method. Null bounds mean unbounded sides; a null value means no defensible point estimate. A numeric point estimate with unbounded bounds is allowed so the system can show its best guess without pretending scale is known. **Our proposed target is 0.90 coverage** unless the evaluator specifies another level; the schema allows any fraction strictly between zero and one until scoring rules clarify it. Report point estimates and intervals even if they fail a gate.

The schema checks structure and types. Cross-references, unique IDs, valid polygons, non-overlapping rooms, `lower <= value <= upper`, consistent areas, and calibration require separate semantic checks in the pipeline/evaluator. A JSON file passing this schema alone does **not** establish accuracy or full compliance.

The damage-class vocabulary, concealed-damage rules, scope-item vocabulary, multi-floor convention, and exact interval target remain open decisions. `class`, `rule_id`, and `work_type` are strings for now; version these vocabularies before real benchmark runs. If an official evaluator schema arrives, map this contract to it and publish the conversion.
