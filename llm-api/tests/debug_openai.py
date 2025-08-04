#!/usr/bin/env python3
"""
Debug OpenAI API connection issues
"""
import os
import openai

def debug_openai():
    api_key = os.getenv('OPENAI_API_KEY')
    
    print(f"API Key length: {len(api_key) if api_key else 'None'}")
    print(f"API Key starts with: {api_key[:20]}..." if api_key else "No API key")
    
    # Try different models
    client = openai.OpenAI(api_key=api_key)
    
    models_to_try = ["gpt-3.5-turbo", "gpt-4", "gpt-4o-mini"]
    
    for model in models_to_try:
        try:
            print(f"\nTrying {model}...")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Say 'hello' in one word"}],
                max_tokens=5
            )
            print(f"✅ {model} works!")
            print(f"Response: {response.choices[0].message.content}")
            break
        except Exception as e:
            print(f"❌ {model} failed: {e}")

if __name__ == "__main__":
    debug_openai()