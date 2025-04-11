#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
import sys
import time
from urllib.parse import urlparse, parse_qs
from datetime import datetime

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

# Configuration
PORT = 3000
ALLOWED_ORIGINS = ['http://localhost:8000', 'http://localhost:3000', 'http://127.0.0.1:8000', 'https://akashpatelresume.us', '*']
STOCK_SYMBOLS = ['SPY', 'AAPL', 'MSFT', 'NVDA', 'META', 'TSLA', 'GOOGL', 'PLTR', 'GME']
CRYPTO_SYMBOLS = ['BTC-USD', 'ETH-USD', 'XRP-USD', 'DOGE-USD']
CACHE_DURATION = 300  # 5 minutes in seconds
REQUEST_DELAY = 0.2  # 200ms between requests to avoid rate limiting

# MongoDB Configuration
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = 'stock_ticker'
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

print(f"Starting yfinance stock data server on port {PORT}")

class StockDataHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Override to provide more detailed logging"""
        sys.stderr.write("%s - - [%s] %s\n" %
                        (self.address_string(),
                        self.log_date_time_string(),
                        format % args))
    
    def _set_headers(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        
        # Add CORS headers
        origin = self.headers.get('Origin', '')
        print(f"Received request with origin: {origin}")
        
        # Always add CORS headers - allow from all origins for testing
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
        
        self.end_headers()
    
    def _json_response(self, data, status_code=200):
        self._set_headers(status_code)
        response = json.dumps(data).encode()
        self.wfile.write(response)
    
    def do_OPTIONS(self):
        # Handle CORS preflight requests
        print("Handling OPTIONS request (CORS preflight)")
        self._set_headers()
        self.wfile.write(b'')
    
    def do_GET(self):
        print(f"Handling GET request for: {self.path}")
        
        # Parse the URL
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        # Health check endpoint
        if path == '/health' or path == '/':
            self._json_response({
                'status': 'up',
                'message': 'yfinance stock data server with MongoDB is running',
                'mongo_connected': mongo_client is not None,
                'timestamp': datetime.now().isoformat()
            })
            return
        
        # Historical data endpoint
        if path.startswith('/api/historical/'):
            symbol = path.split('/')[-1]
            days = int(query_params.get('days', ['30'])[0])
            print(f"Fetching historical data for: {symbol}, days: {days}")
            
            try:
                historical_data = self._get_historical_data(symbol, days)
                self._json_response(historical_data)
            except Exception as e:
                print(f"Error fetching historical data for {symbol}: {e}")
                self._json_response({
                    'error': f"Failed to fetch historical data for {symbol}: {str(e)}"
                }, 500)
            return
        
        # Single quote endpoint
        if path.startswith('/api/quote/'):
            symbol = path.split('/')[-1]
            print(f"Fetching quote for: {symbol}")
            
            try:
                # Get data for the symbol
                quote_data = self._get_stock_data(symbol)
                self._json_response(quote_data)
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
                self._json_response({
                    'error': f"Failed to fetch data for {symbol}: {str(e)}"
                }, 500)
            return
        
        # Multiple quotes endpoint
        if path == '/api/quotes':
            # Parse symbols parameter
            symbols_param = query_params.get('symbols', [''])[0]
            if not symbols_param:
                symbols = STOCK_SYMBOLS + CRYPTO_SYMBOLS
            else:
                symbols = symbols_param.split(',')
            
            print(f"Fetching quotes for: {symbols}")
            
            try:
                # Check if we should use the cache or refresh from API
                current_time = time.time()
                if current_time - last_cache_update > CACHE_DURATION:
                    # Cache expired, refresh data
                    self._refresh_cache()
                
                # Get data from MongoDB or cache
                results = []
                for symbol in symbols:
                    if not symbol:
                        continue
                    
                    # Get from MongoDB if available
                    if mongo_client:
                        data = current_collection.find_one({"symbol": symbol})
                        if data:
                            # Remove MongoDB _id field and convert to dict
                            data.pop('_id', None)
                            results.append(data)
                            continue
                    
                    # Fallback to cache if MongoDB failed or data not found
                    is_crypto = any(crypto in symbol.upper() for crypto in ['BTC', 'ETH', 'XRP', 'DOGE']) or '-USD' in symbol.upper()
                    cache_to_use = crypto_cache if is_crypto else stock_cache
                    
                    if symbol in cache_to_use:
                        results.append(cache_to_use[symbol])
                    else:
                        # Not in cache, fetch it directly
                        try:
                            quote_data = self._get_stock_data(symbol)
                            results.append(quote_data)
                            # Add to appropriate cache
                            cache_to_use[symbol] = quote_data
                        except Exception as e:
                            print(f"Error fetching data for {symbol}: {e}")
                
                self._json_response(results)
            except Exception as e:
                print(f"Error fetching quotes: {e}")
                self._json_response({
                    'error': f"Failed to fetch quotes: {str(e)}"
                }, 500)
            return
        
        # If we reach here, path was not found
        self._json_response({
            'error': f"Endpoint not found: {path}"
        }, 404)
    
    def _get_stock_data(self, symbol):
        """Fetch stock data for a symbol using yfinance and save to MongoDB"""
        data = get_stock_data(symbol)
        
        # Save to MongoDB if available
        if mongo_client:
            try:
                # Update current price in the current collection
                current_collection.update_one(
                    {"symbol": symbol},
                    {"$set": data},
                    upsert=True
                )
                
                # Add to historical collection
                historical_data = data.copy()
                historical_data['timestamp'] = datetime.now()
                historical_collection.insert_one(historical_data)
                
                print(f"Saved {symbol} data to MongoDB")
            except Exception as e:
                print(f"Error saving {symbol} to MongoDB: {e}")
        
        return data
    
    def _get_historical_data(self, symbol, days=30):
        """Get historical data for a symbol from MongoDB or YFinance"""
        if mongo_client:
            # Try to get from MongoDB first
            cutoff_date = datetime.now()
            cutoff_date = cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)
            # Adjust cutoff_date based on days parameter
            
            historical_data = list(historical_collection.find(
                {"symbol": symbol, "timestamp": {"$gte": cutoff_date}},
                {"_id": 0}
            ).sort("timestamp", -1))
            
            if historical_data and len(historical_data) > 10:  # Enough data points
                return historical_data
        
        # If MongoDB doesn't have data or not connected, fetch from YFinance
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=f"{days}d")
        
        # Format the data
        result = []
        for date, row in hist.iterrows():
            data_point = {
                "symbol": symbol,
                "timestamp": date.to_pydatetime(),
                "price": f"{row['Close']:.2f}",
                "open": f"{row['Open']:.2f}",
                "high": f"{row['High']:.2f}",
                "low": f"{row['Low']:.2f}",
                "volume": int(row['Volume'])
            }
            result.append(data_point)
            
            # Save to MongoDB if available
            if mongo_client:
                try:
                    historical_collection.update_one(
                        {"symbol": symbol, "timestamp": data_point["timestamp"]},
                        {"$set": data_point},
                        upsert=True
                    )
                except Exception as e:
                    print(f"Error saving historical data for {symbol} to MongoDB: {e}")
        
        return result
    
    def _refresh_cache(self):
        """Refresh the cache with latest data"""
        refresh_cache()

def run_server():
    # Use ThreadingTCPServer for better handling of multiple requests
    class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True
    
    try:
        httpd = ThreadedHTTPServer(("", PORT), StockDataHandler)
        print(f"yfinance stock data server running at http://localhost:{PORT}")
        
        # Initialize the cache on startup
        print("Initializing stock and crypto cache...")
        refresh_cache()
        
        httpd.serve_forever()
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"ERROR: Port {PORT} is already in use. Try killing any existing processes on this port.")
            print(f"You can use 'lsof -i :{PORT}' to find processes using this port.")
            sys.exit(1)
        else:
            raise

# Helper function to refresh cache outside of the handler class
def refresh_cache():
    """Refresh the cache with latest data and update MongoDB"""
    global last_cache_update, stock_cache, crypto_cache
    
    print("Refreshing stock and crypto cache...")
    
    # Clear existing caches
    stock_cache = {}
    crypto_cache = {}
    
    # Fetch stock data
    for symbol in STOCK_SYMBOLS:
        try:
            data = get_stock_data(symbol)
            stock_cache[symbol] = data
            
            # Save to MongoDB if available
            if mongo_client:
                try:
                    # Update current price
                    current_collection.update_one(
                        {"symbol": symbol},
                        {"$set": data},
                        upsert=True
                    )
                    
                    # Add to historical collection
                    historical_data = data.copy()
                    historical_data['timestamp'] = datetime.now()
                    historical_collection.insert_one(historical_data)
                except Exception as e:
                    print(f"Error saving {symbol} to MongoDB: {e}")
            
            print(f"Cached {symbol}: {data['price']}")
            time.sleep(REQUEST_DELAY)  # Avoid rate limiting
        except Exception as e:
            print(f"Error caching {symbol}: {e}")
    
    # Fetch crypto data
    for symbol in CRYPTO_SYMBOLS:
        try:
            data = get_stock_data(symbol)
            crypto_cache[symbol] = data
            
            # Save to MongoDB if available
            if mongo_client:
                try:
                    # Update current price
                    current_collection.update_one(
                        {"symbol": symbol},
                        {"$set": data},
                        upsert=True
                    )
                    
                    # Add to historical collection
                    historical_data = data.copy()
                    historical_data['timestamp'] = datetime.now()
                    historical_collection.insert_one(historical_data)
                except Exception as e:
                    print(f"Error saving {symbol} to MongoDB: {e}")
            
            print(f"Cached {symbol}: {data['price']}")
            time.sleep(REQUEST_DELAY)  # Avoid rate limiting
        except Exception as e:
            print(f"Error caching {symbol}: {e}")
    
    # Update last cache update time
    last_cache_update = time.time()
    print(f"Cache refresh completed at {datetime.now().isoformat()}")

# Function to get stock data outside of the handler class
def get_stock_data(symbol):
    """Fetch stock data for a symbol using yfinance"""
    # Download the ticker data
    ticker = yf.Ticker(symbol)
    info = ticker.info
    
    # Get current price and previous close
    current_price = info.get('regularMarketPrice', 0)
    prev_close = info.get('previousClose', 0)
    
    # Calculate change
    change = current_price - prev_close
    change_percent = ((current_price / prev_close) - 1) * 100 if prev_close else 0
    
    # Determine if it's a crypto symbol
    is_crypto = any(crypto in symbol.upper() for crypto in ['BTC', 'ETH', 'XRP', 'DOGE']) or '-USD' in symbol.upper()
    
    # Format price based on type (more decimal places for crypto)
    price_str = f"{current_price:.4f}" if is_crypto and current_price < 1 else f"{current_price:.2f}"
    change_str = f"{change:.4f}" if is_crypto and abs(change) < 1 else f"{change:.2f}"
    
    # Format percent change with sign
    change_percent_str = f"{'+' if change_percent >= 0 else ''}{change_percent:.2f}%"
    
    # Extract just the symbol part (e.g., BTC-USD → BTC)
    display_symbol = symbol.split('-')[0]
    
    return {
        'symbol': display_symbol,
        'price': price_str,
        'change': change_str,
        'changePercent': change_percent_str,
        'raw_price': current_price,
        'raw_change': change,
        'raw_change_percent': change_percent,
        'last_updated': datetime.now().isoformat()
    }

if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        print("Server stopped")
        
        # Close MongoDB connection
        if mongo_client:
            mongo_client.close()
            print("MongoDB connection closed")
        
        sys.exit(0) 