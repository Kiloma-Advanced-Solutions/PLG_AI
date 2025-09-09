"""
Chat service for handling chat conversations
"""
import uuid
import logging
from typing import List, Optional, AsyncGenerator, Dict, Any
from core.llm_engine import llm_engine
from core.models import Message
from core.config import llm_config
try:
    from transformers import AutoTokenizer
    TOKENIZER_AVAILABLE = True
except ImportError:
    TOKENIZER_AVAILABLE = False

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling chat conversations"""

    # Default system prompt for chat
    CHAT_SYSTEM_PROMPT = """אתה עוזר בינה מלאכותית שמטרתו לספק מידע מדויק ואמין בשפה העברית. ענה באופן ברור, מדויק, ומבוסס על עובדות בלבד. אל תנחש – אם אינך בטוח בתשובה, כתוב שאתה לא יודע או שהמידע חסר."""
    
    # Token limits
    MAX_CONTEXT_TOKENS = 16384
    RESPONSE_RESERVE_TOKENS = 2048

    def __init__(self):
        """Initialize the chat service"""
        self.engine = llm_engine
        self.tokenizer = None
        if TOKENIZER_AVAILABLE:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(llm_config.llm_model_name)
            except:
                pass

    def generate_session_id(self) -> str:
        """Generate a unique session ID for chat sessions"""
        return f"chat_{uuid.uuid4().hex[:12]}"
    
    def _count_tokens(self, messages: List[Message]) -> int:
        """Count tokens in messages using tokenizer"""
        if not self.tokenizer:
            return 0
        
        try:
            formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
            if hasattr(self.tokenizer, 'apply_chat_template'):
                formatted_text = self.tokenizer.apply_chat_template(formatted_messages, tokenize=False, add_generation_prompt=True)
                return len(self.tokenizer.encode(formatted_text))
            else:
                total_text = " ".join([msg.content for msg in messages])
                return len(self.tokenizer.encode(total_text))
        except:
            return 0

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
            # Add system prompt if not present
            if not messages or messages[0].role != "system":
                messages = [Message(role="system", content=self.CHAT_SYSTEM_PROMPT)] + messages
            
            # Prepare conversation context
            validated_messages = self._prepare_conversation(messages)
            
            # Stream from LLM engine
            async for chunk in self.engine.chat_stream(validated_messages, session_id):
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


    def _prepare_conversation(self, messages: List[Message]) -> List[Message]:
        """
        Prepare conversation context for LLM - tokenizer-based truncation
        
        Args:
            messages: Full conversation history
            
        Returns:
            Processed message list ready for LLM
        """
        # Remove consecutive user messages (keep only the last one)
        cleaned_messages = []
        consecutive_users_found = 0
        for msg in messages:
            if msg.role == "user" and cleaned_messages and cleaned_messages[-1].role == "user":
                consecutive_users_found += 1
                # Replace previous user message with current one
                cleaned_messages[-1] = msg
            else:
                cleaned_messages.append(msg)
        
        if consecutive_users_found > 0:
            logger.warning(f"🔧 Fixed {consecutive_users_found} consecutive user messages")
        
        # Simple tokenizer-based truncation
        if not self.tokenizer:
            return cleaned_messages
        
        # Ensure system prompt is present
        if not cleaned_messages or cleaned_messages[0].role != "system":
            cleaned_messages = [Message(role="system", content=self.CHAT_SYSTEM_PROMPT)] + cleaned_messages
        
        available_tokens = self.MAX_CONTEXT_TOKENS - self.RESPONSE_RESERVE_TOKENS
        original_count = len(cleaned_messages)
        
        # Remove oldest messages in pairs until we fit (but keep system prompt)
        while len(cleaned_messages) > 1 and self._count_tokens(cleaned_messages) > available_tokens:
            # Always start from index 1 to preserve system prompt
            if len(cleaned_messages) > 3:
                # Remove 2 messages (user-assistant pair)
                cleaned_messages.pop(1)
                cleaned_messages.pop(1)
            elif len(cleaned_messages) > 1:
                # Remove 1 message
                cleaned_messages.pop(1)
            else:
                break
        
        if len(cleaned_messages) < original_count:
            final_tokens = self._count_tokens(cleaned_messages)
            logger.info(f"🗜️ Truncated to {len(cleaned_messages)} messages, {final_tokens} tokens")
        
        return cleaned_messages
    

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