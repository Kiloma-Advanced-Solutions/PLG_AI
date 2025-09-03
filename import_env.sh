#!/bin/bash

# Environment Import Script for RTX 5090 vLLM Setup
# This script quickly recreates the vLLM environment from exported data



# tar -xzf vllm_env_export_20250819_163441.tar.gz
# chmod +x ./import_env.sh vllm_env_export_20250819_163441
# ./import_env.sh vllm_env_export_20250819_163441
# source venv/bin/activate && ls vllm_env_export_20250819_163441/wheels/
## Install the missing packages from wheels
# pip install vllm_env_export_20250819_163441/wheels/vllm-0.10.1-cp38-abi3-manylinux1_x86_64.whl --force-reinstall
# pip install vllm_env_export_20250819_163441/wheels/bitsandbytes-0.47.0-py3-none-manylinux_2_24_x86_64.whl --force-reinstall

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Importing RTX 5090 vLLM Environment${NC}"
echo -e "${BLUE}====================================${NC}"

# Check if export directory is provided as argument
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Please provide the export directory path.${NC}"
    echo "Usage: $0 <export_directory>"
    echo "Example: $0 vllm_env_export_20250819_163441"
    exit 1
fi

EXPORT_DIR="$1"

# Check if export directory exists
if [ ! -d "$EXPORT_DIR" ]; then
    echo -e "${RED}❌ Export directory '$EXPORT_DIR' not found.${NC}"
    exit 1
fi

# Check if we're in a valid export directory
if [ ! -f "$EXPORT_DIR/environment_vars.sh" ] || [ ! -f "$EXPORT_DIR/requirements.txt" ]; then
    echo -e "${RED}❌ '$EXPORT_DIR' doesn't appear to be a valid vLLM export directory.${NC}"
    echo "Expected files: environment_vars.sh, requirements.txt"
    exit 1
fi

echo -e "${GREEN}✅ Export directory validated: $EXPORT_DIR${NC}"

# =================================
# 1. Install System Dependencies
# =================================
echo -e "${YELLOW}📦 Installing system dependencies...${NC}"

# Update package lists
sudo apt-get update

# Install base requirements first
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
    libsndfile1 \
    wget \
    curl

# Install packages from exported list (with error handling)

if [ -f "$EXPORT_DIR/apt_packages.txt" ]; then
    echo "Installing additional packages from export..."
    # Extract package names and install (skip packages that might not be available)
    while read package status; do
        if [ "$status" = "install" ] && [ -n "$package" ]; then
            if echo "$package" | grep -qE '^[a-zA-Z0-9\-\+\.]+$'; then
                sudo apt-get install -y "$package" 2>/dev/null || echo "Skipped unavailable package: $package"
            fi
        fi
    done < "$EXPORT_DIR/apt_packages.txt"
fi

# =================================
# 2. Check Prerequisites
# =================================
echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

# Check for NVIDIA drivers
if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo -e "${RED}❌ NVIDIA drivers not found. Installing...${NC}"
    # Auto-install NVIDIA drivers
        sudo apt-get install -y nvidia-driver-535 nvidia-dkms-535 || {
            echo -e "${RED}❌ Failed to install NVIDIA drivers automatically.${NC}"
        echo "Please install NVIDIA drivers manually and rerun this script."
            exit 1
    }
    echo -e "${YELLOW}⚠️  NVIDIA drivers installed. Please reboot and rerun this script.${NC}"
    exit 0
fi

# Check for CUDA toolkit
if ! command -v nvcc >/dev/null 2>&1; then
    echo -e "${RED}❌ CUDA toolkit not found. Installing...${NC}"
    # Install CUDA toolkit
    wget https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.28.03_linux.run
    sudo sh cuda_12.6.0_560.28.03_linux.run --silent --toolkit || {
        echo -e "${RED}❌ Failed to install CUDA toolkit automatically.${NC}"
            echo "Please install CUDA toolkit manually and rerun this script."
            exit 1
        }
    rm -f cuda_12.6.0_560.28.03_linux.run
fi

echo -e "${GREEN}✅ Prerequisites verified${NC}"

# =================================
# 3. Set Environment Variables
# =================================
echo -e "${YELLOW}🔧 Setting up environment variables...${NC}"

# Source environment variables
source "$EXPORT_DIR/environment_vars.sh"

