#!/bin/bash

# Environment Export Script for RTX 5090 vLLM Setup
# This script exports the current environment for quick deployment on new instances

# ./export_env.sh
# tar -czf vllm_env_export_20250819_163441.tar.gz vllm_env_export_20250819_163441

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📦 Exporting RTX 5090 vLLM Environment${NC}"
echo -e "${BLUE}=====================================${NC}"

# Create export directory with timestamp
EXPORT_DIR="vllm_env_export_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$EXPORT_DIR"

echo -e "${YELLOW}📁 Export directory: $EXPORT_DIR${NC}"

# =================================
# 1. Export System Package Information
# =================================
echo -e "${YELLOW}📋 Exporting system package information...${NC}"

# Export installed apt packages
dpkg --get-selections > "$EXPORT_DIR/apt_packages.txt"

# Export apt sources
cp /etc/apt/sources.list "$EXPORT_DIR/apt_sources.list" 2>/dev/null || echo "# No custom sources.list" > "$EXPORT_DIR/apt_sources.list"
cp -r /etc/apt/sources.list.d "$EXPORT_DIR/" 2>/dev/null || mkdir -p "$EXPORT_DIR/sources.list.d"

# Export CUDA version info
if command -v nvcc >/dev/null 2>&1; then
    nvcc --version > "$EXPORT_DIR/cuda_version.txt"
    nvidia-smi > "$EXPORT_DIR/nvidia_info.txt"
else
    echo "CUDA not found" > "$EXPORT_DIR/cuda_version.txt"
fi

# =================================
# 2. Export Environment Variables
# =================================
echo -e "${YELLOW}🔧 Exporting environment variables...${NC}"

cat > "$EXPORT_DIR/environment_vars.sh" << 'EOF'
#!/bin/bash
# Environment variables for vLLM setup
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

# API Configuration
export LLM_API_BASE_URL="http://localhost"
export LLM_API_HOST="0.0.0.0"
export LLM_API_PORT=8090
export LLM_API_LOG_LEVEL="INFO"
export LLM_API_MODEL_NAME="gaunernst/gemma-3-12b-it-qat-autoawq"
export LLM_API_REQUEST_TIMEOUT=300
export LLM_API_HEALTH_CHECK_TIMEOUT=5
export LLM_API_CONNECTION_POOL_SIZE=100
export LLM_API_MAX_KEEPALIVE_CONNECTIONS=50
export LLM_API_KEEPALIVE_EXPIRY=60.0
EOF

# =================================
# 3. Export Python Environment
# =================================
echo -e "${YELLOW}🐍 Exporting Python environment...${NC}"

# Check if venv is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "${GREEN}✅ Virtual environment detected: $VIRTUAL_ENV${NC}"
    
    # Export requirements
    pip freeze > "$EXPORT_DIR/requirements.txt"
    
    # Export pip configuration
    pip config list > "$EXPORT_DIR/pip_config.txt" 2>/dev/null || echo "# No pip config" > "$EXPORT_DIR/pip_config.txt"
    
    # Create wheels for custom/source-built packages
    echo -e "${YELLOW}🔄 Creating wheels for source-built packages...${NC}"
    mkdir -p "$EXPORT_DIR/wheels"
    
    # Try to create wheels for the main packages (some might fail if not available)
    echo "Creating wheels..."
    pip wheel --wheel-dir "$EXPORT_DIR/wheels" --no-deps vllm 2>/dev/null || echo "vllm wheel creation failed (expected if built from source)"
    pip wheel --wheel-dir "$EXPORT_DIR/wheels" --no-deps xformers 2>/dev/null || echo "xformers wheel creation failed (expected if built from source)"
    pip wheel --wheel-dir "$EXPORT_DIR/wheels" --no-deps bitsandbytes 2>/dev/null || echo "bitsandbytes wheel creation failed (expected if built from source)"
    pip wheel --wheel-dir "$EXPORT_DIR/wheels" --no-deps flashinfer 2>/dev/null || echo "flashinfer wheel creation failed (expected if built from source)"
    
    # Export site-packages if they exist (for development installs)
    echo -e "${YELLOW}📦 Archiving virtual environment...${NC}"
    if [ -d "$VIRTUAL_ENV" ]; then
        # Create a tar of the entire venv (this will be large but complete)
        tar -czf "$EXPORT_DIR/venv_complete.tar.gz" -C "$(dirname "$VIRTUAL_ENV")" "$(basename "$VIRTUAL_ENV")" 2>/dev/null || {
            echo -e "${YELLOW}⚠️  Full venv archive failed, creating site-packages archive instead...${NC}"
            tar -czf "$EXPORT_DIR/site_packages.tar.gz" -C "$VIRTUAL_ENV/lib/python"*/site-packages . 2>/dev/null || echo "Site-packages archive failed"
        }
    fi
    
