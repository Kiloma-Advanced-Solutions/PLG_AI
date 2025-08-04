"""
Comprehensive test suite for task extraction functionality.
Tests both JSON validation and LLM-as-a-judge output quality evaluation.
"""

import asyncio
import json
import pytest
import os
from datetime import datetime, date
from typing import List, Dict, Any
from pathlib import Path
from pydantic import ValidationError

# Import models and services
import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.models import TaskItem, TaskExtractionResponse, Message
from services.task_service import TaskService

# ChatGPT integration
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

# For automatic .env loading (optional)
try:
    from dotenv import load_dotenv
    # Try to load .env file from tests directory
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"📁 Loaded environment from {env_file}")
except ImportError:
    pass  # python-dotenv not available, that's okay


class TaskExtractionTestSuite:
    """Comprehensive test suite for task extraction"""
    
    def __init__(self):
        self.task_service = TaskService()
        self.api_base_url = "http://localhost:8090/api"
        
        # Initialize ChatGPT client for judge evaluation
        self.openai_client = None
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                # Mask API key in logs for security
                masked_key = f"{api_key[:7]}...{api_key[-4:]}" if len(api_key) > 11 else "****"
                self.openai_client = AsyncOpenAI(api_key=api_key)
                print(f"✅ ChatGPT client initialized for LLM judge (key: {masked_key})")
            else:
                print("⚠️  OPENAI_API_KEY not found in environment variables")
                print("   Set it with: export OPENAI_API_KEY='your_key_here'")
                print("   Or see: llm-api/tests/secure_setup.md")
        else:
            print("⚠️  OpenAI library not available. Install with: pip install openai>=1.3.0")
        
    # ======================================
    # TEST DATA - 10 EDGE CASE SCENARIOS
    # ======================================
    
    @property
    def edge_case_emails(self) -> List[Dict[str, Any]]:
        """10 edge case scenarios for task extraction testing"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        return [
            {
                "name": "single_simple_task",
                "email_content": """נושא: דוח שבועי
מאת: דנה <dana@company.com>
תאריך: 1 בינואר 2024

שלום יוסי,
בבקשה הכן את הדוח השבועי עד מחר.
תודה.""",
                "expected_tasks": [
                    {
                        "sender": "dana@company.com",
                        "sending_date": "2024-01-01",
                        "assigned_to": "יוסי",
                        "title": "הכנת דוח שבועי",
                        "description": "הכן את הדוח השבועי",
                        "due_date": "2024-01-02"  # tomorrow from sending date
                    }
                ],
                "description": "Single simple task with clear assignee and due date"
            },
            
            {
                "name": "multiple_tasks_different_assignees",
                "email_content": """צוות יקר,
לאחר הפגישה של היום (15 במרס 2024):

1. שירה - בצעי ניתוח שוק עד ה-20 במרס
2. אבי - הכן מצגת ללקוח עד יום ראשון הבא
3. מירב - תיאמי פגישה עם ספק עד סוף השבוע
4. דני - סיים את הקוד עד בעוד שבוע

תודה,
מנהלת הפרויקט""",
                "expected_tasks": [
                    {
                        "sender": "מנהלת הפרויקט",
                        "sending_date": "2024-03-15",
                        "assigned_to": "שירה",
                        "title": "ניתוח שוק",
                        "description": "בצעי ניתוח שוק",
                        "due_date": "2024-03-20"
                    },
                    {
                        "sender": "מנהלת הפרויקט", 
                        "sending_date": "2024-03-15",
                        "assigned_to": "אבי",
                        "title": "הכנת מצגת ללקוח",
                        "description": "הכן מצגת ללקוח",
                        "due_date": "2024-03-17"  # next Sunday
                    },
                    {
                        "sender": "מנהלת הפרויקט",
                        "sending_date": "2024-03-15", 
                        "assigned_to": "מירב",
                        "title": "תיאום פגישה עם ספק",
                        "description": "תיאמי פגישה עם ספק",
                        "due_date": "2024-03-17"  # end of week
                    },
                    {
                        "sender": "מנהלת הפרויקט",
                        "sending_date": "2024-03-15",
                        "assigned_to": "דני", 
                        "title": "סיום קוד",
                        "description": "סיים את הקוד",
                        "due_date": "2024-03-22"  # in a week
                    }
                ],
                "description": "Multiple tasks with different assignees and various date formats"
            },
            
            {
                "name": "tasks_no_due_dates",
                "email_content": """היי צוות,
