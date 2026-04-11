#!/bin/bash

# Master setup script for Gold Price Prediction application
# Sets up both backend and frontend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "Gold Price Prediction - Complete Setup"
echo "========================================="

# Backend setup
echo ""
echo "🔨 Setting up Backend..."
echo "========================================="

cd "$PROJECT_DIR/backend"

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Backend setup complete!"

# Frontend setup
echo ""
echo "🔨 Setting up Frontend..."
echo "========================================="

cd "$PROJECT_DIR/frontend"

if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install Node.js 16+ first."
    exit 1
fi

echo "📦 Installing Node.js dependencies..."
npm install

echo "✅ Frontend setup complete!"

# Success message
echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1️⃣  Start Backend (Terminal 1):"
echo "   cd backend"
echo "   python app.py"
echo ""
echo "2️⃣  Start Frontend (Terminal 2):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3️⃣  Open in Browser:"
echo "   Frontend: http://localhost:3000"
echo "   API: http://localhost:5000"
echo ""
echo "📊 First Time Only:"
echo "   - Backend will train 3 models on first run"
echo "   - Models will be saved to: backend/models/saved_models/"
echo "   - Subsequent runs will load cached models"
echo ""
echo "========================================="
