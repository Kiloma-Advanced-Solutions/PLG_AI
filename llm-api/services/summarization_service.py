"""
Service for handling email summarization
"""

import logging
from core.llm_engine import llm_engine
from core.models import Message, EmailSummary

logger = logging.getLogger(__name__)

class SummarizationService:
    """Service for handling email summarization"""

    def __init__(self):
        """Initialize the summarization service"""
        self.engine = llm_engine

    
    def get_summarization_system_prompt(self, length: int):
        """Get the system prompt for summarization"""
        return f"""
עלייך לסכם את המייל הבא.
על הסיכום להכיל את המידע החשוב במייל ולא חייב להכיל את כל תוכן המייל.
הקפד לחלץ את הנקודות החשובות ביותר והשתדל לא להכניס מידע מיותר.

**הפורמט הנדרש לתשובה הוא סיכום מסוג JSON המכיל את כל השדות הבאים:**
- sender: כתובת המייל של השולח (או null במידה ולא מצוין)
- sending_date: תאריך שליחת המייל בפורמט ISO 8601 כמו שמופיע במייל (או null במידה ולא קיים)
- title: כותרת קצרה לסיכום המייל
- summary: סיכום של המייל ב-{length} תווים

החזר רק את הסיכום, ללא הסברים או טקסט נוסף.
        """
    

    async def summarize_email(self, email: str, length: int = 100) -> str:
        """
        Summarize an email according to a given length
        Returns anEmailSummary object with extracted metadata and summary
        """
        try:
            # Prepare messages for LLM
            messages = [
                Message(role="system", content=self.get_summarization_system_prompt(length)),
                Message(role="user", content=email)
            ]

            logger.info("=== SUMMARIZATION - Messages sent to model ===")
            for i, message in enumerate(messages):
                logger.info(f"Message {i+1} [{message.role}]:")
                logger.info(f"Content: {message.content}")
                logger.info("=" * 50)

            # Get structured response from LLM
            logger.info("Sending summarization request to LLM")
            response = await self.engine.get_structured_completion(
            messages=messages, 
            output_schema=EmailSummary, 
            session_id="email_summarization"
            )
            
            logger.info(f"Generated summary response: {response}")
            
            # The response is already an EmailSummary object from structured completion
            return response
    
        except Exception as e:
            logger.error(f"Failed to summarize email: {str(e)}")
            raise
    
# Global summarization service instance
summarization_service = SummarizationService()

    
