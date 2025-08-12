#!/bin/bash

## Set Environment Variables
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


## Install System Dependencies
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


## Create a Virtual Environment
python3 -m venv ~/vllm-env
source ~/vllm-env/bin/activate


## Install Python Dependencies

# Upgrade pip and base packages
pip install --upgrade pip setuptools wheel

# Install PyTorch with CUDA 12.8 support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Install xformers
pip install git+https://github.com/facebookresearch/xformers.git@main#egg=xformers


## Build and Install BitsAndBytes
# Create workspace directory
mkdir -p ~/workspace
cd ~/workspace

# Clone and build bitsandbytes
git clone https://github.com/bitsandbytes-foundation/bitsandbytes.git
cd bitsandbytes
cmake -DCOMPUTE_BACKEND=cuda -S .
make -j 4
pip install -e .


## Build and Install FlashInfer
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


## Install Additional Dependencies
pip install aiohttp==3.12.14
pip install protobuf==5.29.5
pip install click==8.1.8
pip install rich==13.7.1
pip install starlette==0.46.2
pip install typing-extensions==4.14.1


## Build and Install vLLM
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



