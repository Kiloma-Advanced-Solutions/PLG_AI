#!/bin/bash

# MCP Workshop - Start Script

echo "🚀 Starting MCP Workshop..."
echo "=============================================================="

# Function to check if a URL is responding
check_server() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "^[0-9]"; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    echo "❌ $name failed to start"
    return 1
}

# Check if Python virtual environment exists
if [ ! -d "myenv" ]; then
    python3 -m venv myenv
    myenv/bin/pip install -r requirements.txt
fi

# Check if user wants to run workshop or solution
MODE=${1:-workshop}

# Start TypeScript MCP Server
if [ "$MODE" == "solution" ]; then
    npm run start:solution > /tmp/ts_mcp.log 2>&1 &
    TS_PID=$!
else
    npm run start:workshop > /tmp/ts_mcp.log 2>&1 &
    TS_PID=$!
fi

# Start Python MCP Server
myenv/bin/python python_mcp_server.py > /tmp/python_mcp.log 2>&1 &
PY_PID=$!

# Start Chat API
myenv/bin/python -m uvicorn chat_api:app --host 0.0.0.0 --port 8001 > /tmp/chat_api.log 2>&1 &
API_PID=$!

# Start Frontend in background
cd frontend && npm start > /tmp/frontend.log 2>&1 &
FE_PID=$!
cd ..

# Wait for each server to be ready
check_server "http://localhost:8000/health" "TypeScript MCP Server" && echo "✅ TypeScript MCP Server (port 8000)"
check_server "http://localhost:8001/health" "Chat API" && echo "✅ Chat API (port 8001)"
check_server "http://localhost:8002/mcp" "Python MCP Server" && echo "✅ Python MCP Server (port 8002)"
check_server "http://localhost:3000" "Frontend" && echo "✅ Chat UI (port 3000)"

# Open browser to the UI
open http://localhost:3000

# Wait for Ctrl+C, then kill all processes
trap "kill $TS_PID $PY_PID $API_PID $FE_PID 2>/dev/null; wait; exit" INT

# Keep script running
wait
