#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
import sys
import time
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import requests

# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

# Import MongoDB client
try:
    from pymongo import MongoClient
    print("pymongo package loaded successfully")
except ImportError:
    print("ERROR: pymongo package not found. Installing...")
    import subprocess
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pymongo", "--break-system-packages"])
        from pymongo import MongoClient
        print("pymongo package installed successfully")
    except (subprocess.CalledProcessError, ImportError) as e:
        print(f"Failed to install pymongo: {e}")
        
        # Check if we're running in a virtual environment
        in_venv = sys.prefix != sys.base_prefix
        
        if not in_venv:
            print("\nERROR: Cannot install pymongo in an externally managed environment.")
            print("Please use one of the following methods:")
            print("1. Create and activate a virtual environment first:")
            print("   python3 -m venv venv")
            print("   source venv/bin/activate")
            print("   Then run this script again")
            print("2. Install pymongo manually before running this script:")
            print("   pip3 install pymongo --break-system-packages --user")
            sys.exit(1)
        else:
            # If we're in a venv but still failed, try without the flag
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pymongo"])
                from pymongo import MongoClient
                print("pymongo package installed successfully in virtual environment")
            except:
                print("ERROR: Failed to install pymongo even in a virtual environment")
                sys.exit(1)

# Ensure requests is installed
try:
    import requests
    print("requests package loaded successfully")
except ImportError:
    print("ERROR: requests package not found. Installing...")
    import subprocess
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "--break-system-packages"])
        import requests
        print("requests package installed successfully")
    except (subprocess.CalledProcessError, ImportError) as e:
        print(f"Failed to install requests: {e}")
        
        # Check if we're running in a virtual environment
        in_venv = sys.prefix != sys.base_prefix
        
        if not in_venv:
            print("\nERROR: Cannot install requests in an externally managed environment.")
            print("Please use one of the following methods:")
            print("1. Create and activate a virtual environment first:")
            print("   python3 -m venv venv")
            print("   source venv/bin/activate")
            print("   Then run this script again")
            print("2. Install requests manually before running this script:")
            print("   pip3 install requests --break-system-packages --user")
            sys.exit(1)
        else:
            # If we're in a venv but still failed, try without the flag
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
                import requests
                print("requests package installed successfully in virtual environment")
            except:
                print("ERROR: Failed to install requests even in a virtual environment")
                sys.exit(1)

# Configuration
PORT = 3000
MAX_PORT_ATTEMPTS = 5  # Try up to 5 different ports if the default is in use
ALLOWED_ORIGINS = ['http://localhost:8000', 'http://localhost:3000', 'http://127.0.0.1:8000', 'https://akashpatelresume.us', '*']

# CoinGecko API Configuration
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
CRYPTO_SYMBOLS = [
    'bitcoin', 'ethereum', 'ripple', 'dogecoin', 'solana', 
    'cardano', 'polkadot', 'matic-network', 'chainlink', 'avalanche-2'
]
# Mapping from CoinGecko IDs to display symbols
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

CACHE_DURATION = 60  # 1 minute cache duration
REQUEST_DELAY = 0.5  # 500ms between requests to avoid rate limiting

# MongoDB Configuration
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = 'crypto_ticker'
HISTORICAL_COLLECTION = 'historical_prices'
CURRENT_COLLECTION = 'current_prices'

# Initialize MongoDB client
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client[DB_NAME]
    historical_collection = db[HISTORICAL_COLLECTION]
    current_collection = db[CURRENT_COLLECTION]
    
    # Create indexes
    historical_collection.create_index([("symbol", 1), ("timestamp", 1)])
    current_collection.create_index([("symbol", 1)], unique=True)
    
    print(f"Connected to MongoDB at {MONGO_URI}")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    print("Using in-memory cache as fallback")
    mongo_client = None

# Cache for crypto data (fallback if MongoDB connection fails)
crypto_cache = {}
last_cache_update = 0

def get_crypto_price_data(crypto_id):
    """Get current price data for a cryptocurrency from CoinGecko"""
    try:
        # CoinGecko API endpoint for getting current price
        url = f"{COINGECKO_API_URL}/coins/{crypto_id}"
        
        # Make the request with market_data and tickers included
        response = requests.get(url, params={
            'localization': 'false',
            'tickers': 'false',
            'market_data': 'true',
            'community_data': 'false',
            'developer_data': 'false'
        })
        
        if response.status_code != 200:
            print(f"Error fetching data for {crypto_id}: {response.status_code}")
            return None
            
        data = response.json()
        
        # Extract relevant data
        if 'market_data' in data:
            market_data = data['market_data']
            price_usd = market_data.get('current_price', {}).get('usd', 0)
            price_change_24h_percent = market_data.get('price_change_percentage_24h', 0)
            volume = market_data.get('total_volume', {}).get('usd', 0)
            market_cap = market_data.get('market_cap', {}).get('usd', 0)
            
            # Get display symbol
            symbol = CRYPTO_SYMBOL_MAP.get(crypto_id, data.get('symbol', '').upper())
            
            # Format the data
            crypto_data = {
                "symbol": symbol,
                "coingecko_id": crypto_id,
                "name": data.get('name', ''),
                "price": price_usd,
                "change_percent_24h": price_change_24h_percent,
                "volume": volume,
                "market_cap": market_cap,
                "timestamp": datetime.now()
            }
            return crypto_data
        else:
            print(f"No market data found for {crypto_id}")
            return None
    
    except Exception as e:
        print(f"Error getting data for {crypto_id}: {e}")
        return None

