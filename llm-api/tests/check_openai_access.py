"""
Simple script to check OpenAI API access for testing
"""
import os
import sys

def check_openai_access():
    """Check if OpenAI API is accessible"""
    
    # Check if API key is set
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
        return False
    
    print(f"✅ OPENAI_API_KEY found (length: {len(api_key)})")
    
    # Try to import openai
    try:
        import openai
        print("✅ OpenAI package installed")
    except ImportError:
        print("❌ OpenAI package not installed")
        print("Install with: pip install openai")
        return False
    
    # Test API connection
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10
        )
        
        print("✅ OpenAI API connection successful")
        print(f"✅ Response received: {response.choices[0].message.content[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Checking OpenAI API access...")
    print("-" * 40)
    
    success = check_openai_access()
    
    print("-" * 40)
    if success:
        print("🎉 All checks passed! Ready to run tests.")
        sys.exit(0)
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        sys.exit(1)