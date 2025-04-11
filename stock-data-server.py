#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
import sys
import time
from urllib.parse import urlparse, parse_qs
from datetime import datetime

try:
    import yfinance as yf
    print("yfinance package loaded successfully")
except ImportError:
    print("ERROR: yfinance package not found. Installing...")
    import subprocess
    
    try:
        # First attempt: Try installing with --break-system-packages flag
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "--break-system-packages"])
        import yfinance as yf
        print("yfinance package installed successfully")
    except (subprocess.CalledProcessError, ImportError) as e:
        print(f"Failed to install with --break-system-packages: {e}")
        
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
            print("3. Install using brew:")
            print("   brew install yfinance")
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

# Cache for stock data
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
                'message': 'yfinance stock data server is running',
                'timestamp': datetime.now().isoformat()
            })
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
                # Check if we should use the cache
                current_time = time.time()
                if current_time - last_cache_update > CACHE_DURATION:
                    # Cache expired, refresh data
                    self._refresh_cache()
                
                # Get data from cache
                results = []
                for symbol in symbols:
                    if not symbol:
                        continue
                    
                    # Determine if it's a crypto symbol
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
        """Fetch stock data for a symbol using yfinance"""
        return get_stock_data(symbol)
    
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
        
        # Initialize the cache on startup - without creating an invalid handler
        # Refresh the cache directly instead
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
    """Refresh the cache with latest data"""
    global last_cache_update, stock_cache, crypto_cache
    
    print("Refreshing stock and crypto cache...")
    
    # Clear existing caches
    stock_cache = {}
    crypto_cache = {}
    
    # Create a temporary handler to use its methods
    handler = StockDataHandler.__new__(StockDataHandler)
    
    # Fetch stock data
    for symbol in STOCK_SYMBOLS:
        try:
            # Call _get_stock_data directly with just the symbol
            data = get_stock_data(symbol)
            stock_cache[symbol] = data
            print(f"Cached {symbol}: {data['price']}")
            time.sleep(REQUEST_DELAY)  # Avoid rate limiting
        except Exception as e:
            print(f"Error caching {symbol}: {e}")
    
    # Fetch crypto data
    for symbol in CRYPTO_SYMBOLS:
        try:
            data = get_stock_data(symbol)
            crypto_cache[symbol] = data
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
        'last_updated': datetime.now().isoformat()
    }

if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        print("Server stopped")
        sys.exit(0) 