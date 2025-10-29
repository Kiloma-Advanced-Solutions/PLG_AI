#!/bin/bash

# Start all MCP servers and wait for them to be ready
echo "🚀 Starting MCP Chat Workshop..."
echo "=============================================================="

# Function to check if a URL is responding
check_server() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        # Check if server responds (any HTTP response means server is up)
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "^[0-9]"; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    echo "❌ $name failed to start"
    return 1
}

# Start TypeScript MCP Server in background
echo "▶️  Starting TypeScript MCP Server (port 8000)..."
npm run dev > /tmp/ts_mcp.log 2>&1 &
TS_PID=$!

# Start Python MCP Server in background
echo "▶️  Starting Python MCP Server (port 8002)..."
myenv/bin/python python_mcp_server.py > /tmp/python_mcp.log 2>&1 &
PY_PID=$!

# Start Chat API in background
echo "▶️  Starting Chat API (port 8001)..."
myenv/bin/python -m uvicorn chat_api:app --reload --port 8001 > /tmp/chat_api.log 2>&1 &
API_PID=$!

# Start Frontend in background
echo "▶️  Starting Frontend (port 3000)..."
cd frontend && npm start > /tmp/frontend.log 2>&1 &
FE_PID=$!
cd ..

echo ""
echo "⏳ Waiting for servers to start..."
echo ""

# Wait for each server to be ready
check_server "http://localhost:8000/health" "TypeScript MCP Server" && echo "✅ TypeScript MCP Server (port 8000)"
check_server "http://localhost:8002/mcp" "Python MCP Server" && echo "✅ Python MCP Server (port 8002)"
check_server "http://localhost:8001/health" "Chat API" && echo "✅ Chat API (port 8001)"
check_server "http://localhost:3000" "Frontend" && echo "✅ Frontend (port 3000)"

echo ""
echo "================================"
echo "✅ All servers are up and running!"
echo "================================"
echo ""
echo "📝 Logs:"
echo "  TypeScript MCP: tail -f /tmp/ts_mcp.log"
echo "  Python MCP:     tail -f /tmp/python_mcp.log"
echo "  Chat API:       tail -f /tmp/chat_api.log"
echo "  Frontend:       tail -f /tmp/frontend.log"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for Ctrl+C, then kill all processes
trap "echo ''; echo 'Stopping all servers...'; kill $TS_PID $PY_PID $API_PID $FE_PID 2>/dev/null; wait; echo 'All servers stopped.'; exit" INT

# Keep script running
wait
