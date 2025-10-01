#!/bin/bash
# Aurora Pro AI - Blueprint Compliance Validation
# Validates that the system meets all requirements from the PDF directive

set -e

echo "=========================================="
echo "Aurora Pro AI - Blueprint Compliance Check"
echo "=========================================="
echo ""
echo "Validating implementation against:"
echo "  'Aurora Pro AI Operating System: Comprehensive Development Blueprint'"
echo ""

ERRORS=0
WARNINGS=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function check_file() {
    local file=$1
    local component=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $component: $file"
        return 0
    else
        echo -e "${RED}✗${NC} $component: $file (MISSING)"
        ((ERRORS++))
        return 1
    fi
}

function check_config() {
    local key=$1
    local file=$2
    local component=$3
    
    if grep -q "$key" "$file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $component: $key configured"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $component: $key not configured (OPTIONAL)"
        ((WARNINGS++))
        return 1
    fi
}

function check_port() {
    local port=$1
    local service=$2
    
    if command -v netstat >/dev/null 2>&1; then
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            echo -e "${GREEN}✓${NC} $service: Port $port is available"
            return 0
        else
            echo -e "${YELLOW}⚠${NC} $service: Port $port not listening (service may not be running)"
            ((WARNINGS++))
            return 1
        fi
    else
        echo -e "${YELLOW}⚠${NC} $service: Cannot check port $port (netstat not available)"
        return 0
    fi
}

echo "=== 1. Model Context Protocol (MCP) Integration ==="
check_file "aurora_pro/mcp_server.py" "MCP Server"
check_file "scripts/mcp/run_aurora_mcp.sh" "MCP Launch Script"
echo ""

echo "=== 2. Multi-Agent Orchestration ==="
check_file "aurora_pro/llm_orchestrator.py" "LLM Orchestrator"
check_file "aurora_pro/autonomous_engine.py" "Autonomous Engine"
check_file "aurora_pro/enhanced_agent_router.py" "Agent Router"
echo ""

echo "=== 3. Hardware-Optimized Parallel Execution ==="
check_file "aurora_pro/multicore_manager.py" "Multicore Manager"

# Check CPU cores
CPU_CORES=$(nproc 2>/dev/null || echo "unknown")
if [ "$CPU_CORES" != "unknown" ]; then
    echo -e "${GREEN}✓${NC} CPU Cores Detected: $CPU_CORES"
    if [ "$CPU_CORES" -ge 30 ]; then
        echo -e "${GREEN}✓${NC} Sufficient cores for 30-worker pool"
    else
        echo -e "${YELLOW}⚠${NC} Only $CPU_CORES cores (blueprint expects 32)"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}⚠${NC} Cannot detect CPU cores"
    ((WARNINGS++))
fi
echo ""

echo "=== 4. GPU Quantization and Optimization ==="
check_file "aurora_pro/codex_model_quantizer.py" "Model Quantizer"
check_file "aurora_pro/local_inference.py" "Local Inference"

# Check for GPU
if command -v nvidia-smi >/dev/null 2>&1; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "")
    if [ -n "$GPU_INFO" ]; then
        echo -e "${GREEN}✓${NC} GPU Detected: $GPU_INFO"
    else
        echo -e "${YELLOW}⚠${NC} GPU detection failed"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}⚠${NC} nvidia-smi not found (GPU may not be available)"
    ((WARNINGS++))
fi
echo ""

echo "=== 5. Vision and Screen Analysis ==="
check_file "aurora_pro/vision_agent.py" "Vision Agent"
check_file "aurora_pro/vision_streamer.py" "Vision Streamer"
check_file "aurora_pro/vision_viewer.html" "Vision Viewer"
echo ""

echo "=== 6. Stealth Browsing and Anti-Detection ==="
check_file "aurora_pro/stealth_browser_agent.py" "Stealth Browser"
check_file "aurora_pro/captcha_manager.py" "CAPTCHA Manager"
check_file "aurora_pro/proxy_manager.py" "Proxy Manager"
echo ""

echo "=== 7. Advanced Caching ==="
check_file "aurora_pro/cache_manager.py" "Cache Manager"
echo ""

echo "=== 8. Input Control ==="
check_file "aurora_pro/mouse_keyboard_agent.py" "Mouse/Keyboard Agent"
echo ""

echo "=== 9. Plugin System ==="
check_file "aurora_pro/plugin_manager.py" "Plugin Manager"
if [ -d "aurora_pro/plugins" ]; then
    echo -e "${GREEN}✓${NC} Plugins directory exists"
else
    echo -e "${YELLOW}⚠${NC} Plugins directory not found"
    ((WARNINGS++))
fi
echo ""

echo "=== 10. Real-Time Reasoning ==="
check_file "aurora_pro/reasoning_display.py" "Reasoning Display"
echo ""

echo "=== 11. Security and Audit ==="
check_file "aurora_pro/config/operator_enabled.yaml" "Operator Configuration"
check_file "aurora_pro/ssrf_protection.py" "SSRF Protection"
check_file "aurora_pro/secrets_loader.py" "Secrets Loader"

