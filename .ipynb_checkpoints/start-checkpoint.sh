#!/bin/bash

# ChatPLG-UI Startup Script
# This script starts both the FastAPI backend and React frontend

set -e

echo "🚀 Starting ChatPLG-UI..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm."
    exit 1
fi

# Function to check if port is available
check_port() {
    local port=$1
    local service=$2
    
    # Check if lsof is available
    if command -v lsof &> /dev/null; then
        if lsof -i :$port >/dev/null 2>&1; then
            echo "❌ Port $port is already in use (needed for $service)"
            echo "   Please stop the service using port $port or use a different port"
            return 1
        fi
    else
        # Fallback: try to connect to the port
        if timeout 1 bash -c "echo >/dev/tcp/localhost/$port" 2>/dev/null; then
            echo "❌ Port $port appears to be in use (needed for $service)"
            echo "   Please stop the service using port $port or use a different port"
            return 1
        fi
    fi
    return 0
}

# Function to install Python dependencies
install_python_deps() {
    echo "📦 Installing Python dependencies..."
    if [ ! -f "requirements.txt" ]; then
        echo "❌ requirements.txt not found!"
        exit 1
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "chatplg-venv" ]; then
        echo "🐍 Creating Python virtual environment..."
        python3 -m venv chatplg-venv
    fi
    
    # Activate virtual environment
    source chatplg-venv/bin/activate
    
    # Install dependencies
    pip install -r requirements.txt
    
    echo "✅ Python dependencies installed successfully"
}

# Function to install Node.js dependencies
install_node_deps() {
    echo "📦 Installing Node.js dependencies..."
    if [ ! -f "package.json" ]; then
        echo "❌ package.json not found!"
        exit 1
    fi
    
    npm install
    echo "✅ Node.js dependencies installed successfully"
}

# Function to start the FastAPI server
start_backend() {
    echo "🔧 Starting FastAPI backend server..."
    source chatplg-venv/bin/activate
    
    # Check if vLLM server is running
    if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
        echo "✅ vLLM server is running on port 8000"
    else
        echo "⚠️  Warning: vLLM server is not running on port 8000"
        echo "   Please start your vLLM server first with:"
        echo "   python3 -m vllm.entrypoints.openai.api_server \\"
        echo "     --model gaunernst/gemma-3-12b-it-qat-autoawq \\"
        echo "     --max-model-len 131072 \\"
        echo "     --port 8000 \\"
        echo "     --tensor-parallel-size 2"
        echo ""
        echo "   Continuing anyway... (API will show errors until vLLM is running)"
    fi
    
    # Start FastAPI server
    python server.py &
    BACKEND_PID=$!
    
    # Wait for backend to start
    echo "⏳ Waiting for FastAPI server to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8090/api/health > /dev/null 2>&1; then
            echo "✅ FastAPI server is running on port 8090"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "❌ FastAPI server failed to start"
            kill $BACKEND_PID 2>/dev/null || true
            exit 1
        fi
        sleep 1
    done
}

# Function to start the React frontend
start_frontend() {
    echo "🔧 Starting React frontend..."
    
    # Build and start React app
    npm run dev &
    FRONTEND_PID=$!
    
    # Wait for frontend to start
    echo "⏳ Waiting for React app to start..."
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo "✅ React app is running on port 3000"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "❌ React app failed to start"
            kill $FRONTEND_PID 2>/dev/null || true
            kill $BACKEND_PID 2>/dev/null || true
            exit 1
        fi
        sleep 1
    done
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "✅ Services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
echo "🔍 Checking dependencies..."

# Install dependencies if needed
if [ ! -d "chatplg-venv" ] || [ ! -f "chatplg-venv/bin/activate" ]; then
    install_python_deps
fi

if [ ! -d "node_modules" ]; then
    install_node_deps
fi

echo ""
echo "🔍 Checking port availability..."

# Check if required ports are available
if ! check_port 8090 "FastAPI backend"; then
    exit 1
fi

if ! check_port 3000 "React frontend"; then
    exit 1
fi

echo "✅ All required ports are available"
echo ""
echo "🚀 Starting all services..."
echo ""

# Start backend
start_backend

# Start frontend
start_frontend

echo ""
echo "🎉 ChatPLG-UI is now running!"
echo "   • Frontend: http://localhost:3000"
echo "   • Backend API: http://localhost:8090"
echo "   • API Health: http://localhost:8090/api/health"
echo ""
echo "📝 Note: Make sure your vLLM server is running on port 8000"
echo "💡 To stop the application, press Ctrl+C"
echo ""

# Wait for processes to exit
wait $BACKEND_PID $FRONTEND_PID 