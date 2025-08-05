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

    def __init__(self):
        """Initialize the task service"""
        self.engine = llm_engine
            

    def get_task_system_prompt(self):
        today = datetime.now().strftime("%Y-%m-%d")
        return f"""
    חלץ מתוך האימייל הבא את המשימות הנדרשות לביצוע המתוארות בו — כלומר, משימות שטרם בוצעו והוקצו לאדם מסוים.
    שים לב שיתכן ויתקבלו מיילים ללא משימות כלל. במקרה זה יש להחזיר רשימה ריקה ([]).
    
    
    **הפורמט הנדרש לתשובה הוא רשימה של משימות מסוג JSON**, שכל אחת מכילה כל השדות הבאים:
    - sender: שם השולח או null
    - sending_date: תאריך שליחת האימייל בפורמט YYYY-MM-DD או null
    - assigned_to: שם האדם שאליו מוקצת המשימה. ערך זה לא יכול להיות ריק
    - title: כותרת קצרה למשימה. ערך זה לא יכול להיות ריק
    - description: תיאור מפורט של המשימה. ערך זה לא יכול להיות ריק
    - due_date: תאריך היעד בפורמט YYYY-MM-DD או null
    
    
    **חלץ רק משימות שעונות על כל הקריטריונים הבאים**:
    - המשימה מוקצית במפורש לאדם מסוים (למשל: "דני כהן", "רותם"), ולא לנמענים כלליים ("כולם", "הצוות", "מי שיכול").
    - המשימה כוללת פעולה ברורה שיש לבצע, לא הודעות אינפורמטיביות או עדכונים כלליים.
    - המשימה מנוסחת באופן ברור וכוללת אחריות אישית.
    
    
    **אל תכלול משימות** אם מתקיים אחד מהבאים:
    - אל תחזיר את המשימה בכלל אם לפחות אחד מהשדות assigned_to, title, description לא קיים או ריק (מחרוזת ריקה, null או None). 
    - לא צוין שם אדם מפורש ב־assigned_to (למשל מופיע: "מישהו", "מי שיכול", "כולם", "הצוות").
    - מדובר בעדכון, הודעה כללית, סיכום, או מידע אינפורמטיבי בלבד.
    
    
    אם יש תאריכים יחסיים בעברית (כגון "מחר", "בעוד יומיים", "שבוע הבא") — המר אותם לתאריך מפורש בפורמט YYYY-MM-DD, על סמך תאריך שליחת האימייל.
    אם תאריך שליחה אינו מצוין — השתמש בתאריך של היום: {today}.
    
    הקפד להשתמש באנגלית רק לשמות השדות ב-JSON. התוכן עצמו (שמות, כותרות, תיאורים) יכול להיות בעברית.
    
    ענה אך ורק עם רשימת ה-JSON, ללא הסברים, טקסט נוסף או הקדמה.
    
    בהודעה הבאה תקבל את תוכן האימייל.
        """


    @staticmethod
    def is_field_valid(value):
        return isinstance(value, str) and value.strip() and value.strip().lower() not in {"none", "null"}


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

            # Filter out tasks without required fields
            filtered_tasks = [
                task for task in response 
                    if self.is_field_valid(task.assigned_to) and self.is_field_valid(task.title) and self.is_field_valid(task.description)
            ]

            logger.info(f"Successfully extracted {len(filtered_tasks)} tasks")
            return filtered_tasks
            
        except Exception as e:
            raise Exception(f"Failed to extract tasks: {e}")

# Global task service instance
task_service = TaskService() 