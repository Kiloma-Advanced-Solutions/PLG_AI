from typing import Dict, Optional
from datetime import datetime
from core.llm_engine import get_llm_response

class TaskService:
    @staticmethod
    async def extract_tasks(email_content: str) -> Dict[str, Dict[str, str]]:
        """
        Extract tasks from Hebrew email content using LLM.
        Returns tasks in the format:
        {
            "1": {"assigned_to": "person", "description": "task", "due_date": "date"},
            "2": {"assigned_to": "person", "description": "task", "due_date": "date"},
            ...
        }
        """
        # Get today's date in DD-MM-YYYY format
        today = datetime.now().strftime("%d-%m-%Y")
        
        # Construct the prompt for task extraction in Hebrew
        prompt = f"""
        היום התאריך הוא: {today}

        חלץ משימות מתוך תוכן האימייל הבא. עבור כל משימה:
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
        
        ענה רק עם ה-JSON, ללא טקסט נוסף.
        """
        
        # Get response from LLM
        try:
            response = await get_llm_response(prompt)
            
            # Basic validation of response format
            if not isinstance(response, dict):
                raise ValueError("Invalid response format from LLM")
                
            # Validate each task entry
            for task_num, task_data in response.items():
                if not isinstance(task_data, dict):
                    raise ValueError(f"Invalid task data format for task {task_num}")
                    
                required_fields = {"assigned_to", "description", "due_date"}
                if not all(field in task_data for field in required_fields):
                    raise ValueError(f"Missing required fields in task {task_num}")
                
                # Validate date format if not 'unspecified'
                if task_data["due_date"] != "unspecified":
                    try:
                        datetime.strptime(task_data["due_date"], "%d-%m-%Y")
                    except ValueError:
                        raise ValueError(f"Invalid date format in task {task_num}. Must be DD-MM-YYYY")
                    
            return response
            
        except Exception as e:
            raise Exception(f"Failed to extract tasks: {str(e)}") 