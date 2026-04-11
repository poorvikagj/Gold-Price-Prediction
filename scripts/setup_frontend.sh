#!/bin/bash

# Frontend setup script for Gold Price Prediction application

set -e

echo "========================================="
echo "Frontend Setup - Gold Price Prediction"
echo "========================================="

# Navigate to frontend directory
cd "$(dirname "$0")/frontend"

echo ""
echo "📦 Installing Node.js dependencies..."

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install Node.js first."
    exit 1
fi

npm install

echo ""
echo "✅ Frontend setup complete!"
echo ""
echo "To run the frontend:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Frontend will start on: http://localhost:3000"
