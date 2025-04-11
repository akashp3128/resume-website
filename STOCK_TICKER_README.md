# Stock Ticker Feature Documentation

This document explains how to run the resume website with the stock ticker feature.

## Overview

The stock ticker displays real-time or simulated market data for:
- BTC-USD (Bitcoin)
- SPY (S&P 500 ETF)
- GME (GameStop)
- AAPL (Apple)
- MSFT (Microsoft)
- NVDA (NVIDIA)
- XRP-USD (Ripple)
- META (Meta/Facebook)
- TSLA (Tesla)
- GOOGL (Google)
- PLTR (Palantir)

## Running the Website Locally

### Option 1: Use the restart_servers.sh Script (Recommended)

This script handles all necessary setup and ensures the stock ticker works correctly:

```bash
# Make the script executable if needed
chmod +x restart_servers.sh

# Run the script
./restart_servers.sh
```

The server will start at:
- HTTP Server: http://localhost:8000
- Upload Server: http://localhost:8001

### Option 2: Manual Startup

If you prefer to start servers manually:

1. Create upload directories:
```bash
mkdir -p uploads/resume uploads/eval uploads/photo
```

2. Start the HTTP server:
```bash
python3 -m http.server 8000
```

3. In a separate terminal, start the upload server:
```bash
cd upload-handler
python3 upload_server.py
```

## Troubleshooting the Stock Ticker

If the stock ticker isn't working:

1. Check browser console for errors

2. Verify script paths:
   - In the main directory: `stock-ticker.js`
   - In the public/js directory: `stock-ticker.js`

3. Try the fallback implementation:
   - If the main ticker fails due to API limitations, it will automatically switch to a backup mode

4. Refresh at intervals:
   - The ticker tries to fetch fresh data every 2 minutes
   - If API calls fail three times, it switches to simulated data

## API Information

The stock ticker uses the Alpha Vantage API with the following limitations:
- Free tier: 5 API calls per minute, 500 per day
- Due to these limitations, we only fetch data for a subset of stocks
- The script falls back to simulated data if API calls fail

## Customizing the Stock Ticker

To modify the displayed stocks:
1. Edit `public/js/stock-ticker.js`
2. Update the `STOCK_SYMBOLS` array at the top of the file
3. Update the mock data entries in `populateTickerWithMockData()` and `getMockEntryForSymbol()`

## Design Notes

The stock ticker includes several resilience features:
- Immediate display using mock data while API calls are in progress
- Fallback to simulated data if API calls fail
- Visual consistency between real and simulated data
- Automatic refresh at regular intervals 