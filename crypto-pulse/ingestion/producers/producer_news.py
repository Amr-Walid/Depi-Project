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
logger = logging.getLogger("NewsProducer")

# -----------------
# 2. CONFIGURATION
# -----------------
load_dotenv()

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_NEWS", "crypto.news")

# NewsAPI Configuration
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/everything"
QUERY = "bitcoin OR ethereum OR crypto OR cryptocurrency"
POLL_INTERVAL_MINUTES = 15

# Initialize Kafka Producer
producer_conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': 'news-producer'
}

if not NEWS_API_KEY:
    logger.error("NEWS_API_KEY not found in environment variables. Please set it in .env file.")
    # We don't exit here to allow the process to stay alive if it's part of a larger orchestration, 
    # but it won't be able to fetch news.
else:
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
    """ Fetches crypto news from NewsAPI and produces to Kafka. """
    if not NEWS_API_KEY:
        logger.warning("Skipping fetch: NEWS_API_KEY is missing.")
        return

    logger.info(f"Fetching news from NewsAPI for query: {QUERY}")
    
    params = {
        'q': QUERY,
        'apiKey': NEWS_API_KEY,
        'pageSize': 20,
        'sortBy': 'publishedAt',
        'language': 'en'
    }
    
    try:
        response = requests.get(NEWS_API_URL, params=params, timeout=15)
        
        if response.status_code == 429:
            logger.warning("NewsAPI Rate Limit reached. Will retry on next schedule.")
            return
            
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])
        
        if not articles:
            logger.warning("No articles returned from NewsAPI.")
            return
            
        # Local backup path
        local_file = f"data/raw/news/news_{int(time.time())}.json"
        with open(local_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=4)
        logger.info(f"Local backup saved to: {local_file}")
            
        for article in articles:
            # Structure the message according to the requirements
            payload = {
                "source": article.get('source', {}).get('name'),
                "author": article.get('author'),
                "title": article.get('title'),
                "description": article.get('description'),
                "url": article.get('url'),
                "published_at": article.get('publishedAt'),
                "content": article.get('content'),
                "timestamp": int(time.time() * 1000)
            }
            
            producer.produce(
                KAFKA_TOPIC,
                value=json.dumps(payload).encode('utf-8'),
                callback=delivery_report
            )
            
            producer.poll(0)
            logger.debug(f"Sent news article: {payload['title'][:50]}...")
            
        producer.flush(5)
        logger.info(f"Successfully processed and dispatched {len(articles)} articles to Kafka topic: {KAFKA_TOPIC}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching from NewsAPI: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during NewsAPI processing: {e}")

if __name__ == "__main__":
    if not NEWS_API_KEY:
        logger.error("Service cannot start without NEWS_API_KEY.")
    else:
        logger.info(f"News Producer started. Running every {POLL_INTERVAL_MINUTES} minutes.")
        
        # Initial fetch
        fetch_and_produce()
        
        # Schedule
        schedule.every(POLL_INTERVAL_MINUTES).minutes.do(fetch_and_produce)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("News Producer stopped by user.")
        finally:
            logger.info("Flushing Kafka producer...")
            producer.flush()
            logger.info("News Producer exited.")
