# MongoDB-Backed Stock Ticker Backend

This repository contains a MongoDB-backed stock data server for displaying live stock and cryptocurrency prices.

## Key Features

- Live stock and crypto price data via YFinance API
- Data persistence with MongoDB
- Historical price tracking
- Caching for performance
- Fallback to in-memory cache if MongoDB is unavailable
- Nginx proxy configuration for production deployment

## Files

- `stock-data-server-mongodb.py` - The main backend server with MongoDB integration
- `deploy-mongodb-yfinance-backend.sh` - Deployment script for production servers
- `test-mongodb-yfinance-api.sh` - Testing script for API endpoints

## Setup for Development

### Prerequisites

- Python 3.x
- MongoDB

### Local Development Setup

1. Install required packages:

```bash
pip install pymongo yfinance
```

2. Start MongoDB locally:

```bash
# On macOS with Homebrew
brew services start mongodb-community

# On Linux
sudo systemctl start mongod
```

3. Run the stock data server:

```bash
python stock-data-server-mongodb.py
```

4. Test the API endpoints:

```bash
./test-mongodb-yfinance-api.sh --local
```

## Production Deployment

1. Upload the files to your production server:

```bash
scp stock-data-server-mongodb.py deploy-mongodb-yfinance-backend.sh test-mongodb-yfinance-api.sh yourusername@your-server-ip:~/
```

2. SSH into your server and run the deployment script:

```bash
cd ~/
chmod +x deploy-mongodb-yfinance-backend.sh test-mongodb-yfinance-api.sh
sudo ./deploy-mongodb-yfinance-backend.sh
```

3. Follow the instructions provided by the deployment script to:
   - Include the Nginx configuration snippet
   - Test and reload Nginx
   - Verify the service is running

4. Test your production API:

```bash
./test-mongodb-yfinance-api.sh --prod
```

## API Endpoints

- `GET /health` - Health check and MongoDB connection status
- `GET /api/quotes` - Get quotes for all configured symbols
- `GET /api/quotes?symbols=AAPL,MSFT,GOOGL` - Get quotes for specific symbols
- `GET /api/quote/AAPL` - Get a quote for a single symbol
- `GET /api/historical/AAPL?days=30` - Get historical data for a symbol

## Data Storage

The MongoDB database uses two collections:

1. `current_prices` - Stores the latest price data for each symbol
2. `historical_prices` - Stores historical price data with timestamps

## Environment Variables

- `MONGO_URI` - MongoDB connection URI (default: `mongodb://localhost:27017/`)

## Troubleshooting

### MongoDB Issues

If MongoDB doesn't connect:

```bash
# Check MongoDB status
sudo systemctl status mongod

# Check MongoDB logs
sudo journalctl -u mongod

# Restart MongoDB
sudo systemctl restart mongod
```

### Service Issues

If the stock data server isn't working:

```bash
# Check service status
sudo systemctl status mongodb-yfinance-backend

# View service logs
sudo journalctl -u mongodb-yfinance-backend

# Restart the service
sudo systemctl restart mongodb-yfinance-backend
```

### Nginx Issues

Check Nginx configuration:

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log
``` 