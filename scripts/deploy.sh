#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Deploying Aurora Pro"

# Optimize CPU governor if available
if [ -d /sys/devices/system/cpu/cpu0/cpufreq ]; then
  echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null || true
fi

# Start baseline services
sudo systemctl start redis-server || true

# Compose stack (API, GUI, vLLM, Redis, Chroma)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="${SCRIPT_DIR%/scripts}/docker"

if command -v docker >/dev/null 2>&1; then
  docker compose -f "$DOCKER_DIR/docker-compose.yml" up -d --build
else
  echo "⚠️ Docker not installed; skipping compose stack"
fi

# Health checks
curl -fsS http://localhost:8000/health >/dev/null && echo "✅ API healthy" || { echo "❌ API failed"; exit 1; }
curl -fsS http://localhost:8001/api/v1/heartbeat >/dev/null && echo "✅ Chroma healthy" || echo "⚠️ Chroma not responding"
curl -fsS http://localhost:8002/v1/models >/dev/null && echo "✅ vLLM healthy" || echo "⚠️ vLLM not responding"

echo "✅ Aurora Pro deployed successfully"

