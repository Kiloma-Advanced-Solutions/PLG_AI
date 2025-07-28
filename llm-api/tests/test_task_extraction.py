import asyncio
import json
from pathlib import Path
import aiohttp
import pytest
from datetime import datetime

# Load test emails
def load_test_emails():
    test_data_path = Path(__file__).parent / "test_emails.json"
    with open(test_data_path, "r", encoding="utf-8") as f:
        return json.load(f)

async def extract_tasks_from_email(session, email_content):
    """Send email content to task extraction API and return response"""
    async with session.post(
        "http://localhost:8090/api/tasks/extract",
        json={"email_content": email_content}
    ) as response:
        return await response.json()

async def run_extraction_tests():
    """Run task extraction tests on all test emails"""
    test_emails = load_test_emails()
    
    print(f"\nStarting task extraction tests at {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    print("=" * 80)
    
    async with aiohttp.ClientSession() as session:
        for idx, email in enumerate(test_emails, 1):
            print(f"\nTest Email #{idx}")
            print("-" * 40)
            print("\nEmail Content:")
            print(email)
            print("\nExtracted Tasks:")
            
            try:
                result = await extract_tasks_from_email(session, email)
                print(json.dumps(result, ensure_ascii=False, indent=2))
            except Exception as e:
                print(f"Error extracting tasks: {e}")
            
            print("\nPress Enter to continue to next email...")
            input()

if __name__ == "__main__":
    print("Task Extraction Test Suite")
    print("This will test the task extraction API with 10 complex emails.")
    print("You will be able to review each result and continue to the next test.")
    print("\nMake sure the API is running before starting.")
    input("Press Enter to begin...")
    
    asyncio.run(run_extraction_tests()) 