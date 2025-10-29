"""
LLM Engine for handling OpenAI API calls
"""
import json
import logging
import os
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import AsyncOpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Data models
class Message(BaseModel):
    """Chat message model"""
    role: str  # "system", "user", or "assistant"
    content: str

# Configuration
class LLMConfig:
    """Configuration for LLM services"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.llm_model_name = "gpt-3.5-turbo"
        mcp_servers_str = os.getenv("MCP_SERVERS", "http://localhost:8000,http://localhost:8002")
        self.mcp_servers = [url.strip() for url in mcp_servers_str.split(",")]
        self.request_timeout = 60
        self.max_keepalive_connections = 5
        self.connection_pool_size = 10
        self.keepalive_expiry = 30
        
    def get_model_params(self):
        """Get model-specific parameters"""
        return {
            "temperature": 0.7,
            "max_tokens": 1000,
        }

# Global config instance
llm_config = LLMConfig()

class LLMEngine:
    """LLM engine for chat conversations using OpenAI API"""
    
    def __init__(self):
        self.model_name = llm_config.llm_model_name
        self.client = AsyncOpenAI(api_key=llm_config.openai_api_key)
        logger.info(f"Initialized LLM Engine with model: {self.model_name}")

    async def check_health(self) -> bool:
        """Check if OpenAI API is accessible"""
        return self.client is not None

    def _format_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Format messages for OpenAI API"""
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def _build_payload(self, messages: List[Message], tools: Optional[List[Dict[str, Any]]] = None, stream: bool = False) -> Dict[str, Any]:
        """Build request payload for OpenAI API"""
        payload = {
            "model": self.model_name,
            "messages": self._format_messages(messages),
            "temperature": 0.7,
            "max_tokens": 1000,
        }
        if stream:
            payload["stream"] = True
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        return payload

    async def chat_completion(
        self,
        messages: List[Message],
        session_id: str,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Non-streaming chat completion with optional tools support"""
        if not messages:
            raise ValueError("No messages provided")
        
        logger.info(f"Starting chat completion for session {session_id}")
        if tools:
            logger.info(f"Adding {len(tools)} tools to OpenAI request")
        
        payload = self._build_payload(messages, tools)
        logger.debug(f"OpenAI request payload: {json.dumps(payload, ensure_ascii=False)}")
        
        try:
            response = await self.client.chat.completions.create(**payload)
            response_dict = response.model_dump()
            logger.debug(f"OpenAI response received for session {session_id}")
            return response_dict
        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            raise

    async def chat_stream(
        self,
        messages: List[Message],
        session_id: str,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion with optional tools support"""
        if not messages:
            yield 'data: {"error": "No messages provided"}\n\n'
            return
        
        logger.info(f"Starting streaming chat for session {session_id}")
        if tools:
            logger.info(f"Adding {len(tools)} tools to streaming OpenAI request")
        
        payload = self._build_payload(messages, tools, stream=True)
        logger.debug(f"Streaming OpenAI request payload: {json.dumps(payload, ensure_ascii=False)}")
        
        try:
            stream = await self.client.chat.completions.create(**payload)
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        chunk_data = {"content": delta.content}
                        yield f"data: {json.dumps(chunk_data)}\n\n"
            
            yield "data: [DONE]\n\n"
            logger.info(f"Completed streaming chat for session {session_id}")
        except Exception as e:
            logger.error(f"Streaming chat error: {e}")
            yield f'data: {{"error": "An error occurred: {e}"}}\n\n'

# Global LLM engine instance
llm_engine = LLMEngine()

