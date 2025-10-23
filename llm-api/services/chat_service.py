"""
Chat service for handling chat conversations
"""
import uuid
import logging
from typing import List, Optional, AsyncGenerator, Dict, Any
from core.llm_engine import llm_engine
from core.models import Message
from services.mcp_service import mcp_service

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling chat conversations"""

    # Default system prompt for chat
    CHAT_SYSTEM_PROMPT = """אתה עוזר בינה מלאכותית שמטרתו לספק מידע מדויק ואמין בשפה העברית. ענה באופן ברור, מדויק, ומבוסס על עובדות בלבד. אל תנחש – אם אינך בטוח בתשובה, כתוב שאתה לא יודע או שהמידע חסר."""

    def __init__(self):
        """Initialize the chat service"""
        self.engine = llm_engine
        self.use_mcp = True  # Enable MCP integration by default

    def generate_session_id(self) -> str:
        """Generate a unique session ID for chat sessions"""
        return f"chat_{uuid.uuid4().hex[:12]}"

    async def stream_chat(
        self,
        messages: List[Message],
        session_id: str,
        use_mcp: bool = True,
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
            # Check if we should use MCP for this request
            if self.use_mcp and use_mcp:
                # Extract latest user message
                latest_user_msg = self.extract_latest_user_message(messages)
                
                if latest_user_msg:
                    logger.info(f"Attempting MCP processing for: {latest_user_msg[:100]}")
                    
                    try:
                        # Try to process with MCP - returns messages with tool context or None
                        mcp_messages_dict = await mcp_service.process_with_mcp(latest_user_msg)
                        
                        if mcp_messages_dict:
                            # MCP provided context with tool results - stream final answer using LLM engine
                            logger.info("MCP provided context, streaming final answer via LLM engine")
                            
                            # MCP service already returns Message objects, so use them directly
                            async for chunk in self.engine.chat_stream(mcp_messages_dict, session_id):
                                yield chunk
                            return
                        else:
                            logger.info("MCP not needed or unavailable, using regular chat")
                    except Exception as mcp_error:
                        logger.warning(f"MCP processing failed, falling back to regular chat: {mcp_error}")
            
            # Stream from LLM engine (fallback or default)
            async for chunk in self.engine.chat_stream(messages, session_id):
                yield chunk
                
        except ValueError as e:
            logger.warning(f"Chat validation error: {str(e)}")
            yield f'data: {{"error": "Invalid message format"}}\n\n'
        except Exception as e:
            logger.error(f"Chat service error: {str(e)}")
            yield f'data: {{"error": "Chat service unavailable"}}\n\n'
    

    def extract_latest_user_message(self, messages: List[Message]) -> Optional[str]:
        """
        Extract the most recent user message from conversation
        
        Args:
            messages: Conversation history
            
        Returns:
            Latest user message content or None
        """
        for msg in reversed(messages):
            if msg.role == "user":
                return msg.content.strip()
        return None


# Global chat service instance
chat_service = ChatService() 