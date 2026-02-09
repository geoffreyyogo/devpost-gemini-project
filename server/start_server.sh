#!/bin/bash

# Smart Shamba - FastAPI Server Startup Script

echo "🌾 Smart Shamba - FastAPI Server"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Check if virtual environment exists
if [ ! -d "../venv" ]; then
    echo -e "${RED}Virtual environment not found!${NC}"
    echo "Please create one first: python3 -m venv ../venv"
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source ../venv/bin/activate

# Check if FastAPI is installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${BLUE}Installing FastAPI dependencies...${NC}"
    pip install -r requirements-fastapi.txt
fi

# Check if .env exists
if [ ! -f "../.env" ]; then
    echo -e "${RED}Warning: .env file not found${NC}"
    echo "The server will run in demo mode"
fi

# Check if MongoDB is running
echo -e "${BLUE}Checking MongoDB connection...${NC}"
if python -c "from pymongo import MongoClient; MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=2000).server_info()" 2>/dev/null; then
    echo -e "${GREEN}✓ MongoDB is running${NC}"
else
    echo -e "${RED}⚠ MongoDB is not running${NC}"
    echo "Starting server anyway (will use demo mode)"
fi

echo ""
echo -e "${GREEN}Starting FastAPI server...${NC}"
echo ""
echo "API Endpoints:"
echo "  - Main API: http://localhost:8000"
echo "  - Documentation: http://localhost:8000/api/docs"
echo "  - Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the server
python main.py