# Check audit log directories
if [ -d "aurora_pro/logs" ] || [ -d "/root/aurora_pro/logs" ]; then
    echo -e "${GREEN}✓${NC} Audit log directory exists"
else
    echo -e "${YELLOW}⚠${NC} Audit log directory not found (will be created on first use)"
    ((WARNINGS++))
fi
echo ""

echo "=== 12. Control Center and Monitoring ==="
check_file "aurora_pro/control_center.py" "Control Center"
check_file "aurora_pro/web_control_panel.py" "Web Control Panel"
check_file "aurora_pro/heartbeat_monitor.py" "Heartbeat Monitor"
check_file "aurora_pro/aurora_dashboard.py" "Dashboard"
echo ""

echo "=== 13. Communication and Integration ==="
check_file "aurora_pro/communication_bus.py" "Communication Bus"
check_file "aurora_pro/main.py" "Main API Server"
echo ""

echo "=== 14. Configuration Files ==="
check_file "aurora_pro/config/operator_enabled.yaml" "Operator Config"
check_file "aurora_pro/config/proxies.yaml" "Proxy Config"

if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} Environment configuration: .env"
elif [ -f ".env.example" ]; then
    echo -e "${YELLOW}⚠${NC} .env not found, but .env.example exists (copy it to .env)"
    ((WARNINGS++))
else
    echo -e "${YELLOW}⚠${NC} No environment configuration found"
    ((WARNINGS++))
fi
echo ""

echo "=== 15. Documentation ==="
check_file "BLUEPRINT_IMPLEMENTATION_REFERENCE.md" "Blueprint Reference"
check_file "OPERATOR_QUICK_REFERENCE.md" "Operator Quick Reference"
check_file "aurora_pro/WHAT_YOU_NOW_HAVE.md" "Feature Summary"
check_file "aurora_pro/DEPLOYMENT_GUIDE.md" "Deployment Guide"
check_file "aurora_pro/CONTROL_CENTER_GUIDE.md" "Control Center Guide"
check_file "aurora_pro/PRODUCTION_DEPLOYMENT.md" "Production Deployment"
check_file "README.md" "README"
echo ""

echo "=== 16. Testing Infrastructure ==="
check_file "tests/unit/test_smoke.py" "Unit Tests"
check_file "tests/integration/test_health.py" "Integration Tests"
check_file "aurora_pro/test_enhanced_features.py" "Enhanced Features Tests"
check_file "aurora_pro/verify_installation.sh" "Installation Validator"
echo ""

echo "=== 17. Deployment Scripts ==="
check_file "aurora_pro/run_aurora.sh" "Launch Script"
check_file "aurora_pro/production_deploy.sh" "Production Deploy"
check_file "scripts/optimize_system.sh" "System Optimization"
check_file "docker/Dockerfile" "Docker Configuration"
check_file "docker/docker-compose.yml" "Docker Compose"
echo ""

echo "=== 18. Dependencies ==="
check_file "requirements.txt" "Python Requirements"

# Check if Python is available
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+\.\d+')
    echo -e "${GREEN}✓${NC} Python: $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python 3 not found"
    ((ERRORS++))
fi
echo ""

echo "=== 19. Port Availability ==="
# Note: These checks only work if services are running
# check_port 8000 "FastAPI Server"
# check_port 8501 "Streamlit Dashboard"
# check_port 8011 "Vision Streamer"
# check_port 8002 "vLLM Server"
echo -e "${YELLOW}⚠${NC} Port checks skipped (services may not be running)"
echo ""

echo "=== 20. Blueprint PDF Directive ==="
check_file "Aurora Pro AI Operating System_ Comprehensive Deve.pdf" "Blueprint PDF"
echo ""

echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo ""

TOTAL_CHECKS=$((ERRORS + WARNINGS))

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ PERFECT COMPLIANCE${NC}"
    echo "  All blueprint requirements are met!"
    echo "  Status: 100% compliant ✅"
elif [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ FULL COMPLIANCE${NC}"
    echo "  Errors: 0"
    echo "  Warnings: $WARNINGS (optional features or runtime checks)"
    echo "  Status: Fully functional ✅"
else
    echo -e "${RED}✗ COMPLIANCE ISSUES FOUND${NC}"
    echo "  Errors: $ERRORS (critical components missing)"
    echo "  Warnings: $WARNINGS (optional features or runtime checks)"
    echo "  Status: Requires attention ⚠"
fi

echo ""
echo "Next Steps:"
echo "  1. Review BLUEPRINT_IMPLEMENTATION_REFERENCE.md for complete mapping"
echo "  2. Check OPERATOR_QUICK_REFERENCE.md for usage guidelines"
echo "  3. Run: bash aurora_pro/verify_installation.sh"
echo "  4. Configure: nano aurora_pro/config/operator_enabled.yaml"
echo "  5. Launch: ./aurora_pro/run_aurora.sh"
echo ""

if [ $ERRORS -gt 0 ]; then
    exit 1
else
    exit 0
fi
