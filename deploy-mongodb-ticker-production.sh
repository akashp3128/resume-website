#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Server details
echo -e "${YELLOW}Please provide your server details:${NC}"
read -p "Username: " USERNAME
read -p "Server IP: " SERVER_IP
read -p "Server directory (default: ~/): " SERVER_DIR

# Use default if not provided
if [ -z "$SERVER_DIR" ]; then
    SERVER_DIR="~/"
fi

# Files to deploy
FILES=(
    "stock-data-server-mongodb.py"
    "start-mongodb-ticker.sh"
    "run-mongodb-ticker-locally.sh"
)

echo -e "${GREEN}Preparing to deploy MongoDB stock ticker to production...${NC}"

# Create a temporary installation script
TEMP_SCRIPT=$(mktemp)
cat > "$TEMP_SCRIPT" << 'EOF'
#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up MongoDB Stock Ticker on production server...${NC}"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Installing...${NC}"
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip
fi

# Install required packages
echo -e "${YELLOW}Installing required Python packages...${NC}"
python3 -m pip install pymongo yfinance --user

# Check for MongoDB
if ! command -v mongod &> /dev/null; then
    echo -e "${YELLOW}MongoDB is not installed. Installing...${NC}"
    
    # Import MongoDB GPG key
    curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
        sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
        --dearmor
    
    # Add MongoDB repository
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | \
        sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    
    # Update and install MongoDB
    sudo apt-get update
    sudo apt-get install -y mongodb-org
    
    # Start MongoDB
    sudo systemctl start mongod
    sudo systemctl enable mongod
fi

# Check if MongoDB is running
if ! systemctl is-active --quiet mongod; then
    echo -e "${RED}MongoDB is not running. Starting...${NC}"
    sudo systemctl start mongod
    sudo systemctl enable mongod
fi

# Make scripts executable
chmod +x stock-data-server-mongodb.py
chmod +x start-mongodb-ticker.sh
chmod +x run-mongodb-ticker-locally.sh

# Setup systemd service
echo -e "${YELLOW}Setting up systemd service...${NC}"

# Create systemd service file
sudo bash -c 'cat > /etc/systemd/system/mongodb-stock-ticker.service << EOL
[Unit]
Description=MongoDB Stock Ticker Service
After=network.target mongod.service

[Service]
ExecStart=/usr/bin/python3 %h/stock-data-server-mongodb.py
WorkingDirectory=%h
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=mongodb-stock-ticker
User=$USER

[Install]
WantedBy=multi-user.target
EOL'

# Reload systemd
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable mongodb-stock-ticker
sudo systemctl start mongodb-stock-ticker

# Set up Nginx reverse proxy if available
if command -v nginx &> /dev/null; then
    echo -e "${YELLOW}Setting up Nginx reverse proxy...${NC}"
    
    # Create Nginx config file
    sudo bash -c 'cat > /etc/nginx/conf.d/stock-ticker.conf << EOL
server {
    listen 80;
    
    location /api/yfinance/ {
        proxy_pass http://localhost:3000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOL'
    
    # Test Nginx config
    sudo nginx -t
    
    # Reload Nginx if config test passes
    if [ $? -eq 0 ]; then
        sudo systemctl reload nginx
        echo -e "${GREEN}Nginx proxy configured successfully.${NC}"
    else
        echo -e "${RED}Nginx config test failed. Please check your Nginx setup.${NC}"
    fi
else
    echo -e "${YELLOW}Nginx not installed. Skipping proxy setup.${NC}"
    echo -e "${YELLOW}You'll need to configure your web server to proxy requests from /api/yfinance/ to http://localhost:3000/${NC}"
fi

echo -e "${GREEN}MongoDB Stock Ticker deployed successfully!${NC}"
echo -e "${YELLOW}The service is running at http://localhost:3000/${NC}"
echo -e "${YELLOW}It can be accessed via the proxy at /api/yfinance/ if Nginx is configured.${NC}"
echo -e ""
echo -e "${YELLOW}To check the status:${NC} sudo systemctl status mongodb-stock-ticker"
echo -e "${YELLOW}To restart:${NC} sudo systemctl restart mongodb-stock-ticker"
echo -e "${YELLOW}To view logs:${NC} sudo journalctl -u mongodb-stock-ticker"
EOF

# Make the temp script executable
chmod +x "$TEMP_SCRIPT"

# Transfer files to the server
echo -e "${YELLOW}Transferring files to the server...${NC}"
scp "${FILES[@]}" "$TEMP_SCRIPT" "$USERNAME@$SERVER_IP:$SERVER_DIR"

# Run the installation script on the server
echo -e "${YELLOW}Running installation script on the server...${NC}"
ssh "$USERNAME@$SERVER_IP" "cd $SERVER_DIR && bash $(basename "$TEMP_SCRIPT")"

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${YELLOW}Your MongoDB Stock Ticker is now running on the production server.${NC}"
echo -e ""
echo -e "${YELLOW}To verify it's working, run:${NC}"
echo -e "${GREEN}  curl http://$SERVER_IP:3000/health${NC}"
echo -e ""
echo -e "${YELLOW}For any issues, check the logs on the server:${NC}"
echo -e "${GREEN}  sudo journalctl -u mongodb-stock-ticker${NC}"

# Clean up
rm "$TEMP_SCRIPT" 