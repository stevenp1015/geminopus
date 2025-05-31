#!/bin/bash

# Gemini Legion Startup Script
# Starts both backend and frontend servers

echo "🚀 Starting Gemini Legion..."
echo "================================"

# Function to handle cleanup on exit
cleanup() {
    echo -e "\n🛑 Shutting down Gemini Legion..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up trap for cleanup
trap cleanup INT TERM

# Start backend server
echo "📡 Starting Backend Server..."
cd gemini_legion_backend
python main.py &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Give backend time to start
sleep 3

# Start frontend server
echo "🎨 Starting Frontend Server..."
cd ../gemini_legion_frontend
npm run dev &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo "================================"
echo "✅ Gemini Legion is running!"
echo ""
echo "🌐 Frontend: http://localhost:5173"
echo "🔌 Backend:  http://localhost:8888"
echo "📚 API Docs: http://localhost:8888/docs"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "================================"

# Wait for processes
wait