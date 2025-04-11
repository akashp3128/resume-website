#!/bin/bash

# Colors for better output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Checking for running servers...${NC}"

# More forcefully kill any processes using ports 8000 and 8001 (HTTP and upload servers)
echo "Killing any processes on port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

echo "Killing any processes on port 8001..."
lsof -ti:8001 | xargs kill -9 2>/dev/null || true

# Also try the more specific process kills
pkill -f "python3 -m http.server 8000" || true
pkill -f "python3 upload_server.py" || true

echo "Stopped any running servers on ports 8000 and 8001"

# Wait a moment to ensure ports are freed
sleep 2

# Create uploads directory if it doesn't exist
mkdir -p uploads/resume uploads/eval uploads/photo
echo -e "${GREEN}Upload directories created/verified.${NC}"

# Ensure the stock ticker script is in both locations
echo -e "${YELLOW}Ensuring stock ticker script is available...${NC}"
cp -f public/js/stock-ticker.js .
cp -f public/js/stock-ticker.js public/
echo "✓ Stock ticker script copied to multiple locations for redundancy"

# Start the HTTP server from the ROOT directory
echo -e "${GREEN}Starting HTTP server at http://localhost:8000${NC}"
cd "$(dirname "$0")" # Ensure we're in the script's directory
python3 -m http.server 8000 &
HTTP_PID=$!

# Check if HTTP server started correctly
sleep 1
if ! ps -p $HTTP_PID > /dev/null; then
    echo -e "${RED}Failed to start HTTP server.${NC}"
    exit 1
fi

# Start the upload server
echo -e "${GREEN}Starting upload handler at http://localhost:8001${NC}"
cd upload-handler
python3 upload_server.py &
UPLOAD_PID=$!

# Return to original directory
cd ..

# Check if upload server started correctly
sleep 1
if ! ps -p $UPLOAD_PID > /dev/null; then
    echo -e "${RED}Failed to start upload server.${NC}"
    kill $HTTP_PID
    exit 1
fi

echo -e "${GREEN}Both servers running successfully.${NC}"
echo -e "HTTP Server (PID: ${YELLOW}$HTTP_PID${NC}) at http://localhost:8000"
echo -e "Upload Server (PID: ${YELLOW}$UPLOAD_PID${NC}) at http://localhost:8001"
echo -e "${YELLOW}Open http://localhost:8000 in your browser to view the site.${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop both servers.${NC}"

# Wait for both servers to be killed
wait 