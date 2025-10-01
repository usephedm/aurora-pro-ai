#!/bin/bash
# Aurora Pro v3.0.0 - Quick Start Script

clear
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                           ║"
echo "║              🚀 AURORA PRO V3.0.0 - QUICK START 🚀                       ║"
echo "║                                                                           ║"
echo "║        Advanced AI Automation Toolchain - Production Ready               ║"
echo "║                                                                           ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "This script will guide you through the deployment process."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  STEP 1: VALIDATE INSTALLATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "./validate_upgrade.sh" ]; then
    read -p "Run validation script? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./validate_upgrade.sh
    fi
else
    echo "⚠️  validate_upgrade.sh not found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  STEP 2: OPTIMIZE SYSTEM (Recommended)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "This will optimize your 32-core i9 for maximum performance:"
echo "  • Set CPU governor to 'performance'"
echo "  • Enable Turbo Boost"
echo "  • Optimize memory and network settings"
echo ""

if [ -f "./scripts/optimize_system.sh" ]; then
    read -p "Run system optimization? (requires sudo) (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo ./scripts/optimize_system.sh
    fi
else
    echo "⚠️  scripts/optimize_system.sh not found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  STEP 3: CONFIGURE FEATURES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Current feature status:"
echo ""
grep -A 20 "^features:" config/operator_enabled.yaml | grep -v "^#"
echo ""

read -p "Edit configuration? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    nano config/operator_enabled.yaml
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  STEP 4: START AURORA PRO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Starting Aurora Pro with all components..."
echo ""

if [ -f "./run_aurora.sh" ]; then
    read -p "Start Aurora Pro now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Starting Aurora Pro..."
        echo "  • API: http://localhost:8000"
        echo "  • Dashboard: http://localhost:8501"
        echo "  • Docs: http://localhost:8000/docs"
        echo ""
        echo "Press Ctrl+C to stop"
        echo ""
        sleep 2
        ./run_aurora.sh
    fi
else
    echo "⚠️  run_aurora.sh not found"
    echo ""
    echo "Manual start:"
    echo "  source venv/bin/activate"
    echo "  uvicorn main:app --host 0.0.0.0 --port 8000"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📚 NEXT STEPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Read these files for more information:"
echo ""
echo "  • NEXT_STEPS.md              - Quick start guide"
echo "  • DEPLOYMENT_GUIDE.md        - Complete deployment guide"
echo "  • FINAL_SUMMARY.txt          - What was implemented"
echo ""
echo "Test the system:"
echo ""
echo "  curl http://localhost:8000/health/status | jq"
echo "  curl http://localhost:8000/router/status | jq"
echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                           ║"
echo "║                    ✅ AURORA PRO IS READY! ✅                            ║"
echo "║                                                                           ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
