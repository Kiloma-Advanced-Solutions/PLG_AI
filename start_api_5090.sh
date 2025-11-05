#!/usr/bin/env bash

set -euo pipefail

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$SCRIPT_DIR/llm-api"

# Activate the venv created by setup_venv_5090.sh (in repo root)
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Defaults (can be overridden via env)
LLM_API_HOST=${LLM_API_HOST:-0.0.0.0}
LLM_API_PORT=${LLM_API_PORT:-8090}
LLM_API_LOG_LEVEL=${LLM_API_LOG_LEVEL:-INFO}
VLLM_PORT=${LLM_API_VLLM_PORT:-8060}
MODEL=${LLM_API_LLM_MODEL_NAME:-${LLM_API_MODEL_NAME:-gaunernst/gemma-3-12b-it-qat-autoawq}}
MODE="${1:-dev}"  # dev | prod
OPENAI_LOG=${OPENAI_LOG:-debug}
OPENAI_AGENTS_DEBUG=${OPENAI_AGENTS_DEBUG:-1}

export OPENAI_LOG
export OPENAI_AGENTS_DEBUG

# Stop any existing vLLM server
stop_vllm() {
    pkill -f "vllm serve" >/dev/null 2>&1 || true
    pkill -f "vllm.entrypoints.openai.api_server" >/dev/null 2>&1 || true
}

# Stop any existing MCP servers
stop_mcp() {
    pkill -f "mcp_server.py" >/dev/null 2>&1 || true
    pkill -f "mcp_server1.py" >/dev/null 2>&1 || true
}

# Ensure cleanup on exit
trap 'stop_vllm; stop_mcp' INT TERM EXIT

stop_vllm
stop_mcp

# Start vLLM server
start_vllm() {
    python -m vllm.entrypoints.openai.api_server \
        --model "$MODEL" \
        --max-model-len 16384 \
        --port "$VLLM_PORT" \
        --gpu-memory-utilization 0.9 \
        --disable-log-requests \
        --enable-auto-tool-choice \
        --tool-call-parser pythonic &

    echo "Waiting for vLLM to start..."
    for i in {1..1200}; do
        if curl -s -X POST "http://localhost:${VLLM_PORT}/v1/chat/completions" \
            -H "Content-Type: application/json" \
            -d '{"model":"'"$MODEL"'","messages":[{"role":"user","content":"היי"}],"max_tokens":1}' \
            >/dev/null 2>&1; then
            echo "✅ vLLM is ready!"
            break
        fi
        if [ $i -eq 1200 ]; then
            echo "❌ vLLM failed to start after 20 minutes"
            return 1
        fi
        sleep 1
    done
}
start_vllm

# Start MCP servers
start_mcp() {
    cd "$API_DIR"
    python mcp_servers/mcp_server.py &
    MCP_PID1=$!
    python mcp_servers/mcp_server1.py &
    MCP_PID2=$!

    echo "Waiting for MCP servers to start..."
    MCP_PORT1=${LLM_API_MCP_PORT:-8000}
    MCP_PORT2=${LLM_API_MCP_PORT2:-8001}

    # Wait for first MCP server
    for i in {1..30}; do
        if nc -z localhost "$MCP_PORT1" 2>/dev/null; then
            echo "✅ MCP server (mcp_server.py) is ready on port $MCP_PORT1!"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "❌ MCP server (mcp_server.py) failed to start after 30 seconds"
            return 1
        fi
        sleep 1
    done

    # Wait for second MCP server
    for i in {1..30}; do
        if nc -z localhost "$MCP_PORT2" 2>/dev/null; then
            echo "✅ MCP server (mcp_server1.py) is ready on port $MCP_PORT2!"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "❌ MCP server (mcp_server1.py) failed to start after 30 seconds"
            return 1
        fi
        sleep 1
    done
}
start_mcp

# Run API from llm-api directory
cd "$API_DIR"

if [ ! -f "main.py" ]; then
    echo "main.py not found in ${API_DIR}" >&2
    exit 1
fi

MCP_PORT1=${LLM_API_MCP_PORT:-8000}
MCP_PORT2=${LLM_API_MCP_PORT2:-8001}
echo "🚀 All services running:"
echo "  • API:  http://${LLM_API_HOST}:${LLM_API_PORT}"
echo "  • vLLM: http://localhost:${VLLM_PORT}"
echo "  • MCP (mcp_server.py):  http://localhost:${MCP_PORT1}/mcp"
echo "  • MCP (mcp_server1.py): http://localhost:${MCP_PORT2}/mcp"
echo "  • Model: ${MODEL}"


if [ "$MODE" = "prod" ] || [ "$MODE" = "production" ]; then
    python -m uvicorn main:app \
        --host "$LLM_API_HOST" \
        --port "$LLM_API_PORT" \
        --timeout-keep-alive 60 \
        --timeout-graceful-shutdown 30 \
        --log-level "$(echo "$LLM_API_LOG_LEVEL" | tr '[:upper:]' '[:lower:]')"
else
    python -m uvicorn main:app \
        --host "$LLM_API_HOST" \
        --port "$LLM_API_PORT" \
        --log-level "$(echo "$LLM_API_LOG_LEVEL" | tr '[:upper:]' '[:lower:]')"
fi