"""
Chat service for handling chat conversations
"""
import uuid
import logging
from typing import List, Optional, AsyncGenerator, Dict, Any
from core.llm_engine import llm_engine
from core.models import Message

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling chat conversations"""

    # Default system prompt for chat
    CHAT_SYSTEM_PROMPT = """אתה עוזר בינה מלאכותית שמטרתו לספק מידע מדויק ואמין בשפה העברית. ענה באופן ברור, מדויק, ומבוסס על עובדות בלבד. אל תנחש – אם אינך בטוח בתשובה, כתוב שאתה לא יודע או שהמידע חסר."""

    def __init__(self):
        """Initialize the chat service"""
        self.engine = llm_engine

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
            # Stream from LLM engine
            async for chunk in self.engine.chat_stream(messages, session_id):
                yield chunk
                
        except ValueError as e:
            logger.error(f"Chat validation error: {e}")
            logger.error(f"Failed request details:")
            logger.error(f"  Session ID: {session_id}")
            logger.error(f"  Original messages ({len(messages)}):")
            for i, msg in enumerate(messages):
                logger.error(f"    Message {i+1} [{msg.role}]: {msg.content[:200]}...")
            yield f'data: {{"error": "Invalid message format: {str(e)}"}}\n\n'
        except Exception as e:
            logger.error(f"Chat service error: {e}")
            logger.error(f"Failed request details:")
            logger.error(f"  Session ID: {session_id}")
            logger.error(f"  Original messages ({len(messages)}):")
            for i, msg in enumerate(messages):
                logger.error(f"    Message {i+1} [{msg.role}]: {msg.content[:200]}...")
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


    def get_conversation_summary(self, messages: List[Message]) -> Dict[str, Any]:
        """
        Get summary statistics about the conversation
        
        Args:
            messages: Conversation history
            
        Returns:
            Dictionary with conversation statistics
        """
        user_messages = sum(1 for msg in messages if msg.role == "user")
        assistant_messages = sum(1 for msg in messages if msg.role == "assistant")
        total_chars = sum(len(msg.content) for msg in messages)
        
        return {
            "total_messages": len(messages),
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "total_characters": total_chars,
            "average_message_length": total_chars // len(messages) if messages else 0
        }


# Global chat service instance
chat_service = ChatService() 