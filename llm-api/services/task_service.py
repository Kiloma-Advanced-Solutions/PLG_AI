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
חלץ מתוך האימייל הבא את המשימות הנדרשות לביצוע המתוארות בו.
 
**הפורמט הנדרש לתשובה הוא רשימה של משימות מסוג JSON שכל אחת מכילה כל השדות הבאים:**
- sender: שולח המשימה (או null במידה ולא מצוין השם או המייל של שולח המשימה)
- sending_date: תאריך שליחת המייל בפורמט YYYY-MM-DD (במידה ולא קיים יש להחזיר null)
- assigned_to: שם האדם שצריך לבצע את המשימה. חשוב מאוד שיופיע במייל באופן מפורש שהמשימה מיועדת לאותו אדם
- title: כותרת קצרה למשימה
- description: תיאור מפורט של המשימה
- due_date: תאריך היעד בפורמט YYYY-MM-DD (במידה ולא קיים יש להחזיר null)

    
**חלץ רק משימות שעונות על כל הקריטריונים הבאים:**
- המשימה מוקצית במפורש לאדם מסוים, ולא לנמענים כלליים (״כולם״ ,הצוות״, ״מי שיכול״). בגוף האימייל צריך להיות כתוב שהמשימה צריכה להתבצע על ידיו.
- המשימה כוללת פעולה ברורה שיש לבצע, לא הודעות אינפורמטיביות או עדכונים כלליים.
- המשימה מנוסחת באופן ברור וכוללת אחריות אישית.
    
**אל תכלול משימות** אם מתקיים אחד מהבאים:
- מדובר בעדכון, הודעה כללית, סיכום, או מידע אינפורמטיבי בלבד.
- אל תחזיר את המשימה אם לפחות אחד מהשדות assigned_to, title, description לא קיים או ריק (מחרוזת ריקה, null או None).
- לא צוין שם אדם מפורש בשדה ״assigned_to״ (למשל מופיע ״מישהו״, ״מי שיכול״, ״כולם״, ״הצוות״, שם של בעל תפקיד וכו׳..). ערך זה חייב להיות השם של האדם הספציפי שהמשימה הוקצתה לו במייל. 

* שים לב שיתכן ויתקבלו מיילים ללא משימות כלל. במקרה זה יש להחזיר רשימה ריקה ([]).
* אין להמציא מידע שאינו מופיע בתוכן המייל. במידת הצורך, השאר את השדות החסרים ריקים.

אם יש תאריכים יחסיים (כגון "מחר", "בעוד יומיים", "שבוע הבא") - המר אותם לתאריך מפורש בפורמט YYYY-MM-DD על סמך תאריך שליחת האימייל. אם תאריך שליחה אינו מצוין - השתמש בתאריך של היום: {today}.

הקפד להשתמש באנגלית רק לשמות השדות ב-JSON. תוכן השדות עצמם יכול להיות בעברית.
ענה אך ורק עם רשימת ה-JSON, ללא הסברים, טקסט נוסף או הקדמה.

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
            
            # Log the messages being sent to the model
            logger.info("=== TASK EXTRACTION - Messages sent to model ===")
            for i, message in enumerate(messages):
                logger.info(f"Message {i+1} [{message.role}]:")
                logger.info(f"Content: {message.content}")
                logger.info("=" * 50)
            
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