משימות לתקופה הקרובה:

רותם - בדקי את הנתונים מהמחקר האחרון
גל - תכני תכנית שיווק חדשה
אליה - פתחי קשר עם לקוחות פוטנציאליים

ללא לוח זמנים קבוע, רק תתחילו לעבוד על זה.

בהצלחה!""",
                "expected_tasks": [
                    {
                        "sender": None,
                        "sending_date": None,
                        "assigned_to": "רותם",
                        "title": "בדיקת נתונים מהמחקר האחרון",
                        "description": "בדקי את הנתונים מהמחקר האחרון",
                        "due_date": None
                    },
                    {
                        "sender": None,
                        "sending_date": None,
                        "assigned_to": "גל",
                        "title": "תכנון תכנית שיווק חדשה",
                        "description": "תכני תכנית שיווק חדשה",
                        "due_date": None
                    },
                    {
                        "sender": None,
                        "sending_date": None,
                        "assigned_to": "אליה",
                        "title": "פתיחת קשר עם לקוחות פוטנציאליים",
                        "description": "פתחי קשר עם לקוחות פוטנציאליים",
                        "due_date": None
                    }
                ],
                "description": "Tasks without due dates and sender information"
            },
            
            {
                "name": "relative_hebrew_dates",
                "email_content": """מאת: רונית <ronit@company.com>
נשלח: 10 ביוני 2024

אלון,
אנא הכן את הדוח הכספי עד מחר.
בנוסף, תארגן פגישה עם הלקוח בעוד יומיים.
עד סוף השבוע תשלח את הסיכום.
בשבוע הבא נצטרך את התחזית החדשה.

תודה רבה!""",
                "expected_tasks": [
                    {
                        "sender": "ronit@company.com",
                        "sending_date": "2024-06-10",
                        "assigned_to": "אלון",
                        "title": "הכנת דוח כספי",
                        "description": "הכן את הדוח הכספי",
                        "due_date": "2024-06-11"  # tomorrow
                    },
                    {
                        "sender": "ronit@company.com",
                        "sending_date": "2024-06-10",
                        "assigned_to": "אלון",
                        "title": "ארגון פגישה עם לקוח",
                        "description": "תארגן פגישה עם הלקוח",
                        "due_date": "2024-06-12"  # in two days
                    },
                    {
                        "sender": "ronit@company.com",
                        "sending_date": "2024-06-10",
                        "assigned_to": "אלון",
                        "title": "שליחת סיכום",
                        "description": "שלח את הסיכום",
                        "due_date": "2024-06-14"  # end of week (Friday)
                    },
                    {
                        "sender": "ronit@company.com",
                        "sending_date": "2024-06-10",
                        "assigned_to": "אלון",
                        "title": "תחזית חדשה",
                        "description": "הכן את התחזית החדשה",
                        "due_date": "2024-06-17"  # next week
                    }
                ],
                "description": "Tasks with relative Hebrew date expressions"
            },
            
            {
                "name": "no_tasks_email",
                "email_content": """שלום לכולם,

רציתי לעדכן אתכם שהפגישה מחר תהיה בשעה 14:00 במקום 15:00.
בנוסף, המשרדים יהיו סגורים ביום שישי הקרוב עקב חג.

נקודות נוספות:
- הצגנו השבוע תוצאות מעולות
- הלקוח מרוצה מהשירות
- קיבלנו משוב חיובי מהצוות

