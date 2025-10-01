#!/bin/bash
# Aurora Pro - FINAL PRODUCTION LAUNCH
# Complete system with all new features

set -e

cd /root/aurora_pro

echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                           ║"
echo "║              AURORA PRO V3.0 - PRODUCTION LAUNCH                         ║"
echo "║              Complete Autonomous AI System                                ║"
echo "║                                                                           ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Kill existing processes
echo "Cleaning up existing processes..."
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "streamlit run" 2>/dev/null || true
sleep 2

# Activate venv
source venv/bin/activate

echo ""
echo "Starting Aurora Pro components..."
echo ""

# Start API server in new terminal
echo "🚀 Starting API Server (port 8000)..."
x-terminal-emulator -e bash -c "
    cd /root/aurora_pro
    source venv/bin/activate
    clear
    echo '╔═══════════════════════════════════════════════════════════════════════════╗'
    echo '║                    AURORA PRO API SERVER                                  ║'
    echo '║                    http://localhost:8000                                  ║'
    echo '║                    http://localhost:8000/docs (Swagger UI)               ║'
    echo '╚═══════════════════════════════════════════════════════════════════════════╝'
    echo ''
    echo 'API Endpoints:'
    echo '  • Core: /health/status, /metrics'
    echo '  • LLM Orchestrator: /llm/generate, /llm/stats'
    echo '  • Autonomous Engine: /autonomous/execute'
    echo '  • Reasoning Display: /reasoning/steps'
    echo '  • Control Center: /control/metrics, /control/emergency-stop'
    echo '  • Vision: /vision/analyze'
    echo '  • Cache: /cache/stats'
    echo '  • Multi-core: /multicore/stats'
    echo ''
    echo 'Starting server...'
    echo ''
    python -m uvicorn main:app --host 0.0.0.0 --port 8000
    echo ''
    echo 'Press Enter to close...'
    read
" &
sleep 5

# Start Web Control Panel in new terminal
echo "🎛️  Starting Web Control Panel (port 8501)..."
x-terminal-emulator -e bash -c "
    cd /root/aurora_pro
    source venv/bin/activate
    clear
    echo '╔═══════════════════════════════════════════════════════════════════════════╗'
    echo '║                    AURORA PRO CONTROL PANEL                              ║'
    echo '║                    http://localhost:8501                                  ║'
    echo '╚═══════════════════════════════════════════════════════════════════════════╝'
    echo ''
    echo 'Features:'
    echo '  • 🎯 BIG RED STOP BUTTON'
    echo '  • 📊 Live System Metrics'
    echo '  • 🤖 LLM Orchestrator Control'
    echo '  • 🔄 Autonomous Task Execution'
    echo '  • 🧠 Real-time Reasoning Display'
    echo '  • 📈 Performance Analytics'
    echo ''
    echo 'Starting web UI...'
    echo ''
    streamlit run web_control_panel.py --server.port 8501 --server.address 0.0.0.0
    echo ''
    echo 'Press Enter to close...'
    read
" &
sleep 3

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ AURORA PRO IS LIVE! ✅                              ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📡 Services Running:"
echo "   • API Server: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Control Panel: http://localhost:8501"
echo ""
echo "🔧 Quick Tests:"
echo "   curl http://localhost:8000/health/status | jq"
echo "   curl http://localhost:8000/control/metrics | jq"
echo "   curl http://localhost:8000/llm/status | jq"
echo ""
echo "📚 Documentation:"
echo "   • FULL_SYSTEM_AUDIT_REPORT.md"
echo "   • CONTROL_CENTER_GUIDE.md"
echo "   • PRODUCTION_DEPLOYMENT.md"
echo ""
echo "🎯 What You Can Do:"
echo "   1. Open http://localhost:8501 in your browser"
echo "   2. Use the LLM selector to choose AI models"
echo "   3. Submit autonomous tasks"
echo "   4. Watch real-time reasoning"
echo "   5. Monitor system metrics"
echo "   6. Hit the STOP button if needed"
echo ""
echo "System ready for production use! 🚀"
echo ""