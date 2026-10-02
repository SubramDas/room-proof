# Reproducible raw-data bundle

RoomProof uses a local content-addressed bundle, kept outside ordinary Git. The destination is chosen with `--bundle`; `repro/bundle/` is ignored if used locally. Original capture directories stay untouched. The bundle has `captures/*.json` manifests and SHA-256 objects under `objects/sha256/`.

Import one capture folder with metadata (use the actual app/version when known):

```bash
.venv/bin/python -m roomproof import-capture single_room/c00a170fe1 \
  --bundle repro/bundle --property-id prop-starter \
  --tier lidar --source-label supplied-single-room \
  --notes 'Starter export; device and app versions not yet verified'
```

The command prints a capture manifest path and a run manifest path. Check the recorded metadata before using it in a benchmark. Verify all imported bytes:

```bash
.venv/bin/python -m roomproof verify-capture --bundle repro/bundle \
  --manifest repro/bundle/captures/CAPTURE_ID.json
```

After importing a new capture, regenerate the tracked index and commit the index change with the corresponding metadata decision:

```bash
.venv/bin/python -m roomproof index-bundle --bundle repro/bundle --index repro/manifest.json
```

To deliver the bundle, copy its **entire** directory (including `captures/` and `objects/`) to a separate local volume or archive; do not rely on `.gitignore` or a source folder existing on another machine. The tracked [manifest.json](manifest.json) lists expected capture-manifest SHA-256 hashes. On a clean directory, copy the bundle and run:

```bash
.venv/bin/python -m roomproof verify-bundle --bundle /path/to/copied/bundle --index repro/manifest.json
```

This checks the tracked manifest hashes and every raw object. Then run the documented prediction/scoring commands when they exist. Retain the original source folders separately until submission is verified.

The three starter directories total 873,680,157 bytes across 33,434 files. Their manifests in this local bundle are:

| Source | Capture ID | Files | Bytes |
| --- | --- | ---: | ---: |
| `single_room/` | `cap-c07fff0bef1248249509972a948a8ef8` | 3,434 | 88,503,534 |
| `single_scan_floor_only/` | `cap-bb46b443767f4b50ac5d0364bd271808` | 10,506 | 276,731,533 |
| `single_scan_with_ceiling/` | `cap-1e6ed40918ce441dbea5b553dc358c8e` | 19,494 | 508,445,090 |

The complete local bundle is ignored by Git, so the above IDs only resolve on a machine with the bundle. A separate copy at `/tmp/roomproof-foundation-bundle-copy` verified all three manifests on 2 October 2026; the one-command index verification is `run-688b8f671cfc44a28e4b1f88466722e2`. A check against an empty bundle failed as expected and wrote `run-71f0314fa6d64a27b9778de4d327b75c`. These runs only prove byte preservation and logging, not capture format validity or model accuracy.

Copying all three into a bundle needs roughly 874 MB extra storage before filesystem overhead; a second clean-copy rehearsal needs another copy. Future home captures and model weights will add to this amount. No network fetch or paid service is needed for the foundation commands. The final submission destination and size limits remain to be confirmed.
