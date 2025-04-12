#!/bin/bash

# Crypto Server Deployment Script
# Handles starting, stopping, and monitoring the crypto data server

# Configuration
SERVER_SCRIPT="crypto-data-server.py"
PID_FILE="/tmp/crypto-server.pid"
LOG_FILE="/tmp/crypto-server.log"
MONGO_URI="mongodb://localhost:27017/"
PORT=3003
HEALTH_CHECK_URL="http://localhost:${PORT}/health"
HEALTH_CHECK_TIMEOUT=5
CACHE_DURATION=600  # 10 minutes to reduce API hit rate
RATE_LIMIT_COOLDOWN=300  # 5 minutes cooldown if we hit rate limits
RETRY_ATTEMPTS=5  # More retries for API

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if required dependencies are installed
check_dependencies() {
    echo -e "${BLUE}Checking dependencies...${NC}"
    
    # Check for Python3
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python3 is required but not installed${NC}"
        exit 1
    fi
    
    # Check for pip and required packages
    if ! python3 -m pip --version &> /dev/null; then
        echo -e "${RED}Error: pip is required but not installed${NC}"
        exit 1
    fi
    
    # Check for virtual environment
    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}Virtual environment not found, creating one...${NC}"
        python3 -m venv .venv
        echo -e "${GREEN}Virtual environment created at .venv${NC}"
        echo -e "${YELLOW}Activating virtual environment...${NC}"
        source .venv/bin/activate
        echo -e "${GREEN}Virtual environment activated${NC}"
    else
        echo -e "${GREEN}Using existing virtual environment${NC}"
        source .venv/bin/activate
    fi
    
    # Check for required packages
    echo -e "${BLUE}Ensuring required packages are installed...${NC}"
    python3 -m pip install -r requirements.txt
    
    # Check if MongoDB is running
    if ! pgrep -x "mongod" > /dev/null; then
        echo -e "${YELLOW}Warning: MongoDB doesn't appear to be running${NC}"
        echo -e "You can start MongoDB with: brew services start mongodb-community"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo -e "${GREEN}MongoDB is running${NC}"
    fi
}

# Find if the server is already running
find_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null; then
            return 0 # Server is running
        fi
    fi
    
    # Alternative check using pgrep
    PID=$(pgrep -f "$SERVER_SCRIPT")
    if [ -n "$PID" ]; then
        echo $PID > "$PID_FILE"
        return 0 # Server is running
    fi
    
    return 1 # Server is not running
}

# Stop the server
stop_server() {
    echo -e "${BLUE}Stopping crypto server...${NC}"
    
    if find_server; then
        PID=$(cat "$PID_FILE")
        echo -e "Stopping server process (PID: $PID)..."
        kill "$PID"
        
        # Wait for process to terminate
        for i in {1..10}; do
            if ! ps -p "$PID" > /dev/null; then
                echo -e "${GREEN}Server stopped successfully${NC}"
                rm -f "$PID_FILE"
                return 0
            fi
            sleep 1
        done
        
        # Force kill if normal kill didn't work
        echo -e "${YELLOW}Server didn't stop gracefully, force killing...${NC}"
        kill -9 "$PID"
        rm -f "$PID_FILE"
        echo -e "${GREEN}Server stopped forcefully${NC}"
    else
        echo -e "${YELLOW}No running server found${NC}"
    fi
}

# Start the server
start_server() {
    echo -e "${BLUE}Starting crypto server...${NC}"
    
    # First check if server is already running
    if find_server; then
        echo -e "${YELLOW}Server is already running with PID $(cat $PID_FILE)${NC}"
        return 1
    fi
    
    # Ensure virtual environment is activated
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    # Ensure script is executable
    chmod +x "$SERVER_SCRIPT"
    
    # Start the server with MongoDB configuration
    echo -e "Starting server with MongoDB at $MONGO_URI..."
    
    # Export environment variables for the server
    export MONGO_URI="$MONGO_URI"
    export PORT="$PORT"
    export CACHE_DURATION="$CACHE_DURATION"
    export RATE_LIMIT_COOLDOWN="$RATE_LIMIT_COOLDOWN"
    export RETRY_ATTEMPTS="$RETRY_ATTEMPTS"
    
    # Run server in background with output to logfile
    nohup python3 "$SERVER_SCRIPT" > "$LOG_FILE" 2>&1 &
    
    # Save PID
    echo $! > "$PID_FILE"
    echo -e "${GREEN}Server started with PID $!${NC}"
    
    # Wait a moment for server to initialize
    sleep 3
    
    # Check if server is healthy
    if check_server_health; then
        echo -e "${GREEN}Server started successfully and is healthy${NC}"
        return 0
    else
        echo -e "${RED}Server started but health check failed${NC}"
        echo -e "Check logs with: $0 logs"
        return 1
    fi
}

