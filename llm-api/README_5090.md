# vLLM RTX 5090 Native Setup

This repository contains scripts to set up vLLM natively on RTX 5090 GPUs without Docker.

## Prerequisites

- **Ubuntu 24.04** (or compatible Linux distribution)
- **RTX 5090** with proper NVIDIA drivers installed
- **CUDA 12.8.1** toolkit installed
- **Root/sudo access** for system packages

## Quick Start

```bash
# Clone this repository
git clone <your-repo-url>
cd vllm-rtx5090-setup

# Make the setup script executable
chmod +x setup_vllm_rtx5090_start.sh

# Run the setup script
./setup_vllm_rtx5090_start.sh
```

## Manual Installation

If you prefer to install manually, follow these steps:

### 1. Set Environment Variables

```bash
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
```

### 2. Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y kmod git cmake ninja-build build-essential ccache python3-pip python3-dev python3-venv libsndfile1
```

### 3. Create Virtual Environment

```bash
python3 -m venv ~/vllm-env
source ~/vllm-env/bin/activate
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Build Components

Follow the script for building BitsAndBytes, FlashInfer, and vLLM from source.

## Usage

After installation:

```bash
# Activate environment
source ~/vllm-env/bin/activate

# Start vLLM server
python3 -m vllm.entrypoints.openai.api_server \
  --model gaunernst/gemma-3-12b-it-qat-autoawq \
  --max-model-len 131072 \
  --tensor-parallel-size 2 \
  --max-num-seqs 4
```

## Tested Configuration

- **GPU**: RTX 5090
- **CUDA**: 12.8.1
- **OS**: Ubuntu 24.04
- **Python**: 3.12
- **vLLM**: v0.10.1.dev293+gd84b97a3e

## Performance Notes

- Using `tensor-parallel-size 2` for dual-GPU setups
- FlashInfer and AWQ-Marlin kernels enabled for optimal performance
- Chunked prefill enabled for long context support

## Troubleshooting

### Common Issues

1. **Out of memory**: Reduce `max-model-len` or `max-num-seqs`
2. **Download timeouts**: The script sets extended timeouts automatically
3. **CUDA compilation warnings**: These are normal and don't affect functionality

### Environment Variables

The setup script automatically adds environment variables to `~/.bashrc`. For new terminals, run:

```bash
source ~/.bashrc
```

## Files in this Repository

- `setup_vllm_rtx5090_start.sh` - Main setup script
- `requirements.txt` - Python dependencies
- `README.md` - This file
- `.gitignore` - Git ignore rules

## Contributing

Feel free to submit issues and improvements!

## License

This setup is based on open-source projects. Check individual component licenses.