#!/usr/bin/env python3
"""
Standalone runner for comprehensive task extraction tests.
This script can be run directly without pytest for manual testing.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from test_task_extraction_comprehensive import TaskExtractionTestSuite

async def main():
    """Run comprehensive tests"""
    print("🚀 Task Extraction Comprehensive Test Suite")
    print("=" * 60)
    print("This will test the task extraction service with 10 edge cases.")
    print("Each test includes JSON validation and ChatGPT LLM-as-a-judge evaluation.")
    print()
    
    # Check ChatGPT setup
    import os
    if os.getenv("OPENAI_API_KEY"):
        print("✅ ChatGPT judge available (using GPT-4o-mini)")
    else:
        print("⚠️  No OPENAI_API_KEY found - will use local LLM as judge fallback")
    print()
    
    # Check if user wants to continue
    try:
        input("Press Enter to start testing, or Ctrl+C to cancel...")
    except KeyboardInterrupt:
        print("\n❌ Tests cancelled by user.")
        return
    
    # Run the tests
    test_suite = TaskExtractionTestSuite()
    
    try:
        results = await test_suite.run_comprehensive_tests()
        
        # Show final summary
        print("\n" + "🎉 ALL TESTS COMPLETED! 🎉".center(80, "="))
        print(f"📊 Results Summary:")
        print(f"   • Total Tests: {results['test_summary']['total_tests']}")
        print(f"   • JSON Validation Pass Rate: {results['test_summary']['passed_json_validation']}/{results['test_summary']['total_tests']}")
        print(f"   • Average LLM Score: {results['test_summary']['average_llm_score']:.1f}/10")
        
        # Save results
        from datetime import datetime
        import json
        
        results_file = Path(__file__).parent / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"   • Results saved to: {results_file.name}")
        
        # Show recommendations
        avg_score = results['test_summary']['average_llm_score']
        if avg_score >= 8.0:
            print("✅ Excellent performance! The task extraction is working very well.")
        elif avg_score >= 6.0:
            print("⚠️  Good performance with room for improvement.")
        else:
            print("❌ Performance needs significant improvement.")
            
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        print("\nMake sure:")
        print("1. The LLM API service is running")
        print("2. All dependencies are installed")
        print("3. The models and services are accessible")

if __name__ == "__main__":
    asyncio.run(main())