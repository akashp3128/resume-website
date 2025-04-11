#!/usr/bin/env python3
from twelvedata import TDClient
import os
import time

# Get API key from environment variable or use demo
API_KEY = os.environ.get("TWELVEDATA_API_KEY", "demo")

def on_event(event):
    """Handle price update events from Twelvedata"""
    print(f"Received price update: {event}")

def main():
    print("Starting Twelvedata websocket test...")
    
    # List of symbols to track
    symbols = ["AAPL", "MSFT", "NVDA", "SPY", "BTC/USD"]
    
    print(f"Using API key: {API_KEY}")
    
    # Initialize TDClient
    td = TDClient(apikey=API_KEY)
    
    # Initialize websocket connection with event handler
    print(f"Creating websocket for symbols: {symbols}")
    ws = td.websocket(symbols=symbols, on_event=on_event)
    
    # Connect to the websocket
    print("Connecting to Twelvedata websocket...")
    try:
        ws.connect()
        print("Connected successfully! Waiting for price updates (Ctrl+C to exit)")
        
        # Keep the connection alive in the main thread
        ws.keep_alive()
    except Exception as e:
        print(f"Error connecting to websocket: {e}")
        print("Make sure you have a valid API key in the .env file")
        print("Note: The demo key has limited functionality")

if __name__ == "__main__":
    main() 