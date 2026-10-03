#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $# -gt 1 || ( $# -eq 1 && "$1" != "--models" ) ]]; then
  echo 'Usage: bash scripts/setup.sh [--models]' >&2
  exit 2
fi
python_bin="${ASTRA_PYTHON:-python3.12}"
if ! command -v "$python_bin" >/dev/null; then
  echo 'Python 3.12 is required. On Ubuntu 24.04: sudo apt install python3.12 python3.12-venv' >&2
  exit 1
fi
"$python_bin" -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else "Use Python 3.12 (set ASTRA_PYTHON to its executable).")'
if [[ -x .venv/bin/python ]]; then
  .venv/bin/python -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else "Existing .venv uses another Python version. Rename it and rerun setup.")'
fi
"$python_bin" -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
if [[ "${1:-}" == "--models" ]]; then
  .venv/bin/python -m pip install torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cpu
  .venv/bin/python -m pip install -r requirements-models.txt
  .venv/bin/python scripts/fetch_models.py
  .venv/bin/python scripts/fetch_semantic_models.py
  .venv/bin/python scripts/check_environment.py
fi
.venv/bin/python -m pip check
echo 'Setup complete. Run .venv/bin/python -m pytest -q, then follow README.md for dataset placement and commands.'
