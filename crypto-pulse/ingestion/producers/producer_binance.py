import asyncio
import json
import os
import websockets
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
logger = logging.getLogger("BinanceProducer")

# -----------------
# 2. CONFIGURATION
# -----------------
load_dotenv()

# Kafka Configuration
# Getting the bootstrap server address (default: localhost:9092)
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
# Defining the target Kafka topic for real-time prices
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_REALTIME_PRICES", "crypto.realtime.prices")

# Binance Configuration (WebSocket Base URL)
BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"

# List of 10 major crypto symbols to track in USDT
SYMBOLS = ["btcusdt", "ethusdt", "bnbusdt", "xrpusdt", "adausdt", "solusdt", "dotusdt", "dogeusdt", "maticusdt", "linkusdt"]

# Initialize Kafka Producer configuration
producer_conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': 'binance-producer'
}

try:
    producer = Producer(producer_conf)
    logger.info(f"Kafka Producer initialized successfully connected to {KAFKA_BOOTSTRAP_SERVERS}")
except Exception as e:
    logger.error(f"Failed to initialize Kafka Producer: {e}")
    exit(1)

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result. """
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        # Using debug instead of info so it doesn't spam the console 10 times a second
        logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

async def binance_producer():
    """ 
    Main asynchronous function to handle Binance WebSocket connection and message producing.
    Contains bulletproof auto-reconnect logic.
    """
    # Construct the combined stream URL for all selected symbols (ticker stream)
    streams = "/".join([f"{symbol}@ticker" for symbol in SYMBOLS])
    url = f"{BINANCE_WS_URL}/{streams}"
    
    base_delay = 1
    max_delay = 60
    current_delay = base_delay
    
    # Outer loop for bulletproof reconnecting
    while True:
        try:
            logger.info(f"Connecting to Binance WebSocket: {url}")
            
            # Establish a long-living connection to the WebSocket
            async with websockets.connect(url, ping_interval=20, ping_timeout=20) as websocket:
                logger.info("Successfully connected to Binance WebSocket.")
                
                # Reset delay on successful connection
                current_delay = base_delay
                
                # Inner loop for receiving messages continuously
                while True:
                    # Wait for an incoming message from the server
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    # Transform the raw Binance message into our standardized system format
                    payload = {
                        "symbol": data.get('s'),
                        "price": float(data.get('c', 0)),
                        "volume_24h": float(data.get('v', 0)),
                        "timestamp": data.get('E'),
                        "source": "binance"
                    }
                    
                    # Push the formatted JSON message to the specified Kafka topic
                    producer.produce(
                        KAFKA_TOPIC, 
                        value=json.dumps(payload).encode('utf-8'),
                        callback=delivery_report
                    )
                    
                    # Trigger internal event handling (checks for message delivery acknowledgments)
                    producer.poll(0)
                    
                    # Use debug level instead of print to avoid excessive spam
                    logger.debug(f"Sent: {payload}")
                    
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"WebSocket Connection closed: {e}")
        except websockets.exceptions.WebSocketException as e:
             logger.error(f"WebSocket Error: {e}")
        except asyncio.TimeoutError:
            logger.error("Connection timed out.")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
        
        # If we reach here, the connection was dropped or failed to establish.
        # Implement Exponential Backoff
        logger.info(f"Reconnecting in {current_delay} seconds...")
        await asyncio.sleep(current_delay)
        
        # Increase delay exponentially up to max_delay
        current_delay = min(current_delay * 2, max_delay)

if __name__ == "__main__":
    try:
        logger.info("Starting Binance Producer Service...")
        asyncio.run(binance_producer())
    except KeyboardInterrupt:
        logger.info("Producer stopped by user (KeyboardInterrupt).")
    finally:
        logger.info("Flushing remaining Kafka messages before exiting...")
        producer.flush()
        logger.info("Exited gracefully.")
