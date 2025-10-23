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

# Stop any existing vLLM server
stop_vllm() {
    pkill -f "vllm serve" >/dev/null 2>&1 || true
    pkill -f "vllm.entrypoints.openai.api_server" >/dev/null 2>&1 || true
}

# Stop any existing MCP server
stop_mcp() {
    pkill -f "mcp_server.py" >/dev/null 2>&1 || true
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

# Start MCP server
start_mcp() {
    cd "$API_DIR"
    python mcp_server.py &
    MCP_PID=$!
    
    echo "Waiting for MCP server to start..."
    MCP_PORT=${LLM_API_MCP_PORT:-8000}
    for i in {1..30}; do
        # Check if port is listening (nc -z checks if port is open without sending data)
        if nc -z localhost "$MCP_PORT" 2>/dev/null; then
            echo "✅ MCP server is ready on port $MCP_PORT!"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "❌ MCP server failed to start after 30 seconds"
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

MCP_PORT=${LLM_API_MCP_PORT:-8000}
echo "🚀 All services running:"
echo "  • API:  http://${LLM_API_HOST}:${LLM_API_PORT}"
echo "  • vLLM: http://localhost:${VLLM_PORT}"
echo "  • MCP:  http://localhost:${MCP_PORT}/mcp"
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