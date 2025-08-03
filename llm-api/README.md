# PLG-AI LLM API

A production-ready, self-hosted LLM API server providing unified access to advanced language model capabilities through a RESTful interface. Built with FastAPI and vLLM, optimized for secure, air-gapped environments with support for streaming responses, multi-user sessions, and concurrent processing.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Development](#development)
- [Deployment](#deployment)
- [Monitoring & Health](#monitoring-health)
- [Troubleshooting](#troubleshooting)
- [Security](#security)

## Overview

The PLG-AI LLM API is designed for organizations requiring secure, self-hosted AI capabilities without external dependencies. The system provides:

- **Unified API Interface**: Single API for multiple AI tasks (chat, email summarization, task extraction)
- **High-Performance Hardware**: Optimized for dual RTX 4090 GPU configuration
- **Multi-User Concurrent Access**: Support for the use of multiple simultaneous users
- **Air-Gapped Deployment**: Complete self-hosted solution with no external dependencies
- **Real-time Streaming**: Server-Sent Events for responsive user experiences
- **Production-Ready**: Comprehensive error handling, logging, and monitoring

### Key Features

- ✅ RESTful API with FastAPI framework and async support
- ✅ Real-time streaming responses via Server-Sent Events
- ✅ Session-based conversation management for multiple users
- ✅ Multi-language support (Hebrew/English)
- ✅ Health monitoring and metrics endpoints
- ✅ Production-ready error handling and logging
- ✅ vLLM integration for optimized model inference
- ✅ Configurable model deployment with tensor parallelism

## Architecture

### Technology Stack

- **Backend Framework**: FastAPI 0.104+ for high-concurrency support
- **AI/ML Integration**: Local vLLM server with optimized model deployment
- **Model**: Gemma 3-12b IT Quantized (AutoAWQ) - locally stored
- **Context Window**: 131,072 tokens per session
- **Languages**: Hebrew (primary), English (secondary)
- **Deployment**: Local vLLM server with tensor parallelism across dual RTX 4090

### Hardware Requirements

- **GPU Configuration**: Dual NVIDIA RTX 4090 (24GB VRAM each)
- **CPU**: Minimum 16-core CPU (Intel i7-13700K or AMD Ryzen 9 7900X equivalent)
- **RAM**: 64GB DDR4/DDR5 (minimum), 128GB recommended for heavy concurrent usage
- **Storage**: 2TB NVMe SSD for model storage and temporary data
- **Network**: Local network only (no internet connectivity required)
- **Cooling**: Enterprise-grade cooling for sustained dual GPU operation

## Prerequisites

- Python 3.8+
- CUDA-compatible GPU (for vLLM)
- At least 16GB GPU memory (for Gemma-3-12B model)
- Linux/macOS environment
- NVIDIA drivers and CUDA toolkit installed

## Quick Start

### 1. Clone and Navigate

```bash
git clone https://github.com/Kiloma-Advanced-Solutions/PLG_AI.git
cd PLG_AI/llm-api
```

### 2. Make Startup Script Executable

```bash
chmod +x start-api.sh
```

### 3. Run the API Server

```bash
# Production mode (recommended)
./start-api.sh prod

# Development mode (with auto-reload)
./start-api.sh dev

# Default mode
./start-api.sh
```

The startup script automatically:
- Creates a virtual environment
- Installs all dependencies
- Starts the vLLM server on port 8060
- Starts the API server on port 8090
- Configures proper port mappings and CORS on config.py

### 4. Verify Installation

```bash
# Health check
curl http://localhost:8090/api/health

# Test streaming chat
curl -X POST http://localhost:8090/api/chat/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "שלום! תוכל לספר לי בדיחה?"
      }
    ],
    "stream": true
  }' \
  --no-buffer
```

## Project Structure

```
llm-api/
├── main.py               # FastAPI application entry point
├── start-api.sh          # Production startup script
├── requirements.txt      # Python dependencies
├── core/                 # Core application modules
│   ├── config.py         # Configuration management
│   ├── llm_engine.py     # vLLM integration and model management
│   └── models.py         # Pydantic data models
├── api/                  # API layer
│   ├── routes.py         # API endpoint definitions
│   └── middleware.py     # CORS, error handling middleware
├── services/             # Business logic services
│   ├── chat_service.py   # Chat functionality implementation
│   └── task_service.py   # Task extraction and processing
├── utils/                # Utility functions
│   └── health.py         # Health check utilities
└── tests/                # Test suite
    ├── test_emails.json  # Test data
    └── test_task_extraction.py
```

### Core Components

- **`main.py`**: FastAPI application initialization and configuration
- **`core/config.py`**: Centralized configuration management with environment variable support
- **`core/llm_engine.py`**: vLLM server integration and model inference logic
- **`api/routes.py`**: RESTful API endpoint definitions and request/response handling
- **`services/chat_service.py`**: Chat functionality with streaming support
- **`services/task_service.py`**: Task extraction and processing capabilities

## Configuration

### Environment Variables

All configuration uses the `LLM_API_` prefix for consistency:

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `http://localhost` | Base URL for all services |
| `HOST` | `0.0.0.0` | API server host |
| `PORT` | `8090` | API server port |
| `VLLM_PORT` | `8060` | vLLM server port |
| `MODEL_NAME` | `gaunernst/gemma-3-12b-it-qat-autoawq` | Model to load |
| `LOG_LEVEL` | `INFO` | Logging level |
| `REQUEST_TIMEOUT` | `300` | Request timeout in seconds |
| `HEALTH_CHECK_TIMEOUT` | `5` | Health check timeout |
| `CONNECTION_POOL_SIZE` | `100` | HTTP connection pool size |
| `MAX_KEEPALIVE_CONNECTIONS` | `50` | Maximum keepalive connections |
| `KEEPALIVE_EXPIRY` | `60.0` | Keepalive expiry time |

### Model Configuration

The default model is `gaunernst/gemma-3-12b-it-qat-autoawq`, a quantized version of Gemma-3-12B optimized for inference with:

- **Context Window**: 131,072 tokens
- **Tensor Parallelism**: 2 (optimized for dual RTX 4090)
- **Quantization**: AutoAWQ for memory efficiency
- **Languages**: Hebrew and English support

## API Endpoints

### Core Chat API

#### Streaming Chat
```http
POST /api/chat/stream
Content-Type: application/json
Accept: text/event-stream

{
  "messages": [
    {"role": "user", "content": "שלום, איך אתה?"},
    {"role": "assistant", "content": "שלום! אני בסדר, תודה."}
  ],
  "session_id": "chat_abc123def456",
  "language": "hebrew",
  "stream": true
}
```

**Response (Server-Sent Events):**
```
data: {"type": "content", "content": "שלום! "}
data: {"type": "content", "content": "איך "}
data: {"type": "content", "content": "אני יכול לעזור?"}
data: {"type": "done", "session_id": "chat_abc123def456"}
```

### Health & Monitoring

#### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "vllm_healthy": true,
  "active_sessions": 247,
  "vllm_running_requests": 12,
  "vllm_waiting_requests": 3,
  "timestamp": "2024-12-15T10:30:00Z"
}
```

#### Metrics
```http
GET /api/metrics
```

**Response:**
```json
{
  "active_sessions": 247,
  "total_requests_24h": 15420,
  "average_response_time": 1.8,
  "error_rate": 0.02,
  "uptime": 99.97,
  "resource_usage": {
    "memory": "12.4GB",
    "gpu_memory": "18.2GB",
    "cpu_percent": 67
  }
}
```

## Development

### Local Development Setup

1. **Clone and setup:**
   ```bash
   git clone https://github.com/Kiloma-Advanced-Solutions/PLG_AI.git
   cd PLG_AI/llm-api
   chmod +x start-api.sh
   ```

2. **Start in development mode:**
   ```bash
   ./start-api.sh dev
   ```

3. **Run tests:**
   ```bash
   python -m pytest tests/
   ```

### Development Workflow

1. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and test:**
   ```bash
   # Test your changes
   curl http://localhost:8090/api/health
   ```

3. **Submit pull request:**
   - Ensure all tests pass
   - Update documentation if needed
   - Follow the project's coding standards

### Code Standards

- Use type hints throughout the codebase
- Follow FastAPI best practices
- Implement comprehensive error handling
- Add logging for debugging and monitoring
- Write tests for new functionality

## Deployment

### Production Deployment

#### 1. Environment Setup

```bash
# Set production environment variables
export LLM_API_BASE_URL="http://your-production-domain"
export LLM_API_HOST="0.0.0.0"
export LLM_API_PORT=8090
export LLM_API_VLLM_PORT=8060
export LLM_API_LOG_LEVEL="INFO"
```

#### 2. Start Production Server

```bash
./start-api.sh prod
```

### Cloud Deployment

#### AWS EC2 / Google Cloud / Azure VM

1. **Port Configuration:**
   Edit `core/config.py` to match your cloud instance:

   ```python
   frontend_port: int = Field(default=3000, description="Frontend port")
   api_port: int = Field(default=8090, description="API port")
   vllm_port: int = Field(default=8060, description="vLLM server port")
   ```

2. **Security Groups / Firewall:**
   Ensure your cloud instance allows traffic on:
   - Port 8090 (API server)
   - Port 8060 (vLLM server)
   - Port 3000 (if running frontend)

Ensure your cloud instance has:
- CUDA-compatible GPU
- At least 16GB GPU memory
- CUDA drivers installed

## Monitoring & Health

### Health Checks

```bash
# API health
curl http://localhost:8090/api/health

# vLLM health
curl http://localhost:8060/v1/models

# Basic connectivity
curl http://localhost:8090/ping
```

### Metrics Collection

```bash
# API metrics
curl http://localhost:8090/api/metrics

# vLLM metrics
curl http://localhost:8060/metrics
```

### Logging

The application uses structured logging with configurable levels:

```bash
# View API logs
tail -f /var/log/llm-api.log

# View vLLM logs
tail -f /var/log/vllm.log
```

## Troubleshooting

### Common Issues

#### 1. "LLM service is not available"
```bash
# Check if vLLM server is running
curl http://localhost:8060/v1/models

# Verify port configuration
cat core/config.py | grep vllm_port

# Check GPU memory availability
nvidia-smi
```

#### 2. Port already in use
```bash
# Stop existing processes
pkill -f "uvicorn main:app"
pkill -f "vllm serve"

# Check what's using the ports
lsof -i :8090
lsof -i :8060
```

#### 3. GPU out of memory
```bash
# Reduce tensor parallelism in start-api.sh
# Change --tensor-parallel-size from 2 to 1

# Monitor GPU usage
watch -n 1 nvidia-smi
```

#### 4. Permission denied on start-api.sh
```bash
chmod +x start-api.sh
```

### Performance Optimization

1. **GPU Memory Management:**
   - Monitor GPU memory usage: `nvidia-smi`
   - Adjust tensor parallelism based on available memory
   - Consider model quantization for memory efficiency

2. **Concurrent Users:**
   - vLLM handles request queuing automatically
   - Monitor active sessions via health endpoint
   - Scale based on hardware capabilities

3. **Response Time Optimization:**
   - Use streaming responses for better UX
   - Monitor average response times via metrics
   - Optimize model configuration for your use case

## Security

### Production Security Checklist

- [ ] Change default ports for production
- [ ] Implement authentication/authorization
- [ ] Use HTTPS in production
- [ ] Restrict network access with firewalls
- [ ] Monitor resource usage and access logs
- [ ] Regular security updates and patches
- [ ] Implement rate limiting
- [ ] Secure environment variable management

### Security Best Practices

1. **Network Security:**
   - Use firewalls to restrict access
   - Implement VPN for remote access
   - Monitor network traffic

2. **Application Security:**
   - Validate all input data
   - Implement proper error handling
   - Use secure headers and CORS configuration

3. **Infrastructure Security:**
   - Regular system updates
   - Secure SSH configuration
   - Monitor system logs

