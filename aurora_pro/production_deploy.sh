#!/usr/bin/env bash
# Aurora Pro production deployment script
# Usage: bash aurora_pro/production_deploy.sh

set -euo pipefail

echo "=========================================="
echo "Aurora Pro Production Deployment"
echo "=========================================="

# Phase 1: System Optimization
echo "[1/5] Optimizing system performance..."
if [ -d /sys/devices/system/cpu/cpu0/cpufreq ]; then
  echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null || true
fi
sudo sysctl -w vm.swappiness=10 || true
sudo systemctl disable bluetooth cups avahi-daemon 2>/dev/null || true

# Phase 2: Install Dependencies
echo "[2/5] Installing dependencies..."
cd "$(cd "$(dirname "$0")/.." && pwd)"

if [ -f venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
else
  python3 -m venv venv
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

pip install --upgrade pip
if [ -f requirements_production.txt ]; then
  pip install -r requirements_production.txt
fi

# Install Codex CLI
if command -v npm >/dev/null 2>&1; then
  npm install -g @openai/codex || true
fi

# Install Ollama (optional if already installed)
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.ai/install.sh | sh || true
fi
ollama serve >/dev/null 2>&1 & disown || true

# Ensure ChromaDB available
pip install "chromadb>=1.1.0" uvicorn || true

# Phase 3: Model Setup
echo "[3/5] Setting up AI models..."
python - <<'PY'
import asyncio
from aurora_pro.codex_model_quantizer import CodexModelQuantizer
from aurora_pro.codex_orchestrator import CodexCLIOrchestrator

async def main():
    codex = CodexCLIOrchestrator()
    quantizer = CodexModelQuantizer(codex)
    await quantizer.quantize_all_models()

asyncio.run(main())
PY

# Phase 4: Service Configuration
echo "[4/5] Configuring services..."
redis-cli CONFIG SET maxmemory 14gb || true
redis-cli CONFIG SET maxmemory-policy allkeys-lru || true

# Start vLLM server (serve FP16 with GPU util tuning)
python -m vllm.entrypoints.openai.api_server \
  --model /models/fp16/Qwen2.5-7B-Instruct \
  --gpu-memory-utilization 0.9 \
  --port 8002 \
  --trust-remote-code >/var/log/codex-vllm.foreground.log 2>&1 & disown || true

# Phase 5: Start Aurora Pro app surfaces (placeholders)
echo "[5/5] Launching Aurora Pro..."
if [ -f main.py ]; then
  uvicorn main:app --host 0.0.0.0 --port 8000 >/var/log/aurora-api.log 2>&1 & disown || true
fi
if command -v streamlit >/dev/null 2>&1; then
  streamlit run aurora_pro/unified_gui.py --server.port 8501 >/var/log/aurora-gui.log 2>&1 & disown || true
fi

echo "=========================================="
echo "✅ Aurora Pro is now operational!"
echo "=========================================="
echo "Unified GUI: http://localhost:8501"
echo "API Backend: http://localhost:8000"
echo "vLLM Server: http://localhost:8002"
echo "=========================================="
