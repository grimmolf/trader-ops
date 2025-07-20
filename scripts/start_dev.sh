#!/bin/bash

# Trader Ops Development Startup Script
# This script starts the development environment for the Trader Dashboard

echo "🚀 Starting Trader Ops Development Environment..."
echo ""

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "❌ UV not found. Please install UV first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "   Or: pip install uv"
    exit 1
fi

# Check if Python environment is set up
if [ ! -f "pyproject.toml" ]; then
    echo "❌ pyproject.toml not found. Please run from project root."
    exit 1
fi

# Check if Node modules are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Install Python dependencies if needed
echo "🐍 Setting up Python environment with UV..."
uv sync --dev

echo "⚡ Starting Python FastAPI Data Hub Server..."
# Start Python backend in background using UV
uv run python -m src.backend.server &
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