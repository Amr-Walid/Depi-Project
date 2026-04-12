import requests
import json
import os
import time
import schedule
import logging
from confluent_kafka import Producer
from dotenv import load_dotenv

# -----------------
# 1. SETUP LOGGING
# -----------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CoinGeckoProducer")

# -----------------
# 2. CONFIGURATION
# -----------------
load_dotenv()

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_MARKET_DATA", "crypto.market.data")

# CoinGecko API Configuration
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/markets"
POLL_INTERVAL_SECONDS = 60

# Initialize Kafka Producer
producer_conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': 'coingecko-producer'
}

try:
    producer = Producer(producer_conf)
    logger.info(f"Kafka Producer initialized successfully, connecting to {KAFKA_BOOTSTRAP_SERVERS}")
except Exception as e:
    logger.error(f"Failed to initialize Kafka Producer: {e}")
    exit(1)

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result. """
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def fetch_and_produce():
    """ Fetches top 100 coins market data from CoinGecko and produces to Kafka. """
    logger.info("Fetching market data from CoinGecko...")
    
    params = {
        'vs_currency': 'usd',           # Price against USD
        'order': 'market_cap_desc',     # Order by market cap
        'per_page': 100,                # Top 100 coins
        'page': 1,                      # First page
        'sparkline': 'false'            # No mini charts needed
    }
    
    try:
        response = requests.get(COINGECKO_API_URL, params=params, timeout=10)
        
        # Check if we hit rate limits (429 Too Many Requests)
        if response.status_code == 429:
            logger.warning("CoinGecko Rate Limit reached. API overloaded. Will retry on next schedule.")
            return
            
        response.raise_for_status()
        coins = response.json()
        
        if not coins:
            logger.warning("No data returned from CoinGecko.")
            return
            
        for coin in coins:
            payload = {
                "symbol": coin.get('symbol', '').upper(),
                "name": coin.get('name'),
                "price": coin.get('current_price'),
                "market_cap": coin.get('market_cap'),
                "market_cap_rank": coin.get('market_cap_rank'),
                "total_volume": coin.get('total_volume'),
                "price_change_percentage_24h": coin.get('price_change_percentage_24h'),
                "timestamp": int(time.time() * 1000), # Milliseconds timestamp
                "source": "coingecko"
            }
            
            producer.produce(
                KAFKA_TOPIC,
                value=json.dumps(payload).encode('utf-8'),
                callback=delivery_report
            )
            
            # Poll quickly to handle callbacks iteratively
            producer.poll(0)
            
            logger.debug(f"Sent {payload['symbol']} data.")
            
        # Flush any remaining messages in buffer
        producer.flush(1)
        logger.info(f"Successfully processed and dispatched data for {len(coins)} coins to Kafka.")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching from CoinGecko API: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during processing: {e}")


if __name__ == "__main__":
    logger.info(f"CoinGecko producer started. Running every {POLL_INTERVAL_SECONDS} seconds.")
    
    # Execute immediately on start
    fetch_and_produce()
    
    # Schedule to execute periodically
    schedule.every(POLL_INTERVAL_SECONDS).seconds.do(fetch_and_produce)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("CoinGecko Producer stopped by user (KeyboardInterrupt).")
    finally:
        logger.info("Flushing remaining Kafka messages before exiting...")
        producer.flush()
        logger.info("Service Exited.")