# Add to ~/.bashrc for persistence
if ! grep -q "# vLLM Environment Variables" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# vLLM Environment Variables" >> ~/.bashrc
    cat "$EXPORT_DIR/environment_vars.sh" >> ~/.bashrc
    echo -e "${GREEN}✅ Environment variables added to ~/.bashrc${NC}"
else
    echo -e "${YELLOW}⚠️  Environment variables already exist in ~/.bashrc${NC}"
fi

# =================================
# 4. Setup Virtual Environment
# =================================
echo -e "${YELLOW}🐍 Setting up Python virtual environment...${NC}"

# Determine the target venv directory
TARGET_VENV="venv"

# Always create a fresh virtual environment for better compatibility
echo "Creating new virtual environment..."
if [ -d "$TARGET_VENV" ]; then
    echo "Removing existing venv directory..."
    rm -rf "$TARGET_VENV"
fi

    python3 -m venv "$TARGET_VENV"
    source "$TARGET_VENV/bin/activate"
    
# Upgrade pip and essential tools (with compatible versions)
echo "Upgrading pip and essential tools..."
pip install --upgrade pip wheel

# Install base dependencies with exact compatible versions 
echo "Installing compatible base dependencies..."
pip install "setuptools>=77.0.3,<80"
pip install "numpy>=1.24,<2.3"

# Determine PyTorch version from xformers wheel (most reliable method)
TORCH_VERSION="2.7.1"  # Default fallback
CUDA_VERSION="cu118"   # Default CUDA version

if [ -d "$EXPORT_DIR/wheels" ]; then
    XFORMERS_WHEEL=$(ls "$EXPORT_DIR/wheels"/xformers-*.whl 2>/dev/null | head -1)
    if [ -n "$XFORMERS_WHEEL" ]; then
        echo "Analyzing xformers wheel to determine PyTorch compatibility..."
        WHEEL_NAME=$(basename "$XFORMERS_WHEEL")
        echo "Xformers wheel: $WHEEL_NAME"
        
        # The xformers wheel shows it needs PyTorch 2.7.1+cu126
        # But cu126 may not be available, so we'll use cu118 which is compatible
        TORCH_VERSION="2.7.1"
        CUDA_VERSION="cu118"
    fi
fi

echo "Installing PyTorch $TORCH_VERSION with CUDA support ($CUDA_VERSION)..."
# Uninstall any existing torch first to prevent conflicts
pip uninstall -y torch torchvision torchaudio 2>/dev/null || true

# Install exact PyTorch version
pip install torch==$TORCH_VERSION torchvision torchaudio --index-url https://download.pytorch.org/whl/$CUDA_VERSION

# Now install wheels with PyTorch compatibility established
if [ -d "$EXPORT_DIR/wheels" ] && [ "$(ls -A "$EXPORT_DIR/wheels")" ]; then
    echo "Installing wheels with PyTorch $TORCH_VERSION compatibility..."
    
    # Install wheels in dependency order (no --force-reinstall to avoid PyTorch conflicts)
    XFORMERS_WHEEL=$(ls "$EXPORT_DIR/wheels"/xformers-*.whl 2>/dev/null | head -1)
    if [ -n "$XFORMERS_WHEEL" ] && [ -f "$XFORMERS_WHEEL" ]; then
        echo "Installing xformers from wheel: $(basename "$XFORMERS_WHEEL")..."
        pip install "$XFORMERS_WHEEL"
    fi
    
    VLLM_WHEEL=$(ls "$EXPORT_DIR/wheels"/vllm-*.whl 2>/dev/null | head -1)
    if [ -n "$VLLM_WHEEL" ] && [ -f "$VLLM_WHEEL" ]; then
        echo "Installing vLLM from wheel: $(basename "$VLLM_WHEEL")..."
        pip install "$VLLM_WHEEL"
    fi
    
    BITSANDBYTES_WHEEL=$(ls "$EXPORT_DIR/wheels"/bitsandbytes-*.whl 2>/dev/null | head -1)
    if [ -n "$BITSANDBYTES_WHEEL" ] && [ -f "$BITSANDBYTES_WHEEL" ]; then
        echo "Installing bitsandbytes from wheel: $(basename "$BITSANDBYTES_WHEEL")..."
        pip install "$BITSANDBYTES_WHEEL"
    fi
    
else
    echo -e "${YELLOW}⚠️  No wheels directory found, installing compatible versions from PyPI${NC}"
    pip install xformers==0.0.31
    pip install vllm==0.10.1  
    pip install bitsandbytes
