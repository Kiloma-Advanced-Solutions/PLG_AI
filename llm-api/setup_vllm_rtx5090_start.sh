#!/bin/bash

# RTX 5090 vLLM Native Installation Script
# Tested on Ubuntu 24.04 with CUDA 12.8.1 and RTX 5090

set -e  # Exit on any error

echo "🚀 Setting up vLLM for RTX 5090..."

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! nvidia-smi &> /dev/null; then
    echo "❌ NVIDIA drivers not found. Please install NVIDIA drivers first."
    exit 1
fi

if ! nvcc --version &> /dev/null; then
    echo "❌ CUDA toolkit not found. Please install CUDA 12.8.1 first."
    exit 1
fi

# Set environment variables
echo "🔧 Setting up environment variables..."
cat >> ~/.bashrc << 'EOF'
# vLLM Environment Variables for RTX 5090
export MAX_JOBS=16
export NVCC_THREADS=4
export FLASHINFER_ENABLE_AOT=1
export USE_CUDA=1
export CUDA_HOME=/usr/local/cuda
export TORCH_CUDA_ARCH_LIST='12.0+PTX'
export CCACHE_DIR=$HOME/.ccache
export CMAKE_BUILD_TYPE=Release
export PATH="/usr/local/cuda/bin:${PATH}"
export LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"

# Hugging Face optimizations
export HF_HUB_DOWNLOAD_TIMEOUT=3000
export HF_HUB_ENABLE_HF_TRANSFER=1
EOF

# Source the environment
source ~/.bashrc
export MAX_JOBS=16
export NVCC_THREADS=4
export FLASHINFER_ENABLE_AOT=1
export USE_CUDA=1
export CUDA_HOME=/usr/local/cuda
export TORCH_CUDA_ARCH_LIST='12.0+PTX'
export CCACHE_DIR=$HOME/.ccache
export CMAKE_BUILD_TYPE=Release
export PATH="/usr/local/cuda/bin:${PATH}"
export LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"
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

# Create and activate virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv ~/vllm-env
source ~/vllm-env/bin/activate

# Upgrade pip and install base packages
echo "⬆️ Upgrading pip and installing base packages..."
pip install --upgrade pip setuptools wheel

# Install PyTorch with CUDA 12.8 support
echo "🔥 Installing PyTorch with CUDA 12.8..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Install xformers
echo "🔧 Installing xformers..."
pip install git+https://github.com/facebookresearch/xformers.git@main#egg=xformers

# Create workspace directory
echo "📁 Creating workspace..."
mkdir -p ~/workspace
cd ~/workspace

# Build and install BitsAndBytes
echo "🔩 Building BitsAndBytes..."
git clone https://github.com/bitsandbytes-foundation/bitsandbytes.git
cd bitsandbytes
cmake -DCOMPUTE_BACKEND=cuda -S .
make -j 4
pip install -e .

# Build and install FlashInfer
echo "⚡ Building FlashInfer..."
cd ~/workspace
git clone https://github.com/flashinfer-ai/flashinfer.git --branch main --recursive
cd flashinfer
git checkout cd928a7e044c94bdd96e3f7ca79a0514b253ea6d

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
cd ~/workspace
git clone https://github.com/vllm-project/vllm.git --branch main
cd vllm
git checkout d84b97a3e33ed79aaba7552bfe5889d363875562

# Configure for existing PyTorch
python3 use_existing_torch.py

# Install build requirements
pip install -r requirements/build.txt
pip install setuptools_scm

# Build and install vLLM in development mode
python3 setup.py develop

# Install accelerate
pip install accelerate

echo "✅ Installation complete!"
echo ""
echo "🎯 To use vLLM:"
echo "   source ~/vllm-env/bin/activate"
echo ""
echo "🚀 Test with:"
echo "   python3 -m vllm.entrypoints.openai.api_server \\"
echo "     --model gaunernst/gemma-3-12b-it-qat-autoawq \\"
echo "     --max-model-len 131072 \\"
echo "     --tensor-parallel-size 2 \\"
echo "     --max-num-seqs 4"
echo ""
echo "💡 The environment variables have been added to ~/.bashrc"
echo "   Run 'source ~/.bashrc' in new terminals"