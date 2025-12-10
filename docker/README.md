# vLLM Deployment Configurations

### Files

- **`docker-compose.gpu.yml`** - GPU deployment (NVIDIA CUDA)
- **`docker-compose.cpu.yml`** - CPU-only deployment (Apple Silicon M3/M3 Max)

---


### GPU

```bash
# Start vLLM with GPU
docker-compose -f docker-compose.gpu.yml up -d

# Check logs
docker logs vllm -f

# Test the API
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen2-0.5B-Instruct", "messages": [{"role": "user", "content": "Hello!"}]}'
```



### CPU

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

##### This image was built from source for CPU only support following vLLM official documentation:

```bash
# 1. Clone vLLM repository
git clone https://github.com/vllm-project/vllm.git
cd vllm

# 2. Build vLLM image from source
docker build \
  -f docker/Dockerfile.cpu \
  --tag vllm-cpu-env \
  --target vllm-openai \
  --build-arg MAX_JOBS=8 \
  .
```




