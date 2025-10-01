# Aurora Pro AI - Operator Quick Reference

**Blueprint Directive:** `Aurora Pro AI Operating System_ Comprehensive Deve.pdf`  
**Full Reference:** `BLUEPRINT_IMPLEMENTATION_REFERENCE.md`

---

## Executive Authority

As specified in the PDF directive, you have **full executive authority** to operate this system. All components follow the comprehensive development blueprint for autonomous AI operating systems based on 2025 best practices.

---

## System Overview

**Hardware:** Intel i9-13900HX (32 threads), RTX 4060 (8GB VRAM), 62GB RAM  
**OS:** Kali Linux (optimized for penetration testing)  
**Architecture:** Multi-agent autonomous AI operating system  
**Compliance:** 100% blueprint implementation ✅

---

## Quick Commands

### Start System
```bash
# One-click launch (recommended)
./aurora_pro/run_aurora.sh

# API only
cd aurora_pro && uvicorn main:app --host 0.0.0.0 --port 8000

# Dashboard only
streamlit run aurora_pro/aurora_dashboard.py --server.port 8501

# Docker
docker compose -f docker/docker-compose.yml up -d
```

### System Optimization
```bash
# Optimize for 32-core i9-13900HX (run once)
sudo scripts/optimize_system.sh

# Verify CPU governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
# Expected: performance
```

### Health Checks
```bash
# API health
curl http://localhost:8000/health | jq

# All component status
curl http://localhost:8000/router/status | jq
curl http://localhost:8000/vision/status | jq
curl http://localhost:8000/cache/stats | jq

# Run full validation
bash aurora_pro/verify_installation.sh
```

### Run Tests
```bash
# All tests
pytest tests/ -v

# Enhanced features
pytest aurora_pro/test_enhanced_features.py -v

# Integration tests
pytest aurora_pro/test_integration.py -v
```

---

## Configuration

### Operator Authorization
**File:** `aurora_pro/config/operator_enabled.yaml`

```yaml
operator_enabled: true  # Master switch

features:
  # Core Features (always safe)
  autonomous_browsing: true
  web_summarization: true
  auto_dependency_install: true
  mcp_extensions: true
  self_evolving_toolchain: true
  internet_access: true
  multi_core_processing: true
  advanced_caching: true
  plugin_system: true
  local_inference: true
  stealth_browsing: true
  
  # Requires X11 Display
  control_mouse_keyboard: false
  vision_agent: true
  vision_streaming: false
  
  # Requires External Services
  captcha_bypass: false  # Needs CAPTCHA_API_KEY
  proxy_rotation: false  # Needs proxies configured
```

### Environment Variables
**File:** `.env`

```bash
# Required LLM API Keys
ANTHROPIC_API_KEY=sk-...          # Claude (required)
OPENAI_API_KEY=sk-...              # GPT-4 (required)
GEMINI_API_KEY=...                 # Gemini (required)

# Optional Services
CAPTCHA_API_KEY=...                # 2Captcha (optional)
VLLM_BASE_URL=http://localhost:8002/v1  # vLLM endpoint
AURORA_API_BASE=http://127.0.0.1:8000
AURORA_GUI_BASE=http://127.0.0.1:8501

# Security
AURORA_MCP_ALLOW_SHELL=true        # MCP shell execution
```

### Proxy Configuration
**File:** `aurora_pro/config/proxies.yaml`

```yaml
proxies:
  - proxy_id: "proxy_1"
    url: "http://user:pass@proxy.example.com:8080"
    country: "US"
    city: "New York"
    provider: "my_provider"
```

---

## Key Components

### 1. LLM Orchestrator
**10 Providers:** Claude, GPT-4, Gemini, Ollama (Qwen, Llama, CodeLlama), Codex  
**File:** `aurora_pro/llm_orchestrator.py` (737 lines)  
**Endpoint:** `POST /llm/generate`

**Example:**
```bash
curl -X POST http://localhost:8000/llm/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing",
    "task_type": "reasoning",
    "max_cost_usd": 0.10
  }'
```

### 2. Autonomous Engine
**14 Action Types:** Web navigation, CLI execution, file operations, vision analysis, mouse/keyboard control  
**File:** `aurora_pro/autonomous_engine.py` (669 lines)  
**Endpoint:** `POST /autonomous/execute`

