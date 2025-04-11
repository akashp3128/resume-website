#!/bin/bash

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for Python installation
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
    exit 1
fi

# Function to stop any running servers
function stop_servers {
    echo -e "${YELLOW}Checking for existing servers...${NC}"
    
    # Check if HTTP server is running on port 8000
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}Stopping HTTP server on port 8000...${NC}"
        kill $(lsof -t -i:8000) 2>/dev/null || true
        sleep 1
    fi
    
    # Check if backend server is running on port 3000
    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}Stopping backend server on port 3000...${NC}"
        kill $(lsof -t -i:3000) 2>/dev/null || true
        sleep 1
    fi
}

# Function to handle script termination
function cleanup {
    echo -e "${YELLOW}Shutting down servers...${NC}"
    
    # Kill HTTP server
    if [ ! -z "$HTTP_PID" ]; then
        kill $HTTP_PID 2>/dev/null || true
        echo -e "${GREEN}HTTP server stopped.${NC}"
    fi
    
    # Kill backend server
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}Backend server stopped.${NC}"
    fi
    
    echo -e "${GREEN}All servers stopped successfully.${NC}"
    exit 0
}

# Set up trap to call cleanup function on script termination
trap cleanup INT TERM EXIT

# Stop any existing servers
stop_servers

# Make backend server executable
chmod +x stock-data-server.py

# Start the backend server
echo -e "${GREEN}Starting YFinance backend server at http://localhost:3000${NC}"
./stock-data-server.py &
BACKEND_PID=$!
echo -e "${GREEN}Backend server started with PID: $BACKEND_PID${NC}"

# Wait a bit for the backend to start
sleep 2

# Check if backend started successfully
if ! ps -p $BACKEND_PID > /dev/null; then
    echo -e "${RED}Error: Backend server failed to start.${NC}"
    echo -e "${YELLOW}Check if port 3000 is available and Python dependencies are installed.${NC}"
    exit 1
fi

# Start the HTTP server
echo -e "${GREEN}Starting HTTP server at http://localhost:8000${NC}"
echo -e "${GREEN}Access the YFinance ticker at: ${BLUE}http://localhost:8000/yfinance-ticker.html${NC}"
echo -e "${RED}Press Ctrl+C to stop both servers.${NC}"

# Start HTTP server
cd $(dirname "$0")
python3 -m http.server 8000 &
HTTP_PID=$!
echo -e "${GREEN}HTTP server started with PID: $HTTP_PID${NC}"

echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}YFinance Stock Ticker Setup${NC}"
echo -e "${BLUE}=============================================${NC}"
echo -e "${GREEN}Backend server:${NC} http://localhost:3000"
echo -e "${GREEN}Frontend server:${NC} http://localhost:8000"
echo -e "${GREEN}Ticker URL:${NC} http://localhost:8000/yfinance-ticker.html"
echo -e "${BLUE}=============================================${NC}"
echo -e "${YELLOW}Note: The backend will automatically install the yfinance package if needed${NC}"
echo -e "${YELLOW}You can check backend status using the button on the ticker page${NC}"
echo -e "${RED}Press Ctrl+C to stop both servers${NC}"

# Keep script running
wait $HTTP_PID 