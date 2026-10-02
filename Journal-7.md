# Journal 7 — Home benchmark capture and reference truth

Status: waiting on owner capture and independent reference measurements. The
reference-only manifest draft in `docs/benchmark_manifest.md` fixes stable
cross-tier IDs and keeps truth out of inference. Existing `Flat-805` photos and
video remain original development inputs. No LiDAR, repeat room, scored damage,
or tape/laser sheet has been supplied, so T54–T62 are not checked.

**Update, 2 October 2026:** The owner supplied the full Flat-805 Stray ZIP and
four room-level length, breadth, and ceiling-height triples. They confirmed
`room-hall` is the connector. The values are stored in ignored
`repro/bundle/benchmark_truth/flat_805_owner_dimensions.json`, outside the
prediction input. The owner then confirmed a laser instrument and connections
`bed–hall`, `hall–toilet`, and `hall–kitchen`; these were added only to the
reference file. Prior notes identify iPhone 15 Pro Max, owner-reported iOS
26.5, and Stray Scanner 1.4, but these versions have not been reconfirmed for
this scan. The owner has not yet supplied wall/opening IDs, endpoint method,
or repeated readings. The original wording
above records the prior state; the new LiDAR audit is in `Journal-3.md`.

The owner later supplied one laser-measured door, height 2.17 m and width
0.79 m, without identifying its room/wall. It is stored as an unassigned
opening in the ignored reference file and cannot yet be matched for the
opening gate. The owner chose to defer the independent repeat scan and damage
capture. Neither deferred item is marked complete.

The owner's four `Flat-805` photo folders and standalone video cover four
named spaces, but folder name `room-hall` alone is not evidence that the hall
is the required connector or that all spaces connect correctly. Once the
LiDAR export arrives, the next owner inputs are: an independently recaptured
same-tier room; an independent room/opening/height/wall/footprint measurement
sheet; two visible damage classes with reference regions and staging notes;
and any difficult-surface examples. Keep truth outside capture input folders.
The practical handoff is [docs/owner_benchmark_handoff.md](docs/owner_benchmark_handoff.md).
