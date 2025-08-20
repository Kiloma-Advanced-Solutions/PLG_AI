#!/usr/bin/env python3
"""
Test script for the summarization service using the test emails
"""

import json
import asyncio
import sys
import os

# Add the parent directory to the path so we can import from the llm-api modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.summarization_service import summarization_service



async def test_specific_email(email_index: int, summary_length: int = 100):
    """Test summarization on a specific email by index"""
    
    with open('test_summarization_emails.json', 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    if email_index >= len(test_data['emails']):
        print(f"Email index {email_index} not found. Available indices: 0-{len(test_data['emails'])-1}")
        return
    
    email = test_data['emails'][email_index]

    
    print(f"=== Testing Email {email_index}: ===")
    print(f"Original content ({len(email)} chars):")
    print(email)
    print(f"\nGenerating {summary_length}-character summary...")
    
    try:
        summary = await summarization_service.summarize_email(
            email, 
            length=summary_length
        )

        print(f"\nComplete Summary Object:")
        print(f"Sender: {summary.sender}")
        print(f"Sending Date: {summary.sending_date}")
        print(f"Title: {summary.title}")
        print(f"Summary ({len(summary.summary)} chars): {summary.summary}")
        print(f"\nFull object: {summary}")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")

async def run_tests():
    """Run the tests based on command line arguments"""
    if len(sys.argv) > 1:
        # Test specific email by index
        email_idx = int(sys.argv[1]) 
        length = int(sys.argv[2])
        
        await test_specific_email(email_idx, length)

    else:
        # Run the first email in the test suite
        await test_specific_email(0)
        


if __name__ == "__main__":
    asyncio.run(run_tests())
