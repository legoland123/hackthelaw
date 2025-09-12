#!/bin/bash

# LIT Legal Mind Backend Startup Script

echo "🚀 Starting LIT Legal Mind Backend API..."

# Check if we're in the right directory
if [ ! -f "backend/app.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Change to backend directory
cd backend

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: No .env file found"
    echo "Please create a .env file with your GOOGLE_AI_API_KEY"
    echo "Example:"
    echo "GOOGLE_AI_API_KEY=your_api_key_here"
fi

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Start the server
echo "🚀 Starting server..."
python run_app.py 