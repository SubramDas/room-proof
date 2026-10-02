# Journal 0 — Repository, decisions, and reproducibility foundation

**Status:** In progress as of 2 October 2026. Seven of nine Phase 0 tasks are checked in [TASK.md](TASK.md). T02 and T08 remain open under their stated completion conditions. This journal records work done so far; it will be updated when Phase 0 is complete.

## Work completed

| Task | Result | Evidence |
| --- | --- | --- |
| T00 | Recorded Route 2, the three-tier output contract, proposed 90% intervals, working scorer choices, and information limits. | [docs/decisions.md](docs/decisions.md) |
| T01 | Preserved the discovery milestone without raw scans in Git. | Commit `59b1a58` |
| T03 | Mapped requirements, deliverables, planned paths, evidence, and honest status. | [COMPLIANCE.md](COMPLIANCE.md) |
| T04 | Created a Python 3.12.3 standard-library CLI and Ubuntu setup script. A clean temporary setup printed `RoomProof 0.1.0` in 3.07 seconds, used a 16 MB virtual environment, and downloaded 0 bytes. This timing covers only the foundation CLI. | [scripts/setup.sh](scripts/setup.sh), [README.md](README.md) |
| T05 | Imported all three supplied starter scans into a SHA-256 content-addressed local bundle with read-only file objects. Each of 33,434 source files has a path, size, and hash in a capture manifest; originals were not edited. Device and app metadata remain unknown. | [repro/README.md](repro/README.md), [repro/manifest.json](repro/manifest.json); bundle import runs `run-b6bee09fe1dc48c7aa9d57b7e5896ff7`, `run-499d29d33fc3431b98ad450e335d96f4`, `run-71cb9e252f4a496d9c6e04addab5daf3` |
| T06 | Copied the bundle to a second directory and verified all three capture manifests and all 33,434 file objects. The bundle itself is ignored by Git and needs a separate submission location. | Clean committed-code run `run-ea1cf72ec4da4ae9885726059699bf1b`; [repro/README.md](repro/README.md) |
| T07 | Added run records for import, indexing, and verification with command/config, code/data revision, dirty state, stage time, status, warnings, metrics, and artifact hashes. A deliberately empty bundle produced a failed run record. | [roomproof/cli.py](roomproof/cli.py); failed run `run-71f0314fa6d64a27b9778de4d327b75c` |

## Work still open

- **T02:** [ID and manifest rules](docs/ids_and_manifests.md) and capture/run IDs exist. Property-plan output and evaluation do not yet exist, so the physical room/surface/opening/damage IDs have not been reused by both. Check this task when those paths actually use the same IDs.
- **T08:** Meaningful commits exist for discovery and foundation (`59b1a58`, `dd30e38`, `0dfb5e7`, `e841cdc`). The required failed baseline, fix declaration, implementation, and before/after history belong to later phases and cannot be marked complete yet.

## Process rule from the owner

From this point forward, use `.venv/bin/python` for every Python or RoomProof CLI command in this repository. The system interpreter may be used only to create the virtual environment in `scripts/setup.sh`. Earlier foundation checks mixed system Python and the virtual environment because the CLI has no third-party dependencies; the documented commands were corrected in commit `e841cdc`, and a full 33,434-file bundle verification was rerun with `.venv/bin/python` as `run-4e5a7c020a5e4544a846db554d83fe98`.

For each numbered phase in [TASK.md](TASK.md), maintain `Journal-<phase number>.md` at the repository root. Record completed work, task IDs, decisions, commands or run IDs, verification results, unresolved items, and owner handoffs. Update that journal when its phase completes; do not mark a phase complete while its tasks remain open.

## Limits and owner handoff

The imported scans are byte-verified starter inputs only. Their video/depth alignment, units, geometry, device, and app version are not yet validated. No photo/video/LiDAR property-plan processing pipeline or scored benchmark exists. The owner can help by identifying the scans' source device/app/version and choosing storage for the approximately 922 MB local bundle plus upcoming home captures. Neither answer blocks the next coding tasks.
