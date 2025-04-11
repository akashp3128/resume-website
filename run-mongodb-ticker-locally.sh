#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if server is already running
check_server_running() {
    if lsof -i :3000 -sTCP:LISTEN &> /dev/null; then
        PID=$(lsof -i :3000 -sTCP:LISTEN -t)
        if [ -n "$PID" ]; then
            echo -e "${GREEN}MongoDB Stock Ticker already running on PID ${PID}${NC}"
            return 0
        fi
    fi
    return 1
}

# Parse command line arguments
BACKGROUND=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -b|--background) BACKGROUND=true ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

echo -e "${GREEN}Starting MongoDB Stock Ticker locally...${NC}"

# Check if server is already running
if check_server_running; then
    echo -e "${GREEN}MongoDB Stock Ticker is already running.${NC}"
    echo -e "${YELLOW}You can access it at:${NC} http://localhost:3000"
    exit 0
fi

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

# Check for necessary Python packages - using --break-system-packages flag
echo -e "${YELLOW}Checking required Python packages...${NC}"
if ! python3 -c "import pymongo" &> /dev/null; then
    echo -e "${YELLOW}Installing pymongo package...${NC}"
    python3 -m pip install pymongo --break-system-packages --user
fi

if ! python3 -c "import yfinance" &> /dev/null; then
    echo -e "${YELLOW}Installing yfinance package...${NC}"
    python3 -m pip install yfinance --break-system-packages --user
fi

# Add execute permission to the server script
chmod +x stock-data-server-mongodb.py

# Check if port 3000 is already in use
if lsof -i :3000 -sTCP:LISTEN &> /dev/null; then
    echo -e "${YELLOW}Port 3000 is already in use. Attempting to free it...${NC}"
    PID=$(lsof -i :3000 -sTCP:LISTEN -t)
    if [ -n "$PID" ]; then
        echo -e "${YELLOW}Killing process $PID using port 3000...${NC}"
        kill $PID
        sleep 2
    fi
fi

# Run the server
echo -e "${GREEN}Starting stock data server with MongoDB...${NC}"

if [ "$BACKGROUND" = true ]; then
    # Run in background mode
    nohup python3 stock-data-server-mongodb.py > mongodb-ticker.log 2>&1 &
    SERVER_PID=$!
    echo -e "${GREEN}Server started in background with PID ${SERVER_PID}${NC}"
    echo -e "${YELLOW}Logs are being written to mongodb-ticker.log${NC}"
    echo -e "${YELLOW}You can access the server at:${NC} http://localhost:3000"
    echo -e "${YELLOW}To stop the server:${NC} kill ${SERVER_PID}"
else
    # Run in foreground mode
    echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}\n"
    python3 stock-data-server-mongodb.py 