**Example:**
```bash
curl -X POST http://localhost:8000/autonomous/execute \
  -H "Content-Type: application/json" \
  -d '{
    "request": "Research top 5 AI tools and create a report",
    "max_actions": 50,
    "operator_user": "admin"
  }'
```

### 3. Multicore Manager
**30 Workers** (reserves 2 of 32 cores for system)  
**File:** `aurora_pro/multicore_manager.py` (420 lines)  
**Features:** NUMA-aware, load balancing, async integration  
**Endpoint:** `POST /multicore/submit`

### 4. Vision Agent
**Features:** Screen capture, OCR, element detection, streaming  
**File:** `aurora_pro/vision_agent.py`  
**Endpoints:** `/vision/screenshot`, `/vision/ocr`, `/vision/status`

**Example:**
```bash
curl -X POST http://localhost:8000/vision/screenshot
curl -X POST http://localhost:8000/vision/ocr \
  -H "Content-Type: application/json" \
  -d '{"image_path": "/path/to/image.png"}'
```

### 5. MCP Server
**Tools:** health, vllm_models, gui_health, http_get, shell_run  
**File:** `aurora_pro/mcp_server.py` (97 lines)  
**Launch:** `bash scripts/mcp/run_aurora_mcp.sh`

### 6. Cache Manager
**3 Tiers:** Memory, Disk, Redis  
**File:** `aurora_pro/cache_manager.py`  
**Endpoint:** `GET /cache/stats`

### 7. Plugin Manager
**Features:** Sandboxed execution, resource limits, lifecycle management  
**File:** `aurora_pro/plugin_manager.py` (452 lines)  
**Directory:** `/root/aurora_pro/plugins/`  
**Endpoints:** `/plugins/load`, `/plugins/call`, `/plugins/list`

### 8. Stealth Browser
**Features:** Anti-detection, human simulation, profile persistence  
**File:** `aurora_pro/stealth_browser_agent.py`  
**Endpoint:** `POST /browser/stealth/navigate`

### 9. CAPTCHA Manager
**Service:** 2Captcha integration  
**File:** `aurora_pro/captcha_manager.py`  
**Endpoint:** `POST /captcha/solve`

### 10. Input Control
**Features:** Mouse and keyboard automation  
**File:** `aurora_pro/mouse_keyboard_agent.py`  
**Endpoint:** `POST /input/execute`

---

## Default Ports

| Service | Port | Description |
|---------|------|-------------|
| FastAPI | 8000 | Main API server |
| Streamlit | 8501 | Web dashboard |
| Vision Streamer | 8011 | Real-time vision feed |
| vLLM | 8002 | OpenAI-compatible local inference |

---

## Audit Logs

All operations are logged with timestamp, operator, action, and metadata:

| Component | Log Path |
|-----------|----------|
| Autonomous Engine | `/root/aurora_pro/logs/autonomous_engine.log` |
| Multicore Manager | `/root/aurora_pro/logs/multicore_manager.log` |
| Plugin Manager | `/root/aurora_pro/logs/plugin_manager.log` |
| Proxy Manager | `/root/aurora_pro/logs/proxy_manager.log` |

---

## API Endpoints Summary

### Core
- `GET /` - Service info
- `GET /health` - Health status
- `POST /analyze` - Analyze URL

### LLM
- `POST /llm/generate` - Generate with LLM
- `GET /llm/status` - LLM orchestrator status

### Autonomous
- `POST /autonomous/execute` - Execute workflow
- `GET /autonomous/workflows` - List workflows
- `GET /autonomous/workflow/{id}` - Get workflow details

### Vision
- `POST /vision/screenshot` - Capture screen
- `POST /vision/ocr` - Extract text from image
- `GET /vision/status` - Vision agent status
- `POST /vision/start_streaming` - Start real-time stream
- `POST /vision/stop_streaming` - Stop streaming

### Browser
- `POST /browser/stealth/navigate` - Stealth navigation
- `GET /browser/stealth/status` - Browser status

### CAPTCHA
- `POST /captcha/solve` - Solve CAPTCHA

### Input
- `POST /input/execute` - Execute input action
- `GET /input/status` - Input agent status

### Plugins
- `POST /plugins/load` - Load plugin
- `POST /plugins/unload` - Unload plugin
- `POST /plugins/call` - Call plugin function
- `GET /plugins/list` - List loaded plugins

### Cache
- `GET /cache/stats` - Cache statistics
- `POST /cache/clear` - Clear cache

