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
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    
    # Kill the HTTP server
    if [ -n "$SERVER_PID" ] && ps -p $SERVER_PID > /dev/null; then
        echo "Stopping HTTP server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || kill -9 $SERVER_PID 2>/dev/null
    fi
    
    # Kill the upload server
    if [ -n "$UPLOAD_PID" ] && ps -p $UPLOAD_PID > /dev/null; then
        echo "Stopping upload server (PID: $UPLOAD_PID)..."
        kill $UPLOAD_PID 2>/dev/null || kill -9 $UPLOAD_PID 2>/dev/null
    fi
    
    echo -e "${GREEN}Servers stopped successfully.${NC}"
    exit 0
}

# Set up the trap to catch Ctrl+C and other signals
trap cleanup INT TERM EXIT

# Check if ports are available
check_port 8000 || exit 1
check_port 8001 || exit 1

# Create uploads directory
mkdir -p uploads/resume uploads/eval uploads/photo
echo -e "${GREEN}Upload directories created.${NC}"

# Start the HTTP server
echo -e "${GREEN}Starting HTTP server at http://localhost:8000${NC}"
python3 -m http.server 8000 &
SERVER_PID=$!

# Check if HTTP server started correctly
sleep 1
if ! ps -p $SERVER_PID > /dev/null; then
    echo -e "${RED}Failed to start HTTP server.${NC}"
    exit 1
fi

# Start the upload server
echo -e "${GREEN}Starting backup upload handler at http://localhost:8001${NC}"
cd upload-handler
python3 upload_server.py &
UPLOAD_PID=$!

# Return to original directory
cd ..

# Check if upload server started correctly
sleep 1
if ! ps -p $UPLOAD_PID > /dev/null; then
    echo -e "${RED}Failed to start upload server.${NC}"
    echo -e "${RED}Check the upload-handler/upload_server.py file for errors.${NC}"
    echo -e "You can run it manually with: cd upload-handler && python3 upload_server.py"
    kill $SERVER_PID
    exit 1
fi

echo -e "${GREEN}Both servers running successfully.${NC}"
echo -e "HTTP Server (PID: ${YELLOW}$SERVER_PID${NC}) at http://localhost:8000"
echo -e "Upload Server (PID: ${YELLOW}$UPLOAD_PID${NC}) at http://localhost:8001"
echo -e "${YELLOW}Press Ctrl+C to stop both servers.${NC}"

# Wait for both servers to be killed
wait 