def get_crypto_historical_data(crypto_id, days=30):
    """Get historical price data for a cryptocurrency from CoinGecko"""
    try:
        # CoinGecko API endpoint for getting historical market data
        url = f"{COINGECKO_API_URL}/coins/{crypto_id}/market_chart"
        
        # Make the request
        response = requests.get(url, params={
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily'
        })
        
        if response.status_code != 200:
            print(f"Error fetching historical data for {crypto_id}: {response.status_code}")
            return None
            
        data = response.json()
        
        # Get display symbol
        symbol = CRYPTO_SYMBOL_MAP.get(crypto_id, crypto_id.upper())
        
        # Process the data
        historical_data = []
        
        # Prices are returned as [timestamp, price] pairs
        if 'prices' in data:
            for timestamp_ms, price in data['prices']:
                # Convert timestamp from milliseconds to datetime
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                
                # Find the corresponding volume if available
                volume = 0
                if 'total_volumes' in data:
                    for vol_timestamp_ms, vol in data['total_volumes']:
                        if abs(timestamp_ms - vol_timestamp_ms) < 86400000:  # Within 24 hours
                            volume = vol
                            break
                
                # Create data point
                data_point = {
                    "symbol": symbol,
                    "coingecko_id": crypto_id,
                    "timestamp": timestamp,
                    "price": price,
                    "volume": volume
                }
                
                historical_data.append(data_point)
                
                # Save to MongoDB if available
                if mongo_client:
                    try:
                        historical_collection.update_one(
                            {"symbol": symbol, "timestamp": timestamp},
                            {"$set": data_point},
                            upsert=True
                        )
                    except Exception as e:
                        print(f"Error saving historical data for {crypto_id} to MongoDB: {e}")
            
            return historical_data
        else:
            print(f"No historical price data found for {crypto_id}")
            return None
    
    except Exception as e:
        print(f"Error getting historical data for {crypto_id}: {e}")
        return None

def refresh_cache():
    """Refresh the crypto cache with data from CoinGecko"""
    global last_cache_update
    
    current_time = time.time()
    if current_time - last_cache_update < CACHE_DURATION:
        return
    
    print("Refreshing crypto cache from CoinGecko...")
    
    # Update crypto cache
    for crypto_id in CRYPTO_SYMBOLS:
        try:
            data = get_crypto_price_data(crypto_id)
            
            if data:
                symbol = data['symbol']
                
                # Update MongoDB if available
                if mongo_client:
                    try:
                        current_collection.update_one(
                            {"symbol": symbol},
                            {"$set": data},
                            upsert=True
                        )
                    except Exception as e:
                        print(f"Error saving {crypto_id} to MongoDB: {e}")
                
                # Cache in memory as fallback
                crypto_cache[crypto_id] = data
                print(f"Cached {crypto_id} ({symbol}): ${data['price']}")
            else:
                print(f"Error: No price data available for {crypto_id}")
            
            # Add delay between requests to avoid rate limiting
            time.sleep(REQUEST_DELAY)
                
        except Exception as e:
            print(f"Error updating {crypto_id}: {e}")
    
    # Update cache timestamp
    last_cache_update = current_time
    print(f"Cache refresh completed at {datetime.now().isoformat()}")

class StockDataHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Override to customize logging"""
        if args and args[0].startswith('GET /health'):
            # Skip logging health check requests
            return
        
        print("[%s] %s" % (self.log_date_time_string(), format % args))
    
    def _set_headers(self, status_code=200, content_type='application/json'):
        """Set response headers with CORS support"""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        
        # Handle CORS
        origin = self.headers.get('Origin', '')
        
        # Check if the origin is allowed
        if origin in ALLOWED_ORIGINS or '*' in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
        else:
            self.send_header('Access-Control-Allow-Origin', '*')
            
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        self.end_headers()
    
    def _json_response(self, data, status_code=200):
        """Send JSON response"""
        self._set_headers(status_code)
        self.wfile.write(json.dumps(data, cls=DateTimeEncoder).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self._set_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        # Parse the URL path
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)
        
        # Health check endpoint
        if path == '/health':
            self._json_response({'status': 'ok', 'source': 'coingecko'})
            return
        
        # Get all cryptocurrency prices
        if path == '/api/crypto':
            response = self._get_crypto_data()
            self._json_response(response)
            return
        
        # Get all prices (same as /api/crypto for now)
        if path == '/api/prices':
            response = self._get_crypto_data()
            self._json_response(response)
            return
            
        # Get specific crypto data
        if path.startswith('/api/crypto/'):
            crypto_id = path.split('/')[-1]
            response = self._get_specific_crypto(crypto_id)
            self._json_response(response)
            return
            
        # Get historical data
        if path.startswith('/api/historical/'):
            crypto_id = path.split('/')[-1]
            days = int(query.get('days', ['30'])[0])
            response = self._get_historical_data(crypto_id, days)
            self._json_response(response)
            return
        
        # Default response for unknown endpoints
        self._json_response({'error': 'Not found'}, 404)
    
    def _get_specific_crypto(self, crypto_id):
        """Get data for a specific cryptocurrency"""
        # Support both CoinGecko IDs and symbols
        if crypto_id.upper() in [symbol.upper() for symbol in CRYPTO_SYMBOL_MAP.values()]:
            # This is a symbol, find the corresponding CoinGecko ID
            for cg_id, symbol in CRYPTO_SYMBOL_MAP.items():
                if symbol.upper() == crypto_id.upper():
                    crypto_id = cg_id
                    break
        
        # Check MongoDB first
        if mongo_client:
            try:
                symbol = CRYPTO_SYMBOL_MAP.get(crypto_id, crypto_id.upper())
                record = current_collection.find_one({"symbol": symbol})
                
                if record:
                    # Convert MongoDB ObjectId to string
                    if '_id' in record:
                        record['_id'] = str(record['_id'])
                    return record
            except Exception as e:
                print(f"Error fetching {crypto_id} from MongoDB: {e}")
        
        # Check cache if not in MongoDB
        if crypto_id in crypto_cache:
            return crypto_cache[crypto_id]
        
        # If not in cache, fetch fresh data
        try:
            return get_crypto_price_data(crypto_id)
        except Exception as e:
            print(f"Error fetching {crypto_id}: {e}")
            return {'error': str(e)}
    
    def _get_crypto_data(self):
        """Get all cryptocurrency data"""
        # Check if we need to refresh the cache
        current_time = time.time()
        if current_time - last_cache_update > CACHE_DURATION:
            refresh_cache()
        
        # Use MongoDB if available
        if mongo_client:
            try:
                # Get all cryptocurrency records
                crypto_data = list(current_collection.find())
                
                # Convert MongoDB ObjectId to string
                for item in crypto_data:
                    if '_id' in item:
                        item['_id'] = str(item['_id'])
                
                return crypto_data
            except Exception as e:
                print(f"Error fetching crypto data from MongoDB: {e}")
        
        # Fall back to cache
        return list(crypto_cache.values())
    
    def _get_historical_data(self, crypto_id, days=30):
        """Get historical data for a specific cryptocurrency"""
        # Support both CoinGecko IDs and symbols
        if crypto_id.upper() in [symbol.upper() for symbol in CRYPTO_SYMBOL_MAP.values()]:
            # This is a symbol, find the corresponding CoinGecko ID
            for cg_id, symbol in CRYPTO_SYMBOL_MAP.items():
                if symbol.upper() == crypto_id.upper():
                    crypto_id = cg_id
                    break
        
        symbol = CRYPTO_SYMBOL_MAP.get(crypto_id, crypto_id.upper())
        
        # Check MongoDB first
        if mongo_client:
            try:
                cutoff_date = datetime.now() - timedelta(days=days)
                # Query historical collection with the symbol
                data = list(historical_collection.find(
                    {"symbol": symbol, "timestamp": {"$gte": cutoff_date}}
                ).sort("timestamp", -1))
                
                if data and len(data) > 0:
                    # Convert MongoDB ObjectId to string
                    for item in data:
                        if '_id' in item:
                            item['_id'] = str(item['_id'])
                    return data
            except Exception as e:
                print(f"Error fetching historical data for {crypto_id} from MongoDB: {e}")
        
        # If no data in MongoDB or not enough data points, use CoinGecko
        return get_crypto_historical_data(crypto_id, days)

def run_server():
    """Run the HTTP server with port conflict handling"""
    global PORT
    
    for attempt in range(MAX_PORT_ATTEMPTS):
        try:
            # Use ThreadingTCPServer for better handling of multiple requests
            class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
                allow_reuse_address = True
            
            # Create and start the server
            with ThreadedHTTPServer(("", PORT), StockDataHandler) as httpd:
                print(f"CoinGecko crypto data server running at http://localhost:{PORT}")
                
                try:
                    # Start the server
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    print("\nShutting down server...")
                    httpd.server_close()
                    break
            return  # Server started successfully
        except OSError as e:
            if e.errno == 48:  # Address already in use
                print(f"Port {PORT} is already in use. Trying port {PORT + 1}...")
                PORT += 1
            else:
                raise
    
    print(f"Failed to start server after {MAX_PORT_ATTEMPTS} attempts")
    sys.exit(1)

if __name__ == "__main__":
    # Initial cache refresh
    refresh_cache()
    
    # Start the server
    run_server() 