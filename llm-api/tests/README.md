# Task Extraction Testing

This directory contains comprehensive tests for the task extraction functionality using ChatGPT as an LLM judge.

## Overview

The testing framework:
1. **Validates JSON format** - Checks if the model output matches the expected `TaskItem` schema
2. **Uses ChatGPT as judge** - Evaluates the quality of task extraction on a 0-100 scale using Hebrew instructions
3. **Tests 10 edge cases** - Covers various scenarios like missing information, relative dates, unclear assignments, etc.

## Test Cases

The `test_emails.json` file contains 10 carefully crafted test emails:

1. **no_tasks_informational** - Informational email with no actual tasks
2. **multiple_tasks_different_people** - Multiple tasks assigned to different people
3. **relative_dates_hebrew** - Relative dates in Hebrew ("מחר", "השבוע הבא")
4. **unclear_assignment** - Tasks with unclear or missing assignments
5. **missing_sender_info** - Email with missing sender information
6. **complex_nested_tasks** - Complex nested tasks and sub-tasks
7. **ambiguous_dates** - Ambiguous or vague dates
8. **hebrew_dates_times** - Hebrew calendar dates and specific times
9. **contradictory_information** - Contradictory or confusing information
10. **urgent_multiple_deadlines** - Multiple urgent tasks with tight deadlines

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

3. **Check OpenAI access:**
   ```bash
   python tests/check_openai_access.py
   ```

## Running Tests

### Simple Test Runner
```bash
python tests/run_tests.py
```

### Using Pytest
```bash
pytest tests/test_task_extraction.py::test_task_extraction_comprehensive -v
```

### Direct Python Execution
```bash
python tests/test_task_extraction.py
```

## Test Output

The tests generate:
- **Console output** with progress and summary
- **JSON results file** with detailed results (`task_extraction_results_YYYYMMDD_HHMMSS.json`)
- **Log file** with detailed execution logs (`test_run.log`)

## Evaluation Criteria

ChatGPT judges each extraction using Hebrew instructions on:

- **שלמות (40%)** - Did the model extract ALL tasks mentioned?
- **דיוק (40%)** - Are the extracted details correct?
- **איכות שדות (20%)** - Are all fields filled accurately?

### Scoring Scale:
- **90-100**: מעולה - All tasks extracted with perfect details
- **80-89**: טוב מאוד - Minor errors or missing optional details
- **70-79**: טוב - Some tasks missed or moderate errors
- **60-69**: סביר - Several errors or missing tasks
- **0-59**: חלש - Major errors or most tasks missed

The judge provides feedback in Hebrew format:
```
ציון: [number]
נקודות חוזק: [what was done well]
נקודות חולשה: [what was missed/incorrect]
משימות מצופות: [list what should have been found]
```

## Expected TaskItem Format

Each extracted task should follow this schema:

```json
{
  "sender": "string or null",
  "sending_date": "YYYY-MM-DD or null", 
  "assigned_to": "string or null",
  "title": "string (required)",
  "description": "string (required)",
  "due_date": "YYYY-MM-DD or null"
}
```

## Files

- `test_emails.json` - Test email cases
- `test_task_extraction.py` - Main testing framework
- `run_tests.py` - Simple test runner
- `check_openai_access.py` - OpenAI API verification
- `README.md` - This documentation