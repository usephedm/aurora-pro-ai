#!/bin/bash
# Aurora Pro - Installation Verification Script
# Checks that all Stage 3 components are present and configured

echo "=========================================="
echo "Aurora Pro - Installation Verification"
echo "Stage 3: Full Autonomy & Self-Healing"
echo "=========================================="
echo ""

PASS=0
FAIL=0

check_file() {
    if [ -f "$1" ]; then
        echo "✓ $1"
        ((PASS++))
    else
        echo "✗ MISSING: $1"
        ((FAIL++))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo "✓ $1/"
        ((PASS++))
    else
        echo "✗ MISSING: $1/"
        ((FAIL++))
    fi
}

echo "[Core Modules]"
check_file "cli_agent.py"
check_file "mouse_keyboard_agent.py"
check_file "heartbeat_monitor.py"
check_file "ai_coordinator.py"
check_file "main.py"
check_file "aurora_dashboard.py"
echo ""

echo "[Test Suites]"
check_file "test_cli_agent.py"
check_file "test_input_agent.py"
check_file "test_input_agent_comprehensive.py"
check_file "test_integration.py"
echo ""

echo "[Documentation]"
check_file "README.md"
check_file "IMPLEMENTATION_COMPLETE.md"
check_file "STAGE3_COMPLETE.md"
check_file "MANUAL_TEST_PLAN.md"
check_file "QUICK_REFERENCE.md"
echo ""

echo "[Configuration]"
check_dir "config"
check_file "config/operator_enabled.yaml"
echo ""

echo "[Directories]"
check_dir "logs"
check_dir "logs/tasks"
check_dir "venv"
echo ""

echo "[Python Dependencies]"
source venv/bin/activate 2>/dev/null
if command -v python &> /dev/null; then
    echo "✓ Python venv activated"
    ((PASS++))

    # Check key dependencies
    python -c "import aiofiles" 2>/dev/null && echo "✓ aiofiles" && ((PASS++)) || (echo "✗ aiofiles" && ((FAIL++)))
    python -c "import yaml" 2>/dev/null && echo "✓ PyYAML" && ((PASS++)) || (echo "✗ PyYAML" && ((FAIL++)))
    python -c "import fastapi" 2>/dev/null && echo "✓ FastAPI" && ((PASS++)) || (echo "✗ FastAPI" && ((FAIL++)))
    python -c "import streamlit" 2>/dev/null && echo "✓ Streamlit" && ((PASS++)) || (echo "✗ Streamlit" && ((FAIL++)))

    # Check pyautogui (may fail if no display)
    python -c "import pyautogui" 2>/dev/null && echo "✓ pyautogui (input agent available)" && ((PASS++)) || echo "⚠ pyautogui (input agent will be disabled)"
else
    echo "✗ Python venv not activated"
    ((FAIL++))
fi
echo ""

echo "[Configuration Check]"
if [ -f "config/operator_enabled.yaml" ]; then
    ENABLED=$(grep "^operator_enabled:" config/operator_enabled.yaml | awk '{print $2}')
    MOUSE_KB=$(grep "control_mouse_keyboard:" config/operator_enabled.yaml | awk '{print $2}')

    echo "operator_enabled: $ENABLED"
    echo "control_mouse_keyboard: $MOUSE_KB"

    if [ "$ENABLED" = "true" ] && [ "$MOUSE_KB" = "true" ]; then
        echo "⚠ Input control is ENABLED (will control real hardware)"
    else
        echo "✓ Input control is disabled (safe mode)"
    fi
fi
echo ""

echo "=========================================="
echo "Results: $PASS passed, $FAIL failed"

if [ $FAIL -eq 0 ]; then
    echo "✓ Installation verified successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Start system: ./run_aurora.sh"
    echo "  2. Run tests: python test_integration.py"
    echo "  3. View docs: cat QUICK_REFERENCE.md"
    exit 0
else
    echo "✗ Installation incomplete ($FAIL issues found)"
    echo ""
    echo "Please review missing files/dependencies above"
    exit 1
fi