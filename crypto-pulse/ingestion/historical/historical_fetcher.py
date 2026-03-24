import requests
import pandas as pd
import os
import time
from datetime import datetime
from google.cloud import bigquery
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

# BigQuery Configuration
BQ_PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID")
BQ_DATASET_ID = os.getenv("BIGQUERY_DATASET_ID", "crypto_pulse")
BQ_TABLE_ID = os.getenv("BIGQUERY_TABLE_HISTORICAL", "bronze_historical_prices")
BQ_FULL_TABLE_ID = f"{BQ_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_TABLE_ID}"

# Initialize BigQuery client
client = bigquery.Client()

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

def upload_to_bigquery(df):
    """Upload DataFrame to BigQuery table."""
    # Define job configuration
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND", # Or WRITE_TRUNCATE if fresh start
        schema=[
            bigquery.SchemaField("symbol", "STRING"),
            bigquery.SchemaField("open_time", "TIMESTAMP"),
            bigquery.SchemaField("open", "FLOAT"),
            bigquery.SchemaField("high", "FLOAT"),
            bigquery.SchemaField("low", "FLOAT"),
            bigquery.SchemaField("close", "FLOAT"),
            bigquery.SchemaField("volume", "FLOAT"),
            bigquery.SchemaField("close_time", "TIMESTAMP")
        ]
    )
    
    try:
        job = client.load_table_from_dataframe(df, BQ_FULL_TABLE_ID, job_config=job_config)
        job.result()  # Wait for the job to complete
        print(f"Successfully uploaded {len(df)} rows to {BQ_FULL_TABLE_ID}.")
    except Exception as e:
        print(f"BigQuery load failed: {e}")

def run_historical_ingestion():
    for symbol in SYMBOLS:
        raw_data = fetch_klines(symbol, START_DATE)
        
        if not raw_data:
            print(f"No data found for {symbol}")
            continue
            
        # Parse data to DataFrame
        # Binance klines format: [Open time, Open, High, Low, Close, Volume, Close time, ...]
        df = pd.DataFrame(raw_data, columns=[
            "open_time", "open", "high", "low", "close", "volume", 
            "close_time", "quote_asset_vol", "num_trades", "taker_base_vol", "taker_quote_vol", "ignore"
        ])
        
        # Keep relevant columns and convert types
        df = df[["open_time", "open", "high", "low", "close", "volume", "close_time"]].copy()
        df["symbol"] = symbol
        
        # Convert timestamps to datetime
        df["open_time"] = pd.to_datetime(df["open_time"], unit='ms')
        df["close_time"] = pd.to_datetime(df["close_time"], unit='ms')
        
        # Convert numeric columns
        cols = ["open", "high", "low", "close", "volume"]
        df[cols] = df[cols].apply(pd.to_numeric)
        
        # Reorder columns
        df = df[["symbol", "open_time", "open", "high", "low", "close", "volume", "close_time"]]
        
        # Upload symbol data to BQ
        upload_to_bigquery(df)

if __name__ == "__main__":
    if not BQ_PROJECT_ID:
        print("Error: BIGQUERY_PROJECT_ID not set in .env")
    else:
        run_historical_ingestion()
