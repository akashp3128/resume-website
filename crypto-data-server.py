#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
import sys
import time
import requests
import logging
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("CryptoServer")

# JSON encoder to properly handle datetime objects and MongoDB ObjectId
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        # Handle MongoDB ObjectId
        try:
            from bson import ObjectId
            if isinstance(obj, ObjectId):
                return str(obj)
        except ImportError:
            pass
        return super(DateTimeEncoder, self).default(obj)

# Try to import MongoDB for persistence
try:
    from pymongo import MongoClient
    from bson import ObjectId
    logger.info("MongoDB support enabled")
    USE_MONGODB = True
except ImportError:
    logger.warning("MongoDB not available - running with memory cache only")
    USE_MONGODB = False

# Configuration
PORT = 3003  # Different from stock server to avoid conflicts
MAX_PORT_ATTEMPTS = 5
ALLOWED_ORIGINS = ['http://localhost:8000', 'http://localhost:3000', 'http://127.0.0.1:8000', 'https://akashpatelresume.us', '*']

# CoinMarketCap API configuration
CMC_API_URL = "https://pro-api.coinmarketcap.com/v1"
CMC_API_KEY = os.environ.get('CMC_API_KEY', '')  # Get API key from environment variable

# If API key is not set, try to load from .env file
if not CMC_API_KEY:
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('CMC_API_KEY='):
                    CMC_API_KEY = line.strip().split('=', 1)[1].strip()
                    if CMC_API_KEY.startswith('"') and CMC_API_KEY.endswith('"'):
                        CMC_API_KEY = CMC_API_KEY[1:-1]
                    break
    except Exception as e:
        logger.warning(f"Could not load CMC_API_KEY from .env file: {e}")

if not CMC_API_KEY:
    logger.warning("CoinMarketCap API key not found. Please set the CMC_API_KEY environment variable.")
    logger.warning("The server will run with limited functionality.")

# Top cryptocurrencies to track
CRYPTO_SYMBOLS = [
    'BTC', 'ETH', 'XRP', 'DOGE', 'SOL', 
    'ADA', 'DOT', 'MATIC', 'LINK', 'AVAX'
]

# Map of symbols to full names (will be populated from API)
CRYPTO_NAME_MAP = {
    'BTC': 'Bitcoin',
    'ETH': 'Ethereum',
    'XRP': 'XRP',
    'DOGE': 'Dogecoin',
    'SOL': 'Solana',
    'ADA': 'Cardano',
    'DOT': 'Polkadot',
    'MATIC': 'Polygon',
    'LINK': 'Chainlink',
    'AVAX': 'Avalanche'
}

# Cache settings
CACHE_DURATION = int(os.environ.get('CACHE_DURATION', 300))  # 5 minutes 
RATE_LIMIT_COOLDOWN = int(os.environ.get('RATE_LIMIT_COOLDOWN', 300))  # 5 minute cooldown if we hit rate limits
RETRY_ATTEMPTS = int(os.environ.get('RETRY_ATTEMPTS', 5))  # Number of times to retry if rate limited
MAX_BACKOFF_TIME = 30  # Maximum backoff time in seconds

# MongoDB Configuration (if available)
if USE_MONGODB:
    try:
        MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test the connection
        mongo_client.server_info()  
        
        db = mongo_client['crypto_ticker']
        current_prices = db['current_prices']
        historical_prices = db['historical_prices']
        
        # Create indexes
        current_prices.create_index([("symbol", 1)], unique=True)
        historical_prices.create_index([("symbol", 1), ("timestamp", 1)])
        
        logger.info(f"Connected to MongoDB at {MONGO_URI}")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        USE_MONGODB = False
        mongo_client = None

# In-memory cache as fallback
crypto_cache = {}
last_cache_update = 0
rate_limit_until = 0  # Timestamp when we can try again after hitting rate limits

