# core/llm_engine.py - vLLM Communication
"""
Bridge to vLLM server
- HTTP client management
- Connection pooling
- Streaming handling
- Session tracking
"""

import httpx
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from .config import llm_config, get_default_system_prompt, get_model_params
from .models import Message

logger = logging.getLogger(__name__)


class LLMEngine:
    """Simple LLM engine for chat conversations"""
    
    def __init__(self):
        # vLLM server URLs
        self.base_url = llm_config.vllm_api_url.replace("/v1/chat/completions", "")
        self.chat_url = llm_config.vllm_api_url
        self.models_url = f"{self.base_url}/v1/models"  
        self.metrics_url = llm_config.vllm_metrics_url
        
        self.timeout = llm_config.request_timeout
        self.health_timeout = llm_config.health_check_timeout
        
        # Simple session tracking
        self.active_sessions: Dict[str, str] = {}  # session_id -> started_at
        
        # HTTP client with connection pooling
        self.connection_limits = httpx.Limits(
            max_keepalive_connections=llm_config.max_keepalive_connections,
            max_connections=llm_config.connection_pool_size,
            keepalive_expiry=llm_config.keepalive_expiry
        )
        
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                limits=self.connection_limits,
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                follow_redirects=True
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client and cleanup resources"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        self.active_sessions.clear()

    async def check_health(self) -> bool:
        """Check if vLLM server is responding"""
        try:
            client = await self.get_client()
            response = await client.get(self.models_url, timeout=self.health_timeout)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"vLLM health check failed: {e}")
            return False

    async def get_metrics(self) -> Dict[str, Optional[int]]:
        """Get basic vLLM metrics"""
        try:
            client = await self.get_client()
            response = await client.get(self.metrics_url, timeout=self.health_timeout)
            
            if response.status_code != 200:
                return {"running": None, "waiting": None}
            
            # Simple metrics parsing
            text = response.text
            running = waiting = 0
            
            for line in text.split('\n'):
                if "vllm:num_requests_running" in line and not line.startswith('#'):
                    try:
                        running = int(float(line.split()[-1]))
                    except (ValueError, IndexError):
                        pass
                elif "vllm:num_requests_waiting" in line and not line.startswith('#'):
                    try:
                        waiting = int(float(line.split()[-1]))
                    except (ValueError, IndexError):
                        pass
            
            return {"running": running, "waiting": waiting}
            
        except Exception as e:
            logger.warning(f"Failed to get metrics: {e}")
            return {"running": None, "waiting": None}

    async def chat_stream(
        self, 
        messages: List[Message], 
        session_id: str,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion - main method for conversations
        
        Args:
            messages: List of Message objects (including system prompt if needed)
            session_id: Session ID for tracking (always provided by service layer)
        """
        if not messages:
            yield 'data: {"error": "No messages provided"}\n\n'
            return
        
        # Add system prompt if first message isn't system
        formatted_messages = []
        if not messages or messages[0].role != "system":
            system_prompt = get_default_system_prompt("chat")
            formatted_messages.append(Message(role="system", content=system_prompt))
        
        # Add all provided messages
        formatted_messages.extend(messages)
        
        # Build request payload for vLLM
        model_params = get_model_params()
        payload = {
            **model_params,
            "messages": [{"role": msg.role, "content": msg.content} for msg in formatted_messages],
            "stream": True,
        }
        
        # Track session (session_id is always provided)
        self.active_sessions[session_id] = datetime.now().isoformat()
        logger.info(f"Starting chat for session {session_id}")
        
        try:
            client = await self.get_client()
            async with client.stream(
                "POST", 
                self.chat_url, 
                headers={"Content-Type": "application/json"}, 
                json=payload
            ) as response:
                
                if response.status_code != 200:
                    logger.error(f"vLLM API error: {response.status_code}")
                    yield 'data: {"error": "LLM service error"}\n\n'
                    return
                
                # Process streaming response
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                        
                    chunk = line.removeprefix("data: ").strip()
                    
                    if chunk == "[DONE]":
                        logger.info(f"Completed chat for session {session_id}")
                        yield "data: [DONE]\n\n"
                        break
                        
                    yield f"data: {chunk}\n\n"
                    await asyncio.sleep(0.001)
        
        except httpx.TimeoutException:
            logger.error("Request timed out")
            yield 'data: {"error": "Request timed out"}\n\n'
        except httpx.ConnectError:
            logger.error("Cannot connect to vLLM")
            yield 'data: {"error": "Cannot connect to LLM service"}\n\n'
        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield 'data: {"error": "An error occurred"}\n\n'
        finally:
            # Cleanup session
            if session_id in self.active_sessions:
                self.active_sessions.pop(session_id, None)

    def get_session_info(self) -> Dict[str, Any]:
        """Get simple session information"""
        return {
            "active_sessions": len(self.active_sessions),
            "sessions": list(self.active_sessions.keys())
        }


# Global LLM engine instance
llm_engine = LLMEngine() 