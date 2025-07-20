#!/bin/bash

# Trader Ops Development Startup Script
# This script starts the development environment for the Trader Dashboard

echo "🚀 Starting Trader Ops Development Environment..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run the setup first."
    echo "   Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if Node modules are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

echo "🐍 Starting Python FastAPI Data Hub Server..."
# Start Python backend in background
source venv/bin/activate && python -m src.backend.server &
PYTHON_PID=$!

# Give the Python server time to start
sleep 3

echo "📊 Python Data Hub Server started (PID: $PYTHON_PID)"
echo "   API available at: http://localhost:9000"
echo "   WebSocket stream: ws://localhost:9000/stream"
echo "   API docs: http://localhost:9000/docs"
echo ""

echo "⚡ Starting Vite Development Server..."
# Start Vite dev server in background
npm run dev:renderer &
VITE_PID=$!

sleep 2
echo "🌐 Vite Dev Server started (PID: $VITE_PID)"
echo "   Frontend available at: http://localhost:3000"
echo ""

echo "📱 Starting Electron Application..."
# Start Electron app
npm run electron:dev &
ELECTRON_PID=$!

echo "🎯 Electron App started (PID: $ELECTRON_PID)"
echo ""

echo "✅ All services started successfully!"
echo ""
echo "To stop all services, press Ctrl+C or run:"
echo "   kill $PYTHON_PID $VITE_PID $ELECTRON_PID"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $PYTHON_PID $VITE_PID $ELECTRON_PID 2>/dev/null
    echo "✅ All services stopped."
    exit 0
}

# Set trap to cleanup on Ctrl+C
trap cleanup SIGINT SIGTERM

# Wait for user to stop
echo "Press Ctrl+C to stop all services..."
wait