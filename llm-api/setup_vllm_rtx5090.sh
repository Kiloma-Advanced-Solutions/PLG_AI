#!/bin/bash

# vLLM Setup Script for RTX 5090 (Local Environment)
# This script sets up vLLM with PyTorch 2.6 and CUDA 12.8 for Blackwell architecture

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== vLLM RTX 5090 Setup Script ===${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root is not recommended. Consider using a regular user account."
fi

# Detect number of CPU cores and RAM for parallel compilation
CPU_CORES=$(nproc)
TOTAL_RAM_GB=$(free -g | awk '/^Mem:/{print $2}')

# Calculate MAX_JOBS based on both CPU cores and available RAM
# CUDA compilation is memory-intensive: ~2-4GB per job
if [ $TOTAL_RAM_GB -gt 128 ]; then
    MAX_JOBS=$((CPU_CORES / 4))  # Conservative for high-core systems
elif [ $TOTAL_RAM_GB -gt 64 ]; then
    MAX_JOBS=$((CPU_CORES / 6))
elif [ $TOTAL_RAM_GB -gt 32 ]; then
    MAX_JOBS=$((CPU_CORES / 8))
else
    MAX_JOBS=$((CPU_CORES / 12))
fi

# Apply reasonable bounds
if [ $MAX_JOBS -lt 2 ]; then MAX_JOBS=2; fi
if [ $MAX_JOBS -gt 16 ]; then MAX_JOBS=16; fi  # Cap at 16 for stability

print_status "Detected $CPU_CORES CPU cores and ${TOTAL_RAM_GB}GB RAM"
print_status "Will use MAX_JOBS=$MAX_JOBS for compilation (memory-optimized)"

# Check NVIDIA driver and CUDA availability
print_status "Checking NVIDIA GPU setup..."
if ! command -v nvidia-smi &> /dev/null; then
    print_error "nvidia-smi not found. Please install NVIDIA drivers first."
    exit 1
fi

nvidia-smi
if [ $? -ne 0 ]; then
    print_error "nvidia-smi failed. Please check your NVIDIA driver installation."
    exit 1
fi

# Check for RTX 5090
if nvidia-smi | grep -q "RTX 50"; then
    print_status "RTX 50 series GPU detected!"
else
    print_warning "RTX 50 series GPU not clearly detected. Proceeding anyway..."
fi

# Set up directories
WORK_DIR="$HOME/vllm_setup"
CACHE_DIR="$WORK_DIR/ccache"
VLLM_DIR="$WORK_DIR/vllm"

print_status "Creating work directory: $WORK_DIR"
mkdir -p "$WORK_DIR"
mkdir -p "$CACHE_DIR"
cd "$WORK_DIR"

# Install system dependencies (Ubuntu/Debian)
print_status "Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        git \
        ccache \
        kmod \
        python3-dev \
        python3-pip \
        python3-venv \
        libnvidia-compute-550 || libnvidia-compute-555 || echo "NVIDIA compute library may need manual installation"
elif command -v dnf &> /dev/null; then
    sudo dnf install -y gcc gcc-c++ cmake git ccache python3-devel python3-pip
elif command -v pacman &> /dev/null; then
    sudo pacman -S --needed base-devel cmake git ccache python python-pip
else
    print_warning "Unsupported package manager. Please install: build-essential, cmake, git, ccache, python3-dev, python3-pip manually."
fi

# Create and activate virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv vllm_env
source vllm_env/bin/activate

# Upgrade pip and install basic tools
print_status "Upgrading pip and installing basic tools..."
pip install --upgrade pip setuptools wheel

# Install PyTorch 2.6 with CUDA 12.4 (closest available to 12.8)
print_status "Installing PyTorch 2.6 with CUDA support..."
# Note: PyTorch 2.6 with CUDA 12.8 might not be available yet, using 12.4
pip install torch==2.6.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Verify PyTorch CUDA installation
print_status "Verifying PyTorch CUDA installation..."
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}'); print(f'GPU count: {torch.cuda.device_count()}')"

if [ $? -ne 0 ]; then
    print_error "PyTorch CUDA verification failed!"
    exit 1
fi

# Clone vLLM repository
print_status "Cloning vLLM repository..."
if [ -d "$VLLM_DIR" ]; then
    print_status "vLLM directory exists, pulling latest changes..."
    cd "$VLLM_DIR"
    git pull
else
    git clone https://github.com/vllm-project/vllm.git "$VLLM_DIR"
    cd "$VLLM_DIR"
fi

# Ensure we're at or above the required commit
print_status "Checking vLLM commit..."
git log --oneline -1

# Run use_existing_torch.py
print_status "Running use_existing_torch.py..."
python use_existing_torch.py

