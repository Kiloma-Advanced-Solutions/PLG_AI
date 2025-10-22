"""
Conversation utilities for managing chat history and truncation
"""
import logging
from typing import List, Tuple, Optional
from core.models import Message
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation history, truncation, and message processing"""
    
    def __init__(self, model_name: str, max_context_tokens: int = 16384, response_reserve_tokens: int = 2048):
        """
        Initialize conversation manager
        
        Args:
            model_name: Name of the model for tokenizer
            max_context_tokens: Maximum context window size (from config)
            response_reserve_tokens: Tokens to reserve for response (from config)
        """
        self.max_context_tokens = max_context_tokens
        self.response_reserve_tokens = response_reserve_tokens
        self.tokenizer = None
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        except Exception as e:
            logger.error(f"CRITICAL: Could not load tokenizer for {model_name}: {e}")
            logger.error("Token counting is REQUIRED for proper conversation truncation")
            raise RuntimeError(f"Failed to load tokenizer for {model_name}. This is required for accurate token counting.") from e
    
    def _count_tokens(self, messages: List[Message]) -> int:
        """Count tokens in messages using the model's tokenizer (REQUIRED)"""
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not available - this should never happen after initialization")
        
        try:
            formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
            if hasattr(self.tokenizer, 'apply_chat_template'):
                # Use the model's chat template for accurate token counting
                formatted_text = self.tokenizer.apply_chat_template(
                    formatted_messages, 
                    tokenize=False, 
                    add_generation_prompt=True
                )
                token_count = len(self.tokenizer.encode(formatted_text))
                logger.debug(f"Token count via chat template: {token_count} tokens")
                return token_count
            else:
                # Fallback to simple concatenation if no chat template
                total_text = " ".join([msg.content for msg in messages])
                token_count = len(self.tokenizer.encode(total_text))
                logger.debug(f"Token count via direct encoding: {token_count} tokens")
                return token_count
        except Exception as e:
            logger.error(f"CRITICAL: Token counting failed with model tokenizer: {e}")
            logger.error(f"This may cause context length errors. Messages: {len(messages)}")
            # Re-raise the exception instead of falling back to unreliable estimation
            raise RuntimeError(f"Token counting failed: {e}") from e
    
    def prepare_conversation(self, messages: List[Message], system_prompt: str) -> Tuple[List[Message], dict]:
        """
        Prepare conversation for LLM - handles cleaning and truncation
        
        Args:
            messages: Full conversation history
            system_prompt: System prompt to add
            
        Returns:
            Tuple of (processed_messages, metadata)
            - processed_messages: Messages ready for LLM
            - metadata: Dict with truncation info and stats
        """
        metadata = {
            "original_count": len(messages),
            "consecutive_users_fixed": 0,
            "messages_truncated": 0,
            "final_token_count": 0
        }
        
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
        
        metadata["consecutive_users_fixed"] = consecutive_users_found
        if consecutive_users_found > 0:
            logger.warning(f"🔧 Fixed {consecutive_users_found} consecutive user messages")
        
        # Remove any existing system prompt from the conversation history (we'll add it after truncation)
        conversation_messages = [msg for msg in cleaned_messages if msg.role != "system"]
        
        # Perform token-based truncation
        conversation_messages = self._truncate_by_tokens(conversation_messages, system_prompt, metadata)
        
        # Add system prompt at the beginning
        final_messages = [Message(role="system", content=system_prompt)] + conversation_messages
        
        # Calculate final token count for metadata
        if self.tokenizer:
            metadata["final_token_count"] = self._count_tokens(final_messages)
        
        return final_messages, metadata
    
    
    def _truncate_by_tokens(self, messages: List[Message], system_prompt: str, metadata: dict) -> List[Message]:
        """Truncate messages using token-based counting"""
        # Calculate maximum allowed tokens for the entire conversation (system + messages)
        max_allowed_tokens = self.max_context_tokens - self.response_reserve_tokens
        original_count = len(messages)
        
        # Create system message for token counting
        system_message = Message(role="system", content=system_prompt)
        
        # Remove oldest messages until we fit within token limit
        # We check the total token count including the system prompt
        while messages:
            # Test the full conversation including system prompt
            test_messages = [system_message] + messages
            total_tokens = self._count_tokens(test_messages)
            
            if total_tokens <= max_allowed_tokens:
                break  # We fit within the limit
                
            # Remove messages to make room
            if len(messages) >= 2:
                # Check if first two messages form a user-assistant pair
                if (messages[0].role == "user" and messages[1].role == "assistant"):
                    # Remove the pair
                    messages.pop(0)
                    messages.pop(0)
                else:
                    # Just remove the oldest message
                    messages.pop(0)
            else:
                # Remove the last remaining message
                messages.pop(0)
        
        messages_removed = original_count - len(messages)
        metadata["messages_truncated"] = messages_removed
        
        if messages_removed > 0:
            # Calculate final token count with system prompt included
            final_messages = [system_message] + messages
            final_tokens = self._count_tokens(final_messages)
            logger.info(f"🧹 Token-based truncation: kept {len(messages)} messages, removed {messages_removed}, final tokens: {final_tokens}/{max_allowed_tokens}")
        
        return messages


# Global conversation manager instance will be initialized when config is available
conversation_manager: Optional[ConversationManager] = None

def get_conversation_manager() -> ConversationManager:
    """Get or create global conversation manager instance"""
    global conversation_manager
    if conversation_manager is None:
        from core.config import llm_config
        conversation_manager = ConversationManager(
            model_name=llm_config.llm_model_name,
            max_context_tokens=llm_config.max_context_tokens,
            response_reserve_tokens=llm_config.response_reserve_tokens
        )
    return conversation_manager
