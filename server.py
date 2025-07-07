from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
import asyncio
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ChatBot API", version="1.0.0")

# Add CORS middleware to allow React app to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your React app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VLLM_API_URL = "http://localhost:8000/v1/chat/completions"
VLLM_METRICS_URL = "http://localhost:8000/metrics"  # vLLM metrics endpoint
MODEL_NAME = "gaunernst/gemma-3-12b-it-qat-autoawq"

# Request models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    stream: Optional[bool] = True
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.7

class ChatResponse(BaseModel):
    response: str
    usage: Optional[Dict[str, Any]] = None

async def get_vllm_request_metrics():
    """Query vLLM metrics endpoint and extract running/waiting request counts"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(VLLM_METRICS_URL)
            metrics_text = response.text
            
            running_requests = 0
            waiting_requests = 0
            
            # Parse metrics to find running and waiting request counts using the correct metric names
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
        logger.error(f"Error fetching metrics: {e}")
        return None, None

async def stream_vllm_response(messages: List[Message], max_tokens: Optional[int] = None, temperature: float = 0.7):
    """Stream responses from vLLM server"""
    headers = {"Content-Type": "application/json"}
    
    # Convert messages to the format expected by vLLM
    formatted_messages = []
    for msg in messages:
        if msg.role == "system":
            formatted_messages.append({
                "role": "system", 
                "content": [{"type": "text", "text": msg.content}]
            })
        else:
            formatted_messages.append({
                "role": msg.role,
                "content": [{"type": "text", "text": msg.content}]
            })
    
    payload = {
        "model": MODEL_NAME,
        "messages": formatted_messages,
        "stream": True,
        "temperature": temperature
    }
    
    if max_tokens:
        payload["max_tokens"] = max_tokens
    
    logger.info(f"Sending request to vLLM with {len(formatted_messages)} messages")
    
    # Get metrics before sending the request
    running, waiting = await get_vllm_request_metrics()
    logger.info(f"Before request - Running: {running}, Waiting: {waiting}")
    
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", VLLM_API_URL, headers=headers, json=payload) as response:
                response.raise_for_status()
                
                # Get metrics right after the request starts
                running, waiting = await get_vllm_request_metrics()
                logger.info(f"Request started - Running: {running}, Waiting: {waiting}")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        chunk = line.removeprefix("data: ").strip()
                        if chunk == "[DONE]":
                            # Get metrics at the end of response generation
                            running, waiting = await get_vllm_request_metrics()
                            logger.info(f"Request completed - Running: {running}, Waiting: {waiting}")
                            
                            yield "data: [DONE]\n\n"
                            break
                        yield f"data: {chunk}\n\n"
                    await asyncio.sleep(0.01)  # Yield control
                    
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from vLLM: {e}")
        error_data = {
            "error": {
                "message": f"Error from LLM server: {e.response.status_code}",
                "type": "llm_error"
            }
        }
        yield f"data: {json.dumps(error_data)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        error_data = {
            "error": {
                "message": "An unexpected error occurred",
                "type": "server_error"
            }
        }
        yield f"data: {json.dumps(error_data)}\n\n"
        yield "data: [DONE]\n\n"

@app.post("/stream")
async def stream_endpoint(request: ChatRequest):
    """Stream chat completions endpoint"""
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="Messages array cannot be empty")
        
        return StreamingResponse(
            stream_vllm_response(
                request.messages, 
                request.max_tokens, 
                request.temperature
            ), 
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
    except Exception as e:
        logger.error(f"Error in stream endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Non-streaming chat endpoint for cases where you need a simple request-response"""
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="Messages array cannot be empty")
        
        # Collect the full response
        full_response = ""
        async for chunk in stream_vllm_response(request.messages, request.max_tokens, request.temperature):
            if chunk.startswith("data: "):
                chunk_data = chunk.removeprefix("data: ").strip()
                if chunk_data == "[DONE]":
                    break
                try:
                    data = json.loads(chunk_data)
                    if "choices" in data and len(data["choices"]) > 0:
                        delta = data["choices"][0]["delta"].get("content", "")
                        full_response += delta
                except (json.JSONDecodeError, KeyError):
                    continue
        
        return ChatResponse(response=full_response)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if vLLM server is accessible
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(VLLM_METRICS_URL)
            response.raise_for_status()
            
        return {"status": "healthy", "vllm_server": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "vllm_server": "disconnected", "error": str(e)}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "ChatBot API",
        "version": "1.0.0",
        "endpoints": {
            "stream": "/stream - POST - Stream chat completions",
            "chat": "/chat - POST - Non-streaming chat completions", 
            "health": "/health - GET - Health check"
        }
    }
