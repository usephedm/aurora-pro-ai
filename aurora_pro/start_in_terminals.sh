#!/bin/bash
# Start Aurora Pro in external terminals

cd /root/aurora_pro

echo "Starting Aurora Pro in external terminals..."
echo ""
echo "This will open 2 terminal windows:"
echo "  1. API Server (port 8000)"
echo "  2. Test Runner"
echo ""

# Kill any existing instances
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 2

# Start API in new terminal
x-terminal-emulator -e bash -c "
    cd /root/aurora_pro
    source venv/bin/activate
    echo '╔═══════════════════════════════════════════════════════════════════════════╗'
    echo '║                    AURORA PRO API SERVER                                  ║'
    echo '║                    http://localhost:8000                                  ║'
    echo '╚═══════════════════════════════════════════════════════════════════════════╝'
    echo ''
    echo 'Starting API server...'
    echo ''
    python -m uvicorn main:app --host 0.0.0.0 --port 8000
    echo ''
    echo 'Press Enter to close...'
    read
" &

echo "✓ API server starting in new terminal..."
sleep 5

# Start test runner in another terminal
x-terminal-emulator -e bash -c "
    cd /root/aurora_pro
    source venv/bin/activate
    echo '╔═══════════════════════════════════════════════════════════════════════════╗'
    echo '║                    AURORA PRO TEST RUNNER                                 ║'
    echo '╚═══════════════════════════════════════════════════════════════════════════╝'
    echo ''
    echo 'Waiting for API to be ready...'
    sleep 3

    # Wait for API to be ready
    for i in {1..30}; do
        if curl -s http://localhost:8000/health/status >/dev/null 2>&1; then
            echo '✓ API is ready!'
            break
        fi
        echo \"  Waiting for API... (\$i/30)\"
        sleep 1
    done

    echo ''
    echo 'Running comprehensive tests...'
    echo ''
    python real_world_test.py

    echo ''
    echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
    echo 'Additional manual tests you can run:'
    echo ''
    echo '  # Test enhanced router'
    echo '  curl http://localhost:8000/router/status | jq'
    echo ''
    echo '  # Test cache stats'
    echo '  curl http://localhost:8000/cache/stats | jq'
    echo ''
    echo '  # Test multi-core'
    echo '  curl http://localhost:8000/multicore/stats | jq'
    echo ''
    echo '  # View API docs'
    echo '  open http://localhost:8000/docs'
    echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
    echo ''
    echo 'Press Enter to close...'
    read
" &

echo "✓ Test runner starting in new terminal..."
echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║  Aurora Pro is starting in external terminals!                           ║"
echo "║                                                                           ║"
echo "║  You should now see:                                                      ║"
echo "║    • API Server terminal (port 8000)                                      ║"
echo "║    • Test Runner terminal (running tests)                                 ║"
echo "║                                                                           ║"
echo "║  If terminals don't appear:                                               ║"
echo "║    • Check if x-terminal-emulator is installed                            ║"
echo "║    • Or run manually:                                                     ║"
echo "║      Terminal 1: ./run_aurora.sh                                          ║"
echo "║      Terminal 2: python real_world_test.py                                ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""