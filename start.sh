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

# Function to check and kill processes using required ports
check_and_kill_port() {
    local port=$1
    local service=$2
    
    # Check if lsof is available
    if command -v lsof &> /dev/null; then
        if lsof -i :$port >/dev/null 2>&1; then
            echo "🛑 Port $port is in use (needed for $service) - killing process..."
            local pid=$(lsof -t -i:$port)
            if [ ! -z "$pid" ]; then
                kill $pid 2>/dev/null || true
                sleep 2
                # Check if process is still running
                if lsof -i :$port >/dev/null 2>&1; then
                    echo "⚠️  Force killing process on port $port..."
                    kill -9 $pid 2>/dev/null || true
                    sleep 1
                fi
            fi
        fi
    else
        # Fallback: try to connect to the port
        if timeout 1 bash -c "echo >/dev/tcp/localhost/$port" 2>/dev/null; then
            echo "⚠️  Port $port appears to be in use (needed for $service)"
            echo "   Unable to kill process automatically (lsof not available)"
            # Try to find and kill using netstat/ps if available
            if command -v netstat &> /dev/null; then
                local pid=$(netstat -tulpn 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1)
                if [ ! -z "$pid" ]; then
                    echo "🛑 Found process $pid on port $port - killing..."
                    kill $pid 2>/dev/null || true
                    sleep 2
                fi
            fi
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
    ps -eo pid,cmd | grep python | grep -v jupyter-notebook | grep -v grep | awk '{print $1}' | xargs -r kill -9

    echo "✅ Python dependencies installed successfully\n"
}

# Function to install Node.js dependencies
install_node_deps() {
    echo "📦 Installing Node.js dependencies..."
    if [ ! -f "package.json" ]; then
        echo "❌ package.json not found!"
        exit 1
    fi
    
    npm install
    echo "✅ Node.js dependencies installed successfully\n"
}

# Function to start the vLLM server
start_vllm() {
    echo "🤖 Starting vLLM server..."
    
    # Check if vLLM server is already running
    if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
        echo "✅ vLLM server is already running on port 8000"
        return 0
    fi
    
    # Start vLLM server
    echo "🚀 Starting vLLM with model: gaunernst/gemma-3-12b-it-qat-autoawq"
    source chatplg-venv/bin/activate
    python3 -m vllm.entrypoints.openai.api_server \
        --model gaunernst/gemma-3-12b-it-qat-autoawq \
        --max-model-len 131072 \
        --port 8000 \
        --tensor-parallel-size 2 > vllm.log 2>&1 &
    VLLM_PID=$!
    
    # Wait for vLLM to start
    echo "⏳ Waiting for vLLM server to start (this may take 5-10 minutes)..."
    echo "   (vLLM logs are being written to vllm.log)"
    for i in {1..600}; do
        if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
            echo "✅ vLLM server is running on port 8000\n"
            break
        fi
        if [ $i -eq 600 ]; then
            echo "❌ vLLM server failed to start within 10 minutes"
            kill $VLLM_PID 2>/dev/null || true
            exit 1
        fi
        sleep 1
    done
}

# Function to start the FastAPI server
start_backend() {
    echo "🔧 Starting FastAPI backend server..."
    source chatplg-venv/bin/activate
    
    # Start FastAPI server
    python server.py &
    BACKEND_PID=$!
    
    # Wait for backend to start
    echo "⏳ Waiting for FastAPI server to start..."
    for i in {1..60}; do
        if curl -s http://localhost:8090/api/health > /dev/null 2>&1; then
            echo "✅ FastAPI server is running on port 8090\n"
            break
        fi
        if [ $i -eq 60 ]; then
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

    # Go to the frontend directory where package.json is located
    cd "$(dirname "$0")" || {
        echo "❌ Frontend directory not found!"
        exit 1
    }

    # Start frontend with log capture
    npm run dev > frontend.log 2>&1 &
    FRONTEND_PID=$!

    echo "⏳ Waiting for React app to start on port 3000..."
    for i in {1..60}; do
        if ss -tuln 2>/dev/null | grep -q ":3000" || \
           timeout 1 bash -c "echo >/dev/tcp/localhost/3000" 2>/dev/null; then
            echo "✅ React app is running on http://localhost:3000\n"
            return 0
        fi

        # Check if process died
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            echo "❌ React dev server process exited unexpectedly."
            echo "📄 Check 'frontend.log' for details."
            exit 1
        fi

        sleep 1
    done

    echo "❌ React app failed to start on port 3000 after 60 seconds"
    echo "📄 Check 'frontend.log' for debugging"
    kill $FRONTEND_PID 2>/dev/null || true
    exit 1
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $VLLM_PID 2>/dev/null || true
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "✅ Services stopped\n"
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
echo "🔍 Checking and clearing required ports..."

# Check and kill processes using required ports
check_and_kill_port 8000 "vLLM server"
check_and_kill_port 8090 "FastAPI backend"
check_and_kill_port 3000 "React frontend"

echo "✅ Required ports are cleared\n"
echo ""
echo "🚀 Starting all services..."
echo ""


# Start vLLM server first (runs in background)
start_vllm

# Start backend
start_backend

# Start frontend
start_frontend

echo ""
echo "🎉 ChatPLG-UI is now running!"
echo "   • Frontend: http://localhost:3000"
echo "   • Backend API: http://localhost:8090"
echo "   • vLLM Server: http://localhost:8000"
echo "   • API Health: http://localhost:8090/api/health"
echo "   • Model: gaunernst/gemma-3-12b-it-qat-autoawq"
echo "   • vLLM Logs: vllm.log"
echo ""
echo "💡 To stop all services, press Ctrl+C"
echo ""

# Wait for processes to exit
wait $VLLM_PID $BACKEND_PID $FRONTEND_PID 