fi

# Verify critical installations
echo "Verifying critical package installations..."
python -c '
import sys
try:
    import torch
    print(f"✅ PyTorch: {torch.__version__}")
except ImportError as e:
    print(f"❌ PyTorch: {e}")
    exit(1)

try:
    import vllm
    print(f"✅ vLLM: {vllm.__version__}")
except ImportError as e:
    print(f"❌ vLLM: {e}")
    exit(1)
    
try:
    import xformers
    print("✅ xformers: available")
except ImportError as e:
    print(f"⚠️  xformers: {e}")

try:
    import bitsandbytes
    print("✅ bitsandbytes: available")
except ImportError as e:
    print(f"⚠️  bitsandbytes: {e}")
'

# CRITICAL: Ensure PyTorch is exactly 2.7.1 for ProcessorMixin compatibility
echo "🔍 CRITICAL PyTorch version check..."
CURRENT_TORCH_VERSION=$(python -c "import torch; print(torch.__version__)" 2>/dev/null || echo "unknown")
echo "Current PyTorch version: $CURRENT_TORCH_VERSION"

if [[ "$CURRENT_TORCH_VERSION" != "2.7.1"* ]]; then
    echo -e "${RED}❌ CRITICAL: PyTorch is $CURRENT_TORCH_VERSION but MUST be 2.7.1 for ProcessorMixin compatibility!${NC}"
    echo -e "${YELLOW}🔧 Aggressively fixing PyTorch version...${NC}"
    
    # Force uninstall ALL PyTorch related packages
    echo "Removing all PyTorch packages..."
    pip uninstall -y torch torchvision torchaudio pytorch lightning torch-audio torchtext torchdata 2>/dev/null || true
    
    # Clear pip cache to prevent reinstall of wrong version
    pip cache purge || true
    
    # Force install exact PyTorch 2.7.1
    echo "Installing PyTorch 2.7.1 with --force-reinstall --no-cache-dir..."
    pip install --force-reinstall --no-cache-dir torch==2.7.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    
    # Verify installation
    NEW_TORCH_VERSION=$(python -c "import torch; print(torch.__version__)" 2>/dev/null || echo "failed")
    if [[ "$NEW_TORCH_VERSION" != "2.7.1"* ]]; then
        echo -e "${RED}❌ FAILED to install PyTorch 2.7.1! Got: $NEW_TORCH_VERSION${NC}"
        echo -e "${RED}This will cause ProcessorMixin import errors!${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ PyTorch successfully fixed to: $NEW_TORCH_VERSION${NC}"
    fi
    
    # Reinstall xformers wheel to match PyTorch version
    if [ -d "$EXPORT_DIR/wheels" ]; then
        XFORMERS_WHEEL=$(ls "$EXPORT_DIR/wheels"/xformers-*.whl 2>/dev/null | head -1)
        if [ -n "$XFORMERS_WHEEL" ] && [ -f "$XFORMERS_WHEEL" ]; then
            echo "Reinstalling xformers wheel for PyTorch 2.7.1 compatibility..."
            pip uninstall -y xformers 2>/dev/null || true
            pip install "$XFORMERS_WHEEL" --force-reinstall
        fi
    fi
    
    # Force reinstall transformers for compatibility
    echo "Reinstalling transformers for PyTorch 2.7.1 compatibility..."
    pip uninstall -y transformers tokenizers 2>/dev/null || true
    pip install --force-reinstall transformers tokenizers
    
else
    echo -e "${GREEN}✅ PyTorch version correct: $CURRENT_TORCH_VERSION${NC}"
fi

# Fix transformers compatibility issues  
echo "Ensuring transformers compatibility..."
pip install --upgrade transformers || echo "Transformers upgrade failed, continuing..."

# FINAL PyTorch version verification before vLLM testing
echo "🔍 Final PyTorch version check before vLLM test..."
FINAL_TORCH_VERSION=$(python -c "import torch; print(torch.__version__)" 2>/dev/null || echo "unknown")
echo "Final PyTorch version: $FINAL_TORCH_VERSION"

