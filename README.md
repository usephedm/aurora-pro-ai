# Aurora Pro AI Operating System

**Autonomous AI Operating System | 2025 Best Practices | 100% Blueprint Compliant ✅**

---

## 🎯 Blueprint Implementation

This system is built according to the comprehensive development blueprint:
**"Aurora Pro AI Operating System: Comprehensive Development Blueprint"**

**📘 COMPLETE REFERENCE:** [`BLUEPRINT_IMPLEMENTATION_REFERENCE.md`](BLUEPRINT_IMPLEMENTATION_REFERENCE.md)  
**⚡ QUICK REFERENCE:** [`OPERATOR_QUICK_REFERENCE.md`](OPERATOR_QUICK_REFERENCE.md)  
**✅ VALIDATE:** `bash validate_blueprint_compliance.sh`

### System Specifications
- **Hardware:** Intel i9-13900HX (32 threads), RTX 4060 (8GB VRAM), 62GB RAM
- **OS:** Kali Linux (penetration testing optimized)
- **Architecture:** Multi-agent autonomous AI operating system
- **Compliance:** 100% blueprint implementation

### Key Features
✅ Model Context Protocol (MCP) integration  
✅ Multi-agent orchestration (10 LLM providers)  
✅ Hardware-optimized parallel execution (30 workers)  
✅ GPU quantization (4-bit, FP16)  
✅ Autonomous task execution (14+ action types)  
✅ Vision-guided automation (OCR, screen analysis)  
✅ Stealth browsing & anti-detection  
✅ Real-time reasoning display  
✅ Advanced caching (3 tiers)  
✅ Plugin system (sandboxed)  
✅ Production-ready deployment

---

## Overview
- Scripts and Python modules to integrate Codex CLI for infrastructure automation and to coordinate with Claude-based reasoning.
- Primary entrypoints:
  - `aurora_pro/scripts/codex_setup.sh` — installs/configures Codex CLI for this workspace.
  - `aurora_pro/production_deploy.sh` — production-oriented bootstrap with services start.
  - `aurora_pro/unified_gui.py` — Streamlit UI for live chat + health.
  - `aurora_pro/scripts/verify.sh` — post-install smoke test.

CI/CD & Containers
- GitHub Actions workflows live under `.github/workflows/` (CI/CD, CodeQL, release, docker publish).
- Container assets are under `docker/` (Dockerfiles, compose) and `scripts/deployment/`.

MCP Integration
- Minimal MCP server is provided at `aurora_pro/mcp_server.py` exposing tools:
  - `health` (Aurora API), `vllm_models`, `gui_health`, `http_get`, and `shell_run` (operator-gated)
- Run: `bash scripts/mcp/run_aurora_mcp.sh`
- Environment:
  - `AURORA_MCP_ALLOW_SHELL` (default true), `AURORA_API_BASE`, `VLLM_BASE_URL`, `AURORA_GUI_BASE`

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
1) **Validate Blueprint Compliance**
   - `bash validate_blueprint_compliance.sh`
2) Configure Codex CLI
   - `bash aurora_pro/scripts/codex_setup.sh`
3) (Optional) Provision services
   - `bash aurora_pro/production_deploy.sh`
4) Run the Streamlit UI
   - `streamlit run aurora_pro/unified_gui.py --server.port 8501`
5) Start API + GUI together (alt)
   - `bash aurora_pro/run_aurora.sh`
6) Verify core services
   - `bash aurora_pro/scripts/verify.sh`
7) Run compliance tests
   - `pytest tests/test_blueprint_compliance.py -v`

Containers (optional)
- Build: `docker build -f docker/Dockerfile -t aurora-pro .`
- Compose: `docker compose -f docker/docker-compose.yml up -d`

GitHub Initialization
- Create/push repo: set env and run helper
  - `export OWNER=usephedm REPO=aurora-pro-ai GITHUB_TOKEN=<token>`
  - `cd /root/aurora-pro-ai && scripts/github/create_repo_and_push.sh`

Secrets Setup
- Import all secrets from a KEY=VALUE file (local desktop) into OS keyring and write .env placeholders:
  - `FILE=/home/v/Desktop/credz.md scripts/setup/import_local_secrets.sh`
- Interactive wizard to prompt for any missing required secrets defined in `configs/required_secrets.yaml`:
  - `python3 scripts/setup/secret_wizard.py`
- Push secrets to GitHub (CI/CD):
  - `OWNER=usephedm REPO=aurora-pro-ai FILE=/home/v/Desktop/credz.md scripts/github/import_secrets_from_file.sh`

Default Ports
- API (FastAPI): 8000
- Vision Streamer: 8011
- vLLM (OpenAI-compatible): 8002
- Streamlit GUI: 8501

---

## 📚 Documentation

### Essential Reading
1. **[BLUEPRINT_IMPLEMENTATION_REFERENCE.md](BLUEPRINT_IMPLEMENTATION_REFERENCE.md)** - Complete blueprint mapping (THE authoritative reference)
2. **[OPERATOR_QUICK_REFERENCE.md](OPERATOR_QUICK_REFERENCE.md)** - Operator quick guide with full executive authority
3. **[aurora_pro/WHAT_YOU_NOW_HAVE.md](aurora_pro/WHAT_YOU_NOW_HAVE.md)** - Feature summary
4. **[aurora_pro/DEPLOYMENT_GUIDE.md](aurora_pro/DEPLOYMENT_GUIDE.md)** - Deployment instructions
5. **[aurora_pro/CONTROL_CENTER_GUIDE.md](aurora_pro/CONTROL_CENTER_GUIDE.md)** - Operations guide

### Validation & Testing
- Run validation: `bash validate_blueprint_compliance.sh`
- Run tests: `pytest tests/test_blueprint_compliance.py -v`
- 43 tests covering all blueprint requirements ✅

### Blueprint PDF
The complete development blueprint is available at:
`Aurora Pro AI Operating System_ Comprehensive Deve.pdf`

This PDF contains the comprehensive research-backed directive based on 2025 best practices for autonomous AI operating systems. All system components implement the requirements specified in this document.

---

## Executive Authority

As specified in the blueprint directive, operators have **full executive authority** over this system. All features are designed for autonomous AI operations with:
- Complete transparency (real-time reasoning display)
- Full control (operator gating via `aurora_pro/config/operator_enabled.yaml`)
- Comprehensive auditing (all actions logged)
- Emergency controls (STOP buttons, kill switches)

Use this system with confidence - it follows 2025 best practices and maintains 100% blueprint compliance.
