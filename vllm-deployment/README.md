# vLLM Deployment Configurations

This directory contains Docker Compose configurations for deploying vLLM with both CPU and GPU support.

## 📁 Files

- **`docker-compose.cpu.yml`** - CPU-only deployment (Apple Silicon M3/M3 Max)
- **`docker-compose.gpu.yml`** - GPU deployment (NVIDIA CUDA)

---

## 🖥️ CPU Deployment (Apple Silicon)

### Prerequisites

- Mac with M3/M3 Max/M3 Pro chip
- Docker Desktop with **32GB+ memory allocation**
- 15GB+ free RAM

### Quick Start

```bash
# Start vLLM with CPU
docker-compose -f docker-compose.cpu.yml up -d

# Check logs
docker logs vllm-cpu -f

# Test the API
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen2-0.5B-Instruct", "messages": [{"role": "user", "content": "Hello!"}]}'
```

### Configuration Details

```yaml
image: peleg28/vllm-cpu-env:latest  # Custom ARM64 CPU-optimized image
shm_size: '8gb'                      # Shared memory for PyTorch
environment:
  VLLM_CPU_KVCACHE_SPACE: "4"         # 4GB KV cache
  VLLM_CPU_OMP_THREADS_BIND: "0-7"    # Use 8 CPU cores
  VLLM_WORKER_MULTIPROC_METHOD: "spawn"  # macOS stability
command:
  --model Qwen/Qwen2-0.5B-Instruct     # Small, CPU-friendly model
  --max-model-len 2048                  # Context window
  --dtype float16                       # Memory-efficient precision
```

### Performance Expectations

- **First token latency**: ~2-3 seconds
- **Generation speed**: ~5-10 tokens/second
- **Memory usage**: ~14-15GB total
- **Concurrent requests**: 2-3 efficiently

---

## 🚀 GPU Deployment (NVIDIA)

### Prerequisites

- NVIDIA GPU with CUDA support (RTX 3090, 4090, A100, etc.)
- Docker with NVIDIA Container Toolkit installed
- CUDA drivers installed

### Install NVIDIA Container Toolkit

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### Quick Start

```bash
# Start vLLM with GPU
docker-compose -f docker-compose.gpu.yml up -d

# Monitor GPU usage
watch -n 1 nvidia-smi

# Check logs
docker logs vllm-gpu -f

# Test the API
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen2-0.5B-Instruct", "messages": [{"role": "user", "content": "Hello!"}]}'
```

### Configuration Details

```yaml
image: vllm/vllm-openai:latest  # Official GPU-enabled image
shm_size: '16gb'                 # Larger shared memory for GPU
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all             # Use all GPUs
          capabilities: [gpu]
command:
  --model Qwen/Qwen2-0.5B-Instruct
  --max-model-len 8192           # Larger context for GPU
  --dtype auto                    # Auto-detect best dtype
  --tensor-parallel-size 1        # 1 GPU (set to 2+ for multi-GPU)
  --gpu-memory-utilization 0.9    # Use 90% of GPU memory
```

### Performance Expectations

- **First token latency**: <100ms
- **Generation speed**: 100-200+ tokens/second (depends on GPU)
- **Memory usage**: ~8-12GB GPU memory
- **Concurrent requests**: 10-50+ (depends on GPU memory)

---

## 🔨 How We Built the CPU Image

The custom `peleg28/vllm-cpu-env:latest` image was built from source because:
- ❌ No official ARM64 CPU images exist for Apple Silicon
- ❌ Pre-built vLLM images require NVIDIA GPUs
- ✅ Need CPU-only optimization for M3 MAX

### Build Process

```bash
# 1. Clone vLLM repository
git clone https://github.com/vllm-project/vllm.git
cd vllm

# 2. Build custom Docker image (requires 32GB Docker memory)
docker build \
  -f docker/Dockerfile.cpu \
  --tag vllm-cpu-env \
  --target vllm-openai \
  --build-arg MAX_JOBS=8 \
  .

# 3. Tag for Docker Hub
docker tag vllm-cpu-env peleg28/vllm-cpu-env:latest
docker tag vllm-cpu-env peleg28/vllm-cpu-env:m3-arm64

# 4. Push to Docker Hub
docker push peleg28/vllm-cpu-env:latest
docker push peleg28/vllm-cpu-env:m3-arm64
```

