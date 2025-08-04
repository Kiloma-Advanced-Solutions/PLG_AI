# Task Extraction Comprehensive Test Suite

This test suite provides comprehensive testing for the task extraction functionality, covering both JSON validation and LLM-as-a-judge quality evaluation.

## Features

### 🧪 Test Coverage
- **10 Edge Case Scenarios**: Covers various real-world email formats and complexities
- **JSON Schema Validation**: Ensures output matches the expected `TaskExtractionResponse` format
- **LLM-as-a-Judge**: Uses AI to evaluate the quality and accuracy of extracted tasks
- **Field Validation**: Validates individual task fields for correctness
- **Automated Reporting**: Generates detailed test reports with scores and recommendations

### 📊 Edge Cases Tested

1. **Single Simple Task** - Basic email with one clear task
2. **Multiple Tasks with Different Assignees** - Complex email with multiple people and tasks
3. **Tasks Without Due Dates** - Tasks that don't specify deadlines
4. **Relative Hebrew Dates** - Tasks with dates like "מחר", "בעוד יומיים", "בשבוע הבא"
5. **No Tasks Email** - Informational emails without actionable tasks
6. **Ambiguous Assignments** - Tasks with unclear or non-specific assignees
7. **Detailed Complex Tasks** - Technical tasks with comprehensive requirements
8. **Tasks with Dependencies** - Tasks that depend on completion of other tasks
9. **Mixed Languages** - Hebrew/English mixed content
10. **Edge Case Formatting** - Unusual formatting with emojis and symbols

## Running the Tests

### Prerequisites

1. **Install dependencies**:
```bash
cd llm-api
pip install -r requirements.txt
```

2. **Set up ChatGPT API key securely** (for LLM judge):
```bash
# Get your API key from: https://platform.openai.com/api-keys

# SECURE Method 1: Environment variable (recommended)
export OPENAI_API_KEY="your_actual_api_key_here"

# SECURE Method 2: Local .env file (project-specific)
cd tests
echo "OPENAI_API_KEY=your_actual_api_key_here" > .env

# Verify your setup is secure
python verify_secure_setup.py
```

3. **Ensure the LLM API service is running**:
```bash
cd llm-api
python main.py
```

### Option 1: Run with pytest (Recommended)
```bash
cd llm-api/tests
pytest test_task_extraction_comprehensive.py -v
```

### Option 2: Run standalone comprehensive tests
```bash
cd llm-api/tests
python run_comprehensive_tests.py
```

### Option 3: Run specific test categories
```bash
# JSON validation only
pytest test_task_extraction_comprehensive.py::test_json_validation_all_cases -v

# LLM judge evaluation only  
pytest test_task_extraction_comprehensive.py::test_llm_judge_scores_acceptable -v

# Individual edge cases
pytest test_task_extraction_comprehensive.py::test_individual_edge_cases -v
```

## LLM Judge: ChatGPT vs Local LLM

The test suite uses **ChatGPT (GPT-4o-mini)** as the primary judge for evaluating task extraction quality:

### 🤖 Judge Selection Logic
1. **Primary**: ChatGPT (GPT-4o-mini) - More objective and consistent evaluation
2. **Fallback**: Your local LLM (Gemma-3-12b) - If ChatGPT is unavailable
3. **Error**: Mock response - If both fail

### 📊 Why ChatGPT as Judge?
- **Consistency**: More reliable scoring across different test runs
- **Objectivity**: Less influenced by the same biases as your extraction model
- **Quality**: Better understanding of task extraction nuances
- **Cost-effective**: Uses GPT-4o-mini which is very affordable

### 🔧 Configuration Options
You can modify the judge model in the test suite:
- `gpt-4o-mini` (default) - Cost-effective, good quality
- `gpt-4o` - Higher quality, more expensive
- `gpt-3.5-turbo` - Fastest, lowest cost

## Understanding Test Results

### JSON Validation Results
- ✅ **PASSED**: Output matches the expected JSON schema
- ❌ **FAILED**: Output has schema violations or missing required fields

### LLM Judge Scoring (1-10 scale)
- **8-10**: Excellent - Tasks extracted accurately with high quality
- **6-7**: Good - Minor issues but generally correct
- **4-5**: Fair - Some significant issues need attention
- **1-3**: Poor - Major problems with task extraction

### Individual Scoring Criteria
1. **Accuracy (1-5)**: Were all relevant tasks identified?
2. **Completeness (1-5)**: Any missed or extra tasks?
3. **Field Accuracy (1-5)**: Are assigned_to, dates, etc. correct?
4. **Description Quality (1-5)**: Are descriptions clear and accurate?
5. **Date Handling (1-5)**: Were relative dates converted correctly?

## Expected Output Format

Each extracted task should follow this structure:
```json
{
  "sender": "email@domain.com or null",
  "sending_date": "YYYY-MM-DD or null", 
  "assigned_to": "Person Name",
  "title": "Task Title",
  "description": "Detailed task description",
  "due_date": "YYYY-MM-DD or null"
}
```

## Example Test Report

```
🧪 Test 1/10: single_simple_task
📝 Description: Single simple task with clear assignee and due date
------------------------------------------------------------
🔍 Extracting tasks...
✅ Validating JSON schema...
   ✅ JSON validation: PASSED
🔍 Validating individual fields...
   ✅ Field validation: PASSED
🤖 Running LLM judge evaluation...
   🎯 LLM Judge Score: 9/10

📋 Extracted 1 tasks:
   1. יוסי - הכנת דוח שבועי
      Due: 2024-01-02
```

## Troubleshooting

### Common Issues

**LLM Service Not Running**
```
Error: Failed to extract tasks: Connection refused
Solution: Start the LLM API service first
```

**Import Errors**
```
Error: ModuleNotFoundError
Solution: Ensure you're running from the correct directory and dependencies are installed
```

**Low LLM Judge Scores**
```
Indication: The task extraction system may need tuning
Check: Review failed test cases and adjust the system prompt
```

## Customizing Tests

### Adding New Edge Cases
1. Add new test case to `edge_case_emails` property in `TaskExtractionTestSuite`
2. Include expected output for validation
3. Run tests to verify behavior

### Modifying LLM Judge Criteria
Update the `llm_judge_evaluation` method to change scoring criteria or add new evaluation aspects.

### Adjusting Pass/Fail Thresholds
Modify the assertion thresholds in the pytest test functions:
- JSON validation pass rate (default: 80%)
- Average LLM score (default: 6.0/10)

## Files Description

- `test_task_extraction_comprehensive.py` - Main test suite with all test logic
- `run_comprehensive_tests.py` - Standalone runner for manual testing
- `README_TESTING.md` - This documentation file
- `test_results_YYYYMMDD_HHMMSS.json` - Generated test result files