# Cryptocurrency Data Server

A robust cryptocurrency data server that fetches prices and related information from CoinGecko API and serves it via HTTP, with MongoDB persistence for reliability.

## Features

- Real-time cryptocurrency data from CoinGecko API
- MongoDB persistence for reliable data storage
- In-memory caching for fast responses
- Robust error handling and rate limit management
- CORS support for cross-origin requests
- Docker support for easy deployment
- Health endpoint for monitoring

## Quick Start

### Installation

1. Make sure you have Python 3.6+ installed
2. Clone this repository
3. Install dependencies:

```bash
# Create and activate virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Starting the Server

#### Option 1: Using the deployment script (recommended)

```bash
# Start the server with the deployment script
./deploy-crypto-server.sh start

# Check server status
./deploy-crypto-server.sh status

# View logs
./deploy-crypto-server.sh logs

# Stop the server
./deploy-crypto-server.sh stop
```

#### Option 2: Running directly

```bash
python crypto-data-server.py
```

#### Option 3: Using Docker

```bash
# Start Docker containers
./deploy-crypto-server.sh docker

# Or manually:
docker-compose up -d

# Stop Docker containers
./deploy-crypto-server.sh docker-stop

# Or manually:
docker-compose down
```

## API Endpoints

### Health Check

```
GET /health
```

Response:
```json
{
  "status": "ok",
  "source": "coingecko",
  "cache_status": true,
  "rate_limit_reset": 0
}
```

### Get All Cryptocurrencies

```
GET /api/crypto
```

Response:
```json
[
  {
    "symbol": "BTC",
    "coingecko_id": "bitcoin",
    "name": "Bitcoin",
    "price": 50000.0,
    "change_percent_24h": 2.5,
    "volume": 30000000000.0,
    "market_cap": 950000000000.0,
    "timestamp": "2023-04-15T12:34:56.789Z"
  },
  {
    "symbol": "ETH",
    "coingecko_id": "ethereum",
    "name": "Ethereum",
    "price": 3000.0,
    "change_percent_24h": 1.5,
    "volume": 15000000000.0,
    "market_cap": 350000000000.0,
    "timestamp": "2023-04-15T12:34:56.789Z"
  }
]
```

### Get Specific Cryptocurrency

```
GET /api/crypto/{id or symbol}
```

Example:
```
GET /api/crypto/BTC
GET /api/crypto/bitcoin
```

Response:
```json
{
  "symbol": "BTC",
  "coingecko_id": "bitcoin",
  "name": "Bitcoin",
  "price": 50000.0,
  "change_percent_24h": 2.5,
  "volume": 30000000000.0,
  "market_cap": 950000000000.0,
  "timestamp": "2023-04-15T12:34:56.789Z"
}
```

## Error Handling

The server provides detailed error responses in JSON format:

### Not Found

```json
{
  "error": "Endpoint not found"
}
```

### Rate Limited

```json
{
  "error": "Rate limited by CoinGecko API",
  "retry_after": 60
}
```

### No Data Available

```json
{
  "error": "No cryptocurrency data available"
}
```

## Configuration

The server can be configured using environment variables:

- `PORT`: The port to run the server on (default: 3003)
- `MONGO_URI`: MongoDB connection string (default: mongodb://localhost:27017/)
- `CACHE_DURATION`: How long to cache data in seconds (default: 300)
- `RATE_LIMIT_COOLDOWN`: How long to wait after hitting rate limits (default: 300)
- `RETRY_ATTEMPTS`: Number of retry attempts for API calls (default: 5)
- `LOG_LEVEL`: Logging level (default: INFO)

## Supported Cryptocurrencies

The server currently supports the following cryptocurrencies:

- Bitcoin (BTC)
- Ethereum (ETH)
- XRP (XRP)
- Dogecoin (DOGE)
- Solana (SOL)
- Cardano (ADA)
- Polkadot (DOT)
- Polygon (MATIC)
- Chainlink (LINK)
- Avalanche (AVAX)

## Troubleshooting

### MongoDB Connection Issues

If MongoDB is not available, the server will fall back to in-memory storage.

### Rate Limiting

CoinGecko API has rate limits. The server implements exponential backoff and respects the `Retry-After` header.

### "Broken pipe" errors in logs

These errors occur when a client disconnects before receiving the complete response. They are harmless and handled gracefully.

## License

MIT 