סוף שבוע נעים!""",
                "expected_tasks": [],
                "description": "Email with no actionable tasks - only informational content"
            },
            
            {
                "name": "ambiguous_assignments",
                "email_content": """צוות המכירות,

מישהו צריך לקחת אחריות על הלקוח החדש. 
גם כן, אחד מכם יטפל בהכנת ההצעה עד יום רביעי.
מי שרוצה יכול לעזור בארגון האירוע השנתי.

אשמח שמישהו יעדכן אותי מי לוקח מה.

מנהל המכירות""",
                "expected_tasks": [
                    {
                        "sender": "מנהל המכירות",
                        "sending_date": None,
                        "assigned_to": "מישהו מצוות המכירות",
                        "title": "אחריות על לקוח חדש",
                        "description": "קח אחריות על הלקוח החדש",
                        "due_date": None
                    },
                    {
                        "sender": "מנהל המכירות",
                        "sending_date": None,
                        "assigned_to": "אחד מצוות המכירות",
                        "title": "הכנת הצעה",
                        "description": "הכן את ההצעה",
                        "due_date": None  # "יום רביעי" without specific date context
                    },
                    {
                        "sender": "מנהל המכירות",
                        "sending_date": None,
                        "assigned_to": "מתנדב מהצוות",
                        "title": "עזרה בארגון אירוע שנתי",
                        "description": "עזור בארגון האירוע השנתי",
                        "due_date": None
                    }
                ],
                "description": "Tasks with ambiguous or non-specific assignments"
            },
            
            {
                "name": "detailed_complex_tasks",
                "email_content": """מאת: ראש הפיתוח <dev-lead@company.com>
תאריך: 22 בספטמבר 2024

צוות הפיתוח,

לאחר הסקירה הטכנית אתמול:

1. תומר - תוביל את ההגירה של מסד הנתונים מ-MySQL ל-PostgreSQL. 
   זה כולל:
   - ניתוח של הסכימה הקיימת
   - כתיבת סקריפטי הגירה
   - בדיקות איכות נתונים
   - תיעוד תהליך החזרה
   המשימה קריטית ויש לסיים עד ה-30 בספטמבר.

2. לילך - פתחי ממשק API חדש לניהול משתמשים עם authentication מלא.
   הדרישות כוללות:
   - JWT tokens
   - Rate limiting  
   - Audit logs
   - Integration tests
   יעד: 5 באוקטובר

3. עמוס - בצע optimization לביצועי המערכת. התמקד בשאילתות איטיות,
   caching mechanisms ו-database indexing. 
   תכין גם מדידות before/after.
   דדליין: 28 בספטמבר

תודה והצלחה!""",
                "expected_tasks": [
                    {
                        "sender": "dev-lead@company.com",
                        "sending_date": "2024-09-22",
                        "assigned_to": "תומר",
                        "title": "הגירת מסד נתונים מ-MySQL ל-PostgreSQL",
                        "description": "הוביל את ההגירה של מסד הנתונים מ-MySQL ל-PostgreSQL, כולל ניתוח סכימה, כתיבת סקריפטי הגירה, בדיקות איכות נתונים ותיעוד תהליך החזרה",
                        "due_date": "2024-09-30"
                    },
                    {
                        "sender": "dev-lead@company.com",
                        "sending_date": "2024-09-22", 
                        "assigned_to": "לילך",
                        "title": "פיתוח ממשק API לניהול משתמשים",
                        "description": "פתחי ממשק API חדש לניהול משתמשים עם authentication מלא, כולל JWT tokens, Rate limiting, Audit logs ו-Integration tests",
                        "due_date": "2024-10-05"
                    },
                    {
                        "sender": "dev-lead@company.com",
                        "sending_date": "2024-09-22",
                        "assigned_to": "עמוס",
                        "title": "אופטימיזציה לביצועי מערכת",
                        "description": "בצע optimization לביצועי המערכת, התמקד בשאילתות איטיות, caching mechanisms ו-database indexing, והכן מדידות before/after",
                        "due_date": "2024-09-28"
                    }
                ],
                "description": "Complex tasks with detailed technical requirements"
            },
            
            {
                "name": "tasks_with_dependencies",
                "email_content": """שלום צוות,

