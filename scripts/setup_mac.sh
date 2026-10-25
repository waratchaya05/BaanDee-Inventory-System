#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON_BIN=""
for candidate in python3.12 python3.11 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,13) else 1)' >/dev/null 2>&1; then
    PYTHON_BIN="$candidate"
    break
  fi
done

if [ -z "$PYTHON_BIN" ]; then
  echo "Python 3.11 or 3.12 is required. Install Python 3.12, then run this script again."
  exit 1
fi

echo "Using $($PYTHON_BIN --version) at $(command -v "$PYTHON_BIN")"
"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/generate_data.py
python -m src.data_prep
python scripts/build_notebook.py
echo "Setup complete. Next run: ./scripts/smoke_test_mac.sh"
