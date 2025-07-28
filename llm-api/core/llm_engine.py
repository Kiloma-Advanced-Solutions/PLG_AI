"""
LLM engine for handling vLLM server communication
"""
import httpx
import json
import logging
from typing import List, Dict, Any, AsyncGenerator, Tuple
from .config import llm_config, get_model_params
from .models import Message

logger = logging.getLogger(__name__)

class LLMEngine:
    """LLM engine for chat conversations"""
    
    def __init__(self):
        self.chat_url = llm_config.vllm_api_url
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

    async def chat_stream(
        self,
        messages: List[Message],
        session_id: str,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion"""
        if not messages:
            yield 'data: {"error": "No messages provided"}\n\n'
            return

        # Build request payload for vLLM
        model_params = get_model_params()
        payload = {
            **model_params,
            "messages": [{"role": msg.role, "content": msg.content} for msg in formatted_messages],
            "stream": True,
        }
        
        try:
            # Make streaming request
            client = await self.get_client()
            logger.debug(f"Making request to {self.chat_url}")
            async with client.stream("POST", self.chat_url, json=payload, headers=llm_config.vllm_headers) as response:
                if response.status_code != 200:
                    logger.error(f"vLLM API error: {response.status_code}")
                    response_text = await response.text()
                    logger.error(f"vLLM error response: {response_text}")
                    yield f'data: {{"error": "LLM service error: {response.status_code}"}}\n\n'
                    return
                
                # Process streaming response
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                        
                    chunk = line.removeprefix("data: ").strip()
                    if chunk == "[DONE]":
                        yield "data: [DONE]\n\n"
                        break
                        
                    yield f"data: {chunk}\n\n"
        
        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield f'data: {{"error": "An error occurred: {str(e)}"}}\n\n'

# Global LLM engine instance
llm_engine = LLMEngine()
