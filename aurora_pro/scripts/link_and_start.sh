#!/usr/bin/env bash
set -euo pipefail

LOG="/home/v/Desktop/codex_setup_log.txt"
ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { mkdir -p "$(dirname "$LOG")"; printf "%s | %s\n" "$(ts)" "$1" | tee -a "$LOG" >/dev/null; }

require() { command -v "$1" >/dev/null 2>&1 || { log "Missing command: $1"; return 1; }; }

CODex_BIN_DIR="/opt/codex/bin"
WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_BIN_DIR="$WORKSPACE_DIR/scripts"

main() {
  log "Link & Start — begin"
  sudo mkdir -p /usr/local/bin || true

  # Symlink wrappers for convenience
  for f in run_vllm.sh run_chromadb.sh run_ollama_fallback.sh verify.sh logwrap codex_plugin_sandbox; do
    if [ -x "$CODex_BIN_DIR/$f" ]; then
      sudo ln -sf "$CODex_BIN_DIR/$f" "/usr/local/bin/${f%.*}" || true
    elif [ -x "$REPO_BIN_DIR/$f" ]; then
      sudo ln -sf "$REPO_BIN_DIR/$f" "/usr/local/bin/${f%.*}" || true
    fi
  done

  # Write Claude/Claude-compatible endpoints for FastAPI
  ENV_FILE="/root/aurora_pro/.env"
  sudo mkdir -p "/root/aurora_pro" || true
  sudo bash -c "cat > '$ENV_FILE'" <<EOF
VLLM_BASE_URL=http://127.0.0.1:8002/v1
REDIS_URL=redis://127.0.0.1:6379/0
CHROMA_URL=http://127.0.0.1:8001
OLLAMA_URL=http://127.0.0.1:11434
VISION_STREAMER_URL=http://127.0.0.1:8011
EOF
  log "Wrote Claude endpoints to $ENV_FILE"

  # Start Redis if present
  if command -v redis-cli >/dev/null 2>&1; then
    if ! redis-cli ping >/dev/null 2>&1; then
      # Try to start via service or fallback to docker if running elsewhere; ignore errors
      sudo systemctl start redis-server 2>/dev/null || true
      sleep 1 || true
    fi
    if redis-cli ping >/dev/null 2>&1; then
      log "Redis online (PONG)"
    else
      log "Redis not responding; continuing"
    fi
  fi

  # Start ChromaDB
  if [ -x "/opt/codex/venv/chroma/bin/python" ]; then
    if ! ss -ltn | grep -q ":8001\b"; then
      log "Starting ChromaDB on :8001"
      nohup /opt/codex/venv/chroma/bin/python -m chromadb run --host 127.0.0.1 --port 8001 --path /opt/codex/chroma \
        >/var/log/codex-chromadb.foreground.log 2>&1 & disown || true
      sleep 2 || true
    fi
  else
    log "Chroma venv not found; skipping Chroma start"
  fi

  # Pick vLLM FP16 model dir if present
  VLLM_MODEL="/models/fp16/Qwen2.5-7B-Instruct"
  if [ ! -d "$VLLM_MODEL" ]; then
    # choose first subdir under /models/fp16 if available
    first_dir=$(find /models/fp16 -maxdepth 1 -mindepth 1 -type d | head -n1 || true)
    if [ -n "${first_dir:-}" ]; then VLLM_MODEL="$first_dir"; fi
  fi

  # Start vLLM
  if [ -x "/opt/codex/venv/codex/bin/python" ]; then
    if ! ss -ltn | grep -q ":8002\b"; then
      log "Starting vLLM on :8002 with model=$VLLM_MODEL"
      nohup /opt/codex/venv/codex/bin/python -m vllm.entrypoints.openai.api_server \
        --host 127.0.0.1 --port 8002 --model "$VLLM_MODEL" \
        --gpu-memory-utilization 0.9 --trust-remote-code \
        >/var/log/codex-vllm.foreground.log 2>&1 & disown || true
      sleep 2 || true
    fi
  else
    log "vLLM venv not found; skipping vLLM start"
  fi

  # Start Ollama if available
  if command -v ollama >/dev/null 2>&1; then
    if ! ss -ltn | grep -q ":11434\b"; then
      log "Starting Ollama serve on :11434"
      nohup ollama serve >/var/log/codex-ollama.foreground.log 2>&1 & disown || true
      sleep 2 || true
    fi
  else
    log "Ollama not installed; skipping"
  fi

  # Monitoring via docker compose (optional)
  if command -v docker >/dev/null 2>&1; then
    if [ -f "/opt/codex/monitoring/docker-compose.yml" ]; then
      log "Starting monitoring stack via docker compose"
      docker compose -f /opt/codex/monitoring/docker-compose.yml up -d || true
    fi
  fi

  # Health checks
  if command -v curl >/dev/null 2>&1; then
    if curl -fsS http://127.0.0.1:8002/v1/models >/dev/null 2>&1; then
      log "vLLM API healthy"
    else
      log "vLLM API not reachable"
    fi
    if curl -fsS http://127.0.0.1:8001/api/v1/heartbeat >/dev/null 2>&1; then
      log "ChromaDB healthy"
    else
      log "ChromaDB not reachable"
    fi
    if curl -fsS http://127.0.0.1:3000/api/health >/dev/null 2>&1; then
      log "Grafana healthy"
    else
      log "Grafana not reachable"
    fi
  fi

  log "Link & Start — complete"
}

main "$@"
