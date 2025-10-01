#!/usr/bin/env bash
set -euo pipefail

# Aurora Pro post-install smoke test
# Checks core services: API, Streamlit, vLLM, ChromaDB, Redis

ok=0; fail=0
log() { printf "%s\n" "$1"; }
pass() { log "✅ $1"; ok=$((ok+1)); }
warn() { log "⚠️  $1"; }
err() { log "❌ $1"; fail=$((fail+1)); }

check_http() {
  local name=$1 url=$2
  if command -v curl >/dev/null 2>&1 && curl -fsS "$url" >/dev/null 2>&1; then
    pass "$name reachable ($url)"
  else
    err  "$name not reachable ($url)"
  fi
}

check_redis() {
  if command -v redis-cli >/dev/null 2>&1; then
    if redis-cli ping >/dev/null 2>&1; then pass "Redis responsive (PONG)"; else err "Redis not responding"; fi
  else
    warn "Redis CLI not installed; skipping"
  fi
}

log "==== Aurora Pro Verify ===="
check_http "API backend" "http://127.0.0.1:8000/health"
check_http "Streamlit GUI" "http://127.0.0.1:8501/_stcore/health"
check_http "vLLM API" "http://127.0.0.1:8002/v1/models"
check_http "ChromaDB" "http://127.0.0.1:8001/api/v1/heartbeat"
check_http "Vision Streamer" "http://127.0.0.1:8011/video_feed"
check_redis

log "==========================="
log "Passed: $ok  Failed: $fail"

exit $(( fail > 0 ))
