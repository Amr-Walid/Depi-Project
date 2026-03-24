import asyncio
import json
import os
import websockets
from confluent_kafka import Producer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_REALTIME_PRICES", "crypto.realtime.prices")

# Binance Configuration
BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"
# Top 10 coins (standard symbols)
SYMBOLS = ["btcusdt", "ethusdt", "bnbusdt", "xrpusdt", "adausdt", "solusdt", "dotusdt", "dogeusdt", "maticusdt", "linkusdt"]

# Kafka Producer initialization
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
    # Construct combined stream URL
    streams = "/".join([f"{symbol}@ticker" for symbol in SYMBOLS])
    url = f"{BINANCE_WS_URL}/{streams}"

    print(f"Connecting to Binance WebSocket: {url}")
    
    async with websockets.connect(url) as websocket:
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                
                # Transform data to the required JSON format
                # data['s'] = symbol, data['c'] = current price, data['v'] = volume, data['E'] = event time
                payload = {
                    "symbol": data.get('s'),
                    "price": float(data.get('c', 0)),
                    "volume_24h": float(data.get('v', 0)),
                    "timestamp": data.get('E'),
                    "source": "binance"
                }
                
                # Produce to Kafka
                producer.produce(
                    KAFKA_TOPIC, 
                    value=json.dumps(payload).encode('utf-8'),
                    callback=delivery_report
                )
                
                # Serve delivery reports
                producer.poll(0)
                
                print(f"Sent: {payload}")
                
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed. Retrying...")
                break
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(binance_producer())
    except KeyboardInterrupt:
        print("Producer stopped.")
    finally:
        producer.flush()
