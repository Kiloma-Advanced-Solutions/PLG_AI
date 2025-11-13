"""
Chat service for handling chat conversations
"""
import uuid
import logging
import json
from typing import List, Optional, AsyncGenerator
from core.llm_engine import llm_engine
from core.models import Message
from services.agent_service import triage_agent, Runner, mcp_internet, mcp_io

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling chat conversations"""

    # Default system prompt for chat
    CHAT_SYSTEM_PROMPT = """אתה עוזר בינה מלאכותית שמטרתו לספק מידע מדויק ואמין בשפה העברית. ענה באופן ברור, מדויק, ומבוסס על עובדות בלבד. אל תנחש – אם אינך בטוח בתשובה, כתוב שאתה לא יודע או שהמידע חסר."""

    def __init__(self):
        """Initialize the chat service"""
        self.engine = llm_engine
        self._mcp_connected = False
    
    async def _ensure_mcp_connected(self):
        """Ensure MCP servers are connected before agent workflow runs
        
        Note: MCP connections are closed after each agent workflow completes,
        so we reconnect them for each request.
        """
        try:
            # Always reconnect - the agents framework closes connections after workflow completes
            # Wrap in try/except to handle cases where connect() is called on already-connected servers
            try:
                await mcp_internet.connect()
            except Exception as e:
                # If already connected, that's fine - just log and continue
                logger.debug(f"MCP internet server connection attempt: {e}")
            
            try:
                await mcp_io.connect()
            except Exception as e:
                # If already connected, that's fine - just log and continue
                logger.debug(f"MCP IO server connection attempt: {e}")
            
            logger.info("MCP servers ready")
        except Exception as e:
            logger.error(f"Failed to ensure MCP servers are connected: {e}")
            # Don't raise - let the agent workflow handle connection errors

    def generate_session_id(self) -> str:
        """Generate a unique session ID for chat sessions"""
        return f"chat_{uuid.uuid4().hex[:12]}"

    async def stream_chat(
        self,
        messages: List[Message],
        session_id: str,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat responses with validation and error handling

        Args:
            messages: List of Message objects in conversation
            session_id: Session ID for tracking

        Yields:
            Server-sent event formatted strings
        """
        try:
            # Extract latest user message for agent routing
            latest_user_msg = self.extract_latest_user_message(messages)

            if latest_user_msg:
                try:
                    # Ensure MCP servers are connected before running agents
                    await self._ensure_mcp_connected()
                    
                    # Use triage agent with automatic handoffs to specialized agents
                    logger.info(f"Triage: {latest_user_msg[:50]}...")
                    
                    import asyncio
                    try:
                        # Add timeout to prevent hanging
                        logger.info("Starting agent workflow...")
                        result = await asyncio.wait_for(
                            Runner().run(triage_agent, latest_user_msg),
                            timeout=120.0  # 120 second timeout for tool execution
                        )
                        logger.info(f"Agent workflow completed. Result type: {type(result)}")
                        if result:
                            logger.info(f"Result attributes: {dir(result)}")
                            # Check for final_output (the correct attribute for RunResult)
                            has_final_output = hasattr(result, 'final_output') and result.final_output
                            logger.info(f"Result has final_output: {has_final_output}")
                            if has_final_output:
                                logger.info(f"Result final_output type: {type(result.final_output)}")
                                logger.info(f"Result final_output: {result.final_output}")
                    except asyncio.TimeoutError:
                        logger.error("Agent workflow timed out after 120 seconds")
                        raise Exception("Agent workflow timed out - vLLM may be hanging")
                    except Exception as agent_error:
                        logger.exception(f"Agent workflow error: {agent_error}")
                        raise
                    
                    # Stream the agent's response back to the user
                    if result and hasattr(result, 'final_output') and result.final_output:
                        # Format as SSE for the client
                        response_text = str(result.final_output)
                        logger.info(f"Agent response: {response_text[:100]}...")
                        
                        # Stream the response in chunks (simulating streaming)
                        chunk_data = {
                            "choices": [{
                                "delta": {"content": response_text},
                                "index": 0,
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n"
                        
                        # Send finish message
                        finish_data = {
                            "choices": [{
                                "delta": {},
                                "index": 0,
                                "finish_reason": "stop"
                            }]
                        }
                        yield f"data: {json.dumps(finish_data)}\n\n"
                        logger.info("Agent response streamed successfully")
                        return  # Don't fall through to regular chat
                    else:
                        logger.warning(f"No output from agent, falling back. Result: {result}")
                    
                except Exception as e:
                    logger.exception(f"Agent routing failed: {e}")
                    # Fall through to regular chat

            # Fallback: regular chat stream
            logger.info("Using fallback chat stream")
            async for chunk in self.engine.chat_stream(messages, session_id):
                yield chunk

        except ValueError as e:
            logger.warning(f"Chat validation error: {str(e)}")
            yield f'data: {{"error": "Invalid message format"}}\n\n'

        except Exception as e:
            logger.error(f"Chat service error: {str(e)}")
            yield f'data: {{"error": "Chat service unavailable"}}\n\n'

    

    def extract_latest_user_message(self, messages: List[Message]) -> Optional[str]:
        """Extract the most recent user message."""
        for msg in reversed(messages):
            if msg.role == "user":
                return msg.content.strip()
        return None
    



# Global chat service instance
chat_service = ChatService() 