לקראת השקת המוצר החדש:

מיכל - תכיני את חומרי השיווק עד יום שני הבא. 
לאחר מכן, נעמה תוכלי להתחיל בקמפיין הרשתות החברתיות.

רן - סיים את הבדיקות האחרונות עד יום רביעי.
רק אחרי שרן יסיים, יובל יתחיל בהכנת הדמו ללקוחות (יעד: יום שישי).

כולם - נפגש ביום ראשון הבא לסקירה אחרונה לפני השקה.

מנהלת המוצר""",
                "expected_tasks": [
                    {
                        "sender": "מנהלת המוצר",
                        "sending_date": None,
                        "assigned_to": "מיכל",
                        "title": "הכנת חומרי שיווק",
                        "description": "הכיני את חומרי השיווק",
                        "due_date": None  # "יום שני הבא" - relative without context
                    },
                    {
                        "sender": "מנהלת המוצר",
                        "sending_date": None,
                        "assigned_to": "נעמה",
                        "title": "קמפיין רשתות חברתיות",
                        "description": "התחילי בקמפיין הרשתות החברתיות (לאחר שמיכל תסיים את חומרי השיווק)",
                        "due_date": None
                    },
                    {
                        "sender": "מנהלת המוצר",
                        "sending_date": None,
                        "assigned_to": "רן",
                        "title": "סיום בדיקות אחרונות",
                        "description": "סיים את הבדיקות האחרונות",
                        "due_date": None  # "יום רביעי" - relative without context
                    },
                    {
                        "sender": "מנהלת המוצר",
                        "sending_date": None,
                        "assigned_to": "יובל",
                        "title": "הכנת דמו ללקוחות",
                        "description": "הכן את הדמו ללקוחות (לאחר שרן יסיים את הבדיקות)",
                        "due_date": None  # "יום שישי" - relative without context
                    },
                    {
                        "sender": "מנהלת המוצר",
                        "sending_date": None,
                        "assigned_to": "כולם",
                        "title": "סקירה אחרונה לפני השקה",
                        "description": "פגישה לסקירה אחרונה לפני השקה",
                        "due_date": None  # "יום ראשון הבא" - relative
                    }
                ],
                "description": "Tasks with dependencies between team members"
            },
            
            {
                "name": "mixed_languages_tasks",
                "email_content": """Hi Team,

Following our meeting today (15/11/2024):

דניאל - Please prepare the API documentation in English עד ה-20 בנובמבר.
Sarah - תכיני user manual בעברית ובאנגלית, deadline: 25th November.
אילן - Create test cases for the new features by next Friday.

Let me know if you have any questions.

Best regards,
Project Manager""",
                "expected_tasks": [
                    {
                        "sender": "Project Manager",
                        "sending_date": "2024-11-15",
                        "assigned_to": "דניאל",
                        "title": "הכנת תיעוד API באנגלית",
                        "description": "Please prepare the API documentation in English",
                        "due_date": "2024-11-20"
                    },
                    {
                        "sender": "Project Manager",
                        "sending_date": "2024-11-15",
                        "assigned_to": "Sarah",
                        "title": "הכנת מדריך משתמש דו-לשוני",
                        "description": "הכיני user manual בעברית ובאנגלית",
                        "due_date": "2024-11-25"
                    },
                    {
                        "sender": "Project Manager",
                        "sending_date": "2024-11-15",
                        "assigned_to": "אילן",
                        "title": "יצירת test cases לפיצ'רים חדשים",
                        "description": "Create test cases for the new features",
                        "due_date": "2024-11-22"  # next Friday
                    }
                ],
                "description": "Mixed Hebrew/English tasks with various date formats"
            },
            
            {
                "name": "edge_case_formatting",
                "email_content": """דחוף!!! 

