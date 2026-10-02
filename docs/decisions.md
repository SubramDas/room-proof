# Working decisions (2 October 2026)

This log freezes choices for the first implementation. It does not claim evaluator approval or measured accuracy. [SPEC.md](../SPEC.md) is the requirement source; [TASK.md](../TASK.md) records completion.

| Topic | Working decision | Limit / revision trigger |
| --- | --- | --- |
| Capture route | Route 2: Camera stills, Camera video, and Stray Scanner for LiDAR on a supported iPhone. | Freeze app/version/export instructions only after a real owner export and non-engineer rehearsal. Test Scan4D if the free Stray workflow fails. |
| Three-tier contract | One schema (`schema/property_plan.schema.json` v0.1.0), one property-level plan, and one run log per valid capture; never use another tier's sidecars to improve a mandatory photo/video run. | An official evaluator schema would require a versioned mapping. The current CLI only implements import/verification, not processing. |
| Coordinates and units | Metres, capture-local 2D coordinates, x right and y up on the plan. Physical lengths are in m; areas are in m2. Stable IDs follow [IDs and manifests](ids_and_manifests.md). | Floor linkage remains unresolved until the benchmark's floor layout is known. |
| Intervals | Proposed 90% prediction-interval target for each physical quantity. Keep bounds unbounded or value unknown when evidence cannot identify scale. | This is our target, not an evaluator-issued threshold. Calibrate on held-out **properties**, not walls/frames from one home. |
| Openings | Match once by type, physical wall, and center within 0.30 m after rigid alignment. Success needs width error ≤0.02 m; denominator is real plus unmatched predicted openings. | The matching radius and denominator are project rules pending evaluator clarification. |
| Wall repeatability | Report both 1 cm and 0.5% interpretations; use the smaller tolerance as the conservative internal pass per matched wall. | Preserve scores under any later evaluator rule. |
| Photo footprint | Score total area error ≤8%; also report no-rescale aligned outline error and require ≤8% for our internal shape pass. Require correct adjacency and no room-interior overlap. | The official meaning of footprint error is unresolved. |
| Comparison | Preselect two rooms and eligible linear dimensions before seeing errors. Report literal shared-only wins/ties and an expanded omission-aware score separately. | magicplan export availability and any official omission rule are unverified. |
| Fix selection | Freeze all-tier baseline and scorer first. Prioritize a blocking execution/schema failure, otherwise rank failed gates using the predeclared relative-gap rule in SPEC Part 4. Commit the one-page prediction before the fix. | No baseline or fix claim exists yet. |
| Execution stack | Python 3.12 standard library for the CLI, manifests, JSON, CSV, hashing, and future SVG rendering; local CPU processing on Ubuntu 24.04. Add pinned vision packages only when a measured implementation needs them. | Video decoding and geometry are not implemented; they will require explicitly pinned tools before those tasks can pass. No current dependency download is required. |
| Raw data delivery | Content-addressed local bundle with SHA-256 objects and per-capture manifests, outside ordinary Git. Copy the complete bundle to the submission volume and verify in a clean directory. | The exact delivery destination and size cap are still unknown. Ignore rules alone are not delivery. |
| Privacy and provenance | Originals are copied and hashed, never edited. Derived outputs, run logs, truth, and comparator exports live separately. Ground truth is available to scoring only after predictions are frozen. | Owner permits submission/cloud testing, but public release of interiors is not assumed. |

## Information limits and inconsistencies

- Arbitrary unposed photos and monocular video cannot guarantee absolute scale. Separate room folders without shared visual evidence also cannot guarantee a unique adjacency graph. The strict benchmark gates may therefore fail even when the output honestly marks uncertainty.
- The project-owned schema is a draft because no official evaluator schema was supplied. Its synthetic example is not benchmark evidence.
- Only three starter LiDAR-style scans are present. They have no independent tape truth, matched ordinary video/photo captures, or comparator export.
- `TASK.md` previously described the discovery changes as uncommitted; Git commit `59b1a58` already contains them. The tracker is updated in this milestone.
- Installed stock app versions, exact export behavior, evaluator device, submission format, and interpretation of the 15-minute clock remain unverified. These do not block foundation work.
