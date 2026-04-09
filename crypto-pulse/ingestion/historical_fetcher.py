import requests
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Binance API Configuration
BINANCE_KLINE_URL = "https://api.binance.com/api/v3/klines"
# Top 50 coins (list can be expanded)
SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "SOLUSDT", "DOTUSDT", "DOGEUSDT", "MATICUSDT", "LINKUSDT", 
           "LTCUSDT", "BCHUSDT", "XLMUSDT", "SHIBUSDT", "TRXUSDT", "AVAXUSDT", "UNIUSDT", "ALGOUSDT", "XMRUSDT", "ATOMUSDT"]
# Start date: January 1, 2021
START_DATE = int(datetime(2021, 1, 1).timestamp() * 1000)

def fetch_klines(symbol, start_time, interval="1d"):
    """Fetch klines (OHLCV) from Binance with pagination support."""
    all_data = []
    current_start = start_time
    
    print(f"Fetching historical data for {symbol} starting from {datetime.fromtimestamp(start_time/1000)}...")
    
    while True:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": current_start,
            "limit": 1000  # Max limit per request
        }
        
        try:
            response = requests.get(BINANCE_KLINE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                break
                
            all_data.extend(data)
            
            # Update start time for next iteration: last timestamp + 1 interval
            # Binance klines return: [open_time, open, high, low, close, volume, close_time, ...]
            last_timestamp = data[-1][0]
            current_start = last_timestamp + 1
            
            # If the last timestamp is close to current time, stop
            if last_timestamp > int(time.time() * 1000) - (86400 * 1000):
                break
                
            # Rate limiting (respect Binance limits)
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            break
            
    return all_data

def run_historical_ingestion():
    """ Loop through all symbols and trigger their data fetching and saving directly to disk. """
    output_dir = "./data/historical"
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    for symbol in SYMBOLS:
        # 1. Fetch raw list from Binance REST API
        raw_data = fetch_klines(symbol, START_DATE)
        
        if not raw_data:
            print(f"Skipping {symbol}: No data received.")
            continue
            
        # 2. Save raw data as JSON dump to the local directory
        filename = f"{output_dir}/{symbol}_historical.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(raw_data, f)
            print(f"Successfully saved {len(raw_data)} klines to {filename}.")
        except Exception as e:
            print(f"Failed to save {symbol} data: {e}")

if __name__ == "__main__":
    run_historical_ingestion()
