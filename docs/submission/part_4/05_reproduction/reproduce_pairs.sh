#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
REPRO_BASE="$PWD"
PYTHON="$REPRO_BASE/project/.venv/bin/python"
for snapshot in snapshots/*; do
  if [[ ! -e "$snapshot/models" ]]; then ln -s "$REPRO_BASE/project/models" "$snapshot/models"; fi
done
mkdir -p reruns
run_snapshot() {
  local snapshot="$1"
  shift
  (cd "$REPRO_BASE/snapshots/$snapshot"; "$PYTHON" -m astra run "$@")
}
run_snapshot lidar_declared_before --tier lidar --input "$REPRO_BASE/project/three_room/lidar" --output "$REPRO_BASE/reruns/lidar_before" --capture-id three_room --max-frames 140 --semantic-views 12
run_snapshot lidar_declared_after --tier lidar --input "$REPRO_BASE/project/three_room/lidar" --output "$REPRO_BASE/reruns/lidar_after" --capture-id three_room --max-frames 140 --semantic-views 12 --layout-method planes
run_snapshot kitchen_supporting_before --tier lidar --input "$REPRO_BASE/project/kitchen/lidar" --output "$REPRO_BASE/reruns/kitchen_before" --capture-id kitchen --max-frames 100 --semantic-views 8 --single-room --drift off
run_snapshot kitchen_supporting_after --tier lidar --input "$REPRO_BASE/project/kitchen/lidar" --output "$REPRO_BASE/reruns/kitchen_after" --capture-id kitchen_lidar_final --max-frames 100 --semantic-views 8 --single-room --drift on --layout-method planes
run_snapshot photos_declared_before --tier photos --input "$REPRO_BASE/project/three_room" --output "$REPRO_BASE/reruns/photos_before" --capture-id three_room --semantic-views 9
# WARNING: recorded-revision fallback for unrecoverable historical hashes; not exact replay.
run_snapshot photos_declared_after --tier photos --input "$REPRO_BASE/project/three_room" --output "$REPRO_BASE/reruns/photos_after_revision_fallback" --capture-id three_room_photos_final --semantic-views 9 --depth-model depth-pro
