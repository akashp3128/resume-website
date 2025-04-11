#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting MongoDB Stock Ticker locally...${NC}"

# Check for Python and required packages
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install it first.${NC}"
    exit 1
fi

# Check for MongoDB
if brew services list | grep mongodb-community | grep -q started; then
    echo -e "${GREEN}MongoDB is running.${NC}"
else
    echo -e "${YELLOW}MongoDB is not running. Starting it now...${NC}"
    brew services start mongodb-community
    
    # Wait a moment for MongoDB to start
    sleep 3
    
    if brew services list | grep mongodb-community | grep -q started; then
        echo -e "${GREEN}MongoDB started successfully.${NC}"
    else
        echo -e "${RED}Failed to start MongoDB. Please start it manually:${NC}"
        echo -e "  brew services start mongodb-community"
        exit 1
    fi
fi

# Ensure we have the required Python packages
echo -e "${YELLOW}Checking required Python packages...${NC}"
python3 -m pip install pymongo yfinance --quiet

# Add execute permission to the server script
chmod +x stock-data-server-mongodb.py

# Run the server
echo -e "${GREEN}Starting stock data server with MongoDB...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}\n"

# Run the server with Python
python3 stock-data-server-mongodb.py 