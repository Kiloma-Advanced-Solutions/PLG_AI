#!/usr/bin/env python3
"""
Simple test runner for task extraction without ChatGPT judge
Tests only JSON format validation
"""
import asyncio
import sys
import os
import logging
import json
from datetime import datetime

# Add parent directory to path so we can import from core/services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_task_extraction import TaskExtractionTester

class SimpleTaskTester(TaskExtractionTester):
    """Simplified tester that skips OpenAI judge"""
    
    def __init__(self):
        # Don't setup OpenAI
        self.openai_client = None
        
    def _setup_openai(self):
        # Skip OpenAI setup
        pass
    
    async def judge_extraction(self, email_content: str, extracted_tasks: list) -> dict:
        """Simple mock judge that just validates format"""
        return {
            "score": 100 if len(extracted_tasks) > 0 else 0,
            "judgment": f"פורמט תקין. חולצו {len(extracted_tasks)} משימות.",
            "model_used": "format_validator_only"
        }

def setup_logging():
    """Setup logging for the test run"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('tests/test_run_simple.log')
        ]
    )

async def main():
    """Main test runner without ChatGPT"""
    print("🚀 Starting Simple Task Extraction Tests (No ChatGPT Judge)")
    print("=" * 60)
    
    # Setup logging
    setup_logging()
    
    try:
        # Initialize simple tester
        tester = SimpleTaskTester()
        
        # Run all tests
        results = await tester.run_all_tests()
        
        # Save results
        tester.save_results(results, "tests/task_extraction_results_simple.json")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 SIMPLE TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total tests: {results['total_tests']}")
        print(f"Format valid: {results['format_valid_count']}/{results['total_tests']} ({results['format_valid_rate']:.1f}%)")
        
        # Show individual results
        print("\n📋 Individual Test Results:")
        print("-" * 60)
        for result in results['test_results']:
            status = "✅" if result['format_valid'] else "❌"
            print(f"{status} {result['email_id']:<25} | Valid: {result['format_valid']} | Tasks: {result['num_tasks_extracted']}")
        
        print("\n" + "=" * 60)
        
        # Return success/failure code
        if results['format_valid_rate'] >= 70:
            print("🎉 Tests PASSED! (Format validation only)")
            return 0
        else:
            print("❌ Tests FAILED - Too many format errors")
            return 1
            
    except Exception as e:
        print(f"❌ Test run failed: {e}")
        logging.error(f"Test run failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)