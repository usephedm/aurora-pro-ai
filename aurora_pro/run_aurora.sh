#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Activate virtual environment
source venv/bin/activate

API_PORT="${API_PORT:-8000}"
GUI_PORT="${GUI_PORT:-8501}"

python -m uvicorn main:app --host 0.0.0.0 --port "$API_PORT" &
API_PID=$!

streamlit run aurora_gui.py --server.port "$GUI_PORT" --server.address 0.0.0.0 --server.headless true &
GUI_PID=$!

cleanup() {
  trap - INT TERM
  kill "$API_PID" "$GUI_PID" 2>/dev/null || true
}

trap cleanup INT TERM
wait "$API_PID" "$GUI_PID"
