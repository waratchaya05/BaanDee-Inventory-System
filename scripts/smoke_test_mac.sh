#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -x .venv/bin/python ]; then
  echo "Missing .venv. Run ./scripts/setup_mac.sh first."
  exit 1
fi

for port in 8000 7860; do
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Port $port is already in use. Stop that process, then run the smoke test again."
    exit 1
  fi
done

source .venv/bin/activate
mkdir -p logs
API_PID=""
APP_PID=""

cleanup() {
  if [ -n "$APP_PID" ]; then kill "$APP_PID" >/dev/null 2>&1 || true; fi
  if [ -n "$API_PID" ]; then kill "$API_PID" >/dev/null 2>&1 || true; fi
}
trap cleanup EXIT INT TERM

echo "[1/7] Regenerating deterministic data and notebook"
python scripts/generate_data.py
python -m src.data_prep
python scripts/build_notebook.py
python scripts/validate_core.py

echo "[2/7] Running the normal test suite"
python -m pytest -q

echo "[3/7] Starting the local company API"
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 > logs/mac_api.log 2>&1 &
API_PID=$!
for _ in {1..30}; do
  if curl --fail --silent http://127.0.0.1:8000/health >/dev/null 2>&1; then break; fi
  sleep 0.5
done
curl --fail --silent http://127.0.0.1:8000/health >/dev/null

echo "[4/7] Exercising HTTP success, not-found, and unavailable cases"
python - <<'PY'
from src.api_client import fetch_order
valid = fetch_order("ORD-260728-1842")
unknown = fetch_order("ORD-UNKNOWN-77")
unavailable = fetch_order("ORD-260728-1842", base_url="http://127.0.0.1:8999", timeout=0.2)
assert valid.ok and valid.status_code == 200 and valid.data["status"] == "carrier_delay"
assert not unknown.ok and unknown.status_code == 404
assert not unavailable.ok and unavailable.status_code is None
print("HTTP cases passed")
PY

echo "[5/7] Executing every notebook cell"
jupyter nbconvert --to notebook --execute notebooks/class1_demo.ipynb \
  --output class1_demo.executed.ipynb --output-dir notebooks \
  --ExecutePreprocessor.timeout=180

echo "[6/7] Checking Gradio workflow and web page"
python - <<'PY'
from src.app import load_case_for_ui
main = load_case_for_ui("TKT-260731-042", "fixture")
unknown = load_case_for_ui("TKT-260731-099", "fixture")
assert main[0]["current_status"] == "carrier_delay" and main[4]["passed"]
assert unknown[0]["order_verified"] is False and unknown[4]["passed"]
print("Gradio callback cases passed")
PY
BAANDEE_AI_MODE=fixture python -m src.app > logs/mac_app.log 2>&1 &
APP_PID=$!
for _ in {1..60}; do
  if curl --fail --silent http://127.0.0.1:7860 >/dev/null 2>&1; then break; fi
  sleep 0.5
done
curl --fail --silent http://127.0.0.1:7860 >/dev/null

echo "[7/7] Complete"
echo "MAC_SMOKE_TEST_PASS"
echo "Executed notebook: notebooks/class1_demo.executed.ipynb"
echo "Logs: logs/mac_api.log and logs/mac_app.log"
