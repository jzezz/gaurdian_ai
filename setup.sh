#!/bin/bash

# Guardian AI Setup Script
# Quick setup for development environment

set -e

echo "🛡️  Guardian AI Setup"
echo "===================="

# Backend setup
echo ""
echo "Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

echo "✅ Backend setup complete"

# Frontend setup
echo ""
echo "Setting up frontend..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm ci
else
    echo "Node modules already installed"
fi

echo "✅ Frontend setup complete"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start development:"
echo "  Backend:  cd backend && source venv/bin/activate && python run.py"
echo "  Frontend: cd frontend && npm run dev"
