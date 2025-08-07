"""
Unit tests for task extraction functionality using ChatGPT as LLM judge
"""
import json
import asyncio
import logging
import re
from typing import List, Dict, Any
from datetime import date, datetime
import pytest
from pydantic import ValidationError

# Import our models and services
from core.models import TaskItem
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
                log_dir="logs/test_task_extraction/openai_requests",
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
            with open('test_emails.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data['test_emails']
        except Exception as e:
            raise Exception(f"Failed to load test emails: {e}")
    
    def validate_json_format(self, response_data: Any) -> tuple[bool, str]:
        """
        Validate if the response is a list of TaskItems
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


    def make_judgment(self, extracted_tasks: List[Dict], tasks_extreacted_by_judge: List[Dict]) -> str:
        messages = [

            {"role": "system", "content": 
             f"""
אתה שופט מומחה להערכת איכות ביצועי מערכת חדשה שנבחנת לחילוץ משימות. עלייך להעריך עד כמה המשימות שציינה המערכת זהות למשימות הקיימות.

בהודעה הבאה תקבל את המשימות הקיימות (המשימות שהמערכת הייתה צריכה לחלץ) ואת המשימות שהמערכת חילצה.

קריטריונים להערכה:
**1. שלמות המשימות** (0-40 נקודות): האם המערכת זיהתה נכונה את המשימות הקיימות? 
**2. איכות השדות** (0-60 נקודות. 10 נקודות בעבור כל שדה): האם כל השדות (שולח המשימה, תאריכים, האדם שצריך לבצע את המשימה, וכו') מולאו בצורה מדויקת? (במידה ואין משימות קיימות, ציון מלא יינתן אם המערכת לא מילאה את השדות כלל)
חשוב שתהיה ביקורתי והוגן בהערכתך. הורד ניקוד משמעותי אם המערכת לא הצליחה לזהות את כל המשימות, אם היא חילצה משימות שלא קיימות, או אם היא מילאה את השדות בצורה לא מדויקת.

עצב את התשובה שלך כך:
ציון: [0-100. מידת ההצלחה של המערכת בחילוץ המשימות. **חשוב! אם רשימת המשימות הקיימות ריקה והמערכת אכן לא חילצה אף משימה (החזירה רשימה ריקה []), תן ציון 100]**
הערות: [מה הוחמץ/לא נכון]

             """
            },
            {"role": "user", "content": 
             f"""
המשימות הקיימות:
{json.dumps(tasks_extreacted_by_judge, ensure_ascii=False, indent=2, default=str)}

המשימות שחולצו על ידי המערכת:
{json.dumps(extracted_tasks, ensure_ascii=False, indent=2, default=str)}

             """   
            }   
        ]


        return messages


    async def judge_extraction(self, email_content: str, extracted_tasks: List[Dict]) -> Dict[str, Any]:
        """Use ChatGPT to judge the extraction quality"""
        try:
            # Ask the judge model to extract the tasks
            tasks_extreacted_by_judge = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": task_service.get_task_system_prompt()},
                    {"role": "user", "content": email_content}
                ],
                temperature=0.1  # Low temperature for consistent evaluation
            )

            tasks_extreacted_by_judge = tasks_extreacted_by_judge.choices[0].message.content

            print("***Tasks Extreacted By Judge:**")
            print(tasks_extreacted_by_judge)


            # Ask the judge model to make a judgment
            judgment = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.make_judgment(extracted_tasks, tasks_extreacted_by_judge),
                temperature=0.1  # Low temperature for consistent evaluation
            )

            judgment = judgment.choices[0].message.content

            print("***Judgment:**")
            print(judgment)
            
            # Parse the judgment to extract score
            score = None
            for line in judgment.split('\n'):
                if line.startswith('ציון:') or line.lower().startswith('score:'):
                    try:
                        # Extract the part after the colon
                        score_part = line.split(':')[1].strip()
                        # Extract only the numeric part (handle cases like "100. המערכת הצליחה...")
                        score_match = re.search(r'\d+', score_part)
                        if score_match:
                            score = int(score_match.group())
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
            filename = f"logs/test_task_extraction/task_extraction_results_{timestamp}.json"
        
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