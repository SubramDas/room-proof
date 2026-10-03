# Shipped changes and attribution

- Room boundaries: use supported structural wall planes instead of relying only on free-space watershed partitions; estimate floor/ceiling from local room support.
- RGB poses: depth-assisted PnP when supported by matched features; gravity alignment from dominant surface normals; explicit disconnected components.
- RGB depth/focal prior: Apple Depth Pro replaces the small Depth Anything model in the completed photo after run.
- Standalone kitchen pair: drift changes from off to on as well as code changes. Its height improvement cannot be attributed to the structural-plane change alone.

The diff is e3977de → 209371d. It includes later changes beyond the first targeted fix and is labelled accordingly. Per-run source recovery and missing historical file versions are recorded in `../05_reproduction/source_audit.json`. A code revision ID by itself does not guarantee a clean working tree at run time.
