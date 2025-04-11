#!/bin/bash

# Setup script for Twelvedata API
# This script helps you set up and test the Twelvedata API for real-time stock prices

# Text styling
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}===== Twelvedata API Setup for Stock Ticker =====${RESET}"
echo "This script will help you set up the Twelvedata API for real-time stock prices."
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 before proceeding.${RESET}"
    exit 1
fi

echo -e "${BOLD}${GREEN}Step 1: Installing dependencies${RESET}"
# Create a virtual environment
echo "Creating a Python virtual environment..."
python3 -m venv twelvedata-env

# Activate the virtual environment
echo "Activating virtual environment..."
source twelvedata-env/bin/activate

# Install dependencies
echo "Installing Twelvedata package with websocket support..."
pip install 'twelvedata[websocket]'

echo -e "\n${BOLD}${GREEN}Step 2: Get Twelvedata API Key${RESET}"
echo -e "You need an API key from Twelvedata to use real-time data."
echo -e "1. Go to ${BLUE}https://twelvedata.com/${RESET} and sign up for an account"
echo -e "2. Navigate to the API Keys section in your dashboard"
echo -e "3. Copy your API key"
echo ""

# Ask for API key
read -p "Enter your Twelvedata API key (or press Enter to skip): " API_KEY

# Create a test file
echo -e "\n${BOLD}${GREEN}Step 3: Creating a test script${RESET}"
TESTFILE="test-twelvedata.py"

cat > $TESTFILE << EOF
#!/usr/bin/env python3
from twelvedata import TDClient
import time

# Replace with your actual API key
API_KEY = "${API_KEY}"

def on_event(event):
    """Handle price update events from Twelvedata"""
    print(f"Received price: {event}")

def main():
    print("Starting Twelvedata test...")
    
    # List of symbols to track
    symbols = ["AAPL", "MSFT", "NVDA", "SPY", "BTC/USD"]
    
    # Initialize TDClient
    td = TDClient(apikey=API_KEY)
    
    # Initialize websocket connection with event handler
    ws = td.websocket(symbols=symbols, on_event=on_event)
    
    # Connect to the websocket
    print(f"Connecting to Twelvedata websocket for symbols: {symbols}")
    ws.connect()
    print("Connected! Waiting for price updates (Ctrl+C to exit)")
    
    # Keep the connection alive in the main thread
    try:
        ws.keep_alive()
    except KeyboardInterrupt:
        print("Test stopped by user")

if __name__ == "__main__":
    main()
EOF

chmod +x $TESTFILE

# Create an example .env file for the API key
cat > .env.example << EOF
# Twelvedata API configuration
TWELVEDATA_API_KEY=${API_KEY}
EOF

# Create sample script to run the stock server with Twelvedata
cat > run-twelvedata-ticker.sh << EOF
#!/bin/bash

# Run the MongoDB stock ticker with Twelvedata websocket integration
# This script sets up the necessary environment and starts the server

# Check if the .env file exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file"
    export \$(grep -v '^#' .env | xargs)
else
    echo "No .env file found, using default configuration"
    echo "For real-time data, create a .env file with your Twelvedata API key"
fi

# Start the server with Twelvedata API support
echo "Starting stock data server with Twelvedata websocket support..."
python3 stock-data-server-mongodb.py
EOF

chmod +x run-twelvedata-ticker.sh

echo -e "\n${BOLD}${GREEN}Setup complete!${RESET}"
echo -e "\nTo test the Twelvedata API, run:"
echo -e "${YELLOW}./test-twelvedata.py${RESET}"
echo ""
echo -e "To run the stock ticker server with Twelvedata support:"
echo -e "1. Create a ${BLUE}.env${RESET} file with your API key (use .env.example as template)"
echo -e "2. Run ${YELLOW}./run-twelvedata-ticker.sh${RESET}"
echo ""
echo -e "${BOLD}Note:${RESET} The free Twelvedata API has usage limits. Check your plan details at"
echo -e "${BLUE}https://twelvedata.com/pricing${RESET}"
echo ""
echo -e "If you're using the virtual environment, deactivate it when done with:"
echo -e "${YELLOW}deactivate${RESET}" 