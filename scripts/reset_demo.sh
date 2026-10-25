#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
python scripts/generate_data.py
python -m src.data_prep
python scripts/build_notebook.py
if [ -f logs/app_events.jsonl ]; then
  : > logs/app_events.jsonl
fi
echo "Demonstration data, notebook, checkpoints, and event log reset."