def fetch_crypto_data():
    """Fetch data for cryptocurrencies from CoinMarketCap API"""
    global rate_limit_until
    
    # Check if we're in a rate limit cooldown
    if time.time() < rate_limit_until:
        cooldown_remaining = int(rate_limit_until - time.time())
        logger.warning(f"Rate limit cooldown active. Retry in {cooldown_remaining} seconds")
        return None
    
    if not CMC_API_KEY:
        logger.error("Cannot fetch data: CoinMarketCap API key not set")
        return None
    
    for attempt in range(RETRY_ATTEMPTS):
        try:
            logger.info(f"Fetching crypto data from CoinMarketCap (attempt {attempt+1}/{RETRY_ATTEMPTS})")
            
            # Prepare headers with API key
            headers = {
                'X-CMC_PRO_API_KEY': CMC_API_KEY,
                'Accept': 'application/json',
                'User-Agent': 'AkashPatelResume/1.0'
            }
            
            # Make API call to get latest listings
            params = {
                'symbol': ','.join(CRYPTO_SYMBOLS),
                'convert': 'USD'
            }
            
            # Add a randomized sleep to help avoid hitting rate limits at the same time
            # from multiple instances with exponential backoff
            if attempt > 0:
                sleep_time = min(2 + (2 ** attempt), MAX_BACKOFF_TIME)  # Exponential backoff with max cap
                logger.info(f"Backing off for {sleep_time} seconds before retry")
                time.sleep(sleep_time)
            
            response = requests.get(
                f"{CMC_API_URL}/cryptocurrency/quotes/latest", 
                params=params,
                headers=headers,
                timeout=15  # Increased timeout
            )
            
            # Check for rate limiting
            if response.status_code == 429:
                # Note the rate limit and back off
                logger.warning("Rate limit hit (429). Backing off...")
                # Get retry-after header if available
                retry_after = int(response.headers.get('Retry-After', RATE_LIMIT_COOLDOWN))
                rate_limit_until = time.time() + retry_after
                continue  # Try again if we have attempts left
            
            # Raise for other kinds of errors
            response.raise_for_status()
            
            # Process the response
            data = response.json()
            if 'status' not in data or data['status']['error_code'] != 0:
                error_message = data.get('status', {}).get('error_message', 'Unknown error')
                logger.error(f"API error: {error_message}")
                return None
                
            if 'data' not in data:
                logger.error("No data in API response")
                return None
                
            logger.info(f"Successfully fetched data for cryptocurrencies")
            
            # Process and return the data
            return process_crypto_data(data['data'])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            # Specifically handle rate limits that might occur in exception form
            if hasattr(e, 'response') and e.response and e.response.status_code == 429:
                retry_after = int(e.response.headers.get('Retry-After', RATE_LIMIT_COOLDOWN))
                rate_limit_until = time.time() + retry_after
            
        except Exception as e:
            logger.error(f"Unexpected error during fetch: {e}")
            
    # If we've exhausted all retries
    logger.error("All fetch attempts failed")
    return None

def process_crypto_data(data):
    """Process raw CoinMarketCap data into our standard format"""
    processed_data = []
    timestamp = datetime.now()
    
    for symbol, coin_data in data.items():
        try:
            # Skip if not in our list
            if symbol not in CRYPTO_SYMBOLS:
                continue
                
            # Get quote data
            quote = coin_data.get('quote', {}).get('USD', {})
            
            # Skip if missing critical data
            if not quote or 'price' not in quote:
                logger.warning(f"Missing price data for {symbol}, skipping")
                continue
                
            # Extract the data we need
            name = coin_data.get('name', CRYPTO_NAME_MAP.get(symbol, symbol))
            price = quote.get('price')
            market_cap = quote.get('market_cap')
            volume_24h = quote.get('volume_24h')
            percent_change_24h = quote.get('percent_change_24h')
            
            # Format our standard data structure
            coin_data = {
                'symbol': symbol,
                'cmc_id': coin_data.get('id'),
                'name': name,
                'price': float(price) if price is not None else 0,
                'change_percent_24h': float(percent_change_24h) if percent_change_24h is not None else 0,
                'volume': float(volume_24h) if volume_24h is not None else 0,
                'market_cap': float(market_cap) if market_cap is not None else 0,
                'timestamp': timestamp,
                'last_updated': coin_data.get('last_updated')
            }
            
            processed_data.append(coin_data)
            
            # Save to MongoDB if available
            if USE_MONGODB:
                try:
                    current_prices.update_one(
                        {'symbol': symbol},
                        {'$set': coin_data},
                        upsert=True
                    )
                except Exception as e:
                    logger.error(f"MongoDB update error for {symbol}: {e}")
                    
            # Also update memory cache
            crypto_cache[symbol] = coin_data
            
            # Log the price update
            logger.info(f"Updated {symbol}: ${price:.2f}")
            
        except Exception as e:
            logger.error(f"Error processing coin data: {e}")
            
    # Update the last cache time
    global last_cache_update
    last_cache_update = time.time()
    
    return processed_data

