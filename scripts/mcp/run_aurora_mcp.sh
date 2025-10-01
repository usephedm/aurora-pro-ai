#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [ -f venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

export AURORA_MCP_ALLOW_SHELL=${AURORA_MCP_ALLOW_SHELL:-true}
export AURORA_API_BASE=${AURORA_API_BASE:-http://127.0.0.1:8000}
export VLLM_BASE_URL=${VLLM_BASE_URL:-http://127.0.0.1:8002/v1}
export AURORA_GUI_BASE=${AURORA_GUI_BASE:-http://127.0.0.1:8501}

python -m aurora_pro.mcp_server

