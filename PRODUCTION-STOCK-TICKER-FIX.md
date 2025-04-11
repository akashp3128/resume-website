# Production Stock Ticker Fix

## Problem Identified

The stock ticker on your website shows static data in production but works correctly in local development. This is happening because:

1. In local development, the frontend connects directly to the backend at `http://localhost:3000`
2. In production, the frontend attempts to use the relative path `/api/yfinance/*`
3. The Nginx server isn't correctly configured to proxy these requests to the backend
4. The YFinance backend service might not be running in production

## How the Stock Ticker Should Work

1. The JavaScript ticker (`isolated-stock-ticker.js`) tries to fetch data from `/api/yfinance/*` in production
2. Nginx should proxy these requests to the backend service running on port 3000
3. The backend service (powered by `stock-data-server.py`) fetches real-time data using the YFinance library

## Quick Fix Solution

We've created a fix script that automates the entire process. To use it:

1. Upload these files to your production server:
   - `stock-data-server.py`
   - `deploy-yfinance-backend.sh`
   - `test-yfinance-api.sh`
   - `fix-production-stock-ticker.sh`

2. SSH into your server and run:
   ```bash
   chmod +x fix-production-stock-ticker.sh
   sudo ./fix-production-stock-ticker.sh
   ```

3. The script will:
   - Install the YFinance backend service
   - Configure Nginx to proxy requests correctly
   - Test both local and production endpoints

## Manual Fix Steps

If you prefer to do it manually, follow these steps:

### 1. Install and Configure the YFinance Backend

```bash
# Make the script executable
chmod +x deploy-yfinance-backend.sh

# Run the deployment script
sudo ./deploy-yfinance-backend.sh
```

### 2. Configure Nginx

Add this to your Nginx site configuration:

```nginx
include /etc/nginx/conf.d/yfinance-proxy.conf;
```

Test and reload Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Test the API Endpoints

```bash
# Test local endpoints
curl http://localhost:3000/health
curl http://localhost:3000/api/quotes

# Test production endpoints
curl https://yourdomain.com/api/yfinance/health
curl https://yourdomain.com/api/yfinance/quotes
```

## Troubleshooting

If you still have issues after running the fix:

1. **Check if the backend service is running:**
   ```bash
   sudo systemctl status yfinance-backend
   ```

2. **View the service logs:**
   ```bash
   sudo journalctl -u yfinance-backend
   ```

3. **Check Nginx error logs:**
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

4. **Verify the Nginx configuration:**
   Make sure the proxy configuration is included in your site config and that it's correctly forwarding requests.

5. **Test endpoints directly:**
   ```bash
   # Local backend:
   curl http://localhost:3000/health
   
   # Through the proxy:
   curl https://yourdomain.com/api/yfinance/health
   ```

6. **Firewall configuration:**
   Make sure your firewall allows Nginx to access the backend on port 3000:
   ```bash
   sudo ufw allow 'Nginx Full'  # Allow HTTP/HTTPS
   sudo ufw deny 3000           # Block external access to the backend
   ```

## How It Works

- The Nginx config in `/etc/nginx/conf.d/yfinance-proxy.conf` contains:
  ```nginx
  location /api/yfinance/ {
      # Remove /api/yfinance prefix when forwarding to backend
      rewrite ^/api/yfinance/(.*) /$1 break;
      
      # Proxy to local backend on port 3000
      proxy_pass http://localhost:3000/;
      proxy_http_version 1.1;
      # Additional proxy settings...
  }
  ```

- This configuration strips the `/api/yfinance` prefix from incoming requests and forwards them to the backend service running on port 3000.

- The JavaScript file `public/js/isolated-stock-ticker.js` is already configured to use the correct paths:
  ```javascript
  const API_PATH = '/api/yfinance';  // Used in production
  const BACKEND_URL = isLocalHost ? 'http://localhost:3000' : API_PATH;
  ``` 