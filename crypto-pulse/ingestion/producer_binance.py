import asyncio
import json
import os
import websockets
from confluent_kafka import Producer
from dotenv import load_dotenv

# Load environment variables
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
producer = Producer(producer_conf)

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result. """
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

async def binance_producer():
    """ Main asynchronous function to handle Binance WebSocket connection and message producing. """
    # Construct the combined stream URL for all selected symbols (ticker stream)
    streams = "/".join([f"{symbol}@ticker" for symbol in SYMBOLS])
    url = f"{BINANCE_WS_URL}/{streams}"

    print(f"Connecting to Binance WebSocket: {url}")
    
    # Establish a long-living connection to the WebSocket
    async with websockets.connect(url) as websocket:
        while True:
            try:
                # Wait for an incoming message from the server
                message = await websocket.recv()
                data = json.loads(message)
                
                # Transform the raw Binance message into our standardized system format:
                # 's': Symbol (e.g. BTCUSDT)
                # 'c': Current price
                # 'v': 24h Trading Volume
                # 'E': Event Time (millisecond timestamp)
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
                
                print(f"Sent: {payload}")
                
            except websockets.exceptions.ConnectionClosed:
                # Handle unexpected disconnection from the server
                print("Connection closed by server. Retrying in 5 seconds...")
                break
            except Exception as e:
                # Catch general errors and log them
                print(f"An error occurred: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(binance_producer())
    except KeyboardInterrupt:
        print("Producer stopped.")
    finally:
        producer.flush()
