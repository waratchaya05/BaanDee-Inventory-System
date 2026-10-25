#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
export BAANDEE_AI_MODE="${BAANDEE_AI_MODE:-fixture}"
python -m src.app
