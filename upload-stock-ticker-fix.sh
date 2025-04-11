#!/bin/bash

# Upload Stock Ticker Fix to Production
# This script makes it easy to upload the necessary files to fix your production stock ticker

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}    Upload Stock Ticker Fix to Production         ${NC}"
echo -e "${BLUE}==================================================${NC}"

# Required files to upload
FILES_TO_UPLOAD=(
    "stock-data-server.py"
    "deploy-yfinance-backend.sh"
    "test-yfinance-api.sh"
    "fix-production-stock-ticker.sh"
    "PRODUCTION-STOCK-TICKER-FIX.md"
)

# Check if all required files exist
echo -e "${GREEN}Checking for required files...${NC}"
MISSING_FILES=false

for file in "${FILES_TO_UPLOAD[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: $file not found in the current directory.${NC}"
        MISSING_FILES=true
    fi
done

if [ "$MISSING_FILES" = true ]; then
    echo -e "${RED}Error: Some required files are missing. Please make sure all files are in the current directory.${NC}"
    exit 1
fi

echo -e "${GREEN}All required files found.${NC}"

# Get server details
echo -e "${YELLOW}Please enter your server details:${NC}"
read -p "Server username: " SERVER_USER
read -p "Server hostname or IP: " SERVER_HOST
read -p "Destination directory on server (default: ~): " SERVER_DIR

# Use default directory if not specified
if [ -z "$SERVER_DIR" ]; then
    SERVER_DIR="~"
fi

# Create a temporary directory with all the files
echo -e "${GREEN}Preparing files for upload...${NC}"
TEMP_DIR=$(mktemp -d)

for file in "${FILES_TO_UPLOAD[@]}"; do
    cp "$file" "$TEMP_DIR/"
done

# Make scripts executable
chmod +x "$TEMP_DIR/stock-data-server.py"
chmod +x "$TEMP_DIR/deploy-yfinance-backend.sh"
chmod +x "$TEMP_DIR/test-yfinance-api.sh"
chmod +x "$TEMP_DIR/fix-production-stock-ticker.sh"

# Upload files to server
echo -e "${GREEN}Uploading files to server...${NC}"
if scp -r "$TEMP_DIR"/* "${SERVER_USER}@${SERVER_HOST}:${SERVER_DIR}"; then
    echo -e "${GREEN}Files successfully uploaded to ${SERVER_USER}@${SERVER_HOST}:${SERVER_DIR}${NC}"
else
    echo -e "${RED}Error: Failed to upload files to server.${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Clean up temporary directory
rm -rf "$TEMP_DIR"

echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}Upload complete!${NC}"
echo -e "${BLUE}==================================================${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. SSH into your server:"
echo -e "${GREEN}   ssh ${SERVER_USER}@${SERVER_HOST}${NC}"
echo -e "2. Navigate to the directory where the files were uploaded:"
echo -e "${GREEN}   cd ${SERVER_DIR}${NC}"
echo -e "3. Run the fix script:"
echo -e "${GREEN}   sudo ./fix-production-stock-ticker.sh${NC}"
echo -e "4. For more details, see the uploaded guide:"
echo -e "${GREEN}   cat PRODUCTION-STOCK-TICKER-FIX.md${NC}"

exit 0 