#!/bin/bash

# Backend setup script for Gold Price Prediction application
# Run this to install dependencies and train models for the first time

set -e

echo "========================================="
echo "Backend Setup - Gold Price Prediction"
echo "========================================="

# Navigate to backend directory
cd "$(dirname "$0")/backend"

echo ""
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Backend setup complete!"
echo ""
echo "To run the backend:"
echo "  cd backend"
echo "  python app.py"
echo ""
echo "Backend will start on: http://localhost:5000"
