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

try:
    import yfinance as yf
    print("yfinance package loaded successfully")
except ImportError:
    print("ERROR: yfinance package not found. Installing...")
    import subprocess
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "--break-system-packages"])
        import yfinance as yf
        print("yfinance package installed successfully")
    except (subprocess.CalledProcessError, ImportError) as e:
        print(f"Failed to install yfinance: {e}")
        
        # Check if we're running in a virtual environment
        in_venv = sys.prefix != sys.base_prefix
        
        if not in_venv:
            print("\nERROR: Cannot install yfinance in an externally managed environment.")
            print("Please use one of the following methods:")
            print("1. Create and activate a virtual environment first:")
            print("   python3 -m venv venv")
            print("   source venv/bin/activate")
            print("   Then run this script again")
            print("2. Install yfinance manually before running this script:")
            print("   pip3 install yfinance --break-system-packages --user")
            sys.exit(1)
        else:
            # If we're in a venv but still failed, try without the flag
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance"])
                import yfinance as yf
                print("yfinance package installed successfully in virtual environment")
            except:
                print("ERROR: Failed to install yfinance even in a virtual environment")
                sys.exit(1)

# Add support for Twelvedata API for real-time prices
try:
    from twelvedata import TDClient
    print("twelvedata package loaded successfully")
except ImportError:
    print("ERROR: twelvedata package not found. Installing...")
    import subprocess
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "twelvedata", "--break-system-packages"])
        from twelvedata import TDClient
        print("twelvedata package installed successfully")
    except (subprocess.CalledProcessError, ImportError) as e:
        print(f"Failed to install twelvedata: {e}")
        
        # Check if we're running in a virtual environment
        in_venv = sys.prefix != sys.base_prefix
        
        if not in_venv:
            print("\nERROR: Cannot install twelvedata in an externally managed environment.")
            print("Please use one of the following methods:")
            print("1. Create and activate a virtual environment first:")
            print("   python3 -m venv venv")
            print("   source venv/bin/activate")
            print("   Then run this script again")
            print("2. Install twelvedata manually before running this script:")
            print("   pip3 install 'twelvedata[websocket]' --break-system-packages --user")
            print("NOTE: The twelvedata integration is optional and the server will still work with yfinance.")
        else:
            # If we're in a venv but still failed, try without the flag
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "twelvedata[websocket]"])
                from twelvedata import TDClient
                print("twelvedata package installed successfully in virtual environment")
            except:
                print("ERROR: Failed to install twelvedata even in a virtual environment")
                print("NOTE: The twelvedata integration is optional and the server will still work with yfinance.")

# Configuration
PORT = 3000
MAX_PORT_ATTEMPTS = 5  # Try up to 5 different ports if the default is in use
ALLOWED_ORIGINS = ['http://localhost:8000', 'http://localhost:3000', 'http://127.0.0.1:8000', 'https://akashpatelresume.us', '*']
STOCK_SYMBOLS = []  # Removed stock symbols
CRYPTO_SYMBOLS = [
    'BTC-USD', 'ETH-USD', 'XRP-USD', 'DOGE-USD', 'SOL-USD', 
    'ADA-USD', 'DOT-USD', 'MATIC-USD', 'LINK-USD', 'AVAX-USD'
]
CACHE_DURATION = 60  # Reduced to 1 minute for more frequent crypto updates
REQUEST_DELAY = 0.2  # 200ms between requests to avoid rate limiting

# MongoDB Configuration
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = 'crypto_ticker'  # Updated database name
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

# Cache for stock data (fallback if MongoDB connection fails)
stock_cache = {}
crypto_cache = {}
last_cache_update = 0

# Twelvedata API Key (set as environment variable for security)
TWELVEDATA_API_KEY = os.environ.get('TWELVEDATA_API_KEY', '')

# Flag to track if Twelvedata is enabled
twelvedata_enabled = TWELVEDATA_API_KEY != '' and 'TDClient' in globals()

# Twelvedata websocket client
td_client = None
ws_connection = None

def get_symbol_key(symbol):
    """Normalize symbol for consistent MongoDB keys"""
    if '-' in symbol:
        return symbol.split('-')[0]  # Extract BTC from BTC-USD
    return symbol