else
    echo -e "${RED}❌ No virtual environment activated. Please activate your venv first.${NC}"
    echo "Run: source venv/bin/activate"
    exit 1
fi

# =================================
# 4. Export Project Configuration
# =================================
echo -e "${YELLOW}⚙️ Exporting project configuration...${NC}"

# Copy project config files if they exist
[ -f "llm-api/core/config.py" ] && cp "llm-api/core/config.py" "$EXPORT_DIR/"
[ -f "package.json" ] && cp "package.json" "$EXPORT_DIR/"
[ -f "requirements.txt" ] && cp "requirements.txt" "$EXPORT_DIR/project_requirements.txt"

# Export Python version
python --version > "$EXPORT_DIR/python_version.txt"

# =================================
# 5. Create Import Instructions
# =================================
echo -e "${YELLOW}📝 Creating import instructions...${NC}"

cat > "$EXPORT_DIR/README_IMPORT.md" << 'EOF'
# vLLM Environment Import Guide

This package contains a pre-configured vLLM environment that can be quickly deployed on new cloud instances.

## What's Included
- System package list (`apt_packages.txt`)
- Environment variables (`environment_vars.sh`)
- Python requirements (`requirements.txt`)
- Pre-built wheels (`wheels/` directory)
- Complete virtual environment (`venv_complete.tar.gz` or `site_packages.tar.gz`)
- Project configuration files

## Quick Setup on New Instance

1. Copy this export directory to your new instance
2. Run the import script: `./import_env.sh`
3. Activate the environment: `source venv/bin/activate`
4. Start your services

## Manual Setup (if import script fails)

1. Install system dependencies:
   ```bash
   sudo apt-get update
   sudo xargs -a apt_packages.txt apt-get install -y
   ```

2. Set environment variables:
   ```bash
   source environment_vars.sh
   # Add to ~/.bashrc for persistence
   cat environment_vars.sh >> ~/.bashrc
   ```

3. Create and setup virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip setuptools wheel
   ```

4. Install from wheels (fastest):
   ```bash
   pip install wheels/*.whl --force-reinstall --no-deps
   pip install -r requirements.txt
   ```

5. Or extract complete venv:
   ```bash
   tar -xzf venv_complete.tar.gz
   source venv/bin/activate
   ```

## Verification
After setup, verify the installation:
```bash
python -c "import vllm; print('vLLM imported successfully')"
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
```

## Troubleshooting
- Ensure NVIDIA drivers and CUDA toolkit are installed
- Check that environment variables are properly set
- Verify Python version matches the exported environment
EOF

# =================================
# 6. Export Summary
# =================================
echo -e "${GREEN}✅ Export completed successfully!${NC}"
echo ""
echo -e "${BLUE}📊 Export Summary:${NC}"
echo "   📁 Export directory: $EXPORT_DIR"
echo "   📋 System packages: $(wc -l < "$EXPORT_DIR/apt_packages.txt") packages"
echo "   🐍 Python packages: $(wc -l < "$EXPORT_DIR/requirements.txt") packages"
echo "   💾 Archive size: $(du -sh "$EXPORT_DIR" | cut -f1)"
echo ""
echo -e "${YELLOW}📦 To transfer to new instance:${NC}"
echo "   tar -czf ${EXPORT_DIR}.tar.gz $EXPORT_DIR"
echo "   scp ${EXPORT_DIR}.tar.gz user@new-instance:~/"
echo ""
echo -e "${YELLOW}🚀 On new instance:${NC}"
echo "   tar -xzf ${EXPORT_DIR}.tar.gz"
echo "   cd $EXPORT_DIR"
echo "   ./import_env.sh"
echo ""
echo -e "${GREEN}🎯 Next: Create import script with ./import_env.sh${NC}"