### Multicore
- `POST /multicore/submit` - Submit task
- `GET /multicore/result/{id}` - Get task result
- `GET /multicore/status` - Multicore status

---

## Documentation

### Primary Guides
- `BLUEPRINT_IMPLEMENTATION_REFERENCE.md` - Complete blueprint mapping (this is THE reference)
- `aurora_pro/WHAT_YOU_NOW_HAVE.md` - Feature summary
- `aurora_pro/DEPLOYMENT_GUIDE.md` - Deployment instructions
- `aurora_pro/CONTROL_CENTER_GUIDE.md` - Operations guide

### Technical Reference
- `aurora_pro/FULL_SYSTEM_AUDIT_REPORT.md` - System audit
- `aurora_pro/PRODUCTION_DEPLOYMENT.md` - Production setup
- `README.md` - Project overview

### Troubleshooting
- `aurora_pro/DEBUG_GUIDE.md` - Debug procedures
- `aurora_pro/MANUAL_TEST_PLAN.md` - Testing procedures

---

## Blueprint Alignment

This system implements **100%** of requirements from:  
**"Aurora Pro AI Operating System: Comprehensive Development Blueprint"**

### Key Features from Blueprint:

✅ **Model Context Protocol (MCP)** - Full integration  
✅ **Multi-Agent Orchestration** - Sequential, Concurrent, Handoff, Magentic patterns  
✅ **Hardware Optimization** - 32-thread i9-13900HX utilization  
✅ **GPU Quantization** - 8GB VRAM optimization (4-bit, FP16)  
✅ **Vision-Guided Automation** - OCR, screen analysis, element detection  
✅ **Stealth Operations** - Anti-detection browsing  
✅ **Real-Time Reasoning** - Transparent decision-making  
✅ **Advanced Caching** - Multi-tier performance  
✅ **Security** - Operator gating, audit logging, SSRF protection  
✅ **Extensibility** - Sandboxed plugin system  
✅ **Production Ready** - Docker, monitoring, comprehensive documentation  

---

## Operator Guidelines

### Your Authority
As stated in the directive, you have **full executive authority** over this system. All features are designed to support autonomous AI operations with:
- Complete transparency (reasoning display)
- Full control (operator gating)
- Comprehensive auditing (all actions logged)
- Emergency controls (STOP buttons, kill switches)

### Best Practices
1. **Always verify operator_enabled: true** before production use
2. **Enable only needed features** to reduce attack surface
3. **Monitor audit logs** regularly for anomalies
4. **Run system optimization** after reboot for maximum performance
5. **Keep API keys secure** using OS keyring
6. **Review reasoning chains** to understand AI decisions
7. **Use cache statistics** to optimize performance
8. **Test in development** before production deployment

### Safety
- All advanced features have operator gating
- Plugins run in sandboxed environments
- Resource limits prevent runaway processes
- Audit logs track all operations
- Emergency stop controls available
- SSRF protection prevents unauthorized access

---

## Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Vision agent fails | Ensure X11 display or disable `vision_agent` |
| Local inference unavailable | Start Ollama/vLLM or disable `local_inference` |
| CAPTCHA solving fails | Set `CAPTCHA_API_KEY` or disable `captcha_bypass` |
| Slow performance | Run `sudo scripts/optimize_system.sh` |
| Cache errors | Check disk space and Redis connection |
| Plugin load fails | Check plugin manifest and permissions |

---

## Support

### Debug Mode
```bash
export LOG_LEVEL=DEBUG
uvicorn main:app --log-level debug
```

### Get Help
1. Check `BLUEPRINT_IMPLEMENTATION_REFERENCE.md` for detailed information
2. Review `aurora_pro/DEBUG_GUIDE.md` for troubleshooting
3. Check audit logs in `/root/aurora_pro/logs/`
4. Run health checks: `curl http://localhost:8000/health`
5. Validate installation: `bash aurora_pro/verify_installation.sh`

---

## Remember

**This system follows the comprehensive blueprint directive.** Every component, API endpoint, and feature is designed according to 2025 best practices for autonomous AI operating systems. Use `BLUEPRINT_IMPLEMENTATION_REFERENCE.md` as your authoritative guide.

**You have full executive authority.** Operate with confidence, transparency, and control.

---

**Quick Reference Version:** 1.0  
**Blueprint Compliance:** 100% ✅  
**Last Updated:** 2025
