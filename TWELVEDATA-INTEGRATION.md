# Real-time Stock Ticker with Twelvedata

This document explains how to use the Twelvedata API integration for real-time stock and cryptocurrency prices in our stock ticker component.

## Benefits of Twelvedata

1. **Real-time Websocket Updates**: Get live price updates via websocket connection without polling
2. **Accurate & Reliable Data**: Professional-grade financial data with excellent uptime
3. **Higher Rate Limits**: More generous API limits compared to Yahoo Finance
4. **Extensive Symbol Coverage**: Support for stocks, cryptocurrencies, forex, and more
5. **Low Latency**: Millisecond-level price updates directly from exchanges

## Setup Instructions

1. **Install Required Packages**:
   ```bash
   ./setup-twelvedata.sh
   ```
   This script will:
   - Create a Python virtual environment
   - Install the Twelvedata package with websocket support
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
   ```bash
   ./test-twelvedata.py
   ```
   This will verify your API key and connection to Twelvedata.

5. **Run the Server with Twelvedata**:
   ```bash
   ./run-twelvedata-ticker.sh
   ```

## Integration Details

The integration combines the reliability of our MongoDB-backed architecture with the real-time capabilities of Twelvedata:

- **Primary Data Source**: Twelvedata websocket for real-time price updates
- **Fallback Mechanism**: Automatic fallback to yfinance if Twelvedata unavailable
- **Historical Data**: MongoDB storage for historical price tracking
- **Performance**: Background thread handling for websocket connection
- **Resilience**: Graceful degradation if API limits are reached

## Configuration Options

You can adjust the following parameters in `stock-data-server-mongodb.py`:

- `STOCK_SYMBOLS`: List of stock symbols to track
- `CRYPTO_SYMBOLS`: List of cryptocurrency symbols to track
- `TWELVEDATA_API_KEY`: Your API key (set via environment variable)

## Usage in Frontend

The frontend code doesn't need to change - it will automatically receive real-time data from the backend API using the existing endpoints:

- `/api/quote/SYMBOL` - Get data for a single symbol
- `/api/quotes?symbols=AAPL,MSFT,BTC-USD` - Get data for multiple symbols

## Pricing and Limits

- **Free Tier**: Limited to 8 symbols and 800 API credits/day
- **Basic Plan**: $12/month for more symbols and higher rate limits
- **Professional Plans**: Available for higher volume needs

Check [Twelvedata Pricing](https://twelvedata.com/pricing) for current rates.

## Comparison with Other APIs

| Feature | Twelvedata | Yahoo Finance | Alpha Vantage |
|---------|------------|--------------|---------------|
| Real-time Updates | ✅ (Websocket) | ❌ (Delayed) | ❌ (REST only) |
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