#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
