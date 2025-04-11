#!/bin/bash
set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting deployment of MongoDB-backed YFinance backend...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root or with sudo${NC}"
  exit 1
fi

# Install MongoDB if not already installed
if ! command -v mongod &> /dev/null; then
    echo -e "${YELLOW}MongoDB not found. Installing MongoDB...${NC}"
    # Import MongoDB GPG key
    apt-get update
    apt-get install -y gnupg
    wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add -
    
    # Create list file for MongoDB
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list
    
    # Install MongoDB
    apt-get update
    apt-get install -y mongodb-org
    
    # Start MongoDB and enable on boot
    systemctl daemon-reload
    systemctl start mongod
    systemctl enable mongod
    
    echo -e "${GREEN}MongoDB installed and started successfully.${NC}"
else
    echo -e "${GREEN}MongoDB is already installed.${NC}"
fi

# Check if MongoDB is running
if ! systemctl is-active --quiet mongod; then
    echo -e "${YELLOW}MongoDB is not running. Starting...${NC}"
    systemctl start mongod
    echo -e "${GREEN}MongoDB started.${NC}"
else
    echo -e "${GREEN}MongoDB is already running.${NC}"
fi

# Install required Python packages
echo -e "${YELLOW}Installing required Python packages...${NC}"
apt-get update
apt-get install -y python3 python3-pip

# Install required Python packages globally
pip3 install pymongo yfinance

# Create a directory for the backend
echo -e "${YELLOW}Creating directory for the backend...${NC}"
mkdir -p /opt/yfinance-backend

# Copy the backend script to the directory
echo -e "${YELLOW}Copying files...${NC}"
cp stock-data-server-mongodb.py /opt/yfinance-backend/
chmod +x /opt/yfinance-backend/stock-data-server-mongodb.py

# Create a systemd service file
echo -e "${YELLOW}Creating systemd service...${NC}"
cat > /etc/systemd/system/mongodb-yfinance-backend.service << 'EOF'
[Unit]
Description=MongoDB-backed YFinance Stock Data Server
After=network.target mongod.service
Requires=mongod.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/yfinance-backend
ExecStart=/usr/bin/python3 /opt/yfinance-backend/stock-data-server-mongodb.py
Restart=always
RestartSec=5
Environment=MONGO_URI=mongodb://localhost:27017/

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd, enable and start the service
echo -e "${YELLOW}Starting the service...${NC}"
systemctl daemon-reload
systemctl enable mongodb-yfinance-backend
systemctl restart mongodb-yfinance-backend

# Create Nginx configuration to proxy requests
echo -e "${YELLOW}Creating Nginx proxy configuration...${NC}"
cat > /etc/nginx/conf.d/mongodb-yfinance-proxy.conf << 'EOF'
# YFinance API proxy for stock ticker
location /api/yfinance/ {
    proxy_pass http://localhost:3000/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
    proxy_read_timeout 300s;
}

location /api/historical/ {
    proxy_pass http://localhost:3000/api/historical/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
    proxy_read_timeout 300s;
}
EOF

echo -e "${GREEN}Deployment completed.${NC}"
echo -e "${YELLOW}======================================================================${NC}"
echo -e "${YELLOW}Important:${NC}"
echo -e "1. Ensure you include the Nginx configuration in your site configuration:"
echo -e "   ${GREEN}include /etc/nginx/conf.d/mongodb-yfinance-proxy.conf;${NC}"
echo -e "   Add this line inside your server block in Nginx configuration."
echo -e ""
echo -e "2. Test and reload Nginx:"
echo -e "   ${GREEN}nginx -t${NC}"
echo -e "   ${GREEN}systemctl reload nginx${NC}"
echo -e ""
echo -e "3. Check the service status:"
echo -e "   ${GREEN}systemctl status mongodb-yfinance-backend${NC}"
echo -e ""
echo -e "4. Check MongoDB status:"
echo -e "   ${GREEN}systemctl status mongod${NC}"
echo -e ""
echo -e "5. View logs:"
echo -e "   ${GREEN}journalctl -u mongodb-yfinance-backend -f${NC}"
echo -e "${YELLOW}======================================================================${NC}" 