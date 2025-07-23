# ChatPLG Unified LLM API

A unified API server that provides chat functionality using vLLM and Gemma-3-12B model. This API can be used by multiple AI applications and supports streaming responses.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- CUDA-compatible GPU (for vLLM)
- At least 16GB GPU memory (for Gemma-3-12B model)
- Linux/macOS environment

### Installation & Running

1. **Clone the repository and navigate to the API directory:**
   ```bash
   git clone https://github.com/pelegel/ChatPLG-UI.git
   cd ChatPLG-UI
   git checkout new-api
   cd llm-api
   ```

2. **Make the startup script executable:**
   ```bash
   chmod +x start-api.sh
   ```

3. **Run the API server:**
   ```bash
   # For production mode
   ./start-api.sh prod
   
   # For development mode (with auto-reload)
   ./start-api.sh dev
   
   # For default mode
   ./start-api.sh
   ```

The script will automatically:
- Create a virtual environment
- Install all dependencies
- Start the vLLM server on port 8000
- Start the API server on port 8090
- Configure proper port mappings

## 📋 API Endpoints

### Health Check
```bash
curl http://localhost:8090/api/health
```

### Streaming Chat
```bash
curl -X POST http://localhost:8090/api/chat/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Hello! Can you tell me a short joke?"
      }
    ],
    "stream": true
  }' \
  --no-buffer
```

## 🔧 Configuration

### Environment Variables

The API uses the following environment variables (all prefixed with `LLM_API_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `http://localhost` | Base URL for all services |
| `HOST` | `0.0.0.0` | API server host |
| `PORT` | `8090` | API server port |
| `VLLM_PORT` | `8000` | vLLM server port |
| `MODEL_NAME` | `gaunernst/gemma-3-12b-it-qat-autoawq` | Model to load |
| `LOG_LEVEL` | `INFO` | Logging level |

### Model Configuration

The default model is `gaunernst/gemma-3-12b-it-qat-autoawq`, which is a quantized version of Gemma-3-12B optimized for inference.

## ☁️ Cloud Deployment

### AWS EC2 / Google Cloud / Azure VM

For cloud deployment, you'll need to modify the configuration based on your setup:

#### 1. Port Configuration

Edit `core/config.py` to match your cloud instance ports:

```python
# For cloud instances, you might need to change these defaults
frontend_port: int = Field(
    default=3000,  # Your frontend port
    description="Frontend port"
)
api_port: int = Field(
    default=8090,  # Your API port
    description="API port"
)
vllm_port: int = Field(
    default=8000,  # Your vLLM port
    description="vLLM server port"
)
```

#### 2. Security Groups / Firewall

Ensure your cloud instance allows traffic on:
- Port 8090 (API server)
- Port 8000 (vLLM server)
- Port 3000 (if running frontend)

#### 3. Environment Variables

Set environment variables for your cloud instance:

```bash
export LLM_API_BASE_URL="http://your-instance-ip"
export LLM_API_HOST="0.0.0.0"
export LLM_API_PORT=8090
export LLM_API_VLLM_PORT=8000
```

#### 4. GPU Requirements

Ensure your cloud instance has:
- CUDA-compatible GPU
- At least 16GB GPU memory
- CUDA drivers installed

### Docker Deployment

For containerized deployment, create a `Dockerfile`:

```dockerfile
FROM nvidia/cuda:12.1-devel-ubuntu22.04

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy application code
COPY . .

# Make startup script executable
RUN chmod +x start-api.sh

# Expose ports
EXPOSE 8090 8000

# Start the API
CMD ["./start-api.sh", "prod"]
```

### Kubernetes Deployment

For Kubernetes, create deployment manifests:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: llm-api
  template:
    metadata:
      labels:
        app: llm-api
    spec:
      containers:
      - name: llm-api
        image: your-registry/llm-api:latest
        ports:
        - containerPort: 8090
        - containerPort: 8000
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "32Gi"
            cpu: "8"
          requests:
            memory: "16Gi"
            cpu: "4"
---
apiVersion: v1
kind: Service
metadata:
  name: llm-api-service
spec:
  selector:
    app: llm-api
  ports:
  - name: api
    port: 8090
    targetPort: 8090
  - name: vllm
    port: 8000
    targetPort: 8000
  type: LoadBalancer
```

## 🐛 Troubleshooting

### Common Issues

1. **"LLM service is not available"**
   - Check if vLLM server is running: `curl http://localhost:8000/v1/models`
   - Verify port configuration in `core/config.py`
   - Check GPU memory availability

2. **Port already in use**
   - Stop existing processes: `pkill -f "uvicorn main:app"`
   - Change ports in configuration

3. **GPU out of memory**
   - Reduce `tensor-parallel-size` in `start-api.sh`
   - Use a smaller model
   - Increase GPU memory

4. **Permission denied on start-api.sh**
   - Make executable: `chmod +x start-api.sh`

### Logs

Check logs for debugging:
```bash
# API server logs
tail -f /var/log/llm-api.log

# vLLM logs
tail -f /var/log/vllm.log
```

## 📊 Monitoring

### Health Endpoint
```bash
curl http://localhost:8090/api/health
```

### vLLM Metrics
```bash
curl http://localhost:8000/metrics
```

## 🔒 Security Considerations

- Change default ports for production
- Implement authentication/authorization
- Use HTTPS in production
- Restrict network access with firewalls
- Monitor resource usage

## 📝 API Documentation

For detailed API documentation, see:
- `API_OVERVIEW.md` - API structure and design
- `PRD-ChatPLG-Unified-LLM-API.md` - Product requirements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 