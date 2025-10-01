#!/bin/bash

# Aurora Pro AI - Local Development Script
set -e

echo "🚀 Starting Aurora Pro AI (Development Mode)"
echo "============================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create data directory
mkdir -p data

# Start Redis in background if not running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis..."
    redis-server --daemonize yes
fi

# Export environment variables
export REDIS_HOST=localhost
export DATABASE_URL=sqlite:///./data/aurora.db
export OLLAMA_BASE_URL=http://localhost:11434

# Start API in background
echo "Starting FastAPI backend..."
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# Wait for API to start
sleep 3

# Start Streamlit GUI
echo "Starting Streamlit GUI..."
streamlit run src/gui/app.py --server.port 8501 &
GUI_PID=$!

echo ""
echo "============================================"
echo "✅ Aurora Pro AI started successfully!"
echo "============================================"
echo ""
echo "Access:"
echo "  FastAPI: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Streamlit: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Trap Ctrl+C and cleanup
trap "echo 'Stopping services...'; kill $API_PID $GUI_PID; exit" INT

# Wait for processes
wait
