# Isolated Stock Ticker Branch

This branch contains an isolated implementation of the stock ticker feature, allowing for focused development without affecting the main website.

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

## Quick Start

To run the isolated stock ticker demo:

```bash
# Make the script executable if needed
chmod +x run-isolated-ticker.sh

# Run the isolated ticker demo
./run-isolated-ticker.sh
```

Then visit http://localhost:8000/isolated-ticker.html in your browser.

## Files in this Branch

- `isolated-ticker.html` - Standalone HTML page with the ticker component
- `public/js/isolated-stock-ticker.js` - The isolated ticker implementation
- `run-isolated-ticker.sh` - Script to run the demo

## Features

- Real-time data fetching from Alpha Vantage API
- Fallback to simulated data when API limits are reached
- Visual controls for testing and development
- Completely isolated from the rest of the website
- Smooth animation with hover-to-pause functionality

## Integration Path

Once you're satisfied with the isolated ticker, integrate it back into the main site:

1. Update `index.html` to use the new script:
   ```html
   <script src="public/js/isolated-stock-ticker.js"></script>
   ```

2. Make sure the HTML structure in index.html matches what's expected:
   ```html
   <div class="stock-ticker-container">
     <div class="stock-ticker-wrapper">
       <div class="stock-ticker" id="stock-ticker">
         <div class="loading">Loading market data...</div>
       </div>
     </div>
   </div>
   ```

3. Test thoroughly before merging back to main

## API Information

The stock ticker uses the Alpha Vantage API:
- Free tier: 5 API calls per minute, 500 per day
- For production, replace the 'demo' API key with your own 