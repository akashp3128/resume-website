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

# JSON encoder to properly handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

# Try to import MongoDB for persistence
try:
    from pymongo import MongoClient
    logger.info("MongoDB support enabled")
    USE_MONGODB = True
except ImportError:
    logger.warning("MongoDB not available - running with memory cache only")
    USE_MONGODB = False

# Configuration
PORT = 3003  # Different from stock server to avoid conflicts
MAX_PORT_ATTEMPTS = 5
ALLOWED_ORIGINS = ['http://localhost:8000', 'http://localhost:3000', 'http://127.0.0.1:8000', 'https://akashpatelresume.us', '*']

# CoinGecko API configuration
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
# Top cryptocurrencies by market cap
CRYPTO_IDS = [
    'bitcoin', 'ethereum', 'ripple', 'dogecoin', 'solana', 
    'cardano', 'polkadot', 'matic-network', 'chainlink', 'avalanche-2'
]
# Display symbol mapping
CRYPTO_SYMBOL_MAP = {
    'bitcoin': 'BTC',
    'ethereum': 'ETH',
    'ripple': 'XRP',
    'dogecoin': 'DOGE',
    'solana': 'SOL',
    'cardano': 'ADA',
    'polkadot': 'DOT',
    'matic-network': 'MATIC',
    'chainlink': 'LINK',
    'avalanche-2': 'AVAX'
}

# Cache settings
CACHE_DURATION = 300  # 5 minutes 
RATE_LIMIT_COOLDOWN = 300  # 5 minute cooldown if we hit rate limits (increased from 1 min)
RETRY_ATTEMPTS = 5  # Number of times to retry if rate limited (increased from 3)
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
    """Fetch data for all cryptocurrencies in a single API call"""
    global rate_limit_until
    
    # Check if we're in a rate limit cooldown
    if time.time() < rate_limit_until:
        cooldown_remaining = int(rate_limit_until - time.time())
        logger.warning(f"Rate limit cooldown active. Retry in {cooldown_remaining} seconds")
        return None
    
    for attempt in range(RETRY_ATTEMPTS):
        try:
            logger.info(f"Fetching crypto data from CoinGecko (attempt {attempt+1}/{RETRY_ATTEMPTS})")
            
            # Make a single API call for all cryptos
            params = {
                'vs_currency': 'usd',
                'ids': ','.join(CRYPTO_IDS),
                'order': 'market_cap_desc',
                'per_page': 100,  # More than we need
                'page': 1,
                'sparkline': 'false',
                'price_change_percentage': '24h'
            }
            
            # Add a randomized sleep to help avoid hitting rate limits at the same time
            # from multiple instances with exponential backoff
            if attempt > 0:
                sleep_time = min(2 + (2 ** attempt), MAX_BACKOFF_TIME)  # Exponential backoff with max cap
                logger.info(f"Backing off for {sleep_time} seconds before retry")
                time.sleep(sleep_time)
            
            response = requests.get(
                f"{COINGECKO_API_URL}/coins/markets", 
                params=params,
                headers={'Accept': 'application/json', 'User-Agent': 'AkashPatelResume/1.0'},
                timeout=15  # Increased timeout
            )
            
            # Check for rate limiting - important to handle this properly
            if response.status_code == 429:
                # Note the rate limit and back off
                logger.warning("Rate limit hit (429). Backing off...")
                # Inspect headers for retry-after if available
                retry_after = int(response.headers.get('Retry-After', RATE_LIMIT_COOLDOWN))
                rate_limit_until = time.time() + retry_after
                continue  # Try again if we have attempts left
            
            # Raise for other kinds of errors
            response.raise_for_status()
            
            # Process the response
            data = response.json()
            if not isinstance(data, list):
                logger.error(f"Unexpected response format: {type(data)}")
                return None
                
            logger.info(f"Successfully fetched data for {len(data)} cryptocurrencies")
            
            # Process and return the data
            return process_crypto_data(data)
            
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
    """Process raw CoinGecko data into our standard format"""
    processed_data = []
    timestamp = datetime.now()
    
    for coin in data:
        try:
            coin_id = coin.get('id')
            if not coin_id or coin_id not in CRYPTO_IDS:
                continue
                
            # Get known values with safety checks
            symbol = CRYPTO_SYMBOL_MAP.get(coin_id, coin.get('symbol', '').upper())
            name = coin.get('name', '')
            price = coin.get('current_price')
            market_cap = coin.get('market_cap')
            volume = coin.get('total_volume')
            change_24h = coin.get('price_change_percentage_24h')
            
            # Skip if missing critical data
            if price is None:
                logger.warning(f"Missing price data for {symbol}, skipping")
                continue
                
            # Format our standard data structure
            coin_data = {
                'symbol': symbol,
                'coingecko_id': coin_id,
                'name': name,
                'price': float(price),
                'change_percent_24h': float(change_24h) if change_24h is not None else 0,
                'volume': float(volume) if volume is not None else 0,
                'market_cap': float(market_cap) if market_cap is not None else 0,
                'timestamp': timestamp
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
            crypto_cache[coin_id] = coin_data
            
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
            coin_id = record.get('coingecko_id')
            if coin_id:
                crypto_cache[coin_id] = record
                
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
                    'source': 'coingecko',
                    'cache_status': cache_status,
                    'rate_limit_reset': max(0, rate_limit_until - time.time())
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
                crypto_id_or_symbol = path.split('/')[-1]
                self._get_specific_crypto(crypto_id_or_symbol)
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
                'error': 'Rate limited by CoinGecko API',
                'retry_after': int(rate_limit_until - time.time())
            }, 429)
        else:
            # Something else is wrong
            self._json_response({'error': 'No cryptocurrency data available'}, 503)
    
    def _get_specific_crypto(self, crypto_id_or_symbol):
        """Return data for a specific cryptocurrency"""
        # Normalize input to find the right crypto
        target_id = None
        target_symbol = None
        
        # Check if this is a symbol (e.g., BTC)
        for cg_id, symbol in CRYPTO_SYMBOL_MAP.items():
            if symbol.lower() == crypto_id_or_symbol.lower():
                target_id = cg_id
                target_symbol = symbol
                break
                
        # If not found by symbol, check if it's a direct ID (e.g., bitcoin)
        if not target_id and crypto_id_or_symbol.lower() in CRYPTO_IDS:
            target_id = crypto_id_or_symbol.lower()
            target_symbol = CRYPTO_SYMBOL_MAP.get(target_id)
            
        # If we couldn't determine what they're asking for
        if not target_id:
            self._json_response({'error': f'Unknown cryptocurrency: {crypto_id_or_symbol}'}, 404)
            return
            
        # Check MongoDB first
        if USE_MONGODB:
            try:
                record = current_prices.find_one({'symbol': target_symbol})
                if record:
                    if '_id' in record:
                        record['_id'] = str(record['_id'])
                    logger.info(f"Returning {target_symbol} from MongoDB")
                    self._json_response(record)
                    return
            except Exception as e:
                logger.error(f"MongoDB fetch error for {target_symbol}: {e}")
                
        # Try memory cache
        if target_id in crypto_cache:
            logger.info(f"Returning {target_symbol} from memory cache")
            self._json_response(crypto_cache[target_id])
            return
            
        # If we don't have this crypto cached
        self._json_response({'error': f'No data available for {crypto_id_or_symbol}'}, 404)

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
            logger.info(f"CoinGecko crypto server running at http://localhost:{PORT}")
            
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
        logger.info("Starting CoinGecko crypto data server...")
        run_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0) 