class TwelvedataManager:
    """Manages the Twelvedata websocket connection and crypto data"""
    
    def __init__(self, api_key, symbols):
        self.api_key = api_key
        self.symbols = symbols
        self.client = TDClient(apikey=api_key)
        self.ws = None
        self.connected = False
        self.last_prices = {}
        self.error_count = 0
        self.max_retries = 3
        self.connect()
    
    def on_event(self, event):
        """Handle websocket events from Twelvedata"""
        try:
            if isinstance(event, dict) and 'price' in event and 'symbol' in event:
                symbol = event['symbol']
                price = float(event['price'])
                timestamp = datetime.now()
                
                # Update MongoDB if available
                if mongo_client:
                    try:
                        symbol_key = get_symbol_key(symbol)
                        current_collection.update_one(
                            {"symbol": symbol_key},
                            {
                                "$set": {
                                    "full_symbol": symbol,
                                    "price": price,
                                    "timestamp": timestamp
                                }
                            },
                            upsert=True
                        )
                        
                        historical_collection.insert_one({
                            "symbol": symbol_key,
                            "full_symbol": symbol,
                            "price": price,
                            "timestamp": timestamp
                        })
                    except Exception as e:
                        print(f"MongoDB update error for {symbol}: {e}")
                
                # Update cache as fallback
                self.last_prices[symbol] = {
                    "price": price,
                    "timestamp": timestamp
                }
                
        except Exception as e:
            print(f"Error processing websocket event: {e}")
            print(f"Event data: {event}")
    
    def connect(self):
        """Establish websocket connection with error handling and reconnection"""
        try:
            if self.ws:
                self.ws.stop()
            
            # Initialize websocket
            self.ws = self.client.websocket(symbols=self.symbols)
            
            # Set callbacks
            self.ws.subscribe(self.on_event)
            
            # Start the connection
            self.ws.connect()
            self.connected = True
            print("Successfully connected to Twelvedata websocket")
            
        except Exception as e:
            print(f"Error connecting to Twelvedata websocket: {e}")
            self.error_count += 1
            
            if self.error_count < self.max_retries:
                print(f"Retrying connection... Attempt {self.error_count}/{self.max_retries}")
                time.sleep(5)  # Wait 5 seconds before retrying
                self.connect()
            else:
                print("Max retries reached. Falling back to polling method.")
                self.connected = False
    
    def stop(self):
        """Stop the websocket connection"""
        try:
            if self.ws:
                if hasattr(self.ws, 'stop'):
                    self.ws.stop()
                else:
                    # Alternative method to close websocket if stop() doesn't exist
                    if hasattr(self.ws, 'close') and callable(self.ws.close):
                        self.ws.close()
                    elif hasattr(self.ws, 'disconnect') and callable(self.ws.disconnect):
                        self.ws.disconnect()
        except Exception as e:
            print(f"Error stopping websocket: {e}")
        self.connected = False

# Initialize Twelvedata if API key is available
if TWELVEDATA_API_KEY and 'TDClient' in globals():
    try:
        print("Initializing Twelvedata connection...")
        td_manager = TwelvedataManager(TWELVEDATA_API_KEY, CRYPTO_SYMBOLS)
        print("Twelvedata initialization complete")
    except Exception as e:
        print(f"Failed to initialize Twelvedata: {e}")
        print("Falling back to polling method")
        td_manager = None
else:
    print("Twelvedata API key not found or package not available")
    td_manager = None

