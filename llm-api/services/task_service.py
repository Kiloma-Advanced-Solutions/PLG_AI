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
- זהה מי שלח את המשימה (שולח המייל). אם לא צוין, השאר כ-null.
- זהה מתי נשלחה המשימה (תאריך שליחת המייל). אם לא צוין, השאר כ-null.
- זהה למי היא מוקצית
- נסח כותרת המתארת את המשימה
- נסח את תיאור המשימה
- מצא או הסק את תאריך היעד. אם לא צוין,השאר כ-null.

פרמט את התשובה כאובייקט JSON כאשר כל משימה ממוספרת ומכילה:
- sender: האדם ששלח את המשימה
- sending_date: תאריך הקצאת המשימה בפורמט YYYY-MM-DD או null
- assigned_to: האדם האחראי על המשימה
- title: כותרת המשימה
- description: תיאור ברור של המשימה
- due_date: תאריך היעד בפורמט YYYY-MM-DD או null

שים לב:
- תאריכים בעברית כמו "מחר", "בשבוע הבא", "בעוד יומיים" יש להמיר לפורמט YYYY-MM-DD
- יש לשמור על שמות השדות באנגלית (sender, sending_date, assigned_to, title, description, due_date)
- התוכן של השדות יכול להיות בעברית
- השתמש בתאריך של היום ({today}, בפורמט YYYY-MM-DD) לחישוב תאריכי יעד יחסיים (למשל: "מחר", "בעוד שבוע")

ענה רק עם ה-JSON, ללא טקסט נוסף.

בהודעה הבאה תקבל את תוכן האימייל:"""


    def __init__(self):
        """Initialize the task service"""
        self.engine = llm_engine


    def get_task_system_prompt(self: str) -> str:
        """Get the system prompt for task extraction"""
        today = datetime.now().strftime("%Y-%m-%d")   # today's date in YYYY-MM-DD format
        return self.TASK_SYSTEM_PROMPT.format(today=today)


    async def extract_tasks(self, email_content: str) -> TaskExtractionResponse:
        """
        Extract tasks from Hebrew email content using LLM.
        Returns a validated TaskExtractionResponse containing tasks in the format:
        [
            {"sender": "task sender's email", "sending_date": "sending date", "assigned_to": "person", "title": "task title", "description": "task description", "due_date": "task due date"},
            {"sender": "task sender's email", "sending_date": "sending date", "assigned_to": "person", "title": "task title", "description": "task description", "due_date": "task due date"},
            ...
        ]
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
                output_schema=TaskExtractionResponse,   # Expected response format
                session_id="task_extraction"
            )
            
            logger.info(f"Successfully extracted {len(response)} tasks")
            return response
            
        except Exception as e:
            logger.error(f"Failed to extract tasks: {e}")
            raise Exception(f"Failed to extract tasks: {e}")

# Global task service instance
task_service = TaskService() 