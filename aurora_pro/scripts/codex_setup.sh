#!/usr/bin/env bash
# Infrastructure Deployment Controller — Codex CLI integration
# Creates a workspace-level Codex config and runs an initial analysis.
# Usage: bash aurora_pro/scripts/codex_setup.sh

set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="/home/v/Desktop/codex_setup_log.txt"

ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() {
  mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
  printf "%s | %s\n" "$(ts)" "$1" | tee -a "$LOG_FILE" >/dev/null || true
}

section() { log "===== $1 ====="; }
has_cmd() { command -v "$1" >/dev/null 2>&1; }

ensure_npm() {
  if has_cmd npm; then return 0; fi
  log "npm not found; please install Node.js (v18+) before continuing"
  exit 1
}

install_codex_cli() {
  section "Codex CLI installation"
  ensure_npm
  if has_cmd codex; then
    log "Codex CLI already installed: $(codex --version || echo present)"
  else
    log "Installing @openai/codex globally via npm"
    npm install -g @openai/codex
  fi
  codex --version || true
}

write_codex_config() {
  section "Writing Codex workspace configuration"
  mkdir -p "$WORKSPACE_DIR/.codex"
  local src="$WORKSPACE_DIR/configs/codex-config.json"
  if [ ! -f "$src" ]; then
    src="$WORKSPACE_DIR/codex-config.json"
  fi
  local dest="$WORKSPACE_DIR/.codex/config.json"
  if [ -f "$src" ]; then
    cp -f "$src" "$dest"
    log "Copied codex-config.json to $dest"
  else
    cat > "$dest" << 'EOF'
{
  "approval_mode": "auto",
  "memory_persistence": true,
  "model": "gpt-5-codex",
  "reasoning_effort": "high",
  "tool_access": ["file", "network", "shell"],
  "working_directory": "."
}
EOF
    log "Wrote default Codex config to $dest"
  fi
}

initial_analysis() {
  section "Initial codebase analysis via Codex"
  if has_cmd codex; then
    # Non-blocking dry analysis prompt to verify CLI + config
    codex exec "analyze codebase structure and identify optimization opportunities" || true
  else
    log "Codex CLI not available; skipping analysis"
  fi
}

main() {
  section "Aurora Pro — Codex setup start"
  install_codex_cli
  write_codex_config
  initial_analysis
  section "Aurora Pro — Codex setup complete"
}

main "$@"
