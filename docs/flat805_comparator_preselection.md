# Flat-805 consumer-app comparison preselection

Frozen before any consumer-app exports or error comparison, 2 October 2026.

Selected rooms: `room-bed` and `room-kitchen`. Include **every physical wall
length, every door/window opening width, and ceiling height** for each of these
rooms that can be independently laser measured. Use the same physical feature
IDs across reference truth, our LiDAR plan, and the app export. An omitted
dimension remains in the eligible set and is reported as an omission; do not
select only dimensions that both systems happen to report. Floor area is
reported separately. The working ours-only LiDAR wall limit was frozen at
0.05 m in `roomproof/comparator.py` before this preselection.

The exact wall/opening IDs and measurements are pending. Do not adjust the
selected rooms or eligible feature rule after looking at comparator errors.
