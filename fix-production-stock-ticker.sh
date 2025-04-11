#!/bin/bash

# Fix Stock Ticker in Production
# This script follows the instructions in FIX-STOCK-TICKER-PRODUCTION.md to fix the stock ticker in production
# It will install and configure the YFinance backend service and configure Nginx to proxy requests

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}    Fix Stock Ticker in Production               ${NC}"
echo -e "${BLUE}==================================================${NC}"

# This script must be run with root privileges to configure system services
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}This script requires root privileges to install system services.${NC}"
    echo -e "${YELLOW}Please run with sudo:${NC}"
    echo -e "${GREEN}sudo ./fix-production-stock-ticker.sh${NC}"
    exit 1
fi

# Step 1: Check if the required files exist
echo -e "${GREEN}Checking for required files...${NC}"
required_files=(
    "stock-data-server.py"
    "deploy-yfinance-backend.sh"
    "test-yfinance-api.sh"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: $file not found in the current directory.${NC}"
        exit 1
    fi
done

echo -e "${GREEN}All required files found.${NC}"

# Step 2: Make the scripts executable
echo -e "${GREEN}Making scripts executable...${NC}"
chmod +x stock-data-server.py deploy-yfinance-backend.sh test-yfinance-api.sh

# Step 3: Run the deployment script
echo -e "${GREEN}Running the deployment script...${NC}"
./deploy-yfinance-backend.sh

# Step 4: Verify that the service is running
echo -e "${GREEN}Verifying that the YFinance backend service is running...${NC}"
if ! systemctl is-active --quiet yfinance-backend; then
    echo -e "${RED}Error: YFinance backend service is not running.${NC}"
    echo -e "${YELLOW}Attempting to start the service...${NC}"
    systemctl start yfinance-backend
    
    if ! systemctl is-active --quiet yfinance-backend; then
        echo -e "${RED}Error: Failed to start YFinance backend service.${NC}"
        echo -e "${YELLOW}Checking service status...${NC}"
        systemctl status yfinance-backend
        exit 1
    fi
fi

echo -e "${GREEN}YFinance backend service is running.${NC}"

# Step 5: Verify that Nginx is configured correctly
echo -e "${GREEN}Verifying Nginx configuration...${NC}"
NGINX_CONF_DIR="/etc/nginx/conf.d"
NGINX_CONF_FILE="${NGINX_CONF_DIR}/yfinance-proxy.conf"

if [ ! -f "$NGINX_CONF_FILE" ]; then
    echo -e "${RED}Error: Nginx configuration file not found.${NC}"
    exit 1
fi

echo -e "${GREEN}Checking server configuration to see if the proxy is included...${NC}"
NGINX_CONFIG_INCLUDED=$(grep -r "include.*yfinance-proxy.conf" /etc/nginx/sites-enabled/)

if [ -z "$NGINX_CONFIG_INCLUDED" ]; then
    echo -e "${YELLOW}Warning: Nginx configuration not included in any site.${NC}"
    echo -e "${YELLOW}Please add the following line to your Nginx site configuration:${NC}"
    echo -e "${BLUE}include /etc/nginx/conf.d/yfinance-proxy.conf;${NC}"
    
    # Ask if they want to automatically add it to the default site
    echo -e "${YELLOW}Do you want to automatically add it to the default site? (y/n)${NC}"
    read -r ADD_TO_DEFAULT
    
    if [[ "$ADD_TO_DEFAULT" =~ ^[Yy]$ ]]; then
        # Find the server block in the default site
        DEFAULT_SITE="/etc/nginx/sites-enabled/default"
        
        if [ ! -f "$DEFAULT_SITE" ]; then
            echo -e "${RED}Error: Default site configuration not found.${NC}"
            exit 1
        fi
        
        # Add the include line before the closing bracket of the server block
        sed -i '/server {/,/}/{s/}/include \/etc\/nginx\/conf.d\/yfinance-proxy.conf;\n}/}' "$DEFAULT_SITE"
        
        echo -e "${GREEN}Added configuration to default site.${NC}"
    else
        echo -e "${YELLOW}Please manually add the include line to your site configuration.${NC}"
    fi
fi

# Step 6: Test Nginx configuration
echo -e "${GREEN}Testing Nginx configuration...${NC}"
if ! nginx -t; then
    echo -e "${RED}Error: Nginx configuration test failed.${NC}"
    exit 1
fi

# Step 7: Reload Nginx
echo -e "${GREEN}Reloading Nginx...${NC}"
if ! systemctl reload nginx; then
    echo -e "${RED}Error: Failed to reload Nginx.${NC}"
    exit 1
fi

# Step 8: Test the API endpoints
echo -e "${GREEN}Testing API endpoints...${NC}"
echo -e "${YELLOW}Local health check:${NC}"
curl -s http://localhost:3000/health
echo -e "\n\n${YELLOW}Local quotes API:${NC}"
curl -s http://localhost:3000/api/quotes | head -c 200
echo -e "\n\n${YELLOW}Production health check:${NC}"
DOMAIN=$(grep -oP "PRODUCTION_API=\"\K[^/]+" test-yfinance-api.sh)
if [ -z "$DOMAIN" ]; then
    echo -e "${RED}Error: Could not determine domain from test script.${NC}"
    echo -e "${YELLOW}Please enter your domain name (e.g., example.com):${NC}"
    read -r DOMAIN
fi

curl -s "https://$DOMAIN/api/yfinance/health"
echo -e "\n\n${YELLOW}Production quotes API:${NC}"
curl -s "https://$DOMAIN/api/yfinance/quotes" | head -c 200
echo -e "\n"

# Provide troubleshooting info
echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}Setup complete!${NC}"
echo -e "${BLUE}==================================================${NC}"
echo -e "${YELLOW}If you still have issues:${NC}"
echo -e "1. Check the YFinance backend service logs:"
echo -e "${GREEN}   journalctl -u yfinance-backend${NC}"
echo -e "2. Check the Nginx logs:"
echo -e "${GREEN}   tail -f /var/log/nginx/error.log${NC}"
echo -e "3. Make sure your firewall allows Nginx to access the backend:"
echo -e "${GREEN}   sudo ufw allow 'Nginx Full'${NC}"
echo -e "${GREEN}   sudo ufw deny 3000${NC} (only block external access, not internal)"
echo -e "4. Test the API endpoints directly:"
echo -e "${GREEN}   curl http://localhost:3000/health${NC}"
echo -e "${GREEN}   curl http://localhost:3000/api/quotes${NC}"
echo -e "${GREEN}   curl https://$DOMAIN/api/yfinance/health${NC}"
echo -e "${GREEN}   curl https://$DOMAIN/api/yfinance/quotes${NC}"

exit 0 