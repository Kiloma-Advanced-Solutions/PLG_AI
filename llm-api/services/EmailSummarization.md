# Email Summarization Service Documentation

## Overview

The Email Summarization Service is an AI-powered service that automatically extracts metadata and generates concise summaries from email content. It uses a Large Language Model (LLM) to intelligently parse email structures and create structured summaries.


## Request Workflow

When an API request is sent to the email summarization service, the following workflow is executed:

### 1. API Request Reception
- **Endpoint**: `/api/summarization/summarize`
- **Method**: POST with JSON payload
- **Location**: `llm-api/api/routes.py` - `summarize_email()` function

### 2. Request Validation
- **Model**: `EmailSummarizationRequest` (Pydantic validation)
- **Validates**: 
  - `email_content` is a non-empty string
  - `length` is an integer (defaults to 100 if not provided)
- **Location**: `llm-api/core/models.py`

### 3. Service Invocation
- **Service**: `SummarizationService.summarize_email()`
- **Input Processing**: Email content passed as string
- **Location**: `llm-api/services/summarization_service.py`

### 4. LLM Prompt Preparation
```python
messages = [
    Message(role="system", content=get_summarization_system_prompt(length)),
    Message(role="user", content=email_content)
]
```
- **System Prompt**: Hebrew instructions for metadata extraction and summarization
- **User Content**: The actual email content to process

### 5. LLM Engine Processing
- **Engine**: `llm_engine.get_structured_completion()`
- **Schema**: `EmailSummary` model for structured output
- **Session**: "email_summarization" session ID
- **Location**: `llm-api/core/llm_engine.py`

### 6. Model Execution
- **Model**: Configured LLM (e.g., gemma-3-12b-it-qat-autoawq)
- **Process**: 
  - Analyzes email content
  - Extracts metadata (sender, date, title)
  - Generates summary of specified length
  - Returns structured JSON response

### 7. Response Validation
- **Output Schema**: `EmailSummary` Pydantic model
- **Fields Validated**:
  - `sender`: Optional email address
  - `sending_date`: Optional datetime
  - `title`: Optional string
  - `summary`: Optional string

### 8. API Response
- **Success**: Returns `EmailSummary` object as JSON
- **Error Handling**: HTTP exceptions for various failure scenarios
- **Logging**: Request/response details logged for debugging

### Flow Diagram
```
┌─────────────────────────────────────────┐
│ Client HTTP POST Request                │
│ /api/summarization/summarize            │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ routes.py                               │
│ @app.post("/api/summarization/summarize│
│ summarize_email(request)                │
│ - FastAPI route handler                 │
│ - Request body parsing                  │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ models.py                               │
│ EmailSummarizationRequest(**request)    │
│ - Pydantic validation                   │
│ - email_content: str                    │
│ - length: int = 100                     │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ summarization_service.py                │
│ summarization_service_instance          │
│ .summarize_email(email_content, length) │
│ - Business logic layer                  │
│ - Input processing                      │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ summarization_service.py                │
│ get_summarization_system_prompt(length) │
│ - Generate Hebrew system prompt         │
│ - Include JSON schema instructions      │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ models.py                               │
│ Message(role="system", content=prompt)  │
│ Message(role="user", content=email)     │
│ - Create LLM message objects            │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ llm_engine.py                           │
│ llm_engine.get_structured_completion()  │
│ - messages: List[Message]               │
│ - output_schema: EmailSummary           │
│ - session_id: "email_summarization"    │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ llm_engine.py                           │
│ _make_completion_request()              │
│ - HTTP request to LLM model             │
│ - Model: gemma-3-12b-it-qat-autoawq     │
│ - Temperature: 0.7, Max tokens: 2048    │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ LLM Model Processing                    │
│ - Parse email content                   │
│ - Extract metadata (sender, date, title)│
│ - Generate summary                      │
│ - Return structured JSON                │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ llm_engine.py                           │
│ _parse_structured_response()            │
│ - JSON parsing                          │
│ - Schema validation                     │
│ - Return parsed object                  │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ models.py                               │
│ EmailSummary(**parsed_response)         │
│ - sender: Optional[EmailStr]            │
│ - sending_date: Optional[datetime]      │
│ - title: Optional[str]                  │
│ - summary: Optional[str]                │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ routes.py                               │
│ return EmailSummary object              │
│ - FastAPI automatic JSON serialization │
│ - HTTP 200 response                     │
│ - Content-Type: application/json        │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ Client Response                         │
│ {                                       │
│   "sender": "email@domain.com",         │
│   "sending_date": "2024-01-16T14:22:15Z"│
│   "title": "Email Summary Title",       │
│   "summary": "Generated summary text"   │
│ }                                       │
└─────────────────────────────────────────┘
```


## API Endpoint

### POST `/api/summarization/summarize`

Summarizes an email and extracts metadata.

#### Request Format

```json
{
  "email_content": "string",
  "length": 100
}
```

**Parameters:**
- `email_content` (string, required): The email content to summarize including its metadata
- `length` (integer, optional): Target summary length in characters (default: 100)

#### Response Format

```json
{
  "sender": "string|null",
  "sending_datetime": "string|null", 
  "title": "string|null",
  "summary": "string|null"
}
```

**Response Fields:**
- `sender`: Email address of the sender
- `sending_datetime`: ISO 8601 formatted datetime (e.g., "2024-01-16T14:22:15Z")
- `title`: Short descriptive title for the email
- `summary`: Concise summary of the email content

## Email Input Formats

### Format 1: Structured Email (Recommended)
```
מאת: sender@example.com
תאריך: 2024-01-16T14:22:15Z
נושא: נושא המייל

תוכן המייל כאן...
```

### Format 2: Plain Text Email
```
שלום, זהו תוכן המייל ללא מטאדאטה...
```

## Usage Examples

### Example 1: cURL Request

```bash
curl -X POST http://localhost:8090/api/summarization/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "email_content": "מאת: john@company.com\nתאריך: 2024-01-15T09:30:00Z\nנושא: פגישת צוות\n\nשלום לכולם, הפגישה השבועית תתקיים מחר ב-10:00. נדון על התקדמות הפרויקט.",
    "length": 80
  }'
```

**Response:**
```json
{
  "sender": "john@company.com",
  "sending_date": "2024-01-15T09:30:00Z",
  "title": "פגישת צוות שבועית",
  "summary": "הפגישה השבועית מחר ב-10:00 לדיון בהתקדמות הפרויקט"
}
```

### Example 2: JavaScript/Fetch

```javascript
const response = await fetch('http://localhost:8090/api/summarization/summarize', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email_content: `מאת: sarah@tech.il
תאריך: 2024-01-16T14:22:15Z
נושא: הצעה לשיתוף פעולה

היי רבקה, אני כותבת אליך לגבי הצעה מעניינת לשיתוף פעולה...`,
    length: 150
  })
});

const summary = await response.json();
console.log(summary);
```

### Example 3: Python

```python
import requests

url = "http://localhost:8090/api/summarization/summarize"
data = {
    "email_content": """מאת: admin@university.ac.il
תאריך: 2024-01-18T08:15:45Z
נושא: שינויים במערכת ההרשמה

שלום סטודנטים יקרים, אנו רוצים להודיע לכם על שינויים חשובים...""",
    "length": 120
}

response = requests.post(url, json=data)
summary = response.json()
print(summary)
```

## Testing

### Running Tests

```bash
# Test specific email with custom length
cd llm-api/tests
python test_summarization.py 0 150

# Test comprehensive suite
python test_summarization.py
```

### Test Data

Test emails are available in `llm-api/tests/test_summarization_emails.json` with various scenarios:
- Short announcements
- Long business emails
- Technical reports
- Meeting invitations
- Legal documents


### API Integration

```javascript
// Example integration function
async function summarizeEmail(emailContent, targetLength = 100) {
  try {
    const response = await fetch('/api/summarization/summarize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email_content: emailContent,
        length: targetLength
      })
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Summarization failed:', error);
    throw error;
  }
}
```


