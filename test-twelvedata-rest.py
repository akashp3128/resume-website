#!/usr/bin/env python3
import requests
import json
import os
from datetime import datetime, timedelta

# Replace with your actual API key or get from environment variable
API_KEY = os.environ.get("TWELVEDATA_API_KEY", "demo")

# If no API key is provided, prompt the user only if demo key is not acceptable
if API_KEY == "demo":
    use_demo = input("Use demo API key? (y/n, default: y): ").lower()
    if use_demo != "n":
        print("Using demo API key with limited functionality")
    else:
        API_KEY = input("Enter your Twelvedata API key: ")

def get_time_series(symbol="SPY", interval="1day", start_date=None, end_date=None):
    """
    Get time series data for a symbol using Twelvedata REST API
    """
    # Calculate start date if not provided (default to 30 days ago)
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # Base URL for the API
    base_url = "https://api.twelvedata.com/time_series"
    
    # Parameters for the request
    params = {
        "apikey": API_KEY,
        "symbol": symbol,
        "interval": interval,
        "format": "JSON",
        "start_date": start_date
    }
    
    # Add end_date if provided
    if end_date:
        params["end_date"] = end_date
    
    # Make the request
    print(f"Fetching time series data for {symbol} from {start_date}...")
    response = requests.get(base_url, params=params)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def main():
    # Example usage
    symbol = "SPY"
    interval = "1day"
    start_date = "2020-12-29"
    
    # Get the time series data
    data = get_time_series(symbol, interval, start_date)
    
    # Print the data
    if data and "values" in data:
        print(f"Retrieved {len(data['values'])} data points for {symbol}")
        print("\nMost recent data points:")
        for i, value in enumerate(data["values"][:5]):
            print(f"{value['datetime']}: Open: {value['open']}, Close: {value['close']}, High: {value['high']}, Low: {value['low']}")
    else:
        print("Failed to retrieve data or no values returned")
        if data:
            print(json.dumps(data, indent=2))

if __name__ == "__main__":
    main() 