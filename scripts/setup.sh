#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
if [[ "${1:-}" == "--models" ]]; then
  .venv/bin/python -m pip install torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cpu
  .venv/bin/python -m pip install -r requirements-models.txt
  .venv/bin/python scripts/fetch_models.py
fi
