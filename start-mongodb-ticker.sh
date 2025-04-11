#!/bin/bash

# This script is designed to be run at system startup or via crontab
# Add to crontab with: @reboot /path/to/this/script
# Or: */5 * * * * /path/to/this/script (to check every 5 minutes)

# Change to the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="${SCRIPT_DIR}/mongodb-ticker-startup.log"

# Function to log messages
log() {
    echo "$(date): $1" >> "$LOG_FILE"
    echo -e "$1"
}

# Check if MongoDB stock ticker is running
check_server_running() {
    if lsof -i :3000 -sTCP:LISTEN &> /dev/null; then
        PID=$(lsof -i :3000 -sTCP:LISTEN -t)
        if [ -n "$PID" ]; then
            log "${GREEN}MongoDB Stock Ticker already running on PID ${PID}${NC}"
            return 0
        fi
    fi
    return 1
}

# Start a new log entry
log "Checking MongoDB Stock Ticker status..."

# If the ticker is already running, exit
if check_server_running; then
    log "${GREEN}MongoDB Stock Ticker is already running. No action needed.${NC}"
    exit 0
fi

# If we're here, we need to start the ticker
log "${YELLOW}MongoDB Stock Ticker not running. Starting it now...${NC}"

# Make sure the script is executable
chmod +x run-mongodb-ticker-locally.sh

# Run the ticker in background mode
./run-mongodb-ticker-locally.sh --background

# Verify the ticker started successfully
sleep 5
if check_server_running; then
    log "${GREEN}Successfully started MongoDB Stock Ticker.${NC}"
else
    log "${RED}Failed to start MongoDB Stock Ticker. Check the logs.${NC}"
fi 