### What the Build Includes

The `Dockerfile.cpu` builds vLLM with:
- **ARM Compute Library** - Apple Silicon optimization
- **Intel oneDNN** - Deep Neural Network primitives for CPU
- **CPU-specific optimizations** - No CUDA/GPU dependencies
- **OpenMP support** - Multi-threaded CPU inference
- **vLLM v0.11.2** - Latest stable version

### Build Time & Resources

- **Build time**: 10-15 minutes
- **Docker memory needed**: 32GB (build fails with less)
- **Final image size**: 2.8GB
- **Architecture**: linux/arm64 (Apple Silicon)

### Why Build from Source?

```
Official vLLM Images:
├── vllm/vllm-openai:latest (GPU only, x86_64) ❌
├── vllm/vllm-openai:v0.x.x (GPU only, x86_64) ❌
└── No ARM64 CPU images ❌

Custom Build:
└── peleg28/vllm-cpu-env:latest (CPU, ARM64) ✅
    ├── Optimized for Apple Silicon
    ├── No GPU dependencies
    └── Production-ready OpenAI API
```

---

## 📊 Comparison: CPU vs GPU

| Feature | CPU (M3 MAX) | GPU (RTX 4090) |
|---------|--------------|----------------|
| **Speed** | ~5-10 tok/s | ~150-200 tok/s |
| **Latency** | 2-3s | <100ms |
| **Cost** | Mac only | GPU server needed |
| **Memory** | 15GB RAM | 12GB VRAM |
| **Context** | 2K tokens | 32K+ tokens |
| **Concurrent Users** | 2-3 | 20-50+ |
| **Best For** | Development, testing | Production, large models |

---

## 🔧 Configuration Options

### CPU Tuning

```yaml
environment:
  # Increase for more parallel requests (uses more RAM)
  VLLM_CPU_KVCACHE_SPACE: "8"
  
  # Use more CPU cores (adjust for your CPU)
  VLLM_CPU_OMP_THREADS_BIND: "0-11"  # 12 cores
  
command:
  # Increase context window (uses more RAM)
  --max-model-len 4096
  
  # Use different model
  --model meta-llama/Llama-3.2-1B-Instruct
```

### GPU Tuning

```yaml
command:
  # Multi-GPU setup (for 2 GPUs)
  --tensor-parallel-size 2
  
  # Larger context for powerful GPUs
  --max-model-len 32768
  
  # Enable prefix caching (speeds up repeated prompts)
  --enable-prefix-caching
  
  # Use specific GPUs
  environment:
    CUDA_VISIBLE_DEVICES: "0,1"  # Use GPU 0 and 1
```

---

## 🐛 Troubleshooting

### CPU Issues

**"Cannot allocate memory"**
```bash
# Increase Docker memory to 32GB in Docker Desktop settings
# Settings → Resources → Memory → 32GB
```

**"Container exits immediately"**
```bash
# Check logs
docker logs vllm-cpu

# Reduce memory usage
VLLM_CPU_KVCACHE_SPACE: "2"
--max-model-len 1024
```

### GPU Issues

**"CUDA not available"**
```bash
# Install NVIDIA Container Toolkit
# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

**"Out of GPU memory"**
```bash
# Reduce GPU memory utilization
--gpu-memory-utilization 0.7

# Use smaller model
--model Qwen/Qwen2-0.5B-Instruct

# Enable CPU offloading
--enable-cpu-offload
```

---

## 📚 Additional Resources

- [vLLM Documentation](https://docs.vllm.ai/)
- [Docker Hub - peleg28/vllm-cpu-env](https://hub.docker.com/r/peleg28/vllm-cpu-env)
- [vLLM GitHub Repository](https://github.com/vllm-project/vllm)
- [OpenAI API Compatibility](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html)

---

## 🤝 Contributing

To improve these configurations:
1. Fork the repository
2. Make your changes
3. Test thoroughly
4. Submit a pull request

---

## 📝 License

These configurations are provided as-is for the PLG_AI project.

---

## ✨ Credits

Custom vLLM CPU image built and maintained by [@pelegel](https://github.com/pelegel)

