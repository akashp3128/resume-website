#!/bin/bash

# Run the MongoDB stock ticker with Twelvedata websocket integration
# This script sets up the necessary environment and starts the server

# Text styling
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}===== Twelvedata Stock Ticker Server =====${RESET}"

# Check if the virtual environment exists and activate it
if [ -d "twelvedata-env" ]; then
    echo "Activating virtual environment..."
    source twelvedata-env/bin/activate
fi

# Check if the .env file exists
if [ -f .env ]; then
    echo -e "${GREEN}Loading environment variables from .env file${RESET}"
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${YELLOW}No .env file found, using default configuration${RESET}"
    echo "For real-time data, create a .env file with your Twelvedata API key"
fi

# Check if API key is set
if [ -z "$TWELVEDATA_API_KEY" ]; then
    echo -e "${YELLOW}Warning: TWELVEDATA_API_KEY not set. Using demo mode with limited functionality.${RESET}"
    export TWELVEDATA_API_KEY="demo"
fi

echo -e "${GREEN}Using Twelvedata API key: ${TWELVEDATA_API_KEY}${RESET}"

# Start the server with Twelvedata API support
echo -e "${BOLD}Starting stock data server with Twelvedata websocket support...${RESET}"
echo "Press Ctrl+C to stop the server"
echo ""

python3 stock-data-server-mongodb.py

# Deactivate virtual environment when done
if [ -d "twelvedata-env" ]; then
    deactivate
fi 