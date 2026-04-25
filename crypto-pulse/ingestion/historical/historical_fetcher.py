import requests
import json
import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Binance API Configuration
BINANCE_KLINE_URL = "https://api.binance.com/api/v3/klines"
# Top 50 coins (list can be expanded)
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "SOLUSDT", "DOTUSDT", "DOGEUSDT", 
    "MATICUSDT", "LINKUSDT", "LTCUSDT", "BCHUSDT", "XLMUSDT", "SHIBUSDT", "TRXUSDT", 
    "AVAXUSDT", "UNIUSDT", "ALGOUSDT", "XMRUSDT", "ATOMUSDT"
]

# Start date: January 1, 2021
START_DATE = int(datetime(2021, 1, 1).timestamp() * 1000)

def fetch_klines_for_symbol(symbol, start_time, interval="1d"):
    """Fetch klines (OHLCV) from Binance with pagination support."""
    all_data = []
    current_start = start_time
    
    logger.info(f"Fetching raw historical data for {symbol} starting from {datetime.fromtimestamp(start_time/1000)}...")
    
    # Retry configuration
    max_retries = 3
    
    while True:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": current_start,
            "limit": 1000  # Max limit per request
        }
        
        retries = 0
        success = False
        while retries < max_retries and not success:
            try:
                response = requests.get(BINANCE_KLINE_URL, params=params, timeout=10)
                
                # Check for rate limit
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logger.warning(f"Rate limited for {symbol}. Retrying in {retry_after} seconds...")
                    time.sleep(retry_after)
                    retries += 1
                    continue
                    
                response.raise_for_status()
                data = response.json()
                success = True
            except Exception as e:
                logger.error(f"Error fetching {symbol} at {current_start}: {e}")
                retries += 1
                time.sleep(2)
        
        if not success or not data:
            break
            
        all_data.extend(data)
        
        # Last timestamp + 1 millisecond
        last_timestamp = data[-1][0]
        current_start = last_timestamp + 1
        
        # Stop condition: reached within yesterday
        if last_timestamp > int(time.time() * 1000) - (86400 * 1000):
            break
            
        # Optional sleep to be gentle on API
        time.sleep(0.1)
        
    return symbol, all_data

def get_start_date(symbol, output_dir):
    """Determines the start date by reading the last timestamp from the existing JSON file."""
    filename = os.path.join(output_dir, f"{symbol.lower()}_raw_klines.json")
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                if data:
                    last_timestamp = data[-1][0]
                    logger.info(f"Found existing data for {symbol}. Resuming from timestamp: {last_timestamp}")
                    return last_timestamp + 1
        except Exception as e:
            logger.warning(f"Could not read existing data for {symbol}. Starting from default date. Error: {e}")
    return START_DATE

def save_raw_data_to_json(symbol, new_data, output_dir):
    """Saves the raw klines data to a local JSON file, appending to existing data if present."""
    if not new_data:
        logger.info(f"No new data to save for {symbol}. It is already up to date.")
        return False
        
    filename = os.path.join(output_dir, f"{symbol.lower()}_raw_klines.json")
    existing_data = []
    
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                existing_data = json.load(f)
        except Exception as e:
            logger.error(f"Error reading existing data for {symbol}: {e}")
            
    existing_data.extend(new_data)
    
    try:
        with open(filename, 'w') as f:
            json.dump(existing_data, f)
        logger.info(f"Successfully saved {len(new_data)} new records for {symbol} to {filename} (Total: {len(existing_data)})")
        return True
    except Exception as e:
        logger.error(f"Failed to save {symbol} data: {e}")
        return False

def run_historical_ingestion(max_workers=5):
    """ Fetch and save raw data for all symbols using multithreading. """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    output_dir = os.path.join(project_root, "data", "historical")
    
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Starting raw historical data ingestion for {len(SYMBOLS)} symbols with {max_workers} workers.")
    logger.info(f"Output directory: {output_dir}")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_symbol = {}
        for symbol in SYMBOLS:
            start_date = get_start_date(symbol, output_dir)
            future = executor.submit(fetch_klines_for_symbol, symbol, start_date, "1d")
            future_to_symbol[future] = symbol
        
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                ret_symbol, raw_data = future.result()
                if raw_data:
                    save_raw_data_to_json(ret_symbol, raw_data, output_dir)
                else:
                    logger.warning(f"No data returned for {symbol}")
            except Exception as e:
                logger.error(f"Exception generated for {symbol}: {e}")
                
    logger.info("Raw historical data ingestion completed.")

if __name__ == "__main__":
    run_historical_ingestion()
