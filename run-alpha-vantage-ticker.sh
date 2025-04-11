#!/bin/bash

# Colors for better output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a port is available
check_port() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        if lsof -i :$port >/dev/null 2>&1; then
            echo -e "${RED}Error: Port $port is already in use.${NC}"
            echo -e "Run the following command to see which process is using it:"
            echo -e "${YELLOW}lsof -i :$port${NC}"
            return 1
        fi
    else
        # If lsof is not available, try netstat
        if command -v netstat >/dev/null 2>&1; then
            if netstat -tuln | grep ":$port " >/dev/null 2>&1; then
                echo -e "${RED}Error: Port $port is already in use.${NC}"
                return 1
            fi
        fi
    fi
    return 0
}

# Function to kill processes and clean up
cleanup() {
    echo -e "\n${YELLOW}Shutting down server...${NC}"
    if [ -n "$SERVER_PID" ] && ps -p $SERVER_PID > /dev/null; then
        echo "Stopping HTTP server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || kill -9 $SERVER_PID 2>/dev/null
    fi
    echo -e "${GREEN}Server stopped successfully.${NC}"
    exit 0
}

# Set up the trap to catch Ctrl+C and other signals
trap cleanup INT TERM EXIT

# Check if port 8000 is available
check_port 8000 || exit 1

# Start the HTTP server
echo -e "${GREEN}Starting HTTP server at http://localhost:8000${NC}"
echo -e "${YELLOW}Access the Alpha Vantage stock ticker at: http://localhost:8000/alpha-vantage-ticker.html${NC}"
echo -e "${YELLOW}Note: You may need to visit https://cors-anywhere.herokuapp.com/ and request temporary access${NC}"
echo -e "Press Ctrl+C to stop the server.\n"

python3 -m http.server 8000 &
SERVER_PID=$!

# Check if HTTP server started correctly
sleep 1
if ! ps -p $SERVER_PID > /dev/null; then
    echo -e "${RED}Failed to start HTTP server.${NC}"
    exit 1
fi

echo -e "${GREEN}Server running with PID: ${SERVER_PID}${NC}"
# Wait for server to be killed
wait $SERVER_PID 