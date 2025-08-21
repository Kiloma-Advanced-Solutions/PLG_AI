#!/bin/bash

# Integrated RTX 5090 vLLM + Unified API Startup Script
# This script sets up and starts both vLLM and the unified API server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Integrated vLLM + API Server for RTX 5090${NC}"
echo -e "${BLUE}====================================================${NC}"

# =================================
# Environment Configuration
# =================================

# Append environment variable settings to ~/.bashrc so they persist across terminal sessions
cat >> ~/.bashrc << 'EOF'
export MAX_JOBS=16
export NVCC_THREADS=4
export FLASHINFER_ENABLE_AOT=1
export USE_CUDA=1
export CUDA_HOME=/usr/local/cuda
export TORCH_CUDA_ARCH_LIST='12.0+PTX'
export CCACHE_DIR=$HOME/.ccache
export CMAKE_BUILD_TYPE=Release
export PATH="/usr/local/cuda/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/cuda/lib64:$LD_LIBRARY_PATH"
export HF_HUB_DOWNLOAD_TIMEOUT=3000
export HF_HUB_ENABLE_HF_TRANSFER=1
EOF

# Apply the changes immediately to the current terminal session
source ~/.bashrc

# Also export them explicitly in this session to ensure they're available
export MAX_JOBS=16
export NVCC_THREADS=4
export FLASHINFER_ENABLE_AOT=1
export USE_CUDA=1
export CUDA_HOME=/usr/local/cuda
export TORCH_CUDA_ARCH_LIST='12.0+PTX'
export CCACHE_DIR=$HOME/.ccache
export CMAKE_BUILD_TYPE=Release
export PATH="/usr/local/cuda/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/cuda/lib64:$LD_LIBRARY_PATH"
export HF_HUB_DOWNLOAD_TIMEOUT=3000
export HF_HUB_ENABLE_HF_TRANSFER=1


# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    kmod \
    git \
    cmake \
    ninja-build \
    build-essential \
    ccache \
    python3-pip \
    python3-dev \
    python3-venv \
    libsndfile1


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


# Function to check if a process is running
is_process_running() {
    local search_term=$1
    if pgrep -f "$search_term" > /dev/null; then
        return 0  # Process is running
    else
        return 1  # Process is not running
    fi
}


# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    stop_vllm
    exit 0
}

# Register cleanup function
trap cleanup SIGINT SIGTERM


# Check NVIDIA drivers and CUDA. If not found, print a red error message and exit.
echo -e "📋 ${YELLOW}Checking prerequisites...${NC}"
command -v nvidia-smi >/dev/null 2>&1 || { echo -e "${RED}❌ NVIDIA drivers not found.${NC}"; exit 1; }
command -v nvcc >/dev/null 2>&1 || { echo -e "${RED}❌ CUDA toolkit not found.${NC}"; exit 1; }


# Create and activate virtual environment
echo -e "🔧 ${YELLOW}Activating project virtual environment...${NC}"
[ -d "venv" ] || python3 -m venv venv
source venv/bin/activate


# Upgrade pip and install base packages
echo "⬆️ Upgrading pip and installing base packages..."
pip install --upgrade pip setuptools wheel

# Install PyTorch with CUDA 12.8 support
echo "🔥 Installing PyTorch with CUDA 12.8..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Install xformers
echo "🔧 Installing xformers..."
pip install git+https://github.com/facebookresearch/xformers.git@main#egg=xformers


## Create workspace directory for building and installing dependencies
# echo "📁 Creating workspace..."
# mkdir -p ~/workspace 


# Build and install BitsAndBytes
echo "🔩 Building BitsAndBytes..."
cd ./external_sources/bitsandbytes
# Already cloned and compiled bitsandbytes
# cd ./external_sources && git clone https://github.com/bitsandbytes-foundation/bitsandbytes.git && cd bitsandbytes
# cmake -DCOMPUTE_BACKEND=cuda -S . && make -j 4
pip install -e .  # Instead of copying files to site-packages, it creates a link to your source code


# Build and install FlashInfer
echo "⚡ Building FlashInfer..."

# cd ~/workspace && git clone https://github.com/flashinfer-ai/flashinfer.git --branch main --recursive
# cd flashinfer && git checkout cd928a7e044c94bdd96e3f7ca79a0514b253ea6d
cd ../flashinfer

# Install build dependencies
pip install ninja build packaging "setuptools>=75.6.0"

# Build flashinfer
python3 -m flashinfer.aot
python3 -m build --no-isolation --wheel
pip install dist/flashinfer*.whl


# Install additional dependencies
echo "📚 Installing additional dependencies..."
pip install hf_transfer  # For faster downloads
pip install aiohttp==3.12.14
pip install protobuf==5.29.5
pip install click==8.1.8
pip install rich==13.7.1
pip install starlette==0.46.2
pip install typing-extensions==4.14.1

# Build and install vLLM
echo "🏗️ Building vLLM..."
# cd ~/workspace && git clone https://github.com/vllm-project/vllm.git --branch main
# cd vllm && git checkout d84b97a3e33ed79aaba7552bfe5889d363875562


cd ../vllm

# # Configure for existing PyTorch
# python3 use_existing_torch.py

# Install build requirements
pip install -r requirements/build.txt
pip install setuptools_scm

# Build and install vLLM in development mode
python3 setup.py develop  # <=> pip install -e .

# Install accelerate
pip install accelerate

# Install API server dependencies
pip install fastapi>=0.104.1 uvicorn[standard]>=0.24.0 pydantic>=2.4.0 pydantic-settings>=2.0.0 httpx>=0.25.0 python-dotenv>=1.0.0 uvloop>=0.19.0 httptools>=0.6.1 pytest openai>=1.3.0


# Load port mappings configuration from Python config if available or use defaults
if [ -f "core/config.py" ]; then
    echo -e "🔍 ${YELLOW}Loading configuration...${NC}"
    read -r FRONTEND_PORT API_PORT VLLM_PORT FRONTEND_URL API_URL VLLM_URL VLLM_API_URL <<< "$(
        python - << 'PY'
try:
    from core.config import llm_config
    print('\n'.join(map(str, [
        llm_config.frontend_port,
        llm_config.api_port,
        llm_config.vllm_port,
        llm_config.frontend_url,
        llm_config.api_url,
        llm_config.vllm_url,
        llm_config.vllm_api_url
    ])))
except:
    print('\n'.join(map(str, [
        3000, 8090, 8060,
        'http://localhost:3000',
        'http://localhost:8090',
        'http://localhost:8060',
        'http://localhost:8060/v1'
    ])))
PY
    )"
else
    echo -e "${YELLOW}⚠️  No config file found. Using default values.${NC}"
    FRONTEND_PORT=3000
    API_PORT=8090
    VLLM_PORT=8060
    FRONTEND_URL="http://localhost:3000"
    API_URL="http://localhost:8090"
    VLLM_URL="http://localhost:8060"
    VLLM_API_URL="http://localhost:8060/v1"
fi

echo "✅ venv setup complete!"
echo ""
echo "🎯 To start API:"
echo "   ./start_api_5090.sh"