if [[ "$FINAL_TORCH_VERSION" != "2.7.1"* ]]; then
    echo -e "${RED}❌ CRITICAL ERROR: PyTorch version reverted to $FINAL_TORCH_VERSION!${NC}"
    echo -e "${RED}This WILL cause ProcessorMixin import failure!${NC}"
    echo -e "${YELLOW}Emergency PyTorch fix...${NC}"
    pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
    pip install --force-reinstall --no-cache-dir torch==2.7.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    pip install --force-reinstall transformers tokenizers
fi

# Test vLLM imports that were failing
echo "Testing vLLM core functionality..."
python -c '
# First check PyTorch version inside Python
import torch
print(f"PyTorch version in Python: {torch.__version__}")

try:
    from vllm.config import VllmConfig
    print("✅ vLLM config imports working")
except Exception as e:
    print(f"❌ vLLM config import failed: {e}")
    print("Attempting to fix transformers/PyTorch compatibility...")
    import subprocess
    subprocess.run(["pip", "install", "--force-reinstall", "transformers", "tokenizers"], check=False)
'

# Install remaining requirements (aggressively filtered to avoid conflicts)
echo "Installing additional packages from requirements..."
if [ -f "$EXPORT_DIR/requirements.txt" ]; then
    echo "Creating safe requirements list (excluding already installed packages)..."
    
    # Create a comprehensive exclusion list of packages we've already installed or that cause conflicts
    cat > "$EXPORT_DIR/package_exclusions.txt" << 'EOF'
