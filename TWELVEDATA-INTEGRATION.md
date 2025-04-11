# Real-time Stock Ticker with Twelvedata

This document explains how to use the Twelvedata API integration for real-time stock and cryptocurrency prices in our stock ticker component.

## Benefits of Twelvedata

1. **Real-time Websocket Updates**: Get live price updates via websocket connection without polling
2. **Accurate & Reliable Data**: Professional-grade financial data with excellent uptime
3. **Higher Rate Limits**: More generous API limits compared to Yahoo Finance
4. **Extensive Symbol Coverage**: Support for stocks, cryptocurrencies, forex, and more
5. **Low Latency**: Millisecond-level price updates directly from exchanges
6. **Historical Data Access**: Comprehensive historical price data via REST API

## Setup Instructions

1. **Install Required Packages**:
   ```bash
   ./setup-twelvedata.sh
   ```
   This script will:
   - Create a Python virtual environment
   - Install the Twelvedata package with websocket support
   - Install additional dependencies (requests)
   - Generate example code and configuration files

2. **Get an API Key**:
   - Sign up at [Twelvedata.com](https://twelvedata.com)
   - Get your API key from the dashboard
   - Free tier available with limited usage

3. **Configure Environment**:
   - Create a `.env` file in the project root with your API key:
   ```
   TWELVEDATA_API_KEY=your_api_key_here
   ```

4. **Test the Connection**:
   - For websocket (real-time data):
   ```bash
   ./test-twelvedata.py
   ```
   
   - For REST API (historical data):
   ```bash
   ./test-twelvedata-rest.py
   ```

5. **Run the Server with Twelvedata**:
   ```bash
   ./run-twelvedata-ticker.sh
   ```

## Integration Details

The integration combines the reliability of our MongoDB-backed architecture with the real-time capabilities of Twelvedata:

- **Real-time Data**: Twelvedata websocket for live price updates
- **Historical Data**: Twelvedata REST API for comprehensive historical price data
- **Fallback Mechanism**: Automatic fallback to yfinance if Twelvedata unavailable
- **Persistence**: MongoDB storage for caching and tracking
- **Performance**: Background thread handling for websocket connection
- **Resilience**: Graceful degradation if API limits are reached

## How It Works

### Real-time Price Updates (Websocket)
1. When the server starts, it establishes a websocket connection to Twelvedata
2. Price updates are received in real-time and stored in MongoDB
3. Client requests are served from the most recent data

### Historical Data (REST API)
1. When a client requests historical data, the server first checks Twelvedata
2. The data is fetched using the `/time_series` REST endpoint 
3. Results are cached in MongoDB for future requests
4. If Twelvedata is unavailable, the server falls back to MongoDB cache or yfinance

## Configuration Options

You can adjust the following parameters in `stock-data-server-mongodb.py`:

- `STOCK_SYMBOLS`: List of stock symbols to track
- `CRYPTO_SYMBOLS`: List of cryptocurrency symbols to track
- `TWELVEDATA_API_KEY`: Your API key (set via environment variable)

## Usage in Frontend

The frontend code doesn't need to change - it will automatically receive data from the backend API using the existing endpoints:

- `/api/quote/SYMBOL` - Get current data for a single symbol
- `/api/quotes?symbols=AAPL,MSFT,BTC-USD` - Get current data for multiple symbols
- `/api/historical/SYMBOL?days=30` - Get historical data for a symbol

## REST API Examples

### Time Series Data
```
GET https://api.twelvedata.com/time_series?apikey=YOUR_API_KEY&interval=1day&symbol=SPY&format=JSON&start_date=2020-12-29
```

### Real-time Price
```
GET https://api.twelvedata.com/price?apikey=YOUR_API_KEY&symbol=AAPL&format=JSON
```

## Pricing and Limits

- **Free Tier**: Limited to 8 symbols and 800 API credits/day
- **Basic Plan**: $12/month for more symbols and higher rate limits
- **Professional Plans**: Available for higher volume needs

Check [Twelvedata Pricing](https://twelvedata.com/pricing) for current rates.

## Comparison with Other APIs

| Feature | Twelvedata | Yahoo Finance | Alpha Vantage |
|---------|------------|--------------|---------------|
| Real-time Updates | ✅ (Websocket) | ❌ (Delayed) | ❌ (REST only) |
| Historical Data | ✅ (Comprehensive) | ✅ (Limited) | ✅ (Limited) |
| Rate Limits | Higher | Lower | Moderate |
| Reliability | High | Medium | Medium |
| Price | Free tier + Paid | Free | Free tier + Paid |
| Data Types | More extensive | Limited | Moderate |

## Troubleshooting

If you encounter issues:

1. **Check API Key**: Verify your API key in the `.env` file
2. **Check Rate Limits**: Ensure you haven't exceeded your plan's limits
3. **Connection Issues**: Check your network connection
4. **Server Logs**: Look for error messages in the server output

For additional help, contact Twelvedata support or refer to their [documentation](https://twelvedata.com/docs). 