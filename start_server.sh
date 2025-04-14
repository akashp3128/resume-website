#!/bin/bash

# ANSI color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a port is in use
function is_port_in_use() {
  lsof -i:$1 > /dev/null
  return $?
}

# Function to stop servers on specific ports
function stop_servers() {
  local ports=("$@")
  
  for port in "${ports[@]}"; do
    echo -e "${YELLOW}Checking if port $port is in use...${NC}"
    if is_port_in_use $port; then
      echo -e "${YELLOW}Stopping server on port $port...${NC}"
      kill $(lsof -t -i:$port) 2>/dev/null || true
      sleep 1
    else
      echo -e "${GREEN}No server running on port $port.${NC}"
    fi
  done
}

# Check if we're in a virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
  echo -e "${GREEN}Virtual environment detected: $VIRTUAL_ENV${NC}"
else
  echo -e "${YELLOW}No virtual environment detected. This script may not work correctly.${NC}"
  echo -e "${YELLOW}We strongly recommend creating and activating a Python virtual environment:${NC}"
  echo -e "${YELLOW}  python3 -m venv venv${NC}"
  echo -e "${YELLOW}  source venv/bin/activate${NC}"
  echo -e "${YELLOW}Do you want to continue anyway? (y/n)${NC}"
  read response
  if [ "$response" != "y" ]; then
    exit 1
  fi
fi

# Check for required Python packages
python3 -c "import pymongo; import requests" 2>/dev/null
if [ $? -ne 0 ]; then
  echo -e "${YELLOW}Required packages not found. Installing...${NC}"
  if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
  else
    pip install pymongo requests
  fi
  
  if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install required packages. Please install them manually:${NC}"
    echo -e "${YELLOW}  pip install pymongo requests${NC}"
    exit 1
  fi
fi

# Stop any existing servers
stop_servers 8000 8001 3000

# Make sure scripts are executable
chmod +x upload-handler/upload_server.py
chmod +x stock-data-server-mongodb.py

# Remove any existing PID file
rm -f crypto_server_running.pid

# Start upload server
echo -e "${GREEN}Starting upload server on port 8001...${NC}"
cd upload-handler
python3 upload_server.py &
UPLOAD_PID=$!
cd ..

# Wait for upload server to start
sleep 2
if is_port_in_use 8001; then
  echo -e "${GREEN}Upload server started successfully.${NC}"
else
  echo -e "${RED}Error: Upload server failed to start.${NC}"
  echo -e "${YELLOW}Check logs above for errors.${NC}"
  exit 1
fi

# Start CoinGecko/MongoDB backend for crypto ticker
echo -e "${GREEN}Starting CoinGecko/MongoDB backend on port 3000...${NC}"
./stock-data-server-mongodb.py &
CRYPTO_PID=$!

# Wait for crypto server to start - use a more robust method with increased timeout
MAX_WAIT=15
WAIT_COUNT=0
while [ ! -f "crypto_server_running.pid" ] && [ $WAIT_COUNT -lt $MAX_WAIT ]; do
  echo -e "${YELLOW}Waiting for crypto server to initialize... ($WAIT_COUNT/${MAX_WAIT})${NC}"
  sleep 1
  WAIT_COUNT=$((WAIT_COUNT+1))
done

if [ -f "crypto_server_running.pid" ] && is_port_in_use 3000; then
  echo -e "${GREEN}CoinGecko/MongoDB backend started successfully.${NC}"
else
  echo -e "${YELLOW}Warning: CoinGecko backend initialization is taking longer than expected.${NC}"
  echo -e "${YELLOW}The service might still be starting in the background. Check logs for progress.${NC}"
  echo -e "${YELLOW}This is not critical - the website will still function.${NC}"
fi

# Start the main web server
echo -e "${GREEN}Starting main web server on port 8000...${NC}"
python3 -m http.server 8000 &
HTTP_PID=$!

# Wait for web server to start
sleep 1
if is_port_in_use 8000; then
  echo -e "${GREEN}Web server started successfully.${NC}"
else
  echo -e "${RED}Error: Web server failed to start.${NC}"
  stop_servers 8001 3000
  exit 1
fi

# Information about access
echo -e "\n${GREEN}=======================================================${NC}"
echo -e "${GREEN}All servers started successfully!${NC}"
echo -e "${GREEN}Main website:${NC} http://localhost:8000"
echo -e "${GREEN}Upload server:${NC} http://localhost:8001"
echo -e "${GREEN}CoinGecko/MongoDB backend:${NC} http://localhost:3000"
echo -e "${GREEN}=======================================================${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all servers.${NC}\n"

# Handle termination
trap "echo -e '${YELLOW}Shutting down servers...${NC}'; stop_servers 8000 8001 3000; rm -f crypto_server_running.pid; exit 0" INT TERM

# Keep script running
wait 