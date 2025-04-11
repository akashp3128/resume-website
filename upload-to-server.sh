#!/bin/bash

# Simple script to upload the stock ticker fix to your server

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}    Upload Stock Ticker Fix to Production Server   ${NC}"
echo -e "${BLUE}==================================================${NC}"

# Get server details
echo -e "${YELLOW}Please enter your server details:${NC}"
read -p "Server username: " USERNAME
read -p "Server hostname or IP: " SERVER
read -p "Destination directory (default: ~): " DEST_DIR

# Use default if no destination directory specified
if [ -z "$DEST_DIR" ]; then
    DEST_DIR="~"
fi

# Files to upload
FILES="stock-data-server.py test-yfinance-api.sh deploy-yfinance-backend.sh"

# Upload files
echo -e "${GREEN}Uploading files to server...${NC}"
scp $FILES $USERNAME@$SERVER:$DEST_DIR

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Files uploaded successfully!${NC}"
    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "1. SSH into your server: ${GREEN}ssh $USERNAME@$SERVER${NC}"
    echo -e "2. Go to the upload directory: ${GREEN}cd $DEST_DIR${NC}"
    echo -e "3. Make sure the files are executable: ${GREEN}chmod +x stock-data-server.py test-yfinance-api.sh deploy-yfinance-backend.sh${NC}"
    echo -e "4. Deploy the YFinance backend: ${GREEN}sudo ./deploy-yfinance-backend.sh${NC}"
    echo -e "5. Test the API endpoints: ${GREEN}./test-yfinance-api.sh${NC}"
else
    echo -e "${RED}Error uploading files. Please check your server details and try again.${NC}"
    exit 1
fi

echo -e "${BLUE}==================================================${NC}" 