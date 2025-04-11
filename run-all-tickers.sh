#!/bin/bash

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to stop any running server on port 8000
function stop_server {
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}Stopping existing server on port 8000...${NC}"
        kill $(lsof -t -i:8000) 2>/dev/null || true
        sleep 1
    fi
    
    # Also check for backend server on port 3000
    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}Stopping existing backend server on port 3000...${NC}"
        kill $(lsof -t -i:3000) 2>/dev/null || true
        sleep 1
    fi
}

# Function to run a ticker
function run_ticker {
    ticker_type=$1
    html_file=$2
    title=$3
    
    stop_server
    
    if [[ "$ticker_type" == "yfinance" ]]; then
        # For yfinance, we need to run the dedicated script that handles both servers
        echo -e "${GREEN}Starting YFinance ticker with dedicated backend...${NC}"
        ./run-yfinance-ticker.sh
        return
    fi
    
    echo -e "${GREEN}Starting HTTP server at http://localhost:8000${NC}"
    echo -e "${GREEN}Access the $title at: ${BLUE}http://localhost:8000/$html_file${NC}"
    
    if [[ "$ticker_type" == "yahoo" ]]; then
        echo -e "${YELLOW}This ticker prioritizes Yahoo Finance data with CoinGecko for crypto${NC}"
    elif [[ "$ticker_type" == "realtime" ]]; then
        echo -e "${YELLOW}This ticker combines multiple data sources for real-time updates${NC}"
    elif [[ "$ticker_type" == "alphavantage" ]]; then
        echo -e "${YELLOW}This ticker uses Alpha Vantage API (may require CORS proxy access)${NC}"
        echo -e "${YELLOW}Note: You may need to visit https://cors-anywhere.herokuapp.com/ and request temporary access${NC}"
    fi
    
    echo -e "${RED}Press Ctrl+C to stop the server.${NC}"
    
    # Start HTTP server
    cd $(dirname "$0")
    python3 -m http.server 8000 &
    SERVER_PID=$!
    echo -e "${GREEN}Server running with PID: $SERVER_PID${NC}"
    
    # Keep script running until Ctrl+C
    wait $SERVER_PID
}

# Function to handle script termination
function cleanup {
    echo -e "${YELLOW}Shutting down server...${NC}"
    kill $(lsof -t -i:8000) 2>/dev/null || true
    kill $(lsof -t -i:3000) 2>/dev/null || true
    echo -e "${GREEN}Server stopped successfully.${NC}"
    exit 0
}

# Set up trap to call cleanup function on script termination
trap cleanup INT TERM EXIT

# Main menu
clear
echo -e "${BLUE}=== Stock Ticker Selection ===${NC}"
echo -e "${GREEN}1. YFinance Ticker${NC} (Python-backed implementation using yfinance library - RECOMMENDED)"
echo -e "${GREEN}2. Yahoo Finance Ticker${NC} (Prioritizes Yahoo Finance with CoinGecko for crypto)"
echo -e "${GREEN}3. Real-time Ticker${NC} (Multiple data sources with fallbacks)"
echo -e "${GREEN}4. Alpha Vantage Ticker${NC} (Requires temporary CORS proxy access)"
echo -e "${RED}0. Exit${NC}"
echo
echo -e "${YELLOW}Enter your choice [0-4]:${NC} "
read choice

case $choice in
    1)
        run_ticker "yfinance" "yfinance-ticker.html" "YFinance Ticker"
        ;;
    2)
        run_ticker "yahoo" "yahoo-finance-ticker.html" "Yahoo Finance Ticker"
        ;;
    3)
        run_ticker "realtime" "realtime-ticker.html" "Real-time Ticker"
        ;;
    4)
        run_ticker "alphavantage" "alpha-vantage-ticker.html" "Alpha Vantage Ticker"
        ;;
    0)
        echo -e "${RED}Exiting...${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice. Exiting...${NC}"
        exit 1
        ;;
esac 