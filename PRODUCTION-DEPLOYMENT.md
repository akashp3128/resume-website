# Production Deployment Guide

This guide explains how to deploy the YFinance stock ticker backend on your production server and configure Nginx to proxy requests correctly.

## Overview

The stock ticker on the main website tries to connect to a backend API to get real-time stock data. On localhost, it connects directly to `http://localhost:3000`, but on the production server, it uses a relative path `/api/yfinance/*` that needs to be proxied to the backend.

## Setup Steps

### 1. Deploy the YFinance Backend

1. Copy the `stock-data-server.py` script to your production server.

2. Make it executable:
   ```bash
   chmod +x stock-data-server.py
   ```

3. Install the required dependencies:
   ```bash
   pip3 install yfinance --user
   ```

4. Set up a systemd service to keep it running:
   ```bash
   sudo nano /etc/systemd/system/yfinance-backend.service
   ```

5. Add the following content (adjust paths as needed):
   ```
   [Unit]
   Description=YFinance Stock Ticker Backend
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/var/www/akashpatelresume.us
   ExecStart=/var/www/akashpatelresume.us/stock-data-server.py
   Restart=always
   RestartSec=5
   StandardOutput=syslog
   StandardError=syslog
   SyslogIdentifier=yfinance-backend

   [Install]
   WantedBy=multi-user.target
   ```

6. Enable and start the service:
   ```bash
   sudo systemctl enable yfinance-backend
   sudo systemctl start yfinance-backend
   ```

7. Check that it's running:
   ```bash
   sudo systemctl status yfinance-backend
   curl http://localhost:3000/health
   ```

### 2. Configure Nginx as a Proxy

1. Copy the provided Nginx configuration to your server:
   ```bash
   sudo cp nginx_config/nginx_yfinance_proxy.conf /etc/nginx/sites-available/akashpatelresume.us
   ```

2. If you already have a configuration, you can just add the proxy section:
   ```
   # Proxy for YFinance backend API
   location /api/yfinance/ {
       # Remove /api/yfinance prefix when forwarding to backend
       rewrite ^/api/yfinance/(.*) /$1 break;
       
       # Proxy to local backend on port 3000
       proxy_pass http://localhost:3000/;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection 'upgrade';
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_cache_bypass $http_upgrade;
       
       # Set response headers
       add_header 'Access-Control-Allow-Origin' '*';
       add_header 'Access-Control-Allow-Methods' 'GET, OPTIONS';
       add_header 'Access-Control-Allow-Headers' 'Content-Type';
   }
   ```

3. Test your Nginx configuration:
   ```bash
   sudo nginx -t
   ```

4. Reload Nginx:
   ```bash
   sudo systemctl reload nginx
   ```

5. Test the proxy:
   ```bash
   curl https://akashpatelresume.us/api/yfinance/health
   ```

### 3. Firewall Configuration

Make sure your firewall allows Nginx (ports 80 and 443), but blocks direct access to port 3000 from the internet:

```bash
sudo ufw allow 'Nginx Full'
sudo ufw deny 3000
sudo ufw status
```

## Troubleshooting

1. **Backend not running**: Check the systemd service status:
   ```bash
   sudo systemctl status yfinance-backend
   sudo journalctl -u yfinance-backend
   ```

2. **Proxy not working**: Check Nginx error logs:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. **CORS issues**: Verify the Access-Control-Allow-Origin headers are being set correctly:
   ```bash
   curl -I https://akashpatelresume.us/api/yfinance/health
   ```

## Testing the Deployment

Once everything is set up, visit your website and verify that the stock ticker is showing the current prices. You can check the browser console for any errors or messages related to the stock ticker. 