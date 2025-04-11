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

# Stop any existing servers
stop_servers 8000 8001 3000

# Make sure scripts are executable
chmod +x upload-handler/upload_server.py
chmod +x stock-data-server.py

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

# Start YFinance backend for stock ticker
echo -e "${GREEN}Starting YFinance backend for stock ticker on port 3000...${NC}"
./stock-data-server.py &
YFINANCE_PID=$!

# Wait for YFinance backend to start
sleep 2
if is_port_in_use 3000; then
  echo -e "${GREEN}YFinance backend started successfully.${NC}"
else
  echo -e "${YELLOW}Warning: YFinance backend failed to start. Stock ticker will use fallback data.${NC}"
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
echo -e "${GREEN}YFinance backend:${NC} http://localhost:3000"
echo -e "${GREEN}=======================================================${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all servers.${NC}\n"

# Handle termination
trap "echo -e '${YELLOW}Shutting down servers...${NC}'; stop_servers 8000 8001 3000; exit 0" INT TERM

# Keep script running
wait 