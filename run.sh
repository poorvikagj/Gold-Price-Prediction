#!/bin/bash

# Run script to start both backend and frontend servers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo "========================================="
echo "🚀 Starting Gold Price Prediction App"
echo "========================================="
echo ""
echo "Starting Backend on port 5000..."
echo "Starting Frontend on port 3000..."
echo ""

# Fail fast when expected ports are already occupied.
if lsof -ti :5000 >/dev/null 2>&1; then
    echo "❌ Port 5000 is already in use. Stop the existing backend process first."
    exit 1
fi

if lsof -ti :3000 >/dev/null 2>&1; then
    echo "❌ Port 3000 is already in use. Stop the existing frontend process first."
    exit 1
fi

# Resolve Python executable (prefer project venv)
PYTHON_BIN=""
if [ -x "$PROJECT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    echo "❌ Python executable not found. Activate your virtual environment or install Python."
    exit 1
fi

# Check if backend data exists
if [ ! -f "$PROJECT_DIR/backend/data/raw/financial_regression.csv" ]; then
    echo "⚠️  Warning: financial_regression.csv not found in backend/data/raw/"
    echo "   Please ensure the CSV file is in the correct location."
fi

# Start backend in background
echo ""
echo "Starting Backend..."
cd "$PROJECT_DIR/backend"
"$PYTHON_BIN" app.py &
BACKEND_PID=$!

# Give backend time to start
sleep 3

# Start frontend in background
echo ""
echo "Starting Frontend..."
cd "$PROJECT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================="
echo "✅ Application Started!"
echo "========================================="
echo ""
echo "Frontend:  http://localhost:3000"
echo "Backend:   http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
