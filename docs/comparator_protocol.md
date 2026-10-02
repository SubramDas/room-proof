# Consumer-app comparison protocol

Before inspecting app or RoomProof errors, record exactly two distinct room
IDs and every eligible wall length, opening width, and ceiling height reference
ID. Keep this frozen list in the external benchmark bundle. Include a dimension
even when one or both systems omit it. Measure each feature independently and
preserve both original app exports and our raw LiDAR captures.

The working scorer is `roomproof.comparator.compare`. Shared-only and expanded
scores have separate denominators. The expanded score credits an ours-only wall
only when its absolute error is at most **0.05 m**, a project limit declared
before the baseline. Opening and ceiling limits are 0.02 m and 0.015 m. Report
unedited values at exported precision; do not manually correct either plan.

The owner must confirm the comparator app's installed version, export access,
and two same-visit scans. The default candidate is magicplan. If its free
account cannot export dimensions, document that result and choose another free
app before freezing the comparison.
