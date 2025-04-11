#!/bin/bash

# Colors for better output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running isolated stock ticker demo...${NC}"

# Kill any existing server on port 8000
echo "Cleaning up any existing servers on port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
pkill -f "python3 -m http.server 8000" || true

# Wait a moment to ensure port is freed
sleep 1

echo -e "${GREEN}Starting HTTP server for isolated ticker at http://localhost:8000${NC}"
python3 -m http.server 8000 &
SERVER_PID=$!

# Check if server started correctly
sleep 1
if ! ps -p $SERVER_PID > /dev/null; then
    echo -e "${RED}Failed to start HTTP server.${NC}"
    exit 1
fi

echo -e "${GREEN}Server running at http://localhost:8000${NC}"
echo -e "${YELLOW}Visit http://localhost:8000/isolated-ticker.html to view the isolated stock ticker${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server.${NC}"

# Show a helpful message about the isolation
echo ""
echo -e "${GREEN}=== ISOLATED STOCK TICKER INFO ===${NC}"
echo "This stock ticker implementation is completely isolated from the main website,"
echo "allowing you to develop and test the ticker without affecting other features."
echo "The following files are part of this isolated implementation:"
echo " - isolated-ticker.html - The standalone ticker page"
echo " - public/js/isolated-stock-ticker.js - The isolated ticker script"
echo ""
echo "When you're satisfied with the isolated ticker, you can integrate it back into"
echo "the main website by updating index.html to use the new script."
echo ""

# Wait for the server to be killed
wait $SERVER_PID 