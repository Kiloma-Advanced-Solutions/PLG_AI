#!/usr/bin/env python3
"""
Simple test to verify ChatGPT judge functionality.
Run this before running the full test suite to ensure ChatGPT integration works.
"""

import asyncio
import os
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

async def test_chatgpt_judge():
    """Simple test for ChatGPT judge functionality"""
    
    print("🧪 Testing ChatGPT Judge Integration")
    print("=" * 50)
    
    # Check OpenAI library
    if not OPENAI_AVAILABLE:
        print("❌ OpenAI library not available")
        print("Install with: pip install openai>=1.3.0")
        return False
    
    print("✅ OpenAI library available")
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        print("Set it with: export OPENAI_API_KEY='your_api_key'")
        return False
    
    print("✅ OpenAI API key found")
    
    # Test connection
    try:
        client = AsyncOpenAI(api_key=api_key)
        
        print("🤖 Testing ChatGPT connection...")
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a task extraction judge. Always respond in JSON format."
                },
                {
                    "role": "user", 
                    "content": """Test evaluation. Rate this simple task extraction:

Email: "שלום יוסי, בבקשה הכן דוח עד מחר. תודה, דנה"

Extracted task: {
  "assigned_to": "יוסי",
  "title": "הכנת דוח", 
  "description": "הכן דוח",
  "due_date": "2024-01-02",
  "sender": "דנה"
}

Give a score 1-10 and brief feedback in JSON:
{
  "overall_score": <score>,
  "feedback": "brief evaluation in Hebrew"
}"""
                }
            ],
            temperature=0.1,
            max_tokens=300,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        print(f"📝 Raw response: {content}")
        
        # Try to parse JSON
        try:
            result = json.loads(content)
            score = result.get("overall_score", 0)
            feedback = result.get("feedback", "No feedback")
            
            print("✅ ChatGPT judge test successful!")
            print(f"   Score: {score}/10")
            print(f"   Feedback: {feedback}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            return False
            
    except Exception as e:
        print(f"❌ ChatGPT test failed: {str(e)}")
        return False

async def main():
    """Main test function"""
    success = await test_chatgpt_judge()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ChatGPT judge is ready!")
        print("You can now run the full test suite with ChatGPT evaluation.")
        print("\nNext steps:")
        print("  python test_task_extraction_comprehensive.py")
        print("  or")
        print("  python run_comprehensive_tests.py")
    else:
        print("❌ ChatGPT judge setup incomplete")
        print("Please fix the issues above before running the full test suite.")

if __name__ == "__main__":
    asyncio.run(main())