print(f"Starting yfinance stock data server on port {PORT}")

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
            self._json_response({'status': 'ok'})
            return
        
        # Get latest cryptocurrency prices
        if path == '/api/crypto':
            response = self._get_crypto_data()
            self._json_response(response)
            return
        
        # Get all stock and crypto prices 
        if path == '/api/prices':
            response = self._get_all_prices()
            self._json_response(response)
            return
            
        # Get specific stock data
        if path.startswith('/api/stock/'):
            symbol = path.split('/')[-1]
            response = self._get_stock_data(symbol)
            self._json_response(response)
            return
            
        # Get historical data
        if path.startswith('/api/historical/'):
            symbol = path.split('/')[-1]
            days = int(query.get('days', ['30'])[0])
            response = self._get_historical_data(symbol, days)
            self._json_response(response)
            return
        
        # Default response for unknown endpoints
        self._json_response({'error': 'Not found'}, 404)
    
    def _get_stock_data(self, symbol):
        """Get data for a specific stock or crypto"""
        # Check MongoDB first
        if mongo_client:
            try:
                # Use normalized symbol key
                symbol_key = get_symbol_key(symbol)
                record = current_collection.find_one({"symbol": symbol_key})
                
                if record:
                    # Convert MongoDB ObjectId to string
                    if '_id' in record:
                        record['_id'] = str(record['_id'])
                    return record
            except Exception as e:
                print(f"Error fetching {symbol} from MongoDB: {e}")
        
        # Check cache if not in MongoDB
        if "-USD" in symbol:
            if symbol in crypto_cache:
                return crypto_cache[symbol]
        elif symbol in stock_cache:
            return stock_cache[symbol]
        
        # Fetch fresh data if not in cache
        try:
            return get_stock_data(symbol)
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return {'error': str(e)}
    
    def _get_crypto_data(self):
        """Get cryptocurrency data"""
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
    
    def _get_all_prices(self):
        """Get all stock and crypto prices"""
        # Check if we need to refresh the cache
        current_time = time.time()
        if current_time - last_cache_update > CACHE_DURATION:
            refresh_cache()
        
        # Combine stock and crypto data
        all_data = []
        
        # Use MongoDB if available
        if mongo_client:
            try:
                # Get all records
                all_data = list(current_collection.find())
                
                # Convert MongoDB ObjectId to string
                for item in all_data:
                    if '_id' in item:
                        item['_id'] = str(item['_id'])
                
                return all_data
            except Exception as e:
                print(f"Error fetching all data from MongoDB: {e}")
        
        # Fall back to cache
        all_data = list(stock_cache.values()) + list(crypto_cache.values())
        return all_data

    def _get_historical_data(self, symbol, days=30):
        """Get historical data for a specific symbol"""
        symbol_key = get_symbol_key(symbol)
        
        # Check MongoDB first
        if mongo_client:
            try:
                cutoff_date = datetime.now() - timedelta(days=days)
                # Query historical collection with the normalized symbol key
                data = list(historical_collection.find(
                    {"symbol": symbol_key, "timestamp": {"$gte": cutoff_date}}
                ).sort("timestamp", -1))
                
                if data and len(data) > 0:
                    # Convert MongoDB ObjectId to string
                    for item in data:
                        if '_id' in item:
                            item['_id'] = str(item['_id'])
                    return data
            except Exception as e:
                print(f"Error fetching historical data for {symbol} from MongoDB: {e}")
        
        # If no data in MongoDB or not enough data points, use yfinance
        try:
            ticker = yf.Ticker(symbol)
            history = ticker.history(period=f"{days}d")
            
            if history.empty:
                return {"error": f"No historical data found for {symbol}"}
            
            # Format the data
            historical_data = []
            for date, row in history.iterrows():
                timestamp = date.to_pydatetime()
                
                data_point = {
                    "symbol": symbol_key,
                    "full_symbol": symbol,
                    "timestamp": timestamp,
                    "price": float(row["Close"]),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "volume": int(row["Volume"]) if "Volume" in row else 0
                }
                
                historical_data.append(data_point)
                
                # Save to MongoDB if available
                if mongo_client:
                    try:
                        historical_collection.insert_one(data_point)
                    except Exception as e:
                        print(f"Error saving historical data for {symbol} to MongoDB: {e}")
            
            return historical_data
        except Exception as e:
            print(f"Error fetching historical data for {symbol} from yfinance: {e}")
            return {"error": str(e)}

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
                print(f"Server running at http://localhost:{PORT}")
                
                try:
                    # Start the server
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    print("\nShutting down server...")
                    if td_manager:
                        td_manager.stop()
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
    if td_manager:
        td_manager.stop()
    sys.exit(1)

