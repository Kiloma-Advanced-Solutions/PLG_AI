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

async def test_summarization():
    """Test the summarization service with various email lengths"""
    
    # Load test emails
    with open('test_summarization_emails.json', 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    print("=== Testing Email Summarization Service ===\n")
    
    # Test different summary lengths
    summary_lengths = [50, 100, 200]
    
    for i, email in enumerate(test_data['emails'][:5], 1):  # Test first 5 emails
        print(f"--- Test Email {i}: {email['title']} ---")
        print(f"Sender: {email['sender_email']}")
        print(f"Date: {email['sent_datetime']}")
        print(f"Original Length: {len(email['content'])} characters")
        print(f"Content Preview: {email['content'][:100]}...")
        print()
        
        # Test different summary lengths
        for length in summary_lengths:
            try:
                print(f"Testing {length}-character summary:")
                summary = await summarization_service.summarize_email(
                    email['content'], 
                    length=length
                )
                
                if hasattr(summary, 'summary'):
                    summary_text = summary.summary
                else:
                    summary_text = str(summary)
                
                print(f"Summary ({len(summary_text)} chars): {summary_text}")
                print(f"Target vs Actual: {length} vs {len(summary_text)} characters")
                print("-" * 50)
                
            except Exception as e:
                print(f"ERROR during {length}-char summarization: {str(e)}")
                print("-" * 50)
        
        print("=" * 80)
        print()

async def test_specific_email(email_index: int, summary_length: int = 100):
    """Test summarization on a specific email by index"""
    
    with open('test_summarization_emails.json', 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    if email_index >= len(test_data['emails']):
        print(f"Email index {email_index} not found. Available indices: 0-{len(test_data['emails'])-1}")
        return
    
    email = test_data['emails'][email_index]
    
    print(f"=== Testing Email {email_index}: {email['title']} ===")
    print(f"Original content ({len(email['content'])} chars):")
    print(email['content'])
    print(f"\nGenerating {summary_length}-character summary...")
    
    try:
        summary = await summarization_service.summarize_email(
            email['content'], 
            length=summary_length
        )
        
        if hasattr(summary, 'summary'):
            summary_text = summary.summary
        else:
            summary_text = str(summary)
        
        print(f"\nSummary ({len(summary_text)} chars):")
        print(summary_text)
        
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific email by index
        email_idx = int(sys.argv[1])
        length = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        asyncio.run(test_specific_email(email_idx, length))
    else:
        # Run full test suite
        asyncio.run(test_summarization())
