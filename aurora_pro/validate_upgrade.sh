#!/bin/bash
# Aurora Pro Upgrade Validation Script
# Validates all components are properly installed

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Aurora Pro Upgrade Validation Script v3.0.0           ║"
echo "║     Complete AI Automation Toolchain Verification         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0

check_pass() {
    echo "✅ $1"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo "❌ $1"
    ((CHECKS_FAILED++))
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SECTION 1: Python Modules"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Activate venv
source venv/bin/activate 2>/dev/null || true

# Check core modules
for module in enhanced_agent_router vision_agent stealth_browser_agent captcha_manager plugin_manager local_inference multicore_manager cache_manager proxy_manager; do
    if [ -f "${module}.py" ]; then
        if python -m py_compile "${module}.py" 2>/dev/null; then
            check_pass "Module: ${module}.py (syntax valid)"
        else
            check_fail "Module: ${module}.py (syntax error)"
        fi
    else
        check_fail "Module: ${module}.py (not found)"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SECTION 2: Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check critical dependencies
DEPS=("undetected-chromedriver" "selenium-stealth" "2captcha-python" "pytesseract" "aiohttp" "diskcache" "redis" "py-cpuinfo")

for dep in "${DEPS[@]}"; do
    if pip show "$dep" >/dev/null 2>&1; then
        check_pass "Dependency: $dep"
    else
        check_fail "Dependency: $dep (not installed)"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SECTION 3: Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "config/operator_enabled.yaml" ]; then
    check_pass "Config: operator_enabled.yaml exists"

    # Check for new feature flags
    for feature in vision_agent stealth_browsing captcha_bypass plugin_system local_inference proxy_rotation multi_core_processing advanced_caching; do
        if grep -q "$feature:" config/operator_enabled.yaml; then
            check_pass "Config: $feature flag present"
        else
            check_fail "Config: $feature flag missing"
        fi
    done
else
    check_fail "Config: operator_enabled.yaml not found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SECTION 4: Directories"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for dir in logs plugins scripts cache; do
    if [ -d "$dir" ]; then
        check_pass "Directory: $dir/ exists"
    else
        mkdir -p "$dir" 2>/dev/null && check_pass "Directory: $dir/ created" || check_fail "Directory: $dir/ missing"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SECTION 5: Scripts & Executables"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "scripts/optimize_system.sh" ]; then
    check_pass "Script: optimize_system.sh exists"
    if [ -x "scripts/optimize_system.sh" ]; then
        check_pass "Script: optimize_system.sh is executable"
    else
        chmod +x scripts/optimize_system.sh 2>/dev/null && check_pass "Script: optimize_system.sh made executable" || check_fail "Script: optimize_system.sh not executable"
    fi
else
    check_fail "Script: optimize_system.sh not found"
fi

if [ -f "run_aurora.sh" ]; then
    check_pass "Script: run_aurora.sh exists"
else
    check_fail "Script: run_aurora.sh not found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SECTION 6: Test Suite"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for test in test_enhanced_features test_integration test_cli_agent; do
    if [ -f "${test}.py" ]; then
        check_pass "Test: ${test}.py exists"
    else
        check_fail "Test: ${test}.py not found"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SECTION 7: System Requirements"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check CPU cores
CPU_CORES=$(nproc)
if [ "$CPU_CORES" -ge 16 ]; then
    check_pass "CPU: $CPU_CORES cores detected (sufficient)"
else
    check_fail "CPU: $CPU_CORES cores detected (recommend 16+)"
fi

# Check memory
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
if [ "$TOTAL_MEM" -ge 16 ]; then
    check_pass "Memory: ${TOTAL_MEM}GB detected (sufficient)"
else
    check_fail "Memory: ${TOTAL_MEM}GB detected (recommend 16GB+)"
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
if [[ "$PYTHON_VERSION" =~ ^3\.(1[1-9]|[2-9][0-9]) ]]; then
    check_pass "Python: $PYTHON_VERSION (compatible)"
else
    check_fail "Python: $PYTHON_VERSION (recommend 3.11+)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SECTION 8: Optional Components"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Tesseract (for Vision Agent)
if command -v tesseract >/dev/null 2>&1; then
    TESSERACT_VERSION=$(tesseract --version 2>&1 | head -1)
    check_pass "Tesseract: Installed ($TESSERACT_VERSION)"
else
    echo "⚠️  Tesseract: Not installed (required for Vision Agent)"
fi

# Check Ollama (for Local Inference)
if command -v ollama >/dev/null 2>&1; then
    check_pass "Ollama: Installed"
else
    echo "⚠️  Ollama: Not installed (optional for Local Inference)"
fi

# Check Chrome/Chromium (for Stealth Browser)
if command -v google-chrome >/dev/null 2>&1 || command -v chromium >/dev/null 2>&1; then
    check_pass "Chrome/Chromium: Installed"
else
    echo "⚠️  Chrome/Chromium: Not installed (required for Stealth Browser)"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   VALIDATION RESULTS                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "  ✅ Checks Passed: $CHECKS_PASSED"
echo "  ❌ Checks Failed: $CHECKS_FAILED"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  🎉 SUCCESS! All validation checks passed.                ║"
    echo "║                                                            ║"
    echo "║  Aurora Pro upgrade is complete and ready for deployment. ║"
    echo "║                                                            ║"
    echo "║  Next Steps:                                               ║"
    echo "║  1. Review config/operator_enabled.yaml                    ║"
    echo "║  2. Run: sudo ./scripts/optimize_system.sh                 ║"
    echo "║  3. Run: ./run_aurora.sh                                   ║"
    echo "║  4. Test: python test_enhanced_features.py                 ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    exit 0
else
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  ⚠️  ISSUES DETECTED                                       ║"
    echo "║                                                            ║"
    echo "║  Some validation checks failed. Please review the output   ║"
    echo "║  above and resolve any issues before deployment.           ║"
    echo "║                                                            ║"
    echo "║  See DEPLOYMENT_GUIDE.md for troubleshooting.              ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    exit 1
fi