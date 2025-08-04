#!/usr/bin/env python3
"""
Verify that your API key setup is secure and working.
This script checks all security best practices.
"""

import os
import sys
from pathlib import Path

def check_security():
    """Check if API key setup follows security best practices"""
    
    print("🔐 API Key Security Verification")
    print("=" * 50)
    
    checks_passed = 0
    total_checks = 6
    
    # Check 1: API key is loaded
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("✅ 1. API key is loaded from environment")
        checks_passed += 1
        
        # Validate key format
        if api_key.startswith("sk-") and len(api_key) > 20:
            print("✅    API key format looks correct")
        else:
            print("⚠️     API key format seems incorrect (should start with 'sk-')")
            
    else:
        print("❌ 1. API key NOT found in environment")
        print("     Set it with: export OPENAI_API_KEY='your_key_here'")
    
    # Check 2: No hardcoded keys in source files
    test_files = list(Path(__file__).parent.glob("*.py"))
    hardcoded_found = False
    
    for file_path in test_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'sk-' in content and 'OPENAI_API_KEY' not in content:
                    print(f"⚠️  Potential hardcoded key in {file_path.name}")
                    hardcoded_found = True
        except:
            pass
    
    if not hardcoded_found:
        print("✅ 2. No hardcoded API keys found in source files")
        checks_passed += 1
    else:
        print("❌ 2. Found potential hardcoded keys")
    
    # Check 3: .env file is gitignored
    gitignore_path = Path(__file__).parent.parent.parent / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()
            if '.env' in gitignore_content:
                print("✅ 3. .env files are properly gitignored")
                checks_passed += 1
            else:
                print("❌ 3. .env files might not be gitignored")
    else:
        print("⚠️  3. No .gitignore found")
    
    # Check 4: .env.example exists but .env is not committed
    env_example = Path(__file__).parent / ".env.example"
    env_file = Path(__file__).parent / ".env"
    
    if env_example.exists():
        print("✅ 4. .env.example template exists")
        checks_passed += 1
    else:
        print("⚠️  4. .env.example template missing")
    
    # Check 5: OpenAI library available
    try:
        import openai
        print("✅ 5. OpenAI library is installed")
        checks_passed += 1
    except ImportError:
        print("❌ 5. OpenAI library not installed")
        print("     Install with: pip install openai>=1.3.0")
    
    # Check 6: python-dotenv available (optional)
    try:
        import dotenv
        print("✅ 6. python-dotenv available for automatic .env loading")
        checks_passed += 1
    except ImportError:
        print("⚠️  6. python-dotenv not available (optional)")
        print("     Install with: pip install python-dotenv")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Security Check Results: {checks_passed}/{total_checks} passed")
    
    if checks_passed >= 5:
        print("🎉 Great! Your setup is secure and ready.")
        return True
    elif checks_passed >= 3:
        print("⚠️  Good, but could be improved. Fix the issues above.")
        return False
    else:
        print("❌ Security issues found. Please fix before proceeding.")
        return False

def show_secure_setup_options():
    """Show different secure setup options"""
    
    print("\n🔧 Secure Setup Options:")
    print("-" * 30)
    
    print("\n🌍 Option 1: Global Environment Variable")
    print("   # Add to ~/.bashrc or ~/.zshrc")
    print("   export OPENAI_API_KEY='your_key_here'")
    print("   source ~/.bashrc")
    
    print("\n📁 Option 2: Local .env File")
    print("   cd llm-api/tests")
    print("   echo 'OPENAI_API_KEY=your_key_here' > .env")
    print("   # (this file is automatically gitignored)")
    
    print("\n🐳 Option 3: Docker/Container")
    print("   docker run -e OPENAI_API_KEY='your_key' ...")
    
    print("\n☁️  Option 4: Cloud Environment")
    print("   # Set in your cloud provider's environment variables")
    print("   # (AWS Lambda, Google Cloud Functions, etc.)")

def main():
    """Main verification function"""
    
    # Run security checks
    is_secure = check_security()
    
    if not is_secure:
        show_secure_setup_options()
        print(f"\n📖 For detailed instructions, see:")
        print(f"   {Path(__file__).parent / 'secure_setup.md'}")
    
    # Test connection if secure
    if is_secure and os.getenv("OPENAI_API_KEY"):
        print("\n🧪 Want to test the ChatGPT connection? (y/n)")
        try:
            test_now = input().lower().strip()
            if test_now in ['y', 'yes']:
                print("Running ChatGPT connection test...")
                os.system(f"cd {Path(__file__).parent} && python test_chatgpt_judge_simple.py")
        except KeyboardInterrupt:
            print("\n👋 Test cancelled")

if __name__ == "__main__":
    main()