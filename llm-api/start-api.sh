#!/bin/bash

# Unified LLM API Startup Script
# This script starts the unified API server that can be used by multiple AI applications

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =================================
# Environment Configuration
# =================================

# Base URL (can be overridden)
export LLM_API_BASE_URL=${LLM_API_BASE_URL:-"http://localhost"}

# Server Configuration
export LLM_API_HOST="0.0.0.0"
export LLM_API_PORT=8090
export LLM_API_LOG_LEVEL="INFO"

# Model Configuration
export LLM_API_MODEL_NAME="gaunernst/gemma-3-12b-it-qat-autoawq"

# Connection Settings
export LLM_API_REQUEST_TIMEOUT=300
export LLM_API_HEALTH_CHECK_TIMEOUT=5
export LLM_API_CONNECTION_POOL_SIZE=100
export LLM_API_MAX_KEEPALIVE_CONNECTIONS=50
export LLM_API_KEEPALIVE_EXPIRY=60.0

echo -e "${BLUE}🚀 Starting Unified LLM API${NC}"
echo -e "${BLUE}================================${NC}"

# Function to check if a process is running
is_process_running() {
    local search_term=$1
    if pgrep -f "$search_term" > /dev/null; then
        return 0  # Process is running
    else
        return 1  # Process is not running
    fi
}

# Function to stop vLLM server
stop_vllm() {
    echo -e "${YELLOW}Stopping vLLM server...${NC}"
    pkill -f "vllm serve" || true
    sleep 2  # Give it time to shut down
}

# Function to start vLLM server
start_vllm() {
    echo -e "${YELLOW}Starting vLLM server...${NC}"
    python3 -m vllm.entrypoints.openai.api_server \
        --model $LLM_API_MODEL_NAME \
        --max-model-len 131072 \
        --port 8060 \
        --tensor-parallel-size 2 | grep -Ev "Received request chatcmpl|Added request chatcmpl|HTTP/1.1\" 200 OK" &
        
    for i in {1..600}; do
        if curl -s http://localhost:8060/v1/models > /dev/null; then
            echo -e "${GREEN}vLLM server is ready!${NC}"
            return 0
        fi
        sleep 1
    done
    echo -e "${RED}vLLM server failed to start within 10 minutes${NC}"
    return 1
}

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    stop_vllm
    exit 0
}

# Register cleanup function
trap cleanup SIGINT SIGTERM

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "📦 ${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "🔧 ${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "📚 ${YELLOW}Installing dependencies...${NC}"
echo -e "📍 ${BLUE}Using requirements file: $(pwd)/requirements.txt${NC}"
pip install -r requirements.txt > /dev/null

# Get port mappings from Python config
echo -e "🔍 ${YELLOW}Loading configuration...${NC}"
CONFIG=$(python -c "
from core.config import llm_config
print(llm_config.frontend_port)
print(llm_config.api_port)
print(llm_config.vllm_port)
print(llm_config.frontend_url)
print(llm_config.api_url)
print(llm_config.vllm_url)
print(llm_config.vllm_api_url)
")

# Read port mappings and URLs into variables
IFS=$'\n' read -r FRONTEND_PORT API_PORT VLLM_PORT FRONTEND_URL API_URL VLLM_URL VLLM_API_URL <<< "$CONFIG"

# Stop any existing vLLM server
stop_vllm

# Start vLLM server
start_vllm

# Display configuration
echo -e "${BLUE}📋 Configuration:${NC}"
echo -e "   🌐 API Host: $LLM_API_HOST"
echo -e "   🔌 API Port: $LLM_API_PORT"
echo -e "   🔗 vLLM URL: $VLLM_API_URL"
echo -e "   🤖 Model: $LLM_API_MODEL_NAME"
echo -e "   📊 Log Level: $LLM_API_LOG_LEVEL"
echo -e "   🔒 CORS Origins:"
echo -e "      - Frontend: $FRONTEND_URL"
echo -e "      - API: $API_URL"
echo ""

# Start the API server
echo -e "🚀 ${GREEN}Starting Unified LLM API...${NC}"
echo -e "   📍 Server will be available at: $API_URL"
echo -e "   💊 Health check: $API_URL/api/health"
echo -e "   📊 Metrics: $API_URL/api/metrics"
echo ""



# Choose startup method based on environment
if [ "$1" = "dev" ] || [ "$1" = "development" ]; then
    echo -e "🔧 ${YELLOW}Starting in development mode...${NC}"
    echo -e "   🚀 ${GREEN}vLLM handles all request queuing${NC}"
    python -m uvicorn main:app \
        --host "$LLM_API_HOST" \
        --port "$LLM_API_PORT" \
        --log-level "${LLM_API_LOG_LEVEL,,}" \
        --reload
        
elif [ "$1" = "prod" ] || [ "$1" = "production" ]; then
    echo -e "🏭 ${YELLOW}Starting in production mode...${NC}"
    echo -e "   🚀 ${GREEN}No artificial limits - vLLM manages everything${NC}"
    python -c "import main"
    
    # Production: Single process, let vLLM handle all queuing and batching
    python -m uvicorn main:app \
        --host "$LLM_API_HOST" \
        --port "$LLM_API_PORT" \
        --timeout-keep-alive 60 \
        --timeout-graceful-shutdown 30 \
        --log-level "${LLM_API_LOG_LEVEL,,}"
        
else
    echo -e "🔧 ${YELLOW}Starting with uvicorn - no artificial limits...${NC}"
    echo -e "   🚀 ${GREEN}vLLM handles all request management${NC}"
    python -m uvicorn main:app \
        --host "$LLM_API_HOST" \
        --port "$LLM_API_PORT" \
        --log-level "${LLM_API_LOG_LEVEL,,}" \
        --timeout-keep-alive 60
fi 