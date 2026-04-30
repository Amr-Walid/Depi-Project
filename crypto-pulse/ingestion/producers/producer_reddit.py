import praw
import json
import os
import time
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
logger = logging.getLogger("RedditProducer")

# -----------------
# 2. CONFIGURATION
# -----------------
load_dotenv()

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_SOCIAL", "crypto.social")

# Reddit API Configuration
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "CryptoPulse/1.0")
SUBREDDITS = "CryptoCurrency+Bitcoin+ethereum"

# Initialize Kafka Producer
producer_conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': 'reddit-producer'
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

def start_reddit_stream():
    """ Streams posts and comments from selected subreddits and produces to Kafka. """
    if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET]):
        logger.error("Reddit API credentials missing in .env. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET.")
        return

    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        
        subreddit = reddit.subreddit(SUBREDDITS)
        logger.info(f"Connected to Reddit API. Streaming from: r/{SUBREDDITS}")
        
        # Stream both submissions and comments
        # For simplicity in this POC, we'll stream submissions first
        # In a real production app, you'd probably use two separate threads or processes
        
        logger.info("Starting submission stream...")
        for submission in subreddit.stream.submissions(skip_existing=True):
            payload = {
                "subreddit": submission.subreddit.display_name,
                "post_id": submission.id,
                "title": submission.title,
                "text": submission.selftext,
                "score": submission.score,
                "num_comments": submission.num_comments,
                "created_utc": submission.created_utc,
                "url": submission.url,
                "timestamp": int(time.time() * 1000),
                "type": "submission"
            }
            
            producer.produce(
                KAFKA_TOPIC,
                value=json.dumps(payload).encode('utf-8'),
                callback=delivery_report
            )
            
            # Local backup (Append to JSONL file)
            local_file = "data/raw/social/reddit_stream.jsonl"
            with open(local_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(payload) + "\n")
            
            producer.poll(0)
            logger.info(f"Sent Reddit post: {payload['title'][:50]}... from r/{payload['subreddit']}")

    except Exception as e:
        logger.error(f"Error in Reddit stream: {e}")
        logger.info("Waiting 10 seconds before restarting stream...")
        time.sleep(10)
        start_reddit_stream()

if __name__ == "__main__":
    try:
        start_reddit_stream()
    except KeyboardInterrupt:
        logger.info("Reddit Producer stopped by user.")
    finally:
        logger.info("Flushing Kafka producer...")
        producer.flush()
        logger.info("Reddit Producer exited.")
