# Journal 1 — Route 2 capture and device validation

**Status:** In progress on 2 October 2026. T09, T10, T11, T13, and T14 are checked in [TASK.md](TASK.md). T12 remains open. This journal will be updated when Phase 1 is complete.

## Work and evidence

| Task | Progress | Evidence |
| --- | --- | --- |
| T09 | Drafted a one-page stock capture card covering Camera stills, standalone video, Stray Scanner 1.4, room labels, coverage, doorway views, ZIP handoff, recapture triggers, and separate truth. | [protocols/stock_capture.md](protocols/stock_capture.md) |
| T10 | Owner installed Stray Scanner 1.4 on an iPhone 15 Pro Max, used default app settings, shared the test capture as `dummy_room.zip`, and extracted it to `dummy_room/`. Earlier owner report lists iOS 26.5. | Ignored original ZIP and extraction; ZIP import `cap-56e289351c2c4cd5b564ea64f06a5fe8`, extraction import `cap-f193a28646e74de985d18ea075eaa569` |
| T11 | Audited video decode, PNG layouts/CRC/sample values, pose/intrinsic IDs and timing, IMU timing, ZIP transfer, and known format assumptions. All 1,144 ZIP files match extracted bytes. RGB has 569 frames versus 570 depth/confidence/pose records. The same one-frame difference occurs in all three starter scans. | [JSON report](reports/device_format_dummy_room.json), [readable report](reports/device_format_dummy_room.md), run `run-62dd712f6c2f485e82d9a12bd8eac037` |
| T12 | Owner reports a non-engineer's capture/share trial took less than five minutes. Detailed stage times and a repeat after feedback were not recorded; owner asked to continue other work for now. | Owner report in conversation; task remains open |
| T13 | Published hardware and tier matrix. Photo/video require an iPhone 15+; LiDAR requires an actual LiDAR Scanner and a compatible app/iOS. No per-tier accuracy was invented. | [docs/device_matrix.md](docs/device_matrix.md) |
| T14 | Stray Scanner's free capture → ZIP share → transfer → extraction → checksum comparison → format audit succeeded. Scan4D fallback was not triggered. The one-frame RGB mismatch is explicitly documented for Phase 2 importer handling. | [format report](reports/device_format_dummy_room.md) |

## Reproducibility and decisions

- The original ZIP and extracted folder are **one physical recording**. [repro/archive_links.json](repro/archive_links.json) ties their two import manifests together so they are not counted as repeat captures. The full bundle is ignored by Git; its current index is [repro/manifest.json](repro/manifest.json).
- Added hash-pinned `imageio-ffmpeg==0.6.0` to [requirements.txt](requirements.txt) for HEVC decode. The [Python wrapper is BSD-2-Clause](https://pypi.org/project/imageio-ffmpeg/); its bundled FFmpeg reports version 7.0.2-static and `ffmpeg -L` states GPL version 3 or later. A fresh setup with cached wheel took **14.65 seconds** and used a **92 MB** virtual environment; the uncached Linux wheel is 29.5 MB. All project Python commands used `.venv/bin/python`.
- The [Stray Scanner App Store listing](https://apps.apple.com/in/app/stray-scanner/id1557051662) currently says Free and iOS 18.6+; the [developer format](https://github.com/strayrobots/scanner/blob/main/docs/format.md) specifies millimetre depth PNGs, confidence codes 0–2, per-frame pose/intrinsics, and HEVC RGB. These published units and coordinate conventions still need physical validation before numeric geometry claims.

## Open work and handoff

T12 remains open: the owner reports the protocol was followable in under five minutes, but no repeat-after-feedback evidence was recorded. The [alignment rule](docs/stray_alignment.md) keeps RGB-to-depth references unresolved until offset evidence exists. The format audit establishes transfer and field structure, not a property plan or measured accuracy. Continue with Phase 2 ingestion while preserving the one-frame gap as a warning.
