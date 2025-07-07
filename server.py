from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
import json
import logging
from typing import List, Dict, Any
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatPLG API",
    description="Chat API with streaming responses",
    version="1.0.0"
)

# Configure CORS for React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
VLLM_API_URL = "http://localhost:8000/v1/chat/completions"
VLLM_METRICS_URL = "http://localhost:8000/metrics"
MODEL_NAME = "gaunernst/gemma-3-12b-it-qat-autoawq"

# System prompt for Hebrew responses
SYSTEM_PROMPT = """אתה עוזר בינה מלאכותית שמטרתו לספק מידע מדויק ואמין בשפה העברית. ענה באופן ברור, מדויק, ומבוסס על עובדות בלבד. אל תנחש – אם אינך בטוח בתשובה, כתוב שאתה לא יודע או שהמידע חסר."""

# In-memory session storage (for production, use Redis or similar)
active_sessions: Dict[str, Dict[str, Any]] = {}

running_requests = []
waiting_requests = []

async def get_vllm_request_metrics():
    """Query vLLM metrics endpoint and extract running/waiting request counts"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(VLLM_METRICS_URL)
            metrics_text = response.text
            
            running_requests = 0
            waiting_requests = 0
            
            # Parse metrics to find running and waiting request counts
            for line in metrics_text.split('\n'):
                if "vllm:num_requests_running" in line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2:
                        running_requests = int(float(parts[-1]))
                elif "vllm:num_requests_waiting" in line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2:
                        waiting_requests = int(float(parts[-1]))
            
            return running_requests, waiting_requests
    except Exception as e:
        logger.error(f"Error fetching vLLM metrics: {e}")
        return None, None

async def check_vllm_health():
    """Check if vLLM server is healthy"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(VLLM_API_URL.replace('/v1/chat/completions', '/health'))
            return response.status_code == 200
    except Exception as e:
        logger.error(f"vLLM health check failed: {e}")
        return False

def prepare_messages_for_vllm(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prepare messages for vLLM API format"""
    formatted_messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    
    for msg in messages:
        if msg.get("type") == "user":
            formatted_messages.append({
                "role": "user",
                "content": msg.get("content", "")
            })
        elif msg.get("type") == "assistant":
            formatted_messages.append({
                "role": "assistant", 
                "content": msg.get("content", "")
            })
    
    return formatted_messages

async def stream_vllm_response(messages: List[Dict[str, Any]], session_id: str):
    """Stream response from vLLM with enhanced error handling"""
    try:
        # Check vLLM health first
        if not await check_vllm_health():
            logger.error("vLLM server is not healthy")
            yield f"data: {json.dumps({'error': 'AI service is currently unavailable. Please try again later.'})}\n\n"
            return

        headers = {"Content-Type": "application/json"}
        formatted_messages = prepare_messages_for_vllm(messages)
        
        payload = {
            "model": MODEL_NAME,
            "messages": formatted_messages,
            "stream": True,
        }
        
        logger.info(f"Starting stream for session {session_id}")
        
        # Get metrics before request
        running, waiting = await get_vllm_request_metrics()
        if running is not None and waiting is not None:
            logger.info(f"Session {session_id} - Before request: Running={running}, Waiting={waiting}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", VLLM_API_URL, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    logger.error(f"vLLM API error: {response.status_code}")
                    yield f"data: {json.dumps({'error': 'Failed to get response from AI service.'})}\n\n"
                    return
                
                # Track session
                active_sessions[session_id] = {
                    "started_at": datetime.now().isoformat(),
                    "status": "streaming"
                }
                
                try:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            chunk = line.removeprefix("data: ").strip()
                            if chunk == "[DONE]":
                                # Get final metrics
                                running, waiting = await get_vllm_request_metrics()
                                if running is not None and waiting is not None:
                                    logger.info(f"Session {session_id} - Completed: Running={running}, Waiting={waiting}")
                                
                                # Clean up session
                                active_sessions.pop(session_id, None)
                                yield "data: [DONE]\n\n"
                                break
                            yield f"data: {chunk}\n\n"
                        await asyncio.sleep(0.001)  # Small delay to prevent overwhelming
                        
                except Exception as e:
                    logger.error(f"Error during streaming for session {session_id}: {e}")
                    active_sessions.pop(session_id, None)
                    yield f"data: {json.dumps({'error': 'Stream interrupted. Please try again.'})}\n\n"
                    
    except Exception as e:
        logger.error(f"Error in stream_vllm_response for session {session_id}: {e}")
        active_sessions.pop(session_id, None)
        yield f"data: {json.dumps({'error': 'An unexpected error occurred. Please try again.'})}\n\n"

@app.post("/api/chat/stream")
async def stream_chat(request: Request):
    """Stream chat completions endpoint"""
    try:
        body = await request.json()
        messages = body.get("messages", [])
        session_id = body.get("session_id", str(uuid.uuid4()))
        
        if not messages:
            raise HTTPException(status_code=400, detail="Messages are required")
        
        logger.info(f"Received chat request for session {session_id} with {len(messages)} messages")
        
        return StreamingResponse(
            stream_vllm_response(messages, session_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in stream_chat: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    vllm_healthy = await check_vllm_health()
    running, waiting = await get_vllm_request_metrics()
    
    return {
        "status": "healthy" if vllm_healthy else "unhealthy",
        "vllm_healthy": vllm_healthy,
        "active_sessions": len(active_sessions),
        "vllm_running_requests": running,
        "vllm_waiting_requests": waiting,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/metrics")
async def get_metrics():
    """Get current system metrics"""
    running, waiting = await get_vllm_request_metrics()
    
    return {
        "active_sessions": len(active_sessions),
        "vllm_running_requests": running,
        "vllm_waiting_requests": waiting,
        "sessions": {
            session_id: {
                "started_at": data.get("started_at"),
                "status": data.get("status")
            }
            for session_id, data in active_sessions.items()
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090, log_level="info")