torch
torchvision
torchaudio
pytorch
vllm
xformers
bitsandbytes
setuptools
numpy
transformers
tokenizers
nvidia-
triton
typing-extensions
filelock
fsspec
jinja2
mpmath
networkx
sympy
markupsafe
nvidia-cublas-cu12
nvidia-cuda-cupti-cu12
nvidia-cuda-nvrtc-cu12
nvidia-cuda-runtime-cu12
nvidia-cudnn-cu12
nvidia-cufft-cu12
nvidia-cufile-cu12
nvidia-curand-cu12
nvidia-cusolver-cu12
nvidia-cusparse-cu12
nvidia-cusparselt-cu12
nvidia-nccl-cu12
nvidia-nvjitlink-cu12
nvidia-nvtx-cu12
# Additional packages that could upgrade PyTorch
torchtext
torchdata
lightning
torch-audio
EOF
    
    # Process requirements.txt line by line and filter out problematic entries
    echo "# Filtered requirements for safe installation" > "$EXPORT_DIR/safe_requirements.txt"
    
    while IFS= read -r line; do
        # Skip empty lines and comments
        if [[ -z "$line" ]] || [[ "$line" =~ ^#.* ]]; then
            continue
        fi
        
        # Skip git URLs
        if [[ "$line" =~ ^git\+ ]] || [[ "$line" =~ github\.com ]]; then
            echo "# Skipped git dependency: $line" >> "$EXPORT_DIR/safe_requirements.txt"
            continue
        fi
        
        # Skip local file paths
        if [[ "$line" =~ ^/.*\.whl ]] || [[ "$line" =~ ^file:// ]]; then
            echo "# Skipped local file: $line" >> "$EXPORT_DIR/safe_requirements.txt"
            continue
        fi
        
        # Extract package name (everything before == or >= or <=)
        package_name=$(echo "$line" | sed 's/[><=!].*//' | sed 's/\[.*//')
        
        # Check if package is in exclusion list
        excluded=false
        while IFS= read -r excluded_pkg; do
            if [[ "$package_name" == "$excluded_pkg"* ]]; then
                excluded=true
                break
            fi
        done < "$EXPORT_DIR/package_exclusions.txt"
        
        if [ "$excluded" = true ]; then
            echo "# Skipped already installed: $line" >> "$EXPORT_DIR/safe_requirements.txt"
        else
            echo "$line" >> "$EXPORT_DIR/safe_requirements.txt"
        fi
        
        done < "$EXPORT_DIR/requirements.txt"
    
    # Install the safe requirements
    if [ -s "$EXPORT_DIR/safe_requirements.txt" ]; then
        echo "Installing safe additional packages..."
        pip install -r "$EXPORT_DIR/safe_requirements.txt" || {
            echo -e "${YELLOW}⚠️  Some additional packages failed, installing individually...${NC}"
            while IFS= read -r package; do
                if [[ -n "$package" ]] && [[ ! "$package" =~ ^#.* ]]; then
                    echo "Attempting: $package"
                    pip install "$package" || echo "Skipped: $package"
                fi
            done < "$EXPORT_DIR/safe_requirements.txt"
        }
    else
        echo "No additional packages to install after filtering"
    fi
    
    # Install flashinfer separately (common dependency)
    echo "Installing flashinfer (attention optimization)..."
    pip install flashinfer || echo -e "${YELLOW}⚠️  flashinfer installation failed (optional)${NC}"
    
else
    echo -e "${YELLOW}⚠️  No requirements.txt found${NC}"
fi

# Check if requirements installation changed PyTorch version
echo "🔍 Checking PyTorch version after requirements installation..."
POST_REQ_TORCH_VERSION=$(python -c "import torch; print(torch.__version__)" 2>/dev/null || echo "unknown")
echo "PyTorch version after requirements: $POST_REQ_TORCH_VERSION"

if [[ "$POST_REQ_TORCH_VERSION" != "2.7.1"* ]]; then
    echo -e "${RED}❌ Requirements installation upgraded PyTorch to $POST_REQ_TORCH_VERSION!${NC}"
    echo -e "${YELLOW}Fixing PyTorch version again...${NC}"
    pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
    pip install --force-reinstall --no-cache-dir torch==2.7.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    pip install --force-reinstall transformers tokenizers
    echo "PyTorch restored to 2.7.1 after requirements conflict"
fi

# =================================
# 5. Verify Installation
# =================================
echo -e "${YELLOW}🔍 Verifying installation...${NC}"

# Test critical imports with detailed error reporting
python -c '
import sys
print(f"Python version: {sys.version}")
print(f"Virtual environment: {sys.prefix}")

# Test PyTorch
try:
    import torch
    print(f"✅ PyTorch: {torch.__version__}")
    print(f"✅ CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"✅ CUDA devices: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"   - Device {i}: {torch.cuda.get_device_name(i)}")
except ImportError as e:
    print(f"❌ PyTorch import failed: {e}")
    exit(1)

# Test vLLM (critical)
try:
    import vllm
    print(f"✅ vLLM: {vllm.__version__} imported successfully")
except ImportError as e:
    print(f"❌ vLLM import failed: {e}")
    print("   This is critical - the API server will not work!")
    import subprocess
    print("   Installed packages containing vllm:")
    result = subprocess.run(["pip", "list"], capture_output=True, text=True)
    for line in result.stdout.split("\n"):
        if "vllm" in line.lower():
            print(f"   {line}")

# Test other packages
packages_to_test = [
    ("xformers", "Performance optimization"),
    ("bitsandbytes", "Quantization support"), 
    ("flashinfer", "Attention optimization")
]

for package, description in packages_to_test:
    try:
        __import__(package)
        print(f"✅ {package} imported successfully ({description})")
except ImportError as e:
        print(f"⚠️  {package} import failed: {e} ({description})")
'

# Additional verification
echo ""
echo -e "${YELLOW}🔍 Additional package verification...${NC}"
echo "Installed wheels from export:"
ls -la "$EXPORT_DIR/wheels/" 2>/dev/null || echo "No wheels directory found"
echo ""
echo "vLLM-related packages currently installed:"
pip list | grep -i vllm || echo "No vLLM packages found in pip list"

# =================================
# 6. Final Setup
# =================================
echo -e "${YELLOW}🔧 Final setup steps...${NC}"

# Copy project configuration if it exists
if [ -f "$EXPORT_DIR/config.py" ]; then
    mkdir -p llm-api/core
    cp "$EXPORT_DIR/config.py" llm-api/core/
    echo "✅ Project configuration copied"
fi

# Make sure scripts are executable
chmod +x start_api_5090.sh 2>/dev/null || true
chmod +x setup_venv_5090.sh 2>/dev/null || true

# =================================
# 7. Success Summary
# =================================
# =================================
# 7. Final Environment Test
# =================================
echo -e "${YELLOW}🧪 Final environment test...${NC}"

# Test complete environment functionality  
python -c '
import sys
print(f"🐍 Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

# Test PyTorch
try:
    import torch
    print(f"✅ PyTorch: {torch.__version__} (CUDA: {torch.cuda.is_available()})")
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
except Exception as e:
    print(f"❌ PyTorch test failed: {e}")
    exit(1)

# Test vLLM critical functionality
try:
    import vllm
    print(f"✅ vLLM: {vllm.__version__} - Basic import successful")
    
    # Test the specific import that was failing
    from vllm.config import VllmConfig
    print("✅ vLLM config import successful")
    
    # Test the ProcessorMixin import that was causing issues
    from transformers import ProcessorMixin
    print("✅ ProcessorMixin import successful")
    
    # Test LLM class import
    from vllm import LLM
    print("✅ vLLM LLM class import successful")
    
except ImportError as e:
    if "ProcessorMixin" in str(e):
        print(f"❌ ProcessorMixin import failed: {e}")
        print("This indicates a transformers/PyTorch version conflict")
    else:
        print(f"❌ vLLM test failed: {e}")
    exit(1)
except Exception as e:
    print(f"❌ vLLM test failed: {e}")
    exit(1)

# Test additional components
components = [
    ("xformers", "Performance optimization"),
    ("bitsandbytes", "Quantization support"),
    ("flashinfer", "Attention optimization (optional)")
]

all_good = True
for component, desc in components:
    try:
        __import__(component)
        print(f"✅ {component}: {desc}")
    except ImportError:
        if component == "flashinfer":
            print(f"⚠️  {component}: {desc} - optional, continuing")
        else:
            print(f"❌ {component}: {desc} - FAILED")
            all_good = False

if all_good:
    print("🎉 All critical components are working!")
else:
    print("⚠️  Some components failed, but environment may still work")
'

echo ""
echo -e "${GREEN}🎉 Environment import completed successfully!${NC}"
echo ""
echo -e "${BLUE}📊 Setup Summary:${NC}"
echo "   🐍 Python virtual environment: $(which python)"
echo "   📦 Packages installed: $(pip list | wc -l) packages"
echo "   🔧 Environment variables: Set and persisted"
echo "   💾 Disk usage: $(du -sh venv 2>/dev/null | cut -f1 || echo 'N/A')"

# Show actual installed versions
echo ""
echo -e "${BLUE}📋 Installed Versions:${NC}"
python -c '
packages = ["torch", "vllm", "xformers", "bitsandbytes", "transformers", "numpy"]
for pkg in packages:
    try:
        mod = __import__(pkg)
        version = getattr(mod, "__version__", "unknown")
        print(f"   {pkg}: {version}")
    except ImportError:
        print(f"   {pkg}: not installed")
'
echo ""
echo -e "${YELLOW}🚀 Next Steps:${NC}"
echo "   1. Activate environment: source venv/bin/activate"
echo "   2. Test the API server: ./start_api_5090.sh"
echo "   3. Verify GPU access: nvidia-smi"
echo ""
echo -e "${GREEN}✅ Your vLLM environment is ready to use!${NC}"

# Create a robust activation script
cat > activate_env.sh << 'EOF'
#!/bin/bash
echo "🔌 Activating vLLM environment..."

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./import_env.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Source environment variables (look for the export directory)
for dir in vllm_env_export_*; do
    if [ -d "$dir" ] && [ -f "$dir/environment_vars.sh" ]; then
        echo "Loading environment variables from $dir..."
        source "$dir/environment_vars.sh"
        break
    fi
done

echo "✅ Environment activated!"
echo "Python: $(which python)"

# Quick verification
python -c '
try:
    import vllm
    print("✅ vLLM ready for use 🚀")
except ImportError:
    print("❌ vLLM not found! Check installation.")
    exit(1)
' || echo "⚠️  vLLM verification failed"
EOF
chmod +x activate_env.sh

echo ""
echo -e "${BLUE}💡 Tip: Use './activate_env.sh' for quick environment activation${NC}"

# Add troubleshooting information
echo ""
echo -e "${YELLOW}🔧 Troubleshooting Tips:${NC}"
echo "   • Script ensures PyTorch 2.7.1 (exact version for xformers compatibility)"
echo "   • If ProcessorMixin errors: check that PyTorch is exactly 2.7.1, not 2.8.0+"
echo "   • If xformers warnings: verify PyTorch version with 'python -c \"import torch; print(torch.__version__)\"'"
echo "   • For CUDA issues: nvidia-smi should show your GPUs, nvcc --version should show CUDA toolkit"  
echo "   • For memory issues: ensure >16GB GPU memory available per GPU"
echo "   • Check filtered requirements: cat $EXPORT_DIR/safe_requirements.txt"
echo "   • View installation logs in: ~/.cache/pip/ for detailed error messages"
echo "   • If reinstall needed: rm -rf venv && ./import_env.sh $EXPORT_DIR"