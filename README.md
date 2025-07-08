# ChatPLG-UI

A modern, production-ready Hebrew chat application with real-time streaming AI responses. Built with Next.js, FastAPI, and vLLM for seamless AI-powered conversations.

![ChatPLG-UI](https://img.shields.io/badge/Next.js-15.3.4-black?style=for-the-badge&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688?style=for-the-badge&logo=fastapi)
![vLLM](https://img.shields.io/badge/vLLM-latest-purple?style=for-the-badge)
![TypeScript](https://img.shields.io/badge/TypeScript-latest-3178C6?style=for-the-badge&logo=typescript)

## 🌟 Features

### Core Features
- **🎯 Real-time Streaming**: Live AI responses with streaming support
- **🌍 Hebrew Language Support**: Full RTL support and Hebrew interface
- **💬 Multi-conversation Management**: Persistent chat sessions with local storage
- **📱 Responsive Design**: Mobile-first, modern UI/UX
- **🚀 Production Ready**: Scalable architecture with proper error handling


## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js App   │    │   FastAPI API   │    │   vLLM Server   │
│   (Port 3000)   │◄──►│   (Port 8090)   │◄──►│   (Port 8000)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        │                       │                       │
   ┌─────────┐            ┌─────────────┐        ┌─────────────┐
   │Browser  │            │HTTP Client  │        │AI Model     │
   │Storage  │            │(httpx)      │        │Inference    │
   └─────────┘            └─────────────┘        └─────────────┘
```

### Components
- **Frontend**: Next.js with TypeScript, React components, CSS modules
- **Backend**: FastAPI with streaming responses, session management, CORS
- **AI Engine**: vLLM server with OpenAI-compatible API
- **Storage**: Browser localStorage for conversation persistence

## 🚀 Quick Start

### For Local Development

1. **Clone the repository**:
   ```bash
   git init
   git remote add origin https://github.com/pelegel/ChatPLG-UI.git
   git fetch origin
   git checkout -b connect-to-api origin/connect-to-api
   ```

2. **Start vLLM server** (in separate terminal):
   ```bash
   python3 -m vllm.entrypoints.openai.api_server \   
      --model gaunernst/gemma-3-12b-it-qat-autoawq \ 
      --max-model-len 131072 \
      --port 8000 \  
      --tensor-parallel-size 2 | grep -Ev "Received request chatcmpl|Added request chatcmpl|HTTP/1.1\" 200 OK"
   ```

3. **Use the startup script**:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

   Or manually:
   ```bash
   # Backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python server.py

   # Frontend (new terminal)
   npm install
   npm run dev
   ```

### For Containerized Deployment (vast.ai, etc.)

1. **Setup the environment**:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   npm install
   ```

2. **Configure API endpoint**:
   ```bash
   # Edit src/utils/streaming-api.ts
   # Update API_BASE_URL to your external IP and port
   # Example: 'http://166.113.52.39:42350'
   ```

3. **Start all services**:
   ```bash
   # Terminal 1: vLLM server
   python3 -m vllm.entrypoints.openai.api_server \
     --model gaunernst/gemma-3-12b-it-qat-autoawq \
     --max-model-len 131072 \
     --port 8000 \
     --tensor-parallel-size 2

   # Terminal 2: FastAPI backend
   python server.py

   # Terminal 3: Next.js frontend
   npm run dev
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env.local` file in the root directory:

```env
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8090

# For containerized deployment, use external IP:
# NEXT_PUBLIC_API_BASE_URL=http://your-external-ip:mapped-port
```

### Backend Configuration

Edit `server.py` to customize:

```python
# Model Configuration
MODEL_NAME = "gaunernst/gemma-3-12b-it-qat-autoawq"
VLLM_API_URL = "http://localhost:8000/v1/chat/completions"

# CORS Configuration
allow_origins = ["*"]  # Adjust for production

# System Prompt
SYSTEM_PROMPT = """Your Hebrew AI assistant prompt here..."""
```

### Frontend Configuration

Edit `src/utils/streaming-api.ts` for API settings:

```typescript
// API configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8090';
```

## 📋 API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/stream` | Stream chat completions |
| `GET` | `/api/health` | Health check with vLLM status |
| `GET` | `/api/metrics` | System metrics and active sessions |

### Chat Streaming API

**Request:**
```json
{
  "messages": [
    {
      "type": "user",
      "content": "שלום, מה שלומך?"
    }
  ],
  "session_id": "unique-session-id"
}
```

**Response (Server-Sent Events):**
```
data: {"choices":[{"delta":{"content":"שלום"}}]}
data: {"choices":[{"delta":{"content":"!"}}]}
data: [DONE]
```

## 🛠️ Development

### Project Structure

```
ChatPLG-UI/
├── src/
│   ├── app/                    # Next.js app directory
│   │   ├── page.tsx           # Main chat page
│   │   ├── layout.tsx         # Root layout
│   │   └── globals.css        # Global styles
│   ├── components/            # React components
│   │   ├── chat-container-component/
│   │   ├── chat-message-component/
│   │   ├── sidebar-component/
│   │   └── input-message-container/
│   ├── contexts/              # React contexts
│   │   └── ThemeContext.tsx
│   ├── types/                 # TypeScript definitions
│   │   └── index.ts
│   └── utils/                 # Utilities
│       └── streaming-api.ts   # API client
├── server.py                  # FastAPI backend server
├── requirements.txt           # Python dependencies
├── package.json              # Node.js dependencies
├── start.sh                  # Startup script
└── README.md                 # This file
```

### Key Components

- **`ChatContainerComponent`**: Main chat interface with message display
- **`InputMessageContainer`**: Message input with streaming support
- **`SidebarComponent`**: Conversation management and navigation
- **`ThemeContext`**: Dark/light theme management
- **`streaming-api.ts`**: API client with streaming support

### Development Commands

```bash
# Frontend development
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint

# Backend development
python server.py     # Start FastAPI server
uvicorn server:app --reload  # Development mode with auto-reload
```

## 🐳 Docker Deployment

### Dockerfile Example

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY . .

# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get install -y nodejs

# Install frontend dependencies and build
RUN npm install
RUN npm run build

# Expose ports
EXPOSE 3000 8090

# Start both services
CMD ["./start.sh"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  chatplg-ui:
    build: .
    ports:
      - "3000:3000"
      - "8090:8090"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://localhost:8090
    depends_on:
      - vllm-server
  
  vllm-server:
    image: vllm/vllm-openai:latest
    ports:
      - "8000:8000"
    command: >
      --model gaunernst/gemma-3-12b-it-qat-autoawq
      --port 8000
      --tensor-parallel-size 2
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
```

## 🔍 Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `CONNECTION_REFUSED` | Backend not running | Check if `python server.py` is running |
| `vLLM not healthy` | vLLM server not responding | Verify vLLM server on port 8000 |
| `Model not found` | Incorrect model name | Update `MODEL_NAME` in `server.py` |
| `Port conflicts` | Ports already in use | Check `lsof -i :3000` and `lsof -i :8090` |
| `Hebrew text issues` | Missing font support | Check browser font settings |

### Container-Specific Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `localhost` not working | Container networking | Use external IP instead of localhost |
| Port mapping issues | Incorrect port forwarding | Check port mapping: `external:internal` |
| CORS errors | Missing CORS headers | Update `allow_origins` in `server.py` |

### Debug Commands

```bash
# Check server health
curl http://localhost:8090/api/health

# Check vLLM server
curl http://localhost:8000/v1/models

# Test streaming endpoint
curl -X POST http://localhost:8090/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"type": "user", "content": "שלום"}], "session_id": "test"}'

# Check logs
tail -f /var/log/your-app.log
```

## 🚀 Production Deployment

### Performance Optimizations

1. **Frontend**:
   ```bash
   npm run build
   npm start
   ```

2. **Backend**:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker server:app
   ```

3. **Nginx Configuration**:
   ```nginx
   upstream backend {
       server localhost:8090;
   }

   server {
       listen 80;
       
       location / {
           proxy_pass http://localhost:3000;
       }
       
       location /api/ {
           proxy_pass http://backend;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Security Considerations

- Set specific CORS origins (not `*`)
- Use environment variables for sensitive data
- Implement rate limiting
- Add authentication if needed
- Use HTTPS in production

## 📊 Monitoring

### Health Checks

- **Application**: `GET /api/health`
- **vLLM Server**: `GET /api/health` (includes vLLM status)
- **Metrics**: `GET /api/metrics`

### Logging

- Backend logs: Check terminal running `python server.py`
- Frontend logs: Browser console and Next.js terminal
- vLLM logs: vLLM server terminal

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Development Setup

```bash
# Setup development environment
git clone <your-fork>
cd ChatPLG-UI
npm install
pip install -r requirements.txt

# Run tests
npm test
python -m pytest

# Code formatting
npm run lint
black server.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [vLLM](https://github.com/vllm-project/vllm) for the high-performance inference engine
- [Next.js](https://nextjs.org/) for the React framework
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Hugging Face](https://huggingface.co/) for the model hosting


---

**Made with ❤️ for Hebrew AI conversations**
