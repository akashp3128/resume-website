# Stock Ticker Implementations

This project contains multiple implementations of a stock ticker component for the resume website, each with different data sources and features.

## Quick Start

Run the unified launcher script to choose which implementation to use:

```bash
./run-all-tickers.sh
```

## Available Implementations

### 1. YFinance Python Backend (RECOMMENDED)

**Features:**
- Uses a dedicated Python backend service powered by the `yfinance` package
- Provides the most accurate and reliable stock data directly from Yahoo Finance
- Completely eliminates CORS issues through backend handling of API requests
- Server-side caching for optimal performance and reduced API calls
- Includes up-to-date prices for all stocks, including GME at $25.50
- Visual distinction between stocks and cryptocurrencies
- Automatic installation of required Python packages

**Best for:** Production use where data accuracy and reliability are critical.

```bash
./run-yfinance-ticker.sh
```

### 2. Yahoo Finance Ticker (Client-Side)

**Features:**
- Prioritizes Yahoo Finance API for stock data
- Uses CoinGecko API for cryptocurrency data
- Implements batched fetching to avoid rate limiting
- Visual distinction between stocks and cryptocurrencies
- Proper decimal formatting based on asset type
- Automatic fallbacks to static data when API calls fail

**Best for:** Production use when a Python backend is not available.

```bash
./run-yahoo-finance-ticker.sh
```

### 3. Real-time Ticker

**Features:**
- Multi-API approach with primary and fallback sources
- Combines Yahoo Finance, Finnhub, and Twelve Data APIs
- Graceful degradation with multiple fallback strategies
- Auto-retry logic for failed API calls

**Best for:** Development and testing of the ticker component.

```bash
./run-realtime-ticker.sh
```

### 4. Alpha Vantage Ticker

**Features:**
- Uses Alpha Vantage API for stock data
- Requires temporary CORS proxy access
- Simple implementation with fewer fallbacks

**Best for:** When Yahoo Finance API is unavailable.

```bash
./run-alpha-vantage-ticker.sh
```

## Implementation Details

### Data Source Priorities

1. **YFinance Implementation:**
   - Uses the official `yfinance` Python package
   - Most reliable source with accurate pricing
   - No CORS issues or rate limiting concerns
   - Server-side caching for performance

2. **Stocks (Client-side implementations):**
   - Primary: Yahoo Finance API
   - Secondary: Finnhub API
   - Tertiary: Alpha Vantage API
   - Fallback: Static data with randomized variations

3. **Cryptocurrencies:**
   - Primary: CoinGecko API
   - Fallback: Static data with randomized variations

### CORS Considerations

When testing client-side implementations locally, the ticker implementations use CORS proxies to access the APIs. The recommended proxy is:

```
https://corsproxy.io/?
```

For Alpha Vantage implementation, you may need to request temporary access at:
https://cors-anywhere.herokuapp.com/

### Technical Notes

- The YFinance backend implementation requires Python 3 and will automatically install the required packages
- The backend runs on port 3000 while the frontend runs on port 8000
- All implementations use vanilla JavaScript without external dependencies
- Data refresh intervals are shorter in development mode
- The ticker automatically doubles entries for smooth infinite scrolling
- Failed API calls for specific symbols use static data as a fallback
- After multiple failures, the ticker switches to randomized static data

## Updates and Improvements

### Integration with Main Website (April 11, 2025)

The YFinance-powered stock ticker has been integrated with the main website for better accuracy. Key updates include:

1. **Main Site Integration**: The `isolated-stock-ticker.js` file has been updated to use the YFinance backend when available, with seamless fallback to static data if the backend is not running.

2. **Backend Auto-Start**: The main website startup script (`start_server.sh`) now automatically starts the YFinance backend, providing accurate stock data from the beginning.

3. **Improved Error Handling**: Better error handling ensures the ticker always displays data, even if the backend cannot be reached.

4. **GME Price Fix**: The GME stock price has been updated to the accurate value of approximately $25.50 (as reported by Yahoo Finance).

5. **Timeout Protection**: The ticker now has safeguards against hanging network requests with proper timeouts.

To use the improved stock ticker on the main site, simply run:

```bash
./start_server.sh
```

This will launch the main website on port 8000, the upload server on port 8001, and the YFinance backend on port 3000.