def refresh_cache():
    """Refresh the crypto cache if needed"""
    current_time = time.time()
    
    # Check if cache is still valid
    if current_time - last_cache_update < CACHE_DURATION:
        return True
        
    logger.info("Cache expired, refreshing data...")
    
    # First try to restore from MongoDB if available
    if USE_MONGODB and restore_from_mongodb():
        return True
        
    # Otherwise fetch fresh data
    result = fetch_crypto_data()
    
    # Return success status
    return result is not None

def restore_from_mongodb():
    """Try to restore cache from MongoDB"""
    if not USE_MONGODB:
        return False
        
    try:
        # Find recent records (last hour to be safe)
        cutoff_time = datetime.now() - timedelta(hours=1)
        records = list(current_prices.find(
            {"timestamp": {"$gte": cutoff_time}}
        ))
        
        if not records:
            logger.info("No recent records found in MongoDB")
            return False
            
        # Update the memory cache
        for record in records:
            symbol = record.get('symbol')
            if symbol:
                # Convert _id to string for JSON serialization
                if '_id' in record:
                    record['_id'] = str(record['_id'])
                crypto_cache[symbol] = record
                
        # Update last cache time
        global last_cache_update
        last_cache_update = time.time()
        
        logger.info(f"Restored {len(records)} records from MongoDB")
        return True
        
    except Exception as e:
        logger.error(f"Error restoring from MongoDB: {e}")
        return False

class CryptoDataHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Override to reduce log spam for common requests"""
        if args and args[0].startswith('GET /health'):
            return  # Skip logging health checks
        logger.info(f"{self.address_string()} - {format % args}")
    
    def _set_headers(self, status_code=200, content_type='application/json'):
        """Set response headers with CORS support"""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        
        # Handle CORS
        origin = self.headers.get('Origin', '')
        if origin in ALLOWED_ORIGINS or '*' in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
        else:
            self.send_header('Access-Control-Allow-Origin', '*')
            
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        self.end_headers()
    
    def _json_response(self, data, status_code=200):
        """Send JSON response"""
        try:
            self._set_headers(status_code)
            self.wfile.write(json.dumps(data, cls=DateTimeEncoder).encode())
        except BrokenPipeError:
            # Handle client disconnection gracefully
            logger.debug("Client disconnected before response could be sent")
        except Exception as e:
            logger.error(f"Error sending response: {e}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self._set_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Always refresh cache if needed
            cache_status = refresh_cache()
            
            # Parse the URL path
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            query = parse_qs(parsed_path.query)
            
            # Health check endpoint
            if path == '/health':
                self._json_response({
                    'status': 'ok', 
                    'source': 'coinmarketcap',
                    'cache_status': cache_status,
                    'rate_limit_reset': max(0, rate_limit_until - time.time()),
                    'current_time': datetime.now().isoformat()
                })
                return
            
            # API endpoint to get all crypto prices
            if path == '/api/crypto':
                self._get_all_crypto()
                return
                
            # Legacy endpoint (same as /api/crypto)
            if path == '/api/prices':
                self._get_all_crypto()
                return
                
            # Get specific crypto data
            if path.startswith('/api/crypto/'):
                crypto_symbol = path.split('/')[-1].upper()
                self._get_specific_crypto(crypto_symbol)
                return
            
            # Cache control endpoint - force refresh
            if path == '/api/cache/refresh':
                # Reset cache time to force refresh
                global last_cache_update
                last_cache_update = 0
                # Fetch new data
                success = refresh_cache()
                self._json_response({
                    'status': 'ok' if success else 'error',
                    'message': 'Cache refreshed successfully' if success else 'Failed to refresh cache',
                    'source': 'coinmarketcap',
                    'current_time': datetime.now().isoformat()
                })
                return
            
            # Default response for unknown endpoints
            self._json_response({'error': 'Endpoint not found'}, 404)
            
        except ConnectionResetError:
            logger.debug("Connection reset by client")
        except BrokenPipeError:
            logger.debug("Broken pipe - client disconnected")
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            try:
                self._json_response({'error': 'Internal server error'}, 500)
            except:
                pass
    
    def _get_all_crypto(self):
        """Return all crypto data"""
        result = []
        
        # First try MongoDB for fresh data
        if USE_MONGODB:
            try:
                cutoff_time = datetime.now() - timedelta(minutes=30)  # Recent enough
                records = list(current_prices.find(
                    {"timestamp": {"$gte": cutoff_time}}
                ))
                
                if records:
                    # Convert ObjectId to string for JSON serialization
                    for record in records:
                        if '_id' in record:
                            record['_id'] = str(record['_id'])
                    
                    logger.info(f"Returning {len(records)} records from MongoDB")
                    self._json_response(records)
                    return
            except Exception as e:
                logger.error(f"Error fetching from MongoDB: {e}")
        
        # Fall back to memory cache
        if crypto_cache:
            result = list(crypto_cache.values())
            logger.info(f"Returning {len(result)} records from memory cache")
            self._json_response(result)
            return
            
        # If we got here, we have no data
        if time.time() < rate_limit_until:
            # We're rate limited
            self._json_response({
                'error': 'Rate limited by CoinMarketCap API',
                'retry_after': int(rate_limit_until - time.time())
            }, 429)
        else:
            # Something else is wrong
            self._json_response({'error': 'No cryptocurrency data available'}, 503)
    
    def _get_specific_crypto(self, crypto_symbol):
        """Return data for a specific cryptocurrency"""
        # Normalize input
        crypto_symbol = crypto_symbol.upper()
        
        # Check if this is a valid symbol
        if crypto_symbol not in CRYPTO_SYMBOLS:
            self._json_response({'error': f'Unknown cryptocurrency: {crypto_symbol}'}, 404)
            return
            
        # Check MongoDB first
        if USE_MONGODB:
            try:
                record = current_prices.find_one({'symbol': crypto_symbol})
                if record:
                    if '_id' in record:
                        record['_id'] = str(record['_id'])
                    logger.info(f"Returning {crypto_symbol} from MongoDB")
                    self._json_response(record)
                    return
            except Exception as e:
                logger.error(f"MongoDB fetch error for {crypto_symbol}: {e}")
                
        # Try memory cache
        if crypto_symbol in crypto_cache:
            logger.info(f"Returning {crypto_symbol} from memory cache")
            self._json_response(crypto_cache[crypto_symbol])
            return
            
        # If we don't have this crypto cached
        self._json_response({'error': f'No data available for {crypto_symbol}'}, 404)

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True  # Exit quickly when main thread exits

def run_server():
    """Run the HTTP server with port conflict handling"""
    global PORT
    
    for attempt in range(MAX_PORT_ATTEMPTS):
        try:
            # Create and start the server
            httpd = ThreadedHTTPServer(("", PORT), CryptoDataHandler)
            logger.info(f"CoinMarketCap crypto server running at http://localhost:{PORT}")
            
            # Initial cache population
            refresh_cache()
            
            httpd.serve_forever()
        except OSError as e:
            if e.errno == 48:  # Address already in use
                logger.warning(f"Port {PORT} is already in use. Trying port {PORT + 1}...")
                PORT += 1
            else:
                logger.error(f"Server error: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected server error: {e}")
            raise

if __name__ == "__main__":
    try:
        logger.info("Starting CoinMarketCap crypto data server...")
        run_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0) 