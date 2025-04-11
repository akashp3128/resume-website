#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Set your domain or IP here
PRODUCTION_DOMAIN="akashpatelresume.us"
LOCAL_API="http://localhost:3000"
PROD_API="https://${PRODUCTION_DOMAIN}/api/yfinance"

# Usage information
function show_usage {
  echo "Test MongoDB YFinance API endpoints both locally and in production"
  echo ""
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  -l, --local     Test only local endpoints"
  echo "  -p, --prod      Test only production endpoints"
  echo "  -h, --help      Show this help message"
  echo ""
}

# Parse command line arguments
TEST_LOCAL=true
TEST_PROD=true

while [[ $# -gt 0 ]]; do
  case $1 in
    -l|--local)
      TEST_LOCAL=true
      TEST_PROD=false
      shift
      ;;
    -p|--prod)
      TEST_LOCAL=false
      TEST_PROD=true
      shift
      ;;
    -h|--help)
      show_usage
      exit 0
      ;;
    *)
      # Unknown option
      echo "Unknown option: $1"
      show_usage
      exit 1
      ;;
  esac
done

# Function to test an endpoint
function test_endpoint {
  local url=$1
  local description=$2
  
  echo -e "${YELLOW}Testing: ${description}${NC}"
  echo -e "URL: ${url}"
  
  # Use curl to test the endpoint
  response=$(curl -s -w "\n%{http_code}" "${url}")
  http_code=$(echo "$response" | tail -n1)
  content=$(echo "$response" | sed '$d')
  
  # Check if the request was successful
  if [[ $http_code -ge 200 && $http_code -lt 300 ]]; then
    echo -e "${GREEN}✓ Success (HTTP ${http_code})${NC}"
    
    # Print a shortened version of the response for JSON
    if [[ $content == {* || $content == \[* ]]; then
      # Get the first 200 characters or first line if it's JSON
      echo -e "${YELLOW}Response preview:${NC}"
      echo "$content" | head -c 300
      echo -e "\n..."
    else
      echo -e "${YELLOW}Response:${NC}"
      echo "$content"
    fi
  else
    echo -e "${RED}✗ Failed (HTTP ${http_code})${NC}"
    echo -e "${YELLOW}Response:${NC}"
    echo "$content"
  fi
  
  echo -e "\n-----------------------------------------------\n"
}

echo -e "${GREEN}========== MongoDB YFinance API Testing ===========${NC}"
echo -e "Testing date: $(date)"
echo -e "-----------------------------------------------\n"

# Test local endpoints
if $TEST_LOCAL; then
  echo -e "${GREEN}Testing Local Endpoints${NC}"
  echo -e "-----------------------------------------------\n"
  
  # Test health endpoint
  test_endpoint "${LOCAL_API}/health" "Local Health Check"
  
  # Test quotes endpoint
  test_endpoint "${LOCAL_API}/api/quotes" "Local Multiple Quotes"
  
  # Test single quote endpoint
  test_endpoint "${LOCAL_API}/api/quote/AAPL" "Local Single Quote (AAPL)"
  
  # Test historical data endpoint
  test_endpoint "${LOCAL_API}/api/historical/AAPL?days=10" "Local Historical Data (AAPL, 10 days)"
  
  # Test MongoDB status (this is specific to the MongoDB version)
  test_endpoint "${LOCAL_API}/health" "Local MongoDB Connection Status"
fi

# Test production endpoints
if $TEST_PROD; then
  echo -e "${GREEN}Testing Production Endpoints${NC}"
  echo -e "-----------------------------------------------\n"
  
  # Test health endpoint
  test_endpoint "${PROD_API}/health" "Production Health Check"
  
  # Test quotes endpoint
  test_endpoint "${PROD_API}/quotes" "Production Multiple Quotes"
  
  # Test single quote endpoint
  test_endpoint "${PROD_API}/quote/AAPL" "Production Single Quote (AAPL)"
  
  # Test historical endpoint
  test_endpoint "https://${PRODUCTION_DOMAIN}/api/historical/AAPL?days=10" "Production Historical Data (AAPL, 10 days)"
fi

echo -e "${GREEN}========== Testing Completed ===========${NC}" 