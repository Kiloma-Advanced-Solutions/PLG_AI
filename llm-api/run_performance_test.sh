#!/bin/bash

# Performance Test Runner Script
# This script sets up and runs the LLM performance test

echo "=== LLM Performance Test Runner ==="
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing performance test dependencies..."
pip install -r performance_test_requirements.txt

# Check if API is running
echo "Checking if API is running..."
API_URL="http://localhost:8090"
if curl -s "$API_URL/ping" > /dev/null; then
    echo "✓ API is running at $API_URL"
else
    echo "⚠️  Warning: API doesn't seem to be running at $API_URL"
    echo "   Make sure to start your LLM API before running the test."
    echo "   You can start it with: python -m uvicorn main:app --host 0.0.0.0 --port 8090"
    echo
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting..."
        exit 1
    fi
fi

# Run the performance test
echo
echo "Starting performance test..."
echo "This will simulate 10 concurrent users with increasing context lengths."
echo "The test will automatically stop when appropriate conditions are met."
echo
echo "Press Ctrl+C to interrupt the test if needed."
echo

python3 performance_test.py

echo
echo "Performance test completed!"
echo "Check the generated files for detailed results and graphs."
