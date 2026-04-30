import feedparser
import json
import os
import time
import logging
import schedule
from confluent_kafka import Producer
from dotenv import load_dotenv

# -----------------
# 1. SETUP LOGGING
# -----------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RSSSocialProducer")

# -----------------
# 2. CONFIGURATION
# -----------------
load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_SOCIAL", "crypto.social")

# Top Crypto RSS Feeds
RSS_FEEDS = {
    "CoinTelegraph": "https://cointelegraph.com/rss",
    "Bitcoin.com": "https://news.bitcoin.com/feed/",
    "NewsBTC": "https://www.newsbtc.com/feed/"
}

POLL_INTERVAL_MINUTES = 10

# Initialize Kafka Producer
producer_conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': 'rss-social-producer'
}

try:
    producer = Producer(producer_conf)
    logger.info(f"Kafka Producer initialized successfully, connecting to {KAFKA_BOOTSTRAP_SERVERS}")
except Exception as e:
    logger.error(f"Failed to initialize Kafka Producer: {e}")
    exit(1)

def delivery_report(err, msg):
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def fetch_and_produce_rss():
    """ Fetches crypto opinions from RSS feeds and produces to Kafka. """
    logger.info("Fetching social data from RSS feeds...")
    
    total_items = 0
    for source_name, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:  # Take latest 10 from each
                # Map RSS fields to our social schema (compatible with Ahmed's Reddit structure)
                payload = {
                    "subreddit": source_name,  # Source acts as 'community'
                    "post_id": entry.get('id', entry.link),
                    "title": entry.get('title', ''),
                    "text": entry.get('summary', ''),
                    "score": 0,
                    "num_comments": 0,
                    "created_utc": int(time.time()), # RSS doesn't always have clean unix time
                    "url": entry.link,
                    "timestamp": int(time.time() * 1000),
                    "type": "rss_opinion"
                }
                
                producer.produce(
                    KAFKA_TOPIC,
                    value=json.dumps(payload).encode('utf-8'),
                    callback=delivery_report
                )
                total_items += 1
                
            producer.poll(0)
            logger.info(f"Processed {len(feed.entries[:10])} entries from {source_name}")
            
        except Exception as e:
            logger.error(f"Error fetching RSS from {source_name}: {e}")

    producer.flush(5)
    logger.info(f"Successfully dispatched {total_items} RSS items to Kafka topic: {KAFKA_TOPIC}")

if __name__ == "__main__":
    logger.info("RSS Social Producer started.")
    
    # Initial fetch
    fetch_and_produce_rss()
    
    # Schedule
    schedule.every(POLL_INTERVAL_MINUTES).minutes.do(fetch_and_produce_rss)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("RSS Social Producer stopped by user.")
    finally:
        producer.flush()
