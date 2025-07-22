"""
LLM engine for handling vLLM server communication
"""
import httpx
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
from datetime import datetime

from .config import llm_config, get_default_system_prompt, get_model_params
from .models import Message

logger = logging.getLogger(__name__)

class LLMEngine:
    """LLM engine for chat conversations"""
    
    def __init__(self):
        self.chat_url = llm_config.vllm_api_url
        self.metrics_url = llm_config.vllm_metrics_url
        self.models_url = f"{llm_config.vllm_url}/v1/models"
        self.active_sessions: Dict[str, str] = {}  # session_id -> started_at
        self._client = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling"""
        if self._client is None:
            logger.info(f"Creating new HTTP client with timeout={llm_config.request_timeout}s")
            self._client = httpx.AsyncClient(
                timeout=llm_config.request_timeout,
                limits=httpx.Limits(
                    max_keepalive_connections=llm_config.max_keepalive_connections,
                    max_connections=llm_config.connection_pool_size,
                    keepalive_expiry=llm_config.keepalive_expiry
                )
            )
        return self._client

    async def _make_request(self, method: str, url: str, **kwargs) -> Tuple[bool, Any]:
        """Make HTTP request with error handling"""
        try:
            client = await self.get_client()
            logger.debug(f"Making {method} request to {url}")
            
            # Add headers if not provided
            if 'headers' not in kwargs:
                kwargs['headers'] = llm_config.vllm_headers
            
            response = await client.request(method, url, **kwargs)
            
            if response.status_code == 200:
                return True, response
            elif response.status_code == 401:
                logger.error(f"Authentication failed for {url} (401)")
                return False, "Authentication failed. Check vLLM API key."
            elif response.status_code == 404:
                logger.error(f"Endpoint not found: {url} (404)")
                return False, "vLLM endpoint not found."
            else:
                logger.error(f"vLLM request failed: {url} ({response.status_code})")
                return False, f"vLLM request failed with status {response.status_code}"
                
        except httpx.ConnectError as e:
            logger.error(f"Connection error to {url}: {str(e)}")
            return False, f"Cannot connect to vLLM at {llm_config.vllm_url}"
        except httpx.TimeoutException as e:
            logger.error(f"Timeout connecting to {url}: {str(e)}")
            return False, "vLLM request timed out"
        except Exception as e:
            logger.error(f"Unexpected error connecting to {url}: {str(e)}")
            return False, f"Unexpected error: {str(e)}"

    async def check_health(self) -> bool:
        """Check if vLLM server is healthy"""
        success, result = await self._make_request("GET", self.models_url)
        if success:
            logger.info("vLLM health check passed")
            return True
        logger.warning(f"vLLM health check failed: {result}")
        return False

    async def get_metrics(self) -> Dict[str, Any]:
        """Get vLLM server metrics"""
        success, result = await self._make_request("GET", self.metrics_url)
        if success:
            try:
                return result.json()
            except Exception as e:
                logger.error(f"Failed to parse metrics response: {e}")
                return {}
        return {}

    def get_session_info(self) -> Dict[str, Any]:
        """Get information about active sessions"""
        return {
            "active_sessions": len(self.active_sessions)
        }

    async def chat_stream(
        self,
        messages: List[Message],
        session_id: str,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion"""
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
        
        # Track session
        self.active_sessions[session_id] = datetime.now().isoformat()
        logger.info(f"Starting chat for session {session_id}")
        
        try:
            # First check if vLLM is available
            if not await self.check_health():
                logger.error("vLLM server is not healthy, aborting chat request")
                yield 'data: {"error": "LLM service is not available"}\n\n'
                return

            # Make streaming request
            client = await self.get_client()
            async with client.stream("POST", self.chat_url, json=payload, headers=llm_config.vllm_headers) as response:
                if response.status_code != 200:
                    logger.error(f"vLLM API error: {response.status_code}")
                    yield f'data: {{"error": "LLM service error: {response.status_code}"}}\n\n'
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
        
        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield f'data: {{"error": "An error occurred: {str(e)}"}}\n\n'
        finally:
            # Cleanup session
            if session_id in self.active_sessions:
                self.active_sessions.pop(session_id, None)

# Global LLM engine instance
llm_engine = LLMEngine() 