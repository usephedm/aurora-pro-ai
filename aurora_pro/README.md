Aurora Pro — Codex CLI (ChatGPT-5) Integration

Overview
- Scripts and Python modules to integrate Codex CLI for infrastructure automation and to coordinate with Claude-based reasoning.
- Primary entrypoints:
  - `aurora_pro/scripts/codex_setup.sh` — installs/configures Codex CLI for this workspace.
  - `aurora_pro/production_deploy.sh` — production-oriented bootstrap with services start.
  - `aurora_pro/unified_gui.py` — Streamlit UI for live chat + health.
  - `aurora_pro/scripts/verify.sh` — post-install smoke test.

CI/CD & Containers
- GitHub Actions workflows live under `.github/workflows/` (CI/CD, CodeQL, release, docker publish).
- Container assets are under `docker/` (Dockerfiles, compose) and `scripts/deployment/`.

Config
- `codex-config.json` stores lightweight Codex CLI permissions and runtime flags. The setup script copies this to `.codex/config.json`.
  Top-level keys are alphabetized; extend this file rather than hard-coding in scripts.

Python Modules
- `codex_orchestrator.py` — Async wrapper around Codex CLI execution.
- `codex_model_quantizer.py` — Issues quantization tasks to Codex (ExLlamaV2).
- `unified_chatbox.py` — Multi-agent router (Claude, Codex, Local, Vision).
- `offline_capabilities.py` — Local inference fallbacks (Ollama, vLLM FP16).
- `persistent_state.py` — Checkpoint/restore simple state.

Important Notes
- vLLM does not support EXL2 quantized models. Serve FP16 via vLLM; EXL2 4-bit is for ExLlamaV2 runtimes.
- The setup logs progress to `/home/v/Desktop/codex_setup_log.txt`.

Quick Start
1) Configure Codex CLI
   - `bash aurora_pro/scripts/codex_setup.sh`
2) (Optional) Provision services
   - `bash aurora_pro/production_deploy.sh`
3) Run the Streamlit UI
   - `streamlit run aurora_pro/unified_gui.py --server.port 8501`
4) Start API + GUI together (alt)
   - `bash aurora_pro/run_aurora.sh`
5) Verify core services
   - `bash aurora_pro/scripts/verify.sh`

Containers (optional)
- Build: `docker build -f docker/Dockerfile -t aurora-pro .`
- Compose: `docker compose -f docker/docker-compose.yml up -d`

Default Ports
- API (FastAPI): 8000
- Vision Streamer: 8011
- vLLM (OpenAI-compatible): 8002
- Streamlit GUI: 8501
