"""
LLM Engine for handling OpenAI API calls
"""
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import AsyncOpenAI
from models import Message
from config import llm_config

logger = logging.getLogger(__name__)

class LLMEngine:
    """LLM engine for chat conversations using OpenAI API"""
    
    def __init__(self):
        self.model_name = llm_config.llm_model_name
        self.client = AsyncOpenAI(api_key=llm_config.openai_api_key)
        logger.info(f"Initialized LLM Engine with model: {self.model_name}")

    async def check_health(self) -> bool:
        """Check if OpenAI API is accessible"""
        try:
            # Simple validation that client is initialized
            return self.client is not None
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def _format_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Format messages for OpenAI API"""
        return [{"role": msg.role, "content": msg.content} for msg in messages]

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
        
        # Build request payload
        payload = {
            "model": self.model_name,
            "messages": self._format_messages(messages),
            "temperature": 0.7,
            "max_tokens": 1000,
        }
        
        # Add tools if provided (for function calling)
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
            logger.info(f"Adding {len(tools)} tools to OpenAI request")
        
        logger.debug(f"OpenAI request payload: {json.dumps(payload, ensure_ascii=False)}")
        
        try:
            response = await self.client.chat.completions.create(**payload)
            
            # Convert to the expected format
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
        
        # Build request payload
        payload = {
            "model": self.model_name,
            "messages": self._format_messages(messages),
            "temperature": 0.7,
            "max_tokens": 1000,
            "stream": True,
        }
        
        # Add tools if provided
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
            logger.info(f"Adding {len(tools)} tools to streaming OpenAI request")
        
        logger.debug(f"Streaming OpenAI request payload: {json.dumps(payload, ensure_ascii=False)}")
        
        try:
            stream = await self.client.chat.completions.create(**payload)
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        # Format as SSE
                        chunk_data = {
                            "content": delta.content
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n"
                
                await asyncio.sleep(0.001)
            
            yield "data: [DONE]\n\n"
            logger.info(f"Completed streaming chat for session {session_id}")
        
        except Exception as e:
            logger.error(f"Streaming chat error: {e}")
            yield f'data: {{"error": "An error occurred: {e}"}}\n\n'

# Global LLM engine instance
llm_engine = LLMEngine()

