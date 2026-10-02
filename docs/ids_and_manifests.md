# IDs, raw capture manifests, and run records

IDs are opaque references, not measurements. Use lowercase ASCII letters, digits, and hyphens; never derive a room's adjacency or dimensions from its name. Once an ID is used in a benchmark, keep it stable across tiers, repeated captures, reference rows, outputs, and scorer tables.

| Entity | Form | Assignment |
| --- | --- | --- |
| Property | `prop-<slug>` | Assign before any capture, e.g. `prop-home-a`. |
| Floor | `floor-<slug>` | Assign when known; use `null` in output when unknown. |
| Room/connector | `room-<slug>` | Label physical spaces on the owner's room map once; reuse across tiers. |
| Surface | `surf-<room-slug>-<wall|floor|ceiling>-<number>` | Number walls clockwise from a documented entrance/reference corner. Keep the same physical surface ID in truth and predictions after matching. |
| Opening | `open-<room-slug>-<number>` | Assign physical opening IDs in truth; prediction IDs may be new until the scorer matches them. |
| Damage | `damage-<room-slug>-<number>` | Assign independently marked physical regions before scoring. |
| Capture | `cap-<uuid4-hex>` | Created at raw import; a second take gets a new ID, even on the same room. |
| Run | `run-<uuid4-hex>` | Created for every command execution, including failures. |

The existing synthetic schema example predates these naming rules; it remains an illustrative contract fixture, not a capture manifest. Its IDs should not be copied into real benchmark data.

## Capture manifest v0.1.0

`roomproof import-capture` writes `captures/<capture_id>.json` in a bundle. It contains `property_id`, `capture_id`, `tier`, source label/path at import, import time, device/iOS/app metadata when supplied, notes, and every relative source path with byte size and SHA-256. The exact bytes are stored at `objects/sha256/<first-two-hex>/<full-sha256>`. A capture can refer to a file by relative path and SHA-256; the property-plan output's `capture.source_refs` should use these source paths or stable file references from the manifest. Future benchmark reference rows use physical IDs above and `capture_id` only for provenance; tape values are never copied into inference input.

The import preserves file bytes and checks the copied object against its hash. Objects are read-only in the bundle. Never edit raw source or object files in place. To correct metadata, create a new versioned metadata record rather than rewriting a scored manifest. Generated frames, point clouds, plans, and scores belong under a separate run directory.

## Run manifest v0.1.0

Each command writes `runs/<run_id>/run.json` with argv/config, UTC start/end, Git commit and dirty state, Python/platform version, capture-manifest SHA-256 as data revision, model/API identity or null, seed or null, stage seconds, status/error, warnings, metrics, and output artifact paths/hashes. A failed import or verification still has a run manifest. The CLI version flag is informational and is not a processing run. Runs made while code is dirty are development evidence only; freeze a committed revision before a scored baseline.

For later prediction runs, record every model/version/weight hash, random seed, accepted/rejected input, stage timing, schema-validation result, and JSON/SVG hash in this same structure. Do not present a complete import/verification run as a successful property-plan inference run.
