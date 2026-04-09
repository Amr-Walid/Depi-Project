import requests
import json
import os
import time
import schedule
from confluent_kafka import Producer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Kafka Configuration (Broker addresses and Topic name)
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_REALTIME_MARKET", "crypto.realtime.market")

# CoinGecko REST API Configuration
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/markets"
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")

# Initialize the Kafka Producer
producer_conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': 'coingecko-producer'
}
producer = Producer(producer_conf)

def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

def fetch_coingecko_data():
    """ Fetch top 100 cryptocurrencies by market cap from CoinGecko API. """
    print("Fetching data from CoinGecko API...")
    
    # Query parameters for the REST API call
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "24h"
    }
    
    # Inject API Key into headers/params if configured (Demo API key support)
    if COINGECKO_API_KEY:
        params["x_cg_demo_api_key"] = COINGECKO_API_KEY

    try:
        # Perform the HTTP GET request
        response = requests.get(COINGECKO_API_URL, params=params)
        response.raise_for_status() # Raise exceptions for 4xx/5xx errors
        data = response.json()

        # Iterate through the returned list of coins and transform them
        for coin in data:
            # Map API fields to our internal data standard
            payload = {
                "symbol": coin.get("symbol"),
                "name": coin.get("name"),
                "price": coin.get("current_price"),
                "market_cap": coin.get("market_cap"),
                "volume_24h": coin.get("total_volume"),
                "price_change_24h_pct": coin.get("price_change_percentage_24h"),
                "timestamp": int(time.time() * 1000), # Millisecond precision
                "source": "coingecko"
            }
            
            # Send the payload to Kafka
            producer.produce(
                KAFKA_TOPIC, 
                value=json.dumps(payload).encode('utf-8'),
                callback=delivery_report
            )
            
            # Non-blocking poll to check for internal delivery status
            producer.poll(0)
            
        print(f"Successfully processed {len(data)} coins and pushed to Kafka.")
        # Ensure all pending messages are sent before finishing this tick
        producer.flush()

    except Exception as e:
        # Catch and log any errors during the API call or processing
        print(f"CRITICAL ERROR in CoinGecko fetch: {e}")

# Register the job to run every 60 seconds using the scheduler
schedule.every(60).seconds.do(fetch_coingecko_data)

if __name__ == "__main__":
    print("Starting CoinGecko Producer Scheduler...")
    fetch_coingecko_data()  # Immediate first execution
    
    try:
        # Keep the main thread alive to allow scheduler to run
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Scheduler stopped by user.")
    finally:
        # Final cleanup and flushing of messages
        producer.flush()