# Install build requirements
print_status "Installing build requirements..."
pip install -r requirements/build.txt
pip install setuptools_scm

# Set environment variables for compilation
export CCACHE_DIR="$CACHE_DIR"
export MAX_JOBS="$MAX_JOBS"
export CUDA_HOME="/usr/local/cuda"
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64:$LD_LIBRARY_PATH"

# Additional flags for RTX 5090 (Blackwell architecture)
export TORCH_CUDA_ARCH_LIST="9.0"  # Blackwell architecture
export VLLM_FLASH_ATTN_VERSION=2   # Use Flash Attention 2 as FA3 doesn't work with Blackwell yet

# Memory optimization flags to prevent OOM during compilation
export CUDA_LAUNCH_BLOCKING=1  # Sequential CUDA operations
export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:128"  # Limit CUDA memory fragmentation

print_status "Building vLLM from source..."
print_status "This may take 30-90 minutes depending on your system..."
print_status "Using CCACHE_DIR=$CACHE_DIR and MAX_JOBS=$MAX_JOBS (memory-optimized)"

# Clean any previous failed builds
if [ -d "build" ]; then
    print_status "Cleaning previous build artifacts..."
    rm -rf build/
fi
if [ -d "vllm.egg-info" ]; then
    rm -rf vllm.egg-info/
fi

# Monitor memory usage during build (background process)
(
    while true; do
        sleep 60  # Check every minute
        MEM_USAGE=$(free | awk '/^Mem:/ {printf "%.1f%%", $3/$2 * 100.0}')
        echo "[$(date '+%H:%M:%S')] Build progress - Memory usage: $MEM_USAGE"
        # Warning if memory usage is too high
        MEM_PERCENT=$(free | awk '/^Mem:/ {printf "%.0f", $3/$2 * 100.0}')
        if [ $MEM_PERCENT -gt 90 ]; then
            echo "[WARNING] Memory usage above 90% - build may fail"
        fi
    done
) &
MONITOR_PID=$!

# Trap to kill monitor on script exit
trap "kill $MONITOR_PID 2>/dev/null || true" EXIT

# Build vLLM with error handling
if ! CCACHE_DIR="$CACHE_DIR" MAX_JOBS="$MAX_JOBS" python setup.py develop; then
    # Kill memory monitor
    kill $MONITOR_PID 2>/dev/null || true
    print_error "Build failed! This might be due to memory issues."
    print_error "Try running with lower MAX_JOBS or use the recovery script"
    exit 1
fi

# Kill memory monitor on successful completion
kill $MONITOR_PID 2>/dev/null || true

# Fix dependency issues (especially aiohttp)
print_status "Fixing dependencies..."
pip uninstall -y aiohttp || echo "aiohttp not found to uninstall"
pip install "aiohttp>=3.8.0,<4.0.0"

# Install additional required dependencies
pip install --upgrade \
    "openai>=1.0.0" \
    "fastapi>=0.100.0" \
    "uvicorn[standard]>=0.22.0" \
    "pydantic>=2.0.0" \
    "transformers>=4.36.0" \
    "tokenizers>=0.15.0" \
    "ray[default]>=2.9.0" \
    "numpy>=1.24.0" \
    "packaging>=21.0"

# Test comprehensive installation
print_status "Testing vLLM installation..."
python -c "
import vllm
import torch
import aiohttp
print(f'✓ vLLM version: {vllm.__version__}')
print(f'✓ PyTorch version: {torch.__version__}')
print(f'✓ CUDA available: {torch.cuda.is_available()}')
print(f'✓ GPU count: {torch.cuda.device_count()}')
print(f'✓ aiohttp version: {aiohttp.__version__}')
print('✓ All dependencies working!')
"

if [ $? -eq 0 ]; then
    print_status "🎉 vLLM installation successful! 🎉"
    echo
    print_status "=== Setup Complete ==="
    print_status "vLLM is now ready to use on your RTX 5090!"
    print_status "To use vLLM, activate the virtual environment:"
    print_status "  cd $WORK_DIR"
    print_status "  source vllm_env/bin/activate"
    print_status ""
    print_status "Remember to set VLLM_FLASH_ATTN_VERSION=2 when running vLLM:"
    print_status "  export VLLM_FLASH_ATTN_VERSION=2"
    print_status ""
    print_status "Quick test command:"
    print_status "  python -c \"from vllm import LLM; print('vLLM ready for inference!')\""
    print_status ""
    print_status "Example server startup:"
    print_status "  python -m vllm.entrypoints.openai.api_server \\"
    print_status "    --model microsoft/DialoGPT-medium \\"
    print_status "    --host 0.0.0.0 \\"
    print_status "    --port 8000"
else
    print_error "vLLM installation failed!"
    print_error "Check the error messages above for details"
    exit 1
fi