#!/bin/bash

# Simple Task Extraction Test Runner (No ChatGPT Judge)
echo "🧪 Simple Task Extraction Test Runner (No ChatGPT)"
echo "=================================================="

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

echo ""
echo "🚀 Running simple task extraction tests (format validation only)..."
echo "=================================================="

# Run the simple tests
python tests/test_without_judge.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Simple tests completed successfully!"
    echo "Note: This only tests JSON format validation, not task quality."
    echo "For full evaluation, OpenAI API access is needed."
else
    echo ""
    echo "❌ Some tests failed. Check the output above."
    exit 1
fi