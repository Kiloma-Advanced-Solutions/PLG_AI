"""
Service for generating conversation titles from user message
"""
import logging
from core.llm_engine import llm_engine
from core.models import Message, TitleGenerationResponse

logger = logging.getLogger(__name__)

class TitleService:
    """Service for generating conversation titles"""

    def __init__(self):
        """Initialize the title service"""
        self.engine = llm_engine

    def get_title_system_prompt(self) -> str:
        """Get the system prompt for title generation"""
        return """
אתה עוזר מומחה לסיכום הודעות. המטרה שלך היא ליצור כותרת קצרה להודעת המשתמש עד 6 מילים בעברית.
על הכותרת להיות תמציתית וברורה ולבטא את המטרה המרכבית של ההודעה.

תן תשובה המכילה את הכותרת בלבד, ללא הסברים או טקסט נוסף.
"""

    async def generate_title(self, user_message: str) -> TitleGenerationResponse:
        """
        Generate an up to 6-word Hebrew title for a conversation based on the first user message.
        
        Args:
            user_message: The first message from the user
            
        Returns:
            TitleGenerationResponse containing the generated title
        """
        try:
            # Prepare messages for LLM
            messages = [
                Message(role="system", content=self.get_title_system_prompt()),
                Message(role="user", content=user_message)
            ]
            
            # Log the messages being sent to the model
            logger.info("=== TITLE GENERATION - Messages sent to model ===")
            for i, message in enumerate(messages):
                logger.info(f"Message {i+1} [{message.role}]:")
                logger.info(f"Content: {message.content}")
                logger.info("=" * 50)
            
            # Get structured response from LLM
            logger.info("Sending title generation request to LLM")
            response = await self.engine.get_structured_completion(
                messages=messages,
                output_schema=TitleGenerationResponse,
                session_id="title_generation"
            )

            logger.info(f"Successfully generated title: {response.title}")
            return response
            
        except Exception as e:
            logger.error(f"Title generation error: {e}")
            # Fallback to a truncated version of the user message if LLM fails
            fallback_title = "שיחה חדשה"
            logger.info(f"Using fallback title: {fallback_title}")
            return TitleGenerationResponse(title=fallback_title)

# Global title service instance
title_service = TitleService()
