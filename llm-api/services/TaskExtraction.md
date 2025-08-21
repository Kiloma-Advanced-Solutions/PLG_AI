# Task Extraction Service Documentation

## Overview

The Task Extraction Service is an AI-powered service that automatically identifies and extracts actionable tasks from email content. It uses a Large Language Model (LLM) to intelligently parse email text and extract structured task information including assignments, deadlines, and responsibilities.

## Request Workflow

When an API request is sent to the task extraction service, the following workflow is executed:

### 1. API Request Reception
- **Endpoint**: `/api/tasks/extract`
- **Method**: POST with JSON payload
- **Location**: `llm-api/api/routes.py` - `extract_tasks()` function

### 2. Request Validation
- **Model**: `TaskExtractionRequest` (Pydantic validation)
- **Validates**: 
  - `email_content` is a non-empty string
- **Location**: `llm-api/core/models.py`

### 3. Service Invocation
- **Service**: `TaskService.extract_tasks()`
- **Input Processing**: Email content passed as string
- **Location**: `llm-api/services/task_service.py`

### 4. LLM Prompt Preparation
```python
messages = [
    Message(role="system", content=get_task_system_prompt()),
    Message(role="user", content=email_content)
]
```
- **System Prompt**: Hebrew instructions for task identification and extraction
- **User Content**: The actual email content to analyze

### 5. LLM Engine Processing
- **Engine**: `llm_engine.get_structured_completion()`
- **Schema**: `TaskExtractionResponse` (List[TaskItem])
- **Session**: "task_extraction" session ID
- **Location**: `llm-api/core/llm_engine.py`

### 6. Model Execution
- **Model**: Configured LLM (e.g., gemma-3-12b-it-qat-autoawq)
- **Process**: 
  - Analyzes Hebrew email content
  - Identifies actionable tasks
  - Extracts task metadata (assignee, deadlines, etc.)
  - Returns structured JSON array

### 7. Response Filtering
- **Validation**: Filters tasks with required fields
- **Required Fields**: `assigned_to`, `title`, `description`
- **Function**: `is_field_valid()` validation
- **Location**: `llm-api/services/task_service.py`

### 8. API Response
- **Success**: Returns filtered list of TaskItem objects
- **Error Handling**: HTTP exceptions for various failure scenarios
- **Logging**: Request/response details logged for debugging

### Flow Diagram

```
┌─────────────────────────────────────────┐
│ Client HTTP POST Request                │
│ /api/tasks/extract                      │
│ Content-Type: application/json          │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ FastAPI Framework                       │
│ - Request body parsing (JSON → dict)    │
│ - Pydantic validation                   │
│ - TaskExtractionRequest(**body)         │
│ - email_content: str                    │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ routes.py                               │
│ @app.post("/api/tasks/extract")         │
│ async def extract_tasks(request)        │
│ - Route handler execution               │
│ - Extract request.email_content         │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ task_service.py                         │
│ task_service.extract_tasks()            │
│ - Business logic layer entry           │
│ - Email content processing              │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ task_service.py                         │
│ Prepare LLM messages:                   │
│ 1. get_task_system_prompt()             │
│ 2. Message(role="system", content=...)  │
│ 3. Message(role="user", content=email)  │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ llm_engine.py                           │
│ self.engine.get_structured_completion() │
│ - messages: List[Message]               │
│ - output_schema: TaskExtractionResponse │
│ - session_id: "task_extraction"        │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ llm_engine.py                           │
│ Internal processing:                    │
│ 1. Prepare request payload              │
│ 2. Add structured output instructions   │
│ 3. HTTP POST to LLM model endpoint      │
│ 4. Model: gemma-3-12b-it-qat-autoawq    │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ LLM Model (External)                    │
│ - Parse Hebrew email content            │
│ - Identify actionable tasks             │
│ - Extract task assignments & deadlines  │
│ - Return structured JSON array          │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ llm_engine.py                           │
│ Response processing:                    │
│ 1. Receive HTTP response               │
│ 2. Parse JSON content                   │
│ 3. Validate against TaskItem[] schema   │
│ 4. Return List[TaskItem] objects        │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ task_service.py                         │
│ Filter valid tasks:                     │
│ - Check assigned_to field               │
│ - Check title field                     │
│ - Check description field               │
│ - Return filtered task list             │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ routes.py                               │
│ return filtered_tasks                   │
│ - List[TaskItem] objects returned       │
│ - FastAPI handles JSON serialization    │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ FastAPI Framework                       │
│ - Automatic JSON serialization          │
│ - HTTP 200 OK response                  │
│ - Content-Type: application/json        │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ Client Response                         │
│ [                                       │
│   {                                     │
│     "sender": "email@domain.com",       │
│     "sending_date": "2024-01-16",       │
│     "assigned_to": "דוד",               │
│     "title": "הכנת דוח",                │
│     "description": "הכנת דוח רבעוני",    │
│     "due_date": "2024-01-20"            │
│   }                                     │
│ ]                                       │
└─────────────────────────────────────────┘
```

### Error Handling Flow

```
┌─────────────────────────────────────────┐
│ Any Step in Main Flow                   │
└──────────────────┬──────────────────────┘
                   ↓ (Exception)
┌─────────────────────────────────────────┐
│ routes.py                               │
│ except Exception as e:                  │
│ logger.error(f"Task extraction error") │
│ raise HTTPException(status_code=500)    │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ FastAPI Error Response                  │
│ {                                       │
│   "detail": "Failed to extract tasks"  │
│   "status_code": 500                    │
│ }                                       │
└─────────────────────────────────────────┘
```