@@@משימות חשובות@@@

>>>>>> לירן <<<<<<
• בדוק את הבאג בקוד
• תקן את הבעיה
• עדכן בצ'אט
(הכל עד מחר!!!)

>>>>>> קרן <<<<<<  
☐ שלח מייל ללקוח
☐ תאם פגישה
☐ הכן הצעת מחיר
~~~ללא תאריך יעד~~~

++++ פרטים נוספים ++++
גם: מישהו יכול לקרוא למחר? יש פגישה חשובה!

---
שלח מטלפון""",
                "expected_tasks": [
                    {
                        "sender": None,
                        "sending_date": None,
                        "assigned_to": "לירן",
                        "title": "בדיקה ותיקון באג",
                        "description": "בדוק את הבאג בקוד, תקן את הבעיה ועדכן בצ'אט",
                        "due_date": None  # "מחר" without date context
                    },
                    {
                        "sender": None,
                        "sending_date": None,
                        "assigned_to": "קרן",
                        "title": "שליחת מייל ללקוח",
                        "description": "שלח מייל ללקוח",
                        "due_date": None
                    },
                    {
                        "sender": None,
                        "sending_date": None,
                        "assigned_to": "קרן",
                        "title": "תיאום פגישה",
                        "description": "תאם פגישה",
                        "due_date": None
                    },
                    {
                        "sender": None,
                        "sending_date": None,
                        "assigned_to": "קרן",
                        "title": "הכנת הצעת מחיר",
                        "description": "הכן הצעת מחיר",
                        "due_date": None
                    },
                    {
                        "sender": None,
                        "sending_date": None,
                        "assigned_to": "מישהו",
                        "title": "השתתפות בפגישה חשובה",
                        "description": "קריאה להשתתפות בפגישה חשובה",
                        "due_date": None  # "מחר" without context
                    }
                ],
                "description": "Unusual formatting with emojis, symbols, and informal structure"
            }
        ]

    # ======================================
    # JSON VALIDATION TESTS
    # ======================================
    
    def test_json_schema_validation(self, tasks_response: List[Dict]) -> bool:
        """Test if the response matches the expected JSON schema"""
        try:
            # Validate using Pydantic model
            validated_tasks = TaskExtractionResponse.model_validate(tasks_response)
            return True, "JSON schema validation passed"
        except ValidationError as e:
            return False, f"JSON schema validation failed: {e}"
        except Exception as e:
            return False, f"Unexpected validation error: {e}"
    
    def validate_task_fields(self, task: Dict) -> List[str]:
        """Validate individual task fields and return list of errors"""
        errors = []
        
        # Required fields
        required_fields = ['assigned_to', 'title', 'description']
        for field in required_fields:
            if field not in task or not task[field]:
                errors.append(f"Missing or empty required field: {field}")
        
        # Optional fields with type validation
        if 'sender' in task and task['sender'] is not None:
            if not isinstance(task['sender'], str):
                errors.append("sender must be string or null")
                
        if 'sending_date' in task and task['sending_date'] is not None:
            try:
                datetime.strptime(task['sending_date'], '%Y-%m-%d')
            except ValueError:
                errors.append("sending_date must be in YYYY-MM-DD format or null")
                
        if 'due_date' in task and task['due_date'] is not None:
            try:
                datetime.strptime(task['due_date'], '%Y-%m-%d')
            except ValueError:
                errors.append("due_date must be in YYYY-MM-DD format or null")
        
        return errors

    # ======================================
    # LLM-AS-A-JUDGE FUNCTIONALITY
    # ======================================
    
    async def llm_judge_evaluation(self, email_content: str, extracted_tasks: List[Dict], 
                                 expected_tasks: List[Dict]) -> Dict[str, Any]:
        """Use ChatGPT as a judge to evaluate the quality of task extraction"""
        
        judge_prompt = f"""אתה שופט מומחה להערכת איכות חילוץ משימות מתוכן אימיילים בעברית.

תוכן האימייל המקורי:
{email_content}

המשימות שחולצו על ידי המערכת:
{json.dumps(extracted_tasks, ensure_ascii=False, indent=2)}

המשימות המצופות (להשוואה):
{json.dumps(expected_tasks, ensure_ascii=False, indent=2)}

הערך את איכות החילוץ בהיבטים הבאים:

1. **דיוק (Accuracy)**: האם כל המשימות הרלוונטיות זוהו?
2. **שלמות (Completeness)**: האם יש משימות שהוחמצו או משימות מיותרות?
3. **דיוק שדות (Field Accuracy)**: האם השדות מולאו נכון (assigned_to, dates, etc.)?
4. **איכות תיאור (Description Quality)**: האם התיאורים ברורים ומדויקים?
5. **טיפול בתאריכים (Date Handling)**: האם תאריכים יחסיים תורגמו נכון?

בחזרה תן:
1. ציון כולל מ-1 עד 10
2. פירוט על כל היבט (1-5 נקודות לכל היבט)
3. הערות ספציפיות על בעיות שזוהו
4. התלונות על איכות הפלט

ענה בפורמט JSON:
{{
  "overall_score": <ציון 1-10>,
  "scores": {{
    "accuracy": <1-5>,
    "completeness": <1-5>, 
    "field_accuracy": <1-5>,
    "description_quality": <1-5>,
    "date_handling": <1-5>
  }},
  "issues_found": ["רשימת בעיות"],
  "positive_aspects": ["רשימת היבטים חיוביים"],
  "improvement_suggestions": ["הצעות לשיפור"]
}}
"""

        # Try ChatGPT first, fallback to local LLM if not available
        if self.openai_client:
            try:
                print("   🤖 Using ChatGPT (GPT-4) as judge...")
                
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",  # Using GPT-4o-mini for cost efficiency
                    messages=[
                        {
                            "role": "system", 
                            "content": "אתה מומחה להערכת איכות חילוץ משימות. ענה בפורמט JSON כפי שהתבקש. תמיד החזר JSON תקין."
                        },
                        {
                            "role": "user", 
                            "content": judge_prompt
                        }
                    ],
                    temperature=0.1,  # Low temperature for consistent evaluation
                    max_tokens=1500,
                    response_format={"type": "json_object"}  # Force JSON response
                )
                
                content = response.choices[0].message.content
                
                # Parse the JSON response
                try:
                    result = json.loads(content)
                    # Validate the response structure
                    required_keys = ["overall_score", "scores", "issues_found", "positive_aspects", "improvement_suggestions"]
                    if all(key in result for key in required_keys):
                        print("   ✅ ChatGPT judge evaluation completed successfully")
                        return result
                    else:
                        print("   ⚠️  ChatGPT response missing required keys, using fallback")
                        raise Exception("Incomplete response structure")
                        
                except json.JSONDecodeError as e:
                    print(f"   ⚠️  Failed to parse ChatGPT JSON response: {e}")
                    raise Exception(f"Invalid JSON from ChatGPT: {e}")
                    
            except Exception as e:
                print(f"   ⚠️  ChatGPT evaluation failed: {str(e)}, falling back to local LLM")
                # Fall through to local LLM fallback
        
        # Fallback to local LLM engine
        try:
            print("   🔄 Using local LLM as judge fallback...")
            
            messages = [
                Message(role="system", content="אתה מומחה להערכת איכות חילוץ משימות. ענה בפורמט JSON כפי שהתבקש."),
                Message(role="user", content=judge_prompt)
            ]
            
            # Use the task service's LLM engine for evaluation
            response = await self.task_service.engine.get_structured_completion(
                messages=messages,
                output_schema=dict,  # We expect a JSON dict
                session_id="task_judge"
            )
            
            print("   ✅ Local LLM judge evaluation completed")
            return response
            
        except Exception as e:
            print(f"   ❌ Both ChatGPT and local LLM judge failed")
            return {
                "overall_score": 0,
                "scores": {"accuracy": 0, "completeness": 0, "field_accuracy": 0, 
                          "description_quality": 0, "date_handling": 0},
                "issues_found": [f"LLM judge evaluation failed: {str(e)}"],
                "positive_aspects": [],
                "improvement_suggestions": ["Fix LLM judge integration"],
                "judge_used": "fallback_error"
            }

    # ======================================
    # MAIN TEST RUNNER
    # ======================================
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests and return detailed results"""
        results = {
            "test_summary": {
                "total_tests": len(self.edge_case_emails),
                "passed_json_validation": 0,
                "failed_json_validation": 0,
                "average_llm_score": 0,
                "test_start_time": datetime.now().isoformat()
            },
            "detailed_results": []
        }
        
        total_llm_score = 0
        
        print(f"🚀 Starting comprehensive task extraction tests...")
        print(f"📊 Testing {len(self.edge_case_emails)} edge case scenarios")
        print("=" * 80)
        
        for i, test_case in enumerate(self.edge_case_emails, 1):
            print(f"\n🧪 Test {i}/{len(self.edge_case_emails)}: {test_case['name']}")
            print(f"📝 Description: {test_case['description']}")
            print("-" * 60)
            
            test_result = {
                "test_name": test_case['name'],
                "description": test_case['description'],
                "email_content": test_case['email_content'],
                "expected_tasks": test_case['expected_tasks'],
                "extracted_tasks": None,
                "json_validation": {"passed": False, "message": ""},
                "field_validation_errors": [],
                "llm_judge_evaluation": None,
                "test_duration": 0
            }
            
            start_time = datetime.now()
            
            try:
                # Extract tasks using the service
                print("🔍 Extracting tasks...")
                extracted_tasks = await self.task_service.extract_tasks(test_case['email_content'])
                test_result['extracted_tasks'] = [task.model_dump() for task in extracted_tasks]
                
                # JSON Schema Validation
                print("✅ Validating JSON schema...")
                json_valid, json_message = self.test_json_schema_validation(test_result['extracted_tasks'])
                test_result['json_validation'] = {"passed": json_valid, "message": json_message}
                
                if json_valid:
                    results['test_summary']['passed_json_validation'] += 1
                    print(f"   ✅ JSON validation: PASSED")
                else:
                    results['test_summary']['failed_json_validation'] += 1
                    print(f"   ❌ JSON validation: FAILED - {json_message}")
                
                # Field Validation
                print("🔍 Validating individual fields...")
                all_field_errors = []
                for j, task in enumerate(test_result['extracted_tasks']):
                    field_errors = self.validate_task_fields(task)
                    if field_errors:
                        all_field_errors.extend([f"Task {j+1}: {error}" for error in field_errors])
                
                test_result['field_validation_errors'] = all_field_errors
                if all_field_errors:
                    print(f"   ⚠️  Field validation issues: {len(all_field_errors)} errors found")
                else:
                    print(f"   ✅ Field validation: PASSED")
                
                # LLM Judge Evaluation
                print("🤖 Running LLM judge evaluation...")
                llm_evaluation = await self.llm_judge_evaluation(
                    test_case['email_content'],
                    test_result['extracted_tasks'],
                    test_case['expected_tasks']
                )
                test_result['llm_judge_evaluation'] = llm_evaluation
                
                overall_score = llm_evaluation.get('overall_score', 0)
                total_llm_score += overall_score
                print(f"   🎯 LLM Judge Score: {overall_score}/10")
                
                # Print extracted tasks
                print(f"\n📋 Extracted {len(test_result['extracted_tasks'])} tasks:")
                for j, task in enumerate(test_result['extracted_tasks'], 1):
                    print(f"   {j}. {task.get('assigned_to', 'N/A')} - {task.get('title', 'N/A')}")
                    if task.get('due_date'):
                        print(f"      Due: {task['due_date']}")
                
            except Exception as e:
                test_result['json_validation'] = {"passed": False, "message": f"Test execution failed: {str(e)}"}
                results['test_summary']['failed_json_validation'] += 1
                print(f"   ❌ Test execution failed: {str(e)}")
            
            test_result['test_duration'] = (datetime.now() - start_time).total_seconds()
            results['detailed_results'].append(test_result)
            
            print(f"⏱️  Test completed in {test_result['test_duration']:.2f} seconds")
        
        # Calculate final statistics
        results['test_summary']['average_llm_score'] = total_llm_score / len(self.edge_case_emails) if self.edge_case_emails else 0
        results['test_summary']['test_end_time'] = datetime.now().isoformat()
        
        # Print final summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        print(f"✅ JSON Validation Passed: {results['test_summary']['passed_json_validation']}/{results['test_summary']['total_tests']}")
        print(f"❌ JSON Validation Failed: {results['test_summary']['failed_json_validation']}/{results['test_summary']['total_tests']}")
        print(f"🎯 Average LLM Judge Score: {results['test_summary']['average_llm_score']:.2f}/10")
        
        # Identify worst performing tests
        worst_tests = sorted(results['detailed_results'], 
                           key=lambda x: x.get('llm_judge_evaluation', {}).get('overall_score', 0))[:3]
        
        print(f"\n🚨 Tests needing attention (lowest LLM scores):")
        for test in worst_tests:
            score = test.get('llm_judge_evaluation', {}).get('overall_score', 0)
            print(f"   • {test['test_name']}: {score}/10")
        
        return results


# ======================================
# PYTEST INTEGRATION  
# ======================================

@pytest.fixture
def test_suite():
    """Pytest fixture for the test suite"""
    return TaskExtractionTestSuite()


@pytest.mark.asyncio
async def test_json_validation_all_cases(test_suite):
    """Test JSON validation for all edge cases"""
    results = await test_suite.run_comprehensive_tests()
    
    # Assert that majority of tests pass JSON validation
    passed = results['test_summary']['passed_json_validation']
    total = results['test_summary']['total_tests']
    
    assert passed >= (total * 0.8), f"Less than 80% of tests passed JSON validation: {passed}/{total}"


@pytest.mark.asyncio  
async def test_llm_judge_scores_acceptable(test_suite):
    """Test that LLM judge scores are acceptable"""
    results = await test_suite.run_comprehensive_tests()
    
    avg_score = results['test_summary']['average_llm_score']
    assert avg_score >= 6.0, f"Average LLM judge score too low: {avg_score}/10"


@pytest.mark.asyncio
async def test_individual_edge_cases(test_suite):
    """Test each edge case individually"""
    for test_case in test_suite.edge_case_emails:
        try:
            extracted_tasks = await test_suite.task_service.extract_tasks(test_case['email_content'])
            
            # Basic validation
            assert isinstance(extracted_tasks, list), f"Expected list, got {type(extracted_tasks)}"
            
            # JSON schema validation
            task_dicts = [task.model_dump() for task in extracted_tasks]
            json_valid, message = test_suite.test_json_schema_validation(task_dicts)
            assert json_valid, f"JSON validation failed for {test_case['name']}: {message}"
            
        except Exception as e:
            pytest.fail(f"Test case {test_case['name']} failed: {str(e)}")


# ======================================
# COMMAND LINE RUNNER
# ======================================

async def main():
    """Main function for command line execution"""
    test_suite = TaskExtractionTestSuite()
    results = await test_suite.run_comprehensive_tests()
    
    # Save results to file
    results_file = Path(__file__).parent / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    print("\n🏁 Test suite completed!")


if __name__ == "__main__":
    asyncio.run(main())