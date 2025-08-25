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

# Ensure cleanup on exit
trap 'stop_vllm' INT TERM EXIT

stop_vllm

# Start vLLM server
start_vllm() {
    python -m vllm.entrypoints.openai.api_server \
        --model "$MODEL" \
        --max-model-len 131072 \
        --port "$VLLM_PORT" \
        --tensor-parallel-size 2 \
        --max-num-seqs 4 \
        --gpu-memory-utilization 0.9 \
        --disable-log-requests \
        --trust-remote-code &

    echo "Waiting for vLLM to start..."
    for i in {1..1200}; do
        if curl -s "http://localhost:${VLLM_PORT}/v1/models" >/dev/null 2>&1; then
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

# Run API from llm-api directory
cd "$API_DIR"

if [ ! -f "main.py" ]; then
    echo "main.py not found in ${API_DIR}" >&2
    exit 1
fi

echo "API: http://${LLM_API_HOST}:${LLM_API_PORT} | vLLM: http://localhost:${VLLM_PORT} | Model: ${MODEL}"

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
