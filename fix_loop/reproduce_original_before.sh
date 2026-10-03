#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"
STAGE="$(mktemp -d /tmp/astra-original-before.XXXXXX)"
trap 'rm -rf "$STAGE"' EXIT
git --git-dir="$ROOT/.history" --work-tree="$ROOT" archive e3977de | tar -x -C "$STAGE"
ln -s "$ROOT/models" "$STAGE/models"
cd "$STAGE"
"$PYTHON" -m astra run --tier lidar --input "$ROOT/three_room/lidar" --output "$ROOT/runs/reproduced_original_lidar_before" --capture-id three_room --max-frames 140 --semantic-views 12
"$PYTHON" -m astra run --tier photos --input "$ROOT/three_room" --output "$ROOT/runs/reproduced_original_photo_before" --capture-id three_room --semantic-views 9
