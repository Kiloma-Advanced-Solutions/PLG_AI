"""
Service for handling task extraction from emails
"""
from typing import Dict, Optional
from datetime import datetime
import json
import logging
from core.llm_engine import llm_engine
from core.models import Task

logger = logging.getLogger(__name__)

class TaskService:
    """Service for handling task extraction from emails"""

    # System prompt that defines the task extraction behavior
    TASK_SYSTEM_PROMPT = """חלץ משימות מתוך תוכן האימייל הבא. עבור כל משימה:
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

תוכן האימייל:
{email_content}

ענה רק עם ה-JSON, ללא טקסט נוסף."""

    def __init__(self):
        """Initialize the task service"""
        self.engine = llm_engine

    def get_task_system_prompt(self, email_content: str) -> str:
        """Get the system prompt for task extraction"""
        # Get today's date in DD-MM-YYYY format
        today = datetime.now().strftime("%d-%m-%Y")
        return self.TASK_SYSTEM_PROMPT.format(today=today, email_content=email_content)
    
    async def extract_tasks(self, email_content: str) -> Dict[str, Dict[str, str]]:
        """
        Extract tasks from Hebrew email content using LLM.
        Returns tasks in the format:
        {
            "1": {"assigned_to": "person", "description": "task", "due_date": "date"},
            "2": {"assigned_to": "person", "description": "task", "due_date": "date"},
            ...
        }
        """

        # Get response from LLM
        try:
            logger.info("Sending task extraction request to LLM")
            response = await get_llm_response(prompt)
            logger.debug(f"Raw LLM response: {response}")
            
            # Basic validation of response format
            if not isinstance(response, dict):
                logger.error(f"Invalid response format from LLM - expected dictionary, got {type(response)}")
                raise ValueError("Invalid response format from LLM - expected dictionary")
                
            # Validate each task entry
            for task_num, task_data in response.items():
                if not isinstance(task_data, dict):
                    logger.error(f"Invalid task data format for task {task_num} - expected dictionary, got {type(task_data)}")
                    raise ValueError(f"Invalid task data format for task {task_num} - expected dictionary")
                    
                required_fields = {"assigned_to", "description", "due_date"}
                missing_fields = required_fields - set(task_data.keys())
                if missing_fields:
                    logger.error(f"Missing required fields in task {task_num}: {missing_fields}")
                    raise ValueError(f"Missing required fields in task {task_num}: {missing_fields}")
                
                # Validate date format if not 'unspecified'
                if task_data["due_date"] != "unspecified":
                    try:
                        datetime.strptime(task_data["due_date"], "%d-%m-%Y")
                    except ValueError as e:
                        logger.error(f"Invalid date format in task {task_num}. Must be DD-MM-YYYY: {str(e)}")
                        raise ValueError(f"Invalid date format in task {task_num}. Must be DD-MM-YYYY: {str(e)}")
            
            logger.info(f"Successfully extracted {len(response)} tasks")
            return response
            
        except Exception as e:
            logger.error(f"Failed to extract tasks: {str(e)}")
            raise Exception(f"Failed to extract tasks: {str(e)}") 

# Global task service instance
task_service = TaskService() 