#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
jupyter notebook notebooks/class1_demo.ipynb
