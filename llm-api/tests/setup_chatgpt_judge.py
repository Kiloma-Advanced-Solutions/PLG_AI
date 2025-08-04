#!/usr/bin/env python3
"""
Setup script for ChatGPT judge integration.
This script helps configure the OpenAI API key and test the connection.
"""

import os
import asyncio
from pathlib import Path

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

async def test_chatgpt_connection(api_key: str) -> bool:
    """Test ChatGPT connection with the provided API key"""
    try:
        client = AsyncOpenAI(api_key=api_key)
        
        # Simple test request
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Connection successful!' in Hebrew."}
            ],
            max_tokens=50
        )
        
        content = response.choices[0].message.content
        print(f"✅ ChatGPT connection successful!")
        print(f"   Response: {content}")
        return True
        
    except Exception as e:
        print(f"❌ ChatGPT connection failed: {str(e)}")
        return False

def setup_environment():
    """Set up environment configuration for ChatGPT judge"""
    
    print("🚀 ChatGPT Judge Setup for Task Extraction Tests")
    print("=" * 60)
    
    # Check if OpenAI library is available
    if not OPENAI_AVAILABLE:
        print("❌ OpenAI library not found!")
        print("Please install it with: pip install openai>=1.3.0")
        return False
    
    print("✅ OpenAI library is available")
    
    # Check if API key exists in environment
    existing_key = os.getenv("OPENAI_API_KEY")
    if existing_key:
        print(f"✅ Found existing OPENAI_API_KEY in environment")
        return True
    
    # Guide user to set up API key
    print("\n📝 Setting up OpenAI API Key:")
    print("1. Go to: https://platform.openai.com/api-keys")
    print("2. Create a new API key")
    print("3. Copy the key and run:")
    print('   export OPENAI_API_KEY="your_api_key_here"')
    print("\nOr add it to your .env file:")
    
    env_file = Path(__file__).parent / ".env"
    env_example = Path(__file__).parent / ".env.example"
    
    if env_example.exists() and not env_file.exists():
        print(f"4. Copy {env_example} to {env_file}")
        print(f"5. Edit {env_file} and add your API key")
    
    # Ask user if they want to test a key
    print("\n🧪 Want to test your API key now? (y/n)")
    try:
        test_now = input().lower().strip()
        if test_now in ['y', 'yes']:
            api_key = input("Enter your OpenAI API key: ").strip()
            if api_key:
                print("Testing connection...")
                success = asyncio.run(test_chatgpt_connection(api_key))
                if success:
                    print(f"\n💡 Add this to your environment:")
                    print(f'export OPENAI_API_KEY="{api_key}"')
                return success
    except KeyboardInterrupt:
        print("\n👋 Setup cancelled by user")
    
    return False

async def main():
    """Main setup function"""
    success = setup_environment()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Make sure your LLM API service is running")
        print("2. Run the comprehensive tests:")
        print("   python test_task_extraction_comprehensive.py")
        print("   or")
        print("   python run_comprehensive_tests.py")
    else:
        print("\n⚠️  Setup incomplete. Please follow the instructions above.")

if __name__ == "__main__":
    asyncio.run(main())