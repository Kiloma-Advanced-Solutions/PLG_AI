"""
Service for handling task extraction from emails
"""
from typing import Dict
from datetime import datetime
import logging
from core.llm_engine import llm_engine
from core.models import Message, TaskExtractionResponse

logger = logging.getLogger(__name__)

class TaskService:
    """Service for handling task extraction from emails"""

    # System prompt that defines the task extraction behavior
    TASK_SYSTEM_PROMPT = """חלץ משימות מתוך תוכן האימייל הבא שישלח המשתמש. עבור כל משימה:
- זהה למי היא מוקצית
- חלץ את תיאור המשימה
- מצא או הסק את תאריך היעד (אם לא צוין, השתמש ב-'unspecified')

פרמט את התשובה כאובייקט JSON כאשר כל משימה ממוספרת ומכילה:
- assigned_to: האדם האחראי
- description: תיאור ברור של המשימה
- due_date: תאריך היעד בפורמט DD-MM-YYYY או 'unspecified'

שים לב:
- תאריכים בעברית כמו "מחר", "בשבוע הבא", "בעוד יומיים" יש להמיר לפורמט DD-MM-YYYY
- יש לשמור על שמות השדות באנגלית (assigned_to, description, due_date)
- התוכן של השדות יכול להיות בעברית
- השתמש בתאריך של היום ({today}) לחישוב תאריכי יעד יחסיים (למשל: "מחר", "בעוד שבוע")

ענה רק עם ה-JSON, ללא טקסט נוסף.

בהודעה הבאה תקבל את תוכן האימייל:"""

    def __init__(self):
        """Initialize the task service"""
        self.engine = llm_engine

    def get_task_system_prompt(self: str) -> str:
        """Get the system prompt for task extraction"""
        # Get today's date in DD-MM-YYYY format
        today = datetime.now().strftime("%d-%m-%Y")
        return self.TASK_SYSTEM_PROMPT.format(today=today)


    async def extract_tasks(self, email_content: str) -> TaskExtractionResponse:
        """
        Extract tasks from Hebrew email content using LLM.
        Returns a validated TaskExtractionResponse containing tasks in the format:
        {
            [
                {"assigned_to": "person", "description": "task", "due_date": "date"},
                {"assigned_to": "person", "description": "task", "due_date": "date"},
                ...
            ]
        }
        """
        try:
            # Prepare messages for LLM
            messages = [
                Message(role="system", content=self.get_task_system_prompt()),
                Message(role="user", content=email_content)
            ]
            
            # Get structured response from LLM
            logger.info("Sending task extraction request to LLM")
            response = await self.engine.get_structured_completion(
                messages=messages,
                output_schema=TaskExtractionResponse,
                session_id="task_extraction"
            )
            
            logger.info(f"Successfully extracted {len(response.tasks)} tasks")
            return response
            
        except Exception as e:
            logger.error(f"Failed to extract tasks: {e}")
            raise Exception(f"Failed to extract tasks: {e}")

# Global task service instance
task_service = TaskService() 