#!/bin/bash
# Verification script for Aurora Pro upgrade

echo "=============================================="
echo "Aurora Pro Upgrade Verification"
echo "=============================================="
echo ""

PASS=0
FAIL=0

check_file() {
    if [ -f "$1" ]; then
        echo "✓ $1"
        ((PASS++))
    else
        echo "✗ $1 MISSING"
        ((FAIL++))
    fi
}

echo "[1] Checking new agent files..."
check_file "/root/aurora_pro/vision_agent.py"
check_file "/root/aurora_pro/stealth_browser_agent.py"
check_file "/root/aurora_pro/captcha_manager.py"
check_file "/root/aurora_pro/plugin_manager.py"
check_file "/root/aurora_pro/multicore_manager.py"
check_file "/root/aurora_pro/cache_manager.py"
check_file "/root/aurora_pro/proxy_manager.py"
check_file "/root/aurora_pro/local_inference.py"

echo ""
echo "[2] Checking test and documentation files..."
check_file "/root/aurora_pro/test_enhanced_features.py"
check_file "/root/aurora_pro/scripts/optimize_system.sh"
check_file "/root/aurora_pro/AURORA_PRO_UPGRADE_COMPLETE.md"

echo ""
echo "[3] Checking configuration..."
check_file "/root/aurora_pro/config/operator_enabled.yaml"

echo ""
echo "[4] Checking directories..."
if [ -d "/root/aurora_pro/plugins" ]; then
    echo "✓ /root/aurora_pro/plugins/"
    ((PASS++))
else
    echo "✗ /root/aurora_pro/plugins/ MISSING"
    ((FAIL++))
fi

if [ -d "/root/aurora_pro/scripts" ]; then
    echo "✓ /root/aurora_pro/scripts/"
    ((PASS++))
else
    echo "✗ /root/aurora_pro/scripts/ MISSING"
    ((FAIL++))
fi

echo ""
echo "[5] Checking Python imports..."
cd /root/aurora_pro
source venv/bin/activate 2>/dev/null

if python3 -c "from vision_agent import get_vision_agent" 2>/dev/null; then
    echo "✓ vision_agent imports correctly"
    ((PASS++))
else
    echo "✗ vision_agent import failed"
    ((FAIL++))
fi

if python3 -c "from stealth_browser_agent import get_stealth_browser" 2>/dev/null; then
    echo "✓ stealth_browser_agent imports correctly"
    ((PASS++))
else
    echo "✗ stealth_browser_agent import failed"
    ((FAIL++))
fi

if python3 -c "from captcha_manager import get_captcha_manager" 2>/dev/null; then
    echo "✓ captcha_manager imports correctly"
    ((PASS++))
else
    echo "✗ captcha_manager import failed"
    ((FAIL++))
fi

if python3 -c "from plugin_manager import get_plugin_manager" 2>/dev/null; then
    echo "✓ plugin_manager imports correctly"
    ((PASS++))
else
    echo "✗ plugin_manager import failed"
    ((FAIL++))
fi

if python3 -c "from multicore_manager import get_multicore_manager" 2>/dev/null; then
    echo "✓ multicore_manager imports correctly"
    ((PASS++))
else
    echo "✗ multicore_manager import failed"
    ((FAIL++))
fi

if python3 -c "from cache_manager import get_cache_manager" 2>/dev/null; then
    echo "✓ cache_manager imports correctly"
    ((PASS++))
else
    echo "✗ cache_manager import failed"
    ((FAIL++))
fi

if python3 -c "from proxy_manager import get_proxy_manager" 2>/dev/null; then
    echo "✓ proxy_manager imports correctly"
    ((PASS++))
else
    echo "✗ proxy_manager import failed"
    ((FAIL++))
fi

if python3 -c "from local_inference import get_local_inference" 2>/dev/null; then
    echo "✓ local_inference imports correctly"
    ((PASS++))
else
    echo "✗ local_inference import failed"
    ((FAIL++))
fi

echo ""
echo "[6] Checking configuration values..."
if grep -q "vision_agent:" /root/aurora_pro/config/operator_enabled.yaml; then
    echo "✓ vision_agent feature flag present"
    ((PASS++))
else
    echo "✗ vision_agent feature flag missing"
    ((FAIL++))
fi

if grep -q "stealth_browsing:" /root/aurora_pro/config/operator_enabled.yaml; then
    echo "✓ stealth_browsing feature flag present"
    ((PASS++))
else
    echo "✗ stealth_browsing feature flag missing"
    ((FAIL++))
fi

if grep -q "multi_core_processing:" /root/aurora_pro/config/operator_enabled.yaml; then
    echo "✓ multi_core_processing feature flag present"
    ((PASS++))
else
    echo "✗ multi_core_processing feature flag missing"
    ((FAIL++))
fi

echo ""
echo "[7] Checking script permissions..."
if [ -x "/root/aurora_pro/scripts/optimize_system.sh" ]; then
    echo "✓ optimize_system.sh is executable"
    ((PASS++))
else
    echo "✗ optimize_system.sh is not executable"
    ((FAIL++))
fi

echo ""
echo "=============================================="
echo "Verification Results"
echo "=============================================="
echo "PASSED: $PASS"
echo "FAILED: $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "✅ All checks passed! Aurora Pro upgrade is complete."
    echo ""
    echo "Next steps:"
    echo "1. Run system optimization: sudo /root/aurora_pro/scripts/optimize_system.sh"
    echo "2. Install dependencies: pip install mss pytesseract diskcache redis"
    echo "3. Configure Ollama: curl -fsSL https://ollama.com/install.sh | sh"
    echo "4. Enable features in: /root/aurora_pro/config/operator_enabled.yaml"
    echo "5. Start Aurora: uvicorn main:app --host 0.0.0.0 --port 8000"
    echo "6. Run tests: pytest test_enhanced_features.py -v"
    exit 0
else
    echo "❌ Some checks failed. Please review the errors above."
    exit 1
fi