# Helper function to refresh cache outside of the handler class
def refresh_cache():
    """Refresh the stock and crypto cache"""
    global last_cache_update
    
    current_time = time.time()
    if current_time - last_cache_update < CACHE_DURATION:
        return
    
    print("Refreshing stock and crypto cache...")
    
    # Update crypto cache with yfinance fallback
    for symbol in CRYPTO_SYMBOLS:
        try:
            data = get_stock_data(symbol)
            
            if data and 'price' in data:
                symbol_key = get_symbol_key(symbol)
                
                # Update MongoDB if available
                if mongo_client:
                    try:
                        current_collection.update_one(
                            {"symbol": symbol_key},
                            {"$set": {
                                "full_symbol": symbol,
                                "price": data['price'],
                                "timestamp": datetime.now(),
                                "volume": data.get('volume', 0),
                                "change_percent": data.get('change_percent', 0)
                            }},
                            upsert=True
                        )
                    except Exception as e:
                        print(f"Error saving {symbol} to MongoDB: {e}")
                
                # Cache in memory as fallback
                crypto_cache[symbol] = data
                print(f"Cached {symbol}: {data['price']}")
            else:
                print(f"Error: No price data available for {symbol}")
                
        except Exception as e:
            print(f"Error updating {symbol}: {e}")
    
    # Update cache timestamp
    last_cache_update = current_time
    print(f"Cache refresh completed at {datetime.now().isoformat()}")

# Fix the get_stock_data function to handle symbol format consistently
def get_stock_data(symbol):
    """Get stock or crypto data from yfinance API"""
    try:
        # Get data from yfinance
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="1d")
        
        if history.empty:
            print(f"No data found for {symbol}")
            return None
        
        # Get the latest price (last row)
        last_row = history.iloc[-1]
        current_price = round(float(last_row["Close"]), 2)
        
        # Calculate change percentage
        if "Open" in last_row:
            open_price = float(last_row["Open"])
            if open_price > 0:
                change_percent = round(((current_price - open_price) / open_price) * 100, 2)
            else:
                change_percent = 0
        else:
            change_percent = 0
        
        # Get volume if available
        volume = int(last_row["Volume"]) if "Volume" in last_row else 0
        
        data = {
            "symbol": get_symbol_key(symbol),
            "full_symbol": symbol,
            "price": current_price,
            "volume": volume,
            "change_percent": change_percent,
            "timestamp": datetime.now()
        }
        
        return data
    
    except Exception as e:
        print(f"Error getting data for {symbol}: {e}")
        return None

def get_twelvedata_historical(symbol, days=30):
    """Fetch historical data using Twelvedata REST API"""
    if not TWELVEDATA_API_KEY:
        print("Twelvedata API key not set, cannot fetch historical data")
        return None
    
    # Calculate start date (days ago from today)
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    # Base URL for the API
    base_url = "https://api.twelvedata.com/time_series"
    
    # Parameters for the request
    params = {
        "apikey": TWELVEDATA_API_KEY,
        "symbol": symbol,
        "interval": "1day",  # Daily data
        "format": "JSON",
        "start_date": start_date
    }
    
    try:
        # Make the request
        print(f"Fetching historical data for {symbol} from Twelvedata API...")
        response = requests.get(base_url, params=params)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Check if we got valid data
            if "values" in data:
                # Format the response for our API
                result = []
                for value in data["values"]:
                    # Convert string date to datetime object
                    timestamp = datetime.strptime(value["datetime"], "%Y-%m-%d")
                    
                    # Create data point in our format
                    data_point = {
                        "symbol": symbol,
                        "timestamp": timestamp,
                        "price": value["close"],
                        "open": value["open"],
                        "high": value["high"],
                        "low": value["low"],
                        "volume": int(float(value.get("volume", 0))),
                        "source": "twelvedata_rest"
                    }
                    result.append(data_point)
                    
                    # Save to MongoDB if available
                    if mongo_client:
                        try:
                            historical_collection.update_one(
                                {"symbol": symbol, "timestamp": timestamp},
                                {"$set": data_point},
                                upsert=True
                            )
                        except Exception as e:
                            print(f"Error saving historical data for {symbol} to MongoDB: {e}")
                
                print(f"Retrieved {len(result)} historical data points for {symbol}")
                return result
            else:
                print(f"No historical values found for {symbol}")
                if "message" in data:
                    print(f"Twelvedata API message: {data['message']}")
                return None
        else:
            print(f"Error fetching historical data: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Exception fetching historical data from Twelvedata: {e}")
        return None

if __name__ == "__main__":
    # Initial cache refresh
    refresh_cache()
    
    # Start the server
    run_server() 