## API Endpoint

### POST `/api/tasks/extract`

Extracts actionable tasks from Hebrew email content.

#### Request Format

```json
{
  "email_content": "string"
}
```

**Parameters:**
- `email_content` (string, required): The email content to analyze for tasks

#### Response Format

```json
[
  {
    "sender": "string|null",
    "sending_date": "string|null",
    "assigned_to": "string|null",
    "title": "string|null", 
    "description": "string|null",
    "due_date": "string|null"
  }
]
```

**Response Fields:**
- `sender`: Email address or name of task sender
- `sending_date`: Date when email was sent (YYYY-MM-DD format)
- `assigned_to`: Name of person assigned to the task
- `title`: Short task title
- `description`: Detailed task description
- `due_date`: Task deadline (YYYY-MM-DD format)

## Task Extraction Criteria

### ✅ Tasks WILL be extracted if:
- Task is explicitly assigned to a specific person by name
- Task contains a clear action to be performed
- Task is clearly formulated with personal responsibility
- All required fields (assigned_to, title, description) are identifiable

### ❌ Tasks will NOT be extracted if:
- Task is assigned to generic groups ("כולם", "הצוות", "מי שיכול")
- Content is informational/update only (no action required)
- Any of the required fields (assigned_to, title, description) is missing
- Task assignee is a role rather than a specific person name



## Usage Examples

### Example 1: cURL Request

```bash
curl -X POST http://localhost:8090/api/tasks/extract \
  -H "Content-Type: application/json" \
  -d '{
    "email_content": "שלום צוות,\n\nדוד צריך להכין דוח עד יום רביעי.\nרחל תבדוק נתונים עד מחר.\n\nתודה!"
  }'
```

**Response:**
```json
[
  {
    "sender": null,
    "sending_date": null,
    "assigned_to": "דוד",
    "title": "הכנת דוח",
    "description": "הכנת דוח עד יום רביעי",
    "due_date": "2024-01-17"
  },
  {
    "sender": null,
    "sending_date": null,
    "assigned_to": "רחל",
    "title": "בדיקת נתונים",
    "description": "בדיקת נתונים עד מחר",
    "due_date": "2024-01-16"
  }
]
```

### Example 2: JavaScript/Fetch

```javascript
const response = await fetch('http://localhost:8090/api/tasks/extract', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email_content: `מאת: manager@company.com
תאריך: 2024-01-15T10:00:00Z
נושא: משימות דחופות

אבי - בבקשה תתקשר ללקוח עד היום.
שרה צריכה להכין הצעת מחיר עד מחר בצהריים.
יוסי יבדוק המלאי עד סוף השבוע.`
  })
});

const tasks = await response.json();
console.log(`Extracted ${tasks.length} tasks:`, tasks);
```

### Example 3: Python

```python
import requests
from datetime import datetime

url = "http://localhost:8090/api/tasks/extract"
data = {
    "email_content": """
מאת: project.manager@company.com
תאריך: 2024-01-15T09:00:00Z
נושא: תכנון פרויקט חדש

היי צוות,

לפרויקט החדש נדרש:
- דני יכין מסמך דרישות עד יום שלישי
- מיכל תתחיל בעיצוב UI עד סוף השבוע  
- רון יבדוק עם IT את התשתית עד יום חמישי

בהצלחה!
"""
}

response = requests.post(url, json=data)
tasks = response.json()

for i, task in enumerate(tasks, 1):
    print(f"Task {i}: {task['title']} - {task['assigned_to']}")
```

## Testing

### Running Tests

```bash
# Test task extraction with specific email
cd llm-api/tests
python test_task_extraction.py

# Run specific test scenarios
python -m pytest test_task_extraction.py -v

# Test with comprehensive test suite
python run_tests.py
```

### Test Data

Test emails are available in `llm-api/tests/test_emails.json` with various scenarios:
- Simple task assignments
- Complex multi-task emails
- Edge cases (no tasks, invalid assignments)
- Emails with dates and deadlines
- Meeting notes with action items

### Test Results Analysis

The test framework includes:
- **Automated validation** against expected task counts
- **LLM judge evaluation** using ChatGPT for quality assessment
- **Field completeness checking** for required fields
- **Scoring system** (0-100) for extraction accuracy
- **Detailed logging** of extraction results

## Integration

### API Integration

```javascript
// Task extraction utility function
async function extractTasks(emailContent) {
  try {
    const response = await fetch('/api/tasks/extract', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email_content: emailContent })
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Task extraction failed:', error);
    throw error;
  }
}

// Process extracted tasks
function processTasks(tasks) {
  return tasks.map(task => ({
    id: generateTaskId(),
    assignee: task.assigned_to,
    title: task.title,
    description: task.description,
    dueDate: task.due_date ? new Date(task.due_date) : null,
    source: 'email',
    status: 'pending'
  }));
}
```

### Task Management Integration

```javascript
// Integration with task management system
class TaskManager {
  async importFromEmail(emailContent) {
    try {
      const extractedTasks = await extractTasks(emailContent);
      const processedTasks = processTasks(extractedTasks);
      
      for (const task of processedTasks) {
        await this.addTask(task);
        await this.notifyAssignee(task);
      }
      
      return {
        success: true,
        tasksCreated: processedTasks.length,
        tasks: processedTasks
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
}
```