# Restart the server
restart_server() {
    echo -e "${BLUE}Restarting crypto server...${NC}"
    stop_server
    sleep 2
    start_server
}

# Check server status
status_server() {
    echo -e "${BLUE}Checking crypto server status...${NC}"
    
    if find_server; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}Server is running with PID $PID${NC}"
        
        # Check server health
        if check_server_health; then
            echo -e "${GREEN}Server health check passed${NC}"
        else
            echo -e "${RED}Server is running but health check failed${NC}"
        fi
    else
        echo -e "${YELLOW}Server is not running${NC}"
    fi
}

# Check server health via HTTP request
check_server_health() {
    echo -e "Performing health check at $HEALTH_CHECK_URL..."
    
    local health_response
    health_response=$(curl -s -m $HEALTH_CHECK_TIMEOUT "$HEALTH_CHECK_URL")
    local curl_status=$?
    
    if [ $curl_status -eq 0 ] && [[ "$health_response" == *"status"*"ok"* ]]; then
        # Parse and display rate limit info if available
        if [[ "$health_response" == *"rate_limit_reset"* ]]; then
            # Extract rate_limit as a number or default to 0
            local rate_limit=$(echo "$health_response" | grep -o '"rate_limit_reset":[0-9.]*' | cut -d':' -f2 | tr -d ',' || echo "0")
            # Ensure it's a number
            if [[ "$rate_limit" =~ ^[0-9.]+$ ]] && [ "$(echo "$rate_limit > 0" | bc -l)" -eq 1 ]; then
                echo -e "${YELLOW}API rate limit in effect, resets in $rate_limit seconds${NC}"
            fi
        fi
        return 0
    else
        echo -e "${RED}Health check failed${NC}"
        if [ $curl_status -ne 0 ]; then
            echo -e "Curl error: $curl_status - server may not be responding"
        else
            echo -e "Unexpected response: $health_response"
        fi
        return 1
    fi
}

# Show server logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo -e "${BLUE}Showing last 50 lines of server logs:${NC}"
        tail -n 50 "$LOG_FILE"
    else
        echo -e "${YELLOW}No log file found at $LOG_FILE${NC}"
    fi
}

# Deploy with docker
deploy_docker() {
    echo -e "${BLUE}Deploying crypto server with Docker...${NC}"
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is required but not installed${NC}"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Error: Docker Compose is required but not installed${NC}"
        exit 1
    fi
    
    # Start the services
    echo -e "Starting Docker containers..."
    docker-compose up -d
    
    # Check if the containers are running
    if docker-compose ps | grep -q "crypto-data-server"; then
        echo -e "${GREEN}Docker containers started successfully${NC}"
        echo -e "To check container logs, run: docker-compose logs -f crypto-data-server"
        
        # Wait a moment for health checks
        echo -e "Waiting for services to be healthy..."
        sleep 10
        
        # Check server health
        if curl -s -m $HEALTH_CHECK_TIMEOUT "$HEALTH_CHECK_URL" | grep -q "\"status\":\"ok\""; then
            echo -e "${GREEN}Server health check passed${NC}"
            return 0
        else
            echo -e "${RED}Server health check failed${NC}"
            echo -e "Check container logs with: docker-compose logs -f crypto-data-server"
            return 1
        fi
    else
        echo -e "${RED}Failed to start Docker containers${NC}"
        echo -e "Check docker logs with: docker-compose logs"
        return 1
    fi
}

# Stop Docker containers
stop_docker() {
    echo -e "${BLUE}Stopping Docker containers...${NC}"
    docker-compose down
    echo -e "${GREEN}Docker containers stopped${NC}"
}

# Print usage information
print_usage() {
    echo -e "${BLUE}Crypto Server Deployment Script${NC}"
    echo -e "Usage: $0 [command]"
    echo -e ""
    echo -e "Available commands:"
    echo -e "  start   - Start the crypto server locally"
    echo -e "  stop    - Stop the crypto server"
    echo -e "  restart - Restart the crypto server"
    echo -e "  status  - Check server status and health"
    echo -e "  logs    - Show server logs"
    echo -e "  health  - Run a health check against the server"
    echo -e "  docker  - Deploy with Docker Compose"
    echo -e "  docker-stop - Stop Docker containers"
    echo -e ""
}

# Main script logic
case "$1" in
    start)
        check_dependencies
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        status_server
        ;;
    logs)
        show_logs
        ;;
    health)
        if check_server_health; then
            echo -e "${GREEN}Server health check passed${NC}"
        else
            echo -e "${RED}Server health check failed${NC}"
        fi
        ;;
    docker)
        deploy_docker
        ;;
    docker-stop)
        stop_docker
        ;;
    *)
        print_usage
        ;;
esac

exit 0 