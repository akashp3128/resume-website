#!/bin/bash

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
LOCAL_API="http://localhost:3000"
PRODUCTION_API="https://akashpatelresume.us/api/yfinance"

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}       YFinance API Connection Test Tool          ${NC}"
echo -e "${BLUE}==================================================${NC}"

# Function to test an endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local endpoint=$3
    
    echo -e "${YELLOW}Testing $name at ${url}${endpoint}${NC}"
    
    # Use curl to make the request with a timeout
    response=$(curl -s -m 5 "${url}${endpoint}" 2>&1)
    status=$?
    
    if [ $status -ne 0 ]; then
        echo -e "${RED}✗ Connection failed: ${response}${NC}"
        return 1
    fi
    
    # Check if response contains an error message or is empty
    if [[ -z "$response" ]]; then
        echo -e "${RED}✗ Empty response${NC}"
        return 1
    elif [[ "$response" == *"error"* ]]; then
        echo -e "${RED}✗ Error in response: ${response}${NC}"
        return 1
    else
        echo -e "${GREEN}✓ Success: $(echo $response | cut -c 1-100)...${NC}"
        return 0
    fi
}

# Test both local and production endpoints
echo -e "\n${BLUE}Testing Local YFinance Backend:${NC}"
echo -e "----------------------------------"
test_endpoint "Health check" "$LOCAL_API" "/health"
test_endpoint "Quotes API" "$LOCAL_API" "/api/quotes"
test_endpoint "Single quote API" "$LOCAL_API" "/api/quote/AAPL"

echo -e "\n${BLUE}Testing Production YFinance Backend:${NC}"
echo -e "----------------------------------"
test_endpoint "Health check" "$PRODUCTION_API" "/health"
test_endpoint "Quotes API" "$PRODUCTION_API" "/quotes"
test_endpoint "Single quote API" "$PRODUCTION_API" "/quote/AAPL"

echo -e "\n${BLUE}==================================================${NC}"
echo -e "${YELLOW}If local tests pass but production tests fail:${NC}"
echo -e "1. Make sure the backend is running as a service in production"
echo -e "2. Check that Nginx is correctly configured to proxy requests"
echo -e "3. Verify firewall settings allow connections to port 3000 locally"
echo -e "${BLUE}==================================================${NC}" 