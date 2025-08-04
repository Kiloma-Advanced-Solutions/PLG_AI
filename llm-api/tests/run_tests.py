#!/usr/bin/env python3
"""
Simple test runner for task extraction tests
"""
import asyncio
import sys
import os
import logging

# Add parent directory to path so we can import from core/services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_task_extraction import TaskExtractionTester

def setup_logging():
    """Setup logging for the test run"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('tests/test_run.log')
        ]
    )

async def main():
    """Main test runner"""
    print("🚀 Starting Task Extraction Tests")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    
    try:
        # Initialize tester
        tester = TaskExtractionTester()
        
        # Run all tests
        results = await tester.run_all_tests()
        
        # Save results
        tester.save_results(results)
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        print(f"Total tests: {results['total_tests']}")
        print(f"Format valid: {results['format_valid_count']}/{results['total_tests']} ({results['format_valid_rate']:.1f}%)")
        
        if results['average_score'] > 0:
            print(f"Average score: {results['average_score']:.1f}/100")
            print(f"Score range: {results['min_score']}-{results['max_score']}")
        
        # Show individual results
        print("\n📋 Individual Test Results:")
        print("-" * 50)
        for result in results['test_results']:
            status = "✅" if result['format_valid'] else "❌"
            score = result.get('score', 0) or 0
            print(f"{status} {result['email_id']:<25} | Score: {score:3d}/100 | Tasks: {result['num_tasks_extracted']}")
        
        print("\n" + "=" * 50)
        
        # Return success/failure code
        if results['format_valid_rate'] >= 70 and results['average_score'] >= 60:
            print("🎉 Tests PASSED!")
            return 0
        else:
            print("❌ Tests FAILED - Quality below threshold")
            return 1
            
    except Exception as e:
        print(f"❌ Test run failed: {e}")
        logging.error(f"Test run failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())