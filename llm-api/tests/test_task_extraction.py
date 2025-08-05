"""
Unit tests for task extraction functionality using ChatGPT as LLM judge
"""
import json
import asyncio
import logging
from typing import List, Dict, Any
from datetime import date, datetime
import pytest
from pydantic import ValidationError

# Import our models and services
from core.models import TaskItem, TaskExtractionResponse
from services.task_service import task_service

logger = logging.getLogger(__name__)


class TaskExtractionTester:
    """Test framework for task extraction with ChatGPT as judge"""
    
    def __init__(self):
        self.openai_client = None
        self._setup_openai()
    
    def _setup_openai(self):
        """Setup OpenAI client for judging"""
        try:
            import os
            from utils.openai_logger import OpenAILogger
            
            # Get API key from environment
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            self.openai_client = OpenAILogger(
                api_key=api_key,
                log_dir="logs/openai_requests/test_task_extraction",
                max_retries=0,  # Disable auto-retries
                timeout=60      # 60 second timeout
            )            
            logger.info("OpenAI client initialized successfully with automatic logging")
            
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        except Exception as e:
            raise Exception(f"Failed to setup OpenAI: {e}")
    
    def load_test_emails(self) -> List[Dict[str, Any]]:
        """Load test emails from JSON file"""
        try:
            with open('tests/test_emails.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data['test_emails']
        except Exception as e:
            raise Exception(f"Failed to load test emails: {e}")
    
    def validate_json_format(self, response_data: Any) -> tuple[bool, str]:
        """
        Validate if the response is in correct TaskExtractionResponse format
        Returns: (is_valid, error_message)
        """
        try:
            # Check if it's a list
            if not isinstance(response_data, list):
                return False, f"Response must be a list, got {type(response_data)}"
            
            # Validate each item as TaskItem
            validated_items = []
            if response_data:
                for i, item in enumerate(response_data):
                    try:
                        task_item = TaskItem(**item)
                        validated_items.append(task_item)
                    except ValidationError as e:
                        return False, f"Item {i} validation failed: {e}"
            
            logger.info(f"JSON format validation passed: {len(validated_items)} tasks")
            return True, "Valid format"
            
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def get_judge_prompt(self, email_content: str, extracted_tasks: List[Dict]) -> str:
        """Create prompt for ChatGPT judge"""
        return f"""
אתה שופט מומחה להערכת איכות חילוץ משימות מאימיילים בעברית.
על המשימות להכיל אך ורק את הפרטים המצויינים באימייל ולא להמציא מידע שלא מופיע בו.

עלייך להעריך את טיב חילוץ המשימות בהתבסס עם ההנחיות הבאות:
{task_service.get_task_system_prompt()}


קריטריונים להערכה:
1. **שלמות** (0-40 נקודות): האם המודל חילץ את כל המשימות שהוזכרו באימייל?
2. **דיוק** (0-40 נקודות): האם פרטי המשימות שחולצו נכונים?
3. **איכות שדות** (0-20 נקודות): האם כל השדות (שולח, תאריכים, מוקצה, וכו') מולאו בצורה מדויקת?

תוכן האימייל:
{email_content}

המשימות שחולצו:
{json.dumps(extracted_tasks, ensure_ascii=False, indent=2, default=str)}

עצב את התשובה שלך כך:
ציון: [מספר 0-100]
נקודות חולשה: [מה הוחמץ/לא נכון]
משימות מצופות: [כל המשימות שניתן לחלץ מהאימייל בהתאם להנחיות שהתקבלו - חייבות להכיל את שם האדם הספציפי לו מוקצית המשימה (לא בעל תפקיד/ צוות וכו׳), כותרת ותיאור. שדות אלו לא יכולים להיות ריקים]
"""

    async def judge_extraction(self, email_content: str, extracted_tasks: List[Dict]) -> Dict[str, Any]:
        """Use ChatGPT to judge the extraction quality"""
        try:
            prompt = self.get_judge_prompt(email_content, extracted_tasks)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "אתה מעריך מומחה של מערכות חילוץ משימות. היה יסודי והוגן בהערכתך."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # Low temperature for consistent evaluation
            )

            judgment = response.choices[0].message.content

            print("***Judgement:**")
            print(judgment)
            
            # Parse the judgment to extract score
            score = None
            for line in judgment.split('\n'):
                if line.startswith('ציון:') or line.lower().startswith('score:'):
                    try:
                        score = int(line.split(':')[1].strip())
                    except:
                        pass
            
            return {
                "score": score,
                "judgment": judgment,
                "model_used": "gpt-3.5-turbo"
            }
            
        except Exception as e:
            logger.error(f"Failed to judge extraction: {e}")
            return {
                "score": None,
                "judgment": f"Error during judgment: {e}",
                "model_used": "gpt-3.5-turbo"
            }

    async def test_single_email(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test task extraction on a single email"""
        email_id = test_case['id']
        email_content = test_case['email_content']
        description = test_case['description']
        
        logger.info(f"\n\nTesting email: {email_id}")
        
        try:
            # Extract tasks using our model
            extracted_response = await task_service.extract_tasks(email_content)
            
            # Convert to dict for validation and judging
            extracted_dict = [task.model_dump() for task in extracted_response]

            print("---Extracted Tasks:---")
            print(extracted_dict)
            
            # First validation: JSON format
            is_valid, validation_msg = self.validate_json_format(extracted_dict)
            
            result = {
                "email_id": email_id,
                "description": description,
                "format_valid": is_valid,
                "validation_message": validation_msg,
                "email_content": email_content,
                "extracted_tasks": extracted_dict,
                "num_tasks_extracted": len(extracted_dict)
            }
            
            # If format is valid, get ChatGPT judgment
            if is_valid:
                logger.info(f"Format valid, getting ChatGPT judgment for {email_id}")
                judgment = await self.judge_extraction(email_content, extracted_dict)
                # Adds the key-value pairs from judgment into the result dictionary
                result.update(judgment) 
            else:
                logger.warning(f"Format invalid for {email_id}: {validation_msg}")
                result.update({
                    "score": 0,
                    "judgment": f"Format validation failed: {validation_msg}",
                    "model_used": None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing {email_id}: {e}")
            return {
                "email_id": email_id,
                "description": description,
                "format_valid": False,
                "validation_message": f"Error during extraction: {e}",
                "extracted_tasks": [],
                "num_tasks_extracted": 0,
                "score": 0,
                "judgment": f"Extraction failed: {e}",
                "model_used": None
            }

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run tests on all email cases"""
        logger.info("Starting comprehensive task extraction tests")
        
        # Load test emails
        test_emails = self.load_test_emails()
        logger.info(f"Loaded {len(test_emails)} test emails")
        
        # Run tests on all emails
        results = []
        for test_case in test_emails:
            result = await self.test_single_email(test_case)
            results.append(result)
            
            # Log progress
            score = result.get('score', 0)
            logger.info(f"Completed {test_case['id']}: Score={score}, Valid={result['format_valid']}")
        
        # Calculate summary statistics
        valid_count = sum(1 for r in results if r['format_valid'])
        scores = [r['score'] for r in results if r['score'] is not None]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        summary = {
            "total_tests": len(results),
            "format_valid_count": valid_count,
            "format_valid_rate": valid_count / len(results) * 100,
            "average_score": avg_score,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "test_results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Tests completed. Valid format: {valid_count}/{len(results)}, Avg score: {avg_score:.1f}")
        return summary

    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save test results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tests/task_extraction_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"Results saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")


# Test runner functions
async def run_task_extraction_tests():
    """Main test runner function"""
    tester = TaskExtractionTester()
    results = await tester.run_all_tests()
    tester.save_results(results)
    return results


# Pytest integration
@pytest.mark.asyncio
async def test_task_extraction_comprehensive():
    """Pytest function for running comprehensive tests"""
    results = await run_task_extraction_tests()
    
    # Assertions for pytest
    assert results['total_tests'] > 0, "No tests were run"
    assert results['format_valid_rate'] >= 70, f"Too many format failures: {results['format_valid_rate']:.1f}%"
    assert results['average_score'] >= 60, f"Average score too low: {results['average_score']:.1f}"


if __name__ == "__main__":
    # Direct execution
    logging.basicConfig(level=logging.INFO)
    results = asyncio.run(run_task_extraction_tests())
    
    print("\n" + "="*50)
    print("TASK EXTRACTION TEST RESULTS")
    print("="*50)
    print(f"Total tests: {results['total_tests']}")
    print(f"Format valid: {results['format_valid_count']}/{results['total_tests']} ({results['format_valid_rate']:.1f}%)")
    print(f"Average score: {results['average_score']:.1f}")
    print(f"Score range: {results['min_score']}-{results['max_score']}")
    print("="*50)