# ChatPLG-UI with Unified LLM API

A simple Hebrew chatbot with real-time AI responses, powered by a reusable LLM API for multiple AI applications.

![Next.js](https://img.shields.io/badge/Next.js-15.3.4-black?style=for-the-badge&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688?style=for-the-badge&logo=fastapi)

## 🚀 Quick Start

### 1. Start vLLM Server
```bash
python3 -m vllm.entrypoints.openai.api_server \
  --model gaunernst/gemma-3-12b-it-qat-autoawq \
  --max-model-len 131072 \
  --port 8000 \
  --tensor-parallel-size 2
```

### 2. Start LLM API
```bash
cd llm-api
./start-unified-api.sh
```

### 3. Start Frontend
```bash
npm install
npm run dev
```

### 4. Open Chatbot
- **Chatbot**: http://localhost:3000
- **API Docs**: http://localhost:8090/docs

## 🏗️ Project Structure

```
ChatPLG-UI/
├── llm-api/                    # Unified LLM API (reusable)
│   ├── core/                   # Core LLM functionality
│   ├── services/               # AI services (chat, email, tasks)
│   ├── api/                    # REST API endpoints
│   ├── utils/                  # Health monitoring
│   ├── main.py                 # FastAPI entry point
│   └── start-unified-api.sh    # API startup script
├── src/                        # Frontend chatbot
│   ├── app/                    # Next.js pages
│   ├── components/             # React components
│   └── utils/                  # Frontend utilities
└── package.json                # Frontend dependencies
```

## 🔧 Configuration

### LLM API Configuration
Create `llm-api/.env` for custom settings:
```bash
LLM_API_vllm_api_url=http://localhost:8000/v1/chat/completions
LLM_API_MODEL_NAME=gaunernst/gemma-3-12b-it-qat-autoawq
LLM_API_PORT=8090
LLM_API_LOG_LEVEL=INFO
```

### Frontend Configuration
Edit `src/utils/streaming-api.ts`:
```typescript
const API_BASE_URL = 'http://localhost:8090';
```

## 🔌 Using the API for Other Applications

The unified API can be reused for multiple AI applications:

### Email Summarization
```python
import httpx

async def summarize_email(email_content):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8090/api/email/summary",
            json={"email_content": email_content}
        )
        return response.json()
```

### Task Extraction
```javascript
const extractTasks = async (text) => {
  const response = await fetch('http://localhost:8090/api/tasks/extract', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text_content: text })
  });
  return response.json();
};
```

## 📋 Available Endpoints

### Chatbot (Currently Used)
- `POST /api/chat/stream` - Stream chat completions
- `GET /api/health` - Health check

### Future Applications
- `POST /api/email/summary` - Email summarization
- `POST /api/tasks/extract` - Task extraction
- `POST /api/completion` - General text completion

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| API connection refused | Start API: `cd llm-api && ./start-unified-api.sh` |
| vLLM not responding | Start vLLM server on port 8000 |
| Port conflicts | Check `lsof -i :3000` and `lsof -i :8090` |

### Quick Health Check
```bash
curl http://localhost:8090/api/health
```

## 📄 License

MIT License
