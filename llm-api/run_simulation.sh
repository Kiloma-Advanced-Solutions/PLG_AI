#!/bin/bash

# Multi-User LLM Performance Simulation Runner
# This script runs the simulation.py with proper environment setup

echo "Starting Multi-User LLM Performance Simulation..."
echo "================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run setup_venv_5090.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if required packages are installed
echo "Checking dependencies..."
python -c "import aiohttp, matplotlib, pandas, numpy, transformers" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing missing dependencies..."
    pip install aiohttp matplotlib pandas numpy transformers
fi

# Check if API is running
echo "Checking API health..."
curl -s http://localhost:8090/api/health > /dev/null
if [ $? -ne 0 ]; then
    echo "Warning: API at http://localhost:8090 is not responding."
    echo "Please make sure your LLM API is running before starting the simulation."
    echo ""
    echo "To start the API, run: ./start_api_5090.sh"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if vLLM metrics endpoint is accessible
echo "Checking vLLM metrics endpoint..."
curl -s http://localhost:8060/metrics > /dev/null
if [ $? -ne 0 ]; then
    echo "Warning: vLLM metrics endpoint at http://localhost:8060/metrics is not responding."
    echo "Some metrics may not be available during the simulation."
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "Configuration:"
echo "- Number of users: 5 (configurable in simulation.py)"
echo "- User start delay: 5 seconds"
echo "- Request delay: 10 seconds per user"
echo "- API endpoint: http://localhost:8090"
echo "- vLLM metrics: http://localhost:8060/metrics"
echo ""

# Run the simulation
echo "Starting simulation..."
python simulation.py

echo ""
echo "Simulation completed!"
echo "Check the generated files:"
echo "- simulation_results_*.png (performance graphs)"
echo "- simulation_requests_*.csv (detailed request metrics)"
echo "- simulation_system_*.csv (system metrics over time)"
