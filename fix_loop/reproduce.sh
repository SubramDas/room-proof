#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON=.venv/bin/python
# Same new implementation, toggling only structural layout extraction:
"$PYTHON" -m astra run --tier lidar --input three_room/lidar --output runs/fix_reproduced_free_space --max-frames 140 --semantic-views 12 --layout-method free-space
"$PYTHON" -m astra run --tier lidar --input three_room/lidar --output runs/fix_reproduced_planes --max-frames 140 --semantic-views 12 --layout-method planes
"$PYTHON" -m astra evaluate --result runs/fix_reproduced_free_space/result.json --truth measurements.txt --mapping '{"room_1":"room_2","room_2":"room_1","room_3":"room_3"}' --output runs/fix_reproduced_free_space/evaluation
"$PYTHON" -m astra evaluate --result runs/fix_reproduced_planes/result.json --truth measurements.txt --mapping '{"room_1":"room_2","room_2":"room_1","room_3":"room_3"}' --output runs/fix_reproduced_planes/evaluation
# RGB after path. Exact original before source is available at e3977de in history.
"$PYTHON" -m astra run --tier photos --input three_room --output runs/fix_reproduced_photos --depth-model depth-pro --semantic-views 9
