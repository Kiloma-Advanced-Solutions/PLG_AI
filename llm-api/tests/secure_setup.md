# 🔐 Secure API Key Setup Guide

This guide shows you how to securely configure your OpenAI API key without exposing it in your code.

## ✅ **Secure Methods** (Choose One)

### **Method 1: Environment Variables (Recommended)**

1. **Set environment variable in your shell**:
```bash
# Add to your ~/.bashrc, ~/.zshrc, or ~/.profile
export OPENAI_API_KEY="your_actual_api_key_here"

# Then reload your shell
source ~/.bashrc  # or ~/.zshrc
```

2. **Verify it's set**:
```bash
echo $OPENAI_API_KEY
# Should show your key (first few characters)
```

3. **Run tests**:
```bash
cd llm-api/tests
python test_chatgpt_judge_simple.py
```

### **Method 2: Local .env File (Project-specific)**

1. **Create a local .env file**:
```bash
cd llm-api/tests
cp .env.example .env
```

2. **Edit the .env file** (this file is gitignored):
```bash
# In llm-api/tests/.env
OPENAI_API_KEY=your_actual_api_key_here
```

3. **Load environment variables**:
```bash
# Before running tests
export $(cat .env | xargs)
# OR use python-dotenv (see Method 3)
```

### **Method 3: Python-dotenv Integration (Automatic)**

This method automatically loads .env files in your Python code.

1. **Install python-dotenv**:
```bash
pip install python-dotenv
```

2. **Create .env file**:
```bash
cd llm-api/tests
echo "OPENAI_API_KEY=your_actual_api_key_here" > .env
```

3. **The test suite will automatically load it** ✨

## 🚫 **What NOT to do**

❌ **Never do this**:
```python
# DON'T hardcode API keys
api_key = "sk-1234567890abcdef..."  # NEVER!
```

❌ **Never commit .env files**:
```bash
# Make sure .env is in .gitignore
echo ".env" >> .gitignore
```

## 🔍 **Security Checklist**

- [ ] ✅ API key is in environment variable or .env file
- [ ] ✅ .env file is in .gitignore  
- [ ] ✅ No API keys in source code
- [ ] ✅ .env.example shows format (without real key)
- [ ] ✅ API key starts with "sk-" (OpenAI format)

## 🧪 **Testing Your Setup**

Run this to verify everything works securely:

```bash
cd llm-api/tests

# Test 1: Check if key is loaded
python -c "import os; print('✅ API key loaded' if os.getenv('OPENAI_API_KEY') else '❌ No API key')"

# Test 2: Test ChatGPT connection
python test_chatgpt_judge_simple.py

# Test 3: Run full comprehensive tests
python run_comprehensive_tests.py
```

## 📋 **Quick Setup Commands**

```bash
# 1. Get your API key from https://platform.openai.com/api-keys

# 2. Set it in environment (replace with your actual key)
export OPENAI_API_KEY="sk-your_actual_key_here"

# 3. Test the setup
cd llm-api/tests
python test_chatgpt_judge_simple.py

# 4. Run comprehensive tests
python run_comprehensive_tests.py
```

## 🔄 **Rotating API Keys**

When you need to change your API key:

1. **Update environment variable**:
```bash
export OPENAI_API_KEY="sk-new_key_here"
```

2. **Or update .env file**:
```bash
# Edit llm-api/tests/.env
OPENAI_API_KEY=sk-new_key_here
```

3. **Test new key**:
```bash
python test_chatgpt_judge_simple.py
```

## 💡 **Pro Tips**

- **Use different keys for different environments** (dev/staging/prod)
- **Set usage limits** on your OpenAI dashboard
- **Monitor usage** to track costs
- **Regenerate keys periodically** for security