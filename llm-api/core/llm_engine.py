"""
LLM Engine for handling model inference and chat completions
"""
import json
import asyncio
import httpx
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple, Type
from pydantic import BaseModel, TypeAdapter
from datetime import datetime
from .config import llm_config
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

    # get or create HTTP client with connection pooling
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling"""
        if self._client is None:
            logger.info(f"Creating new HTTP client with timeout={llm_config.request_timeout}s")
            self._client = httpx.AsyncClient(
                timeout=llm_config.request_timeout,
                limits=httpx.Limits(
                    max_keepalive_connections=llm_config.max_keepalive_connections,    # Maximum number of keepalive connections
                    max_connections=llm_config.connection_pool_size,    # Maximum number of connections in the pool
                    keepalive_expiry=llm_config.keepalive_expiry    # Time to keep a connection alive (in seconds)
                )
            )
        return self._client

    
    async def _make_request(self, method: str, url: str, **kwargs) -> Tuple[bool, Any]:
        """Make HTTP request with error handling"""
        try:
            client = await self.get_client()    

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
            logger.error(f"Connection error to {url}: {e}")
            return False, f"Cannot connect to vLLM at {llm_config.vllm_url}"
        except httpx.TimeoutException as e:
            logger.error(f"Timeout connecting to {url}: {e}")
            return False, "vLLM request timed out"
        except Exception as e:
            logger.error(f"Unexpected error connecting to {url}: {e}")
            return False, f"Unexpected error: {e}"


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


    def _format_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Format messages for vLLM API"""
        return [{"role": msg.role, "content": msg.content} for msg in messages]



    async def chat_stream(
        self,
        messages: List[Message],
        session_id: str,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion"""
        if not messages:
            yield 'data: {"error": "No messages provided"}\n\n'
            return
        
        # Track session
        self.active_sessions[session_id] = datetime.now().isoformat()
        logger.info(f"Starting chat for session {session_id}")
        
        # Build request payload for vLLM
        model_params = llm_config.get_model_params()
        payload = {
            "model": llm_config.llm_model_name,
            **model_params,
            "messages": self._format_messages(messages),
            "stream": True,
        }
        logger.debug(f"Request payload: {json.dumps(payload, ensure_ascii=False)}")
        
        try:
            # First check if vLLM is available
            if not await self.check_health():
                logger.error("vLLM server is not healthy, aborting chat request")
                yield 'data: {"error": "LLM service is not available"}\n\n'
                return

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
                logger.debug("Starting to process streaming response")
                line_count = 0
                async for line in response.aiter_lines():
                    line_count += 1
                    logger.debug(f"Received line {line_count}: {line}")
                    
                    if not line.startswith("data: "):
                        logger.debug(f"Skipping non-data line: {line}")
                        continue
                        
                    chunk = line.removeprefix("data: ").strip()
                    
                    if chunk == "[DONE]":
                        logger.info(f"Completed chat for session {session_id}")
                        yield "data: [DONE]\n\n"
                        break
                        
                    yield f"data: {chunk}\n\n"
                    await asyncio.sleep(0.001)
                
                logger.debug(f"Processed {line_count} lines from vLLM")
        
        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield f'data: {{"error": "An error occurred: {e}"}}\n\n'
        finally:
            # Cleanup session
            if session_id in self.active_sessions:
                self.active_sessions.pop(session_id, None)


    async def get_structured_completion(
        self,
        messages: List[Message],
        output_schema: Type[BaseModel], # the class of the output schema
        session_id: str = "structured_completion"
    ) -> BaseModel:
        """Get structured completion for task extraction"""
        if not messages:
            raise ValueError("No messages provided")
        
        # Track session
        self.active_sessions[session_id] = datetime.now().isoformat()
        logger.info(f"Starting structured completion for session {session_id}")
        
        # Build request payload for vLLM (non-streaming)
        model_params = llm_config.get_model_params()
        payload = {
            "model": llm_config.llm_model_name,
            **model_params,
            "messages": self._format_messages(messages),
            "stream": False,
        }
        
        logger.debug(f"Structured completion payload: {json.dumps(payload, ensure_ascii=False)}")
        
        try:
            # Make non-streaming request
            client = await self.get_client()
            logger.debug(f"Making structured completion request to {self.chat_url}")
            
            response = await client.post(self.chat_url, json=payload, headers=llm_config.vllm_headers)
            
            if response.status_code != 200:
                logger.error(f"vLLM API error: {response.status_code}")
                response_text = await response.text()
                logger.error(f"vLLM error response: {response_text}")
                raise Exception(f"LLM request failed with status {response.status_code}")
            
            # Parse response
            response_data = response.json()
            logger.debug(f"vLLM response: {json.dumps(response_data, ensure_ascii=False)}")
            
            # Extract content from response
            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0]["message"]["content"]
                logger.debug(f"Extracted content: {content}")
                
                # Try to parse as JSON and validate against schema
                try:
                    # Clean the content - remove any markdown formatting
                    if content.startswith("```json"):
                        content = content.split("```json")[1]
                    if content.endswith("```"):
                        content = content.rsplit("```", 1)[0]
                    content = content.strip()
                    
                    json_data = json.loads(content)
                    adapter = TypeAdapter(output_schema)
                    result = adapter.validate_python(json_data)
                    logger.info(f"Successfully validated structured completion for session {session_id}")
                    return result
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from LLM response: {e}\nRaw content: {content}\nPayload: {payload}")
                    raise Exception(f"Failed to parse JSON response: {e}")
                except Exception as e:
                    logger.error(f"Failed to validate response against schema: {e}\nJSON data: {json_data}")
                    raise Exception(f"Failed to validate response: {e}")
            else:
                logger.error("No choices in vLLM response")
                raise Exception("No response content from LLM")
        
        except Exception as e:
            logger.error(f"Structured completion error: {e}")
            raise Exception(f"Structured completion failed: {e}")
        finally:
            # Cleanup session
            if session_id in self.active_sessions:
                self.active_sessions.pop(session_id, None)

# Global LLM engine instance
llm_engine = LLMEngine()
