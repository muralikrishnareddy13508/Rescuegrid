#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
VENV_ACTIVATE="/home/linux1/rescuegrid/venv/bin/activate"
if [[ -f "$VENV_ACTIVATE" ]]; then
  # shellcheck disable=SC1090
  source "$VENV_ACTIVATE"
else
  echo "Could not find venv at $VENV_ACTIVATE" >&2
  echo "Activate the Python environment that has FastAPI, NumPy, SciPy, and scikit-learn installed." >&2
  exit 1
fi
python -c 'import fastapi, sklearn, scipy, numpy' || {
  echo "Python dependencies are not importable in the active environment. See README_FINAL_SETUP.md." >&2
  exit 1
}
exec uvicorn app.main:app --host 127.0.0.1 --port 8000
