#!/bin/bash

# Task Extraction Test Runner
echo "🧪 Task Extraction Test Runner"
echo "================================"

# Check if we're in the right directory
if [ ! -f "tests/test_task_extraction.py" ]; then
    echo "❌ Please run this script from the llm-api directory"
    exit 1
fi

# Check if virtual environment exists and activate it
if [ -d "../venv" ]; then
    echo "📦 Activating virtual environment..."
    source ../venv/bin/activate
elif [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  No virtual environment found, using system Python"
fi

# Check Python version
echo "🐍 Python version: $(python --version)"

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY environment variable not set"
    echo "Set it with: export OPENAI_API_KEY='your-api-key'"
    exit 1
fi

# Check OpenAI access
echo "🔑 Checking OpenAI API access..."
python tests/check_openai_access.py
if [ $? -ne 0 ]; then
    echo "❌ OpenAI access check failed"
    exit 1
fi

echo ""
echo "🚀 Running task extraction tests..."
echo "================================"

# Run the tests
python tests/run_tests.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 All tests completed successfully!"
else
    echo ""
    echo "❌ Some tests failed. Check the output above."
    exit 1
fi