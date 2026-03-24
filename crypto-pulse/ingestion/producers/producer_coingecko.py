import requests
import json
import os
import time
import schedule
from confluent_kafka import Producer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_REALTIME_MARKET", "crypto.realtime.market")

# CoinGecko Configuration
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/markets"
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")

# Kafka Producer initialization
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
    print("Fetching data from CoinGecko...")
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "24h"
    }
    
    # Add API key if provided
    if COINGECKO_API_KEY:
        params["x_cg_demo_api_key"] = COINGECKO_API_KEY

    try:
        response = requests.get(COINGECKO_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        for coin in data:
            payload = {
                "symbol": coin.get("symbol"),
                "name": coin.get("name"),
                "price": coin.get("current_price"),
                "market_cap": coin.get("market_cap"),
                "volume_24h": coin.get("total_volume"),
                "price_change_24h_pct": coin.get("price_change_percentage_24h"),
                "timestamp": int(time.time() * 1000),
                "source": "coingecko"
            }
            
            # Produce to Kafka
            producer.produce(
                KAFKA_TOPIC, 
                value=json.dumps(payload).encode('utf-8'),
                callback=delivery_report
            )
            
            # Poll for feedback
            producer.poll(0)
            
        print(f"Successfully processed {len(data)} coins.")
        producer.flush()

    except Exception as e:
        print(f"Error fetching data from CoinGecko: {e}")

# Schedule task every 60 seconds
schedule.every(60).seconds.do(fetch_coingecko_data)

if __name__ == "__main__":
    print("Starting CoinGecko Producer (scheduler)...")
    fetch_coingecko_data()  # Run immediately once
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Producer stopped.")
    finally:
        producer.flush()
