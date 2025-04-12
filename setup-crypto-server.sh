#!/bin/bash

# Setup script for the crypto data server
# Checks and sets up the required environment

set -e  # Exit on error

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up crypto data server...${NC}"

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python3 not found!${NC}"
    echo -e "Please install Python 3.6 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}Python version: $PYTHON_VERSION${NC}"

# Set up virtual environment
echo -e "${BLUE}Setting up virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    echo -e "Creating virtual environment..."
    python3 -m venv .venv
    echo -e "${GREEN}Virtual environment created at .venv${NC}"
fi

echo -e "${BLUE}Activating virtual environment...${NC}"
source .venv/bin/activate
echo -e "${GREEN}Virtual environment activated${NC}"

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}Dependencies installed${NC}"

# Make scripts executable
echo -e "${BLUE}Making scripts executable...${NC}"
chmod +x crypto-data-server.py deploy-crypto-server.sh
echo -e "${GREEN}Scripts are now executable${NC}"

# Check for MongoDB
echo -e "${BLUE}Checking MongoDB status...${NC}"
if ! command -v mongod &> /dev/null; then
    echo -e "${YELLOW}MongoDB command not found.${NC}"
    echo -e "MongoDB is recommended for better performance but not required."
    echo -e "The server will run with in-memory storage only."
else
    if pgrep -x "mongod" > /dev/null; then
        echo -e "${GREEN}MongoDB is running${NC}"
        
        # Test MongoDB connection
        echo -e "${BLUE}Testing MongoDB connection...${NC}"
        if mongo --eval "db.stats()" > /dev/null 2>&1; then
            echo -e "${GREEN}MongoDB connection successful${NC}"
        else
            echo -e "${YELLOW}Could not connect to MongoDB${NC}"
            echo -e "The server will run with in-memory storage only."
        fi
    else
        echo -e "${YELLOW}MongoDB is installed but not running${NC}"
        echo -e "You can start MongoDB with: brew services start mongodb-community"
        echo -e "The server will run with in-memory storage only."
    fi
fi

# Test starting the server
echo -e "${BLUE}Testing server startup...${NC}"
./deploy-crypto-server.sh start

# Wait a moment
sleep 3

# Test the API
echo -e "${BLUE}Testing API...${NC}"
HEALTH_RESPONSE=$(curl -s http://localhost:3003/health)
if [[ "$HEALTH_RESPONSE" == *"status"*"ok"* ]]; then
    echo -e "${GREEN}API health check passed${NC}"
    
    CRYPTO_RESPONSE=$(curl -s http://localhost:3003/api/crypto)
    if [[ "$CRYPTO_RESPONSE" == \[*\] ]]; then
        echo -e "${GREEN}API data check passed${NC}"
    else
        echo -e "${RED}API data check failed${NC}"
        echo -e "Response: $CRYPTO_RESPONSE"
    fi
else
    echo -e "${RED}API health check failed${NC}"
    echo -e "Response: $HEALTH_RESPONSE"
fi

# Stop the server
echo -e "${BLUE}Stopping server...${NC}"
./deploy-crypto-server.sh stop

echo -e "${GREEN}Setup complete!${NC}"
echo -e ""
echo -e "To start the server:"
echo -e "  ./deploy-crypto-server.sh start"
echo -e ""
echo -e "To stop the server:"
echo -e "  ./deploy-crypto-server.sh stop"
echo -e ""
echo -e "For more commands, run:"
echo -e "  ./deploy-crypto-server.sh" 