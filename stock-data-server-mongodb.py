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
# Use CoinGecko IDs here as the /markets endpoint uses IDs
CRYPTO_IDS = [
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

CACHE_DURATION = 300  # Increased cache duration to 5 minutes
# REQUEST_DELAY = 0.5 # No longer needed with bulk API calls

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
    """Refresh the crypto cache using the bulk /coins/markets endpoint"""
    global last_cache_update, crypto_cache
    
    current_time = time.time()
    if current_time - last_cache_update < CACHE_DURATION:
        return
    
    print(f"Refreshing crypto cache from CoinGecko ({datetime.now().isoformat()})...")
    
    try:
        url = f"{COINGECKO_API_URL}/coins/markets"
        params = {
            'vs_currency': 'usd',
            'ids': ','.join(CRYPTO_IDS),
            'order': 'market_cap_desc', # Although ids are specified, order doesn't hurt
            'per_page': len(CRYPTO_IDS),
            'page': 1,
            'sparkline': 'false',
            'price_change_percentage': '24h' # Request 24h price change
        }
        
        response = requests.get(url, params=params, timeout=10) # Added timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            
        data = response.json()
        new_cache_data = {}
        
        if not isinstance(data, list):
            print(f"Error: Unexpected data format received from CoinGecko: {type(data)}")
            return

        print(f"Received {len(data)} coin records from CoinGecko.")
        processed_count = 0

        for coin_data in data:
            crypto_id = coin_data.get('id')
            if not crypto_id:
                print(f"Warning: Skipping record with missing ID: {coin_data.get('symbol')}")
                continue

            symbol = coin_data.get('symbol', '').upper()
            price_usd = coin_data.get('current_price')
            price_change_24h_percent = coin_data.get('price_change_percentage_24h')
            volume = coin_data.get('total_volume')
            market_cap = coin_data.get('market_cap')
            name = coin_data.get('name')
            
            # Handle potential null values
            if price_usd is None or price_change_24h_percent is None:
                 print(f"Warning: Skipping {symbol} due to missing price or change data.")
                 continue
                 
            formatted_data = {
                "symbol": symbol,
                "coingecko_id": crypto_id,
                "name": name,
                "price": float(price_usd),
                "change_percent_24h": float(price_change_24h_percent),
                "volume": float(volume) if volume is not None else 0,
                "market_cap": float(market_cap) if market_cap is not None else 0,
                "timestamp": datetime.now()
            }
            
            # Update MongoDB if available
            if mongo_client:
                try:
                    current_collection.update_one(
                        {"symbol": symbol}, # Use symbol as the unique key
                        {"$set": formatted_data},
                        upsert=True
                    )
                except Exception as e:
                    print(f"Error saving {symbol} to MongoDB: {e}")
            
            # Update the temporary cache using ID as key
            new_cache_data[crypto_id] = formatted_data
            processed_count += 1

        # Atomically update the main cache
        crypto_cache = new_cache_data
        last_cache_update = current_time
        print(f"Cache refresh successful. Processed {processed_count} coins at {datetime.fromtimestamp(last_cache_update).isoformat()}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from CoinGecko /coins/markets: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response from CoinGecko: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during cache refresh: {e}")

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
        # Refresh cache if needed (moved check here for efficiency)
        refresh_cache()
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)
        
        # Health check endpoint
        if path == '/health':
            self._json_response({'status': 'ok', 'source': 'coingecko'})
            return
        
        # Get all cryptocurrency prices
        if path == '/api/crypto' or path == '/api/prices':
            response = self._get_crypto_data()
            self._json_response(response)
            return
            
        # Get specific crypto data
        if path.startswith('/api/crypto/'):
            crypto_id_or_symbol = path.split('/')[-1]
            response = self._get_specific_crypto(crypto_id_or_symbol)
            self._json_response(response)
            return
            
        # Get historical data
        if path.startswith('/api/historical/'):
            crypto_id_or_symbol = path.split('/')[-1]
            days = int(query.get('days', ['30'])[0])
            response = self._get_historical_data(crypto_id_or_symbol, days)
            self._json_response(response)
            return
        
        # Default response for unknown endpoints
        self._json_response({'error': 'Not found'}, 404)
    
    def _get_specific_crypto(self, crypto_id_or_symbol):
        """Get data for a specific cryptocurrency from cache/DB"""
        target_symbol = None
        target_id = None

        # Check if input is a symbol
        if crypto_id_or_symbol.upper() in CRYPTO_SYMBOL_MAP.values():
            target_symbol = crypto_id_or_symbol.upper()
            # Find the corresponding ID
            for cg_id, sym in CRYPTO_SYMBOL_MAP.items():
                if sym == target_symbol:
                    target_id = cg_id
                    break
        # Assume it's an ID if not a known symbol
        elif crypto_id_or_symbol.lower() in CRYPTO_IDS:
             target_id = crypto_id_or_symbol.lower()
             target_symbol = CRYPTO_SYMBOL_MAP.get(target_id)
        else:
            return {'error': f'Unknown symbol or ID: {crypto_id_or_symbol}'}

        # Check MongoDB first (using symbol as key)
        if mongo_client and target_symbol:
            try:
                record = current_collection.find_one({"symbol": target_symbol})
                if record:
                    if '_id' in record: record['_id'] = str(record['_id']) # Convert ObjectId
                    print(f"Retrieved {target_symbol} from MongoDB")
                    return record
            except Exception as e:
                print(f"Error fetching {target_symbol} from MongoDB: {e}")
        
        # Check cache (using ID as key)
        if target_id and target_id in crypto_cache:
            print(f"Retrieved {target_symbol} ({target_id}) from cache")
            return crypto_cache[target_id]
        
        # Data not found
        print(f"Data for {target_symbol} ({target_id}) not found in cache or DB.")
        return {'error': f'Data for {crypto_id_or_symbol} currently unavailable'}
    
    def _get_crypto_data(self):
        """Get all cryptocurrency data from cache/DB"""
        # Use MongoDB if available
        if mongo_client:
            try:
                crypto_data = list(current_collection.find())
                if crypto_data: # Ensure we have data before returning
                    for item in crypto_data: # Convert ObjectId
                        if '_id' in item: item['_id'] = str(item['_id'])
                    print(f"Retrieved {len(crypto_data)} records from MongoDB")
                    return crypto_data
                else:
                    print("MongoDB collection is empty, falling back to cache.")
            except Exception as e:
                print(f"Error fetching all crypto data from MongoDB: {e}")
        
        # Fall back to in-memory cache
        print(f"Retrieved {len(crypto_cache)} records from in-memory cache.")
        return list(crypto_cache.values())
    
    def _get_historical_data(self, crypto_id_or_symbol, days=30):
         """Get historical data for a specific cryptocurrency"""
         target_symbol = None
         target_id = None

         # Determine ID and Symbol from input
         if crypto_id_or_symbol.upper() in CRYPTO_SYMBOL_MAP.values():
             target_symbol = crypto_id_or_symbol.upper()
             for cg_id, sym in CRYPTO_SYMBOL_MAP.items():
                 if sym == target_symbol:
                     target_id = cg_id
                     break
         elif crypto_id_or_symbol.lower() in CRYPTO_IDS:
             target_id = crypto_id_or_symbol.lower()
             target_symbol = CRYPTO_SYMBOL_MAP.get(target_id)
         else:
             return {'error': f'Unknown symbol or ID for historical data: {crypto_id_or_symbol}'}

         if not target_id or not target_symbol:
             return {'error': f'Could not resolve ID/Symbol: {crypto_id_or_symbol}'}

         # Check MongoDB first
         if mongo_client:
             try:
                 cutoff_date = datetime.now() - timedelta(days=days)
                 data = list(historical_collection.find(
                     {"symbol": target_symbol, "timestamp": {"$gte": cutoff_date}}
                 ).sort("timestamp", -1))
                
                 if data and len(data) >= days * 0.8: # Check if we have reasonable amount of data
                     print(f"Retrieved {len(data)} historical records for {target_symbol} from MongoDB")
                     for item in data: # Convert ObjectId
                         if '_id' in item: item['_id'] = str(item['_id'])
                     return data
                 else:
                     print(f"Found {len(data)} historical records for {target_symbol} in MongoDB, fetching fresh from CoinGecko.")
             except Exception as e:
                 print(f"Error fetching historical data for {target_symbol} from MongoDB: {e}")
        
         # If no/insufficient data in MongoDB, fetch from CoinGecko directly
         print(f"Fetching fresh historical data for {target_symbol} ({target_id}) from CoinGecko.")
         return get_crypto_historical_data(target_id, days)

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
    # Initial cache population before starting server
    refresh_cache()
    # Run the server
    run_server() 