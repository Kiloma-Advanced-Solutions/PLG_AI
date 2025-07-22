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

# Server Configuration
export LLM_API_HOST="0.0.0.0"
export LLM_API_PORT=8090
export LLM_API_LOG_LEVEL="INFO"

# CORS Configuration
export LLM_API_ALLOWED_ORIGINS="http://localhost:3000"  # Frontend URL

# vLLM Configuration
export LLM_API_VLLM_BASE_URL="http://localhost:8000"
export LLM_API_VLLM_API_URL="http://localhost:8000/v1/chat/completions"
export LLM_API_VLLM_METRICS_URL="http://localhost:8000/metrics"
export LLM_API_MODEL_NAME="gaunernst/gemma-3-12b-it-qat-autoawq"

# Model Parameters
export LLM_API_MAX_TOKENS=2048
export LLM_API_TEMPERATURE=0.7
export LLM_API_TOP_P=0.9

# Connection Settings
export LLM_API_REQUEST_TIMEOUT=300
export LLM_API_HEALTH_CHECK_TIMEOUT=5
export LLM_API_CONNECTION_POOL_SIZE=100
export LLM_API_MAX_KEEPALIVE_CONNECTIONS=50
export LLM_API_KEEPALIVE_EXPIRY=60.0

echo -e "${BLUE}🚀 Starting Unified LLM API${NC}"
echo -e "${BLUE}================================${NC}"

# Function to check if a service is running
check_service() {
    local url=$1
    local name=$2
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "✅ ${GREEN}$name is running${NC}"
        return 0
    else
        echo -e "❌ ${RED}$name is not responding${NC}"
        return 1
    fi
}

# Function to wait for a service
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=${3:-60}
    
    echo -e "⏳ ${YELLOW}Waiting for $name to start...${NC}"
    
    for i in $(seq 1 $max_attempts); do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "✅ ${GREEN}$name is ready!${NC}"
            return 0
        fi
        
        if [ $i -eq $max_attempts ]; then
            echo -e "❌ ${RED}$name failed to start within $max_attempts seconds${NC}"
            return 1
        fi
        
        sleep 1
    done
}

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
pip install -r requirements.txt > /dev/null

# Check if vLLM server is running
echo -e "🔍 ${YELLOW}Checking vLLM server availability...${NC}"
VLLM_MODELS_URL="${LLM_API_VLLM_BASE_URL}/v1/models"

if ! check_service "$VLLM_MODELS_URL" "vLLM server"; then
    echo -e "${YELLOW}⚠️  vLLM server is not running. Starting anyway...${NC}"
    echo -e "${YELLOW}   Make sure to start vLLM server for dual RTX 4090 setup:${NC}"
    echo -e "${YELLOW}   python3 -m vllm.entrypoints.openai.api_server \\${NC}"
    echo -e "${YELLOW}     --model $LLM_API_MODEL_NAME \\${NC}"
    echo -e "${YELLOW}     --max-model-len 131072 \\${NC}"
    echo -e "${YELLOW}     --port 8000 \\${NC}"
    echo -e "${YELLOW}     --tensor-parallel-size 2 \\${NC}"
    echo -e "${YELLOW}     --gpu-memory-utilization 0.9${NC}"
    echo ""
fi

# Display configuration
echo -e "${BLUE}📋 Configuration:${NC}"
echo -e "   🌐 API Host: $LLM_API_HOST"
echo -e "   🔌 API Port: $LLM_API_PORT"
echo -e "   🔗 vLLM URL: $LLM_API_VLLM_API_URL"
echo -e "   🤖 Model: $LLM_API_MODEL_NAME"
echo -e "   📊 Log Level: $LLM_API_LOG_LEVEL"
echo -e "   🔒 CORS Origins: $LLM_API_ALLOWED_ORIGINS"
echo ""

# Start the API server
echo -e "🚀 ${GREEN}Starting Unified LLM API...${NC}"
echo -e "   📍 Server will be available at: http://$LLM_API_HOST:$LLM_API_PORT"
echo -e "   💊 Health check: http://$LLM_API_HOST:$LLM_API_PORT/api/health"
echo -e "   📊 Metrics: http://$LLM_API_HOST:$LLM_API_PORT/api/metrics"
echo ""

# Choose startup method based on environment
if [ "$1" = "dev" ] || [ "$1" = "development" ]; then
    echo -e "🔧 ${YELLOW}Starting in development mode...${NC}"
    echo -e "   🚀 ${GREEN}vLLM handles all request queuing${NC}"
    uvicorn llm-api.main:app \
        --host "$LLM_API_HOST" \
        --port "$LLM_API_PORT" \
        --log-level "${LLM_API_LOG_LEVEL,,}" \
        --reload
        
elif [ "$1" = "prod" ] || [ "$1" = "production" ]; then
    echo -e "🏭 ${YELLOW}Starting in production mode...${NC}"
    echo -e "   🚀 ${GREEN}No artificial limits - vLLM manages everything${NC}"
    
    # Production: Single process, let vLLM handle all queuing and batching
    uvicorn llm-api.main:app \
        --host "$LLM_API_HOST" \
        --port "$LLM_API_PORT" \
        --timeout-keep-alive 60 \
        --timeout-graceful-shutdown 30 \
        --log-level "${LLM_API_LOG_LEVEL,,}"
        
else
    echo -e "🔧 ${YELLOW}Starting with uvicorn - no artificial limits...${NC}"
    echo -e "   🚀 ${GREEN}vLLM handles all request management${NC}"
    uvicorn llm-api.main:app \
        --host "$LLM_API_HOST" \
        --port "$LLM_API_PORT" \
        --log-level "${LLM_API_LOG_LEVEL,,}" \
        --timeout-keep-alive 60
fi 