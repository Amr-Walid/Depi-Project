"""
Lightweight Supabase Seeder — Ingests data directly to Supabase without Spark/Kafka.
Perfect for resource-constrained Linux environments.

Usage:
    python scripts/seed_supabase_direct.py
"""
import json
import os
import glob
from datetime import datetime, timezone, timedelta
import random
import psycopg2
from psycopg2.extras import execute_values
import requests
import feedparser

# ── Connection ──────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "aws-0-eu-west-1.pooler.supabase.com")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres.idiidwhgddbxdbnpamag")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "R1m@pi9bw123w123")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

DSN = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}?sslmode=require"

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "historical")
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "DOTUSDT", "DOGEUSDT", "MATICUSDT", "LINKUSDT",
    "AVAXUSDT", "UNIUSDT", "ATOMUSDT", "LTCUSDT", "ETCUSDT",
    "XLMUSDT", "ALGOUSDT", "VETUSDT", "ICPUSDT", "FILUSDT"
]

def get_connection():
    conn = psycopg2.connect(DSN)
    conn.autocommit = False
    return conn

# ── 1. Seed Historical (from JSON) ──────────────────────────────────
def seed_historical(conn):
    print("\n📦 Seeding silver.historical from JSON...")
    cur = conn.cursor()
    cur.execute("TRUNCATE silver.historical")
    
    json_files = sorted(glob.glob(os.path.join(DATA_DIR, "*_raw_klines.json")))
    if not json_files:
        print("  ⚠️ No historical JSON files found. Skipping.")
        return 0

    total_rows = 0
    for filepath in json_files:
        symbol = os.path.basename(filepath).replace("_raw_klines.json", "").upper()
        
        with open(filepath, "r") as f:
            klines = json.load(f)
        
        rows = []
        for k in klines:
            open_time_ms = int(k[0])
            open_time = datetime.fromtimestamp(open_time_ms / 1000, tz=timezone.utc)
            
            try:
                open_price, high_price, low_price, close_price, volume = map(float, k[1:6])
            except (ValueError, IndexError):
                continue
                
            if open_price <= 0 or high_price <= 0 or low_price <= 0 or close_price <= 0 or low_price > high_price:
                continue
            
            rows.append((
                symbol, open_time, open_price, high_price, low_price, 
                close_price, volume, open_time.year, open_time.month, 
                open_time.day, datetime.now(timezone.utc)
            ))
        
        if rows:
            execute_values(
                cur,
                """INSERT INTO silver.historical 
                   (symbol, open_time, open, high, low, close, volume, year, month, day, processed_at)
                   VALUES %s""",
                rows, page_size=1000
            )
            total_rows += len(rows)
            print(f"  ✅ {symbol}: {len(rows)} rows")
    
    conn.commit()
    print(f"  🎯 Total historical rows: {total_rows}")
    return total_rows

# ── 2. Seed Prices (Real Binance API or Fallback) ───────────────────
def seed_prices(conn):
    print("\n📈 Seeding silver.prices (Latest snapshot)...")
    cur = conn.cursor()
    cur.execute("TRUNCATE silver.prices")
    
    rows = []
    now = datetime.now(timezone.utc)
    
    try:
        resp = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=10)
        data = resp.json()
        ticker_map = {item["symbol"]: item for item in data}
        
        for symbol in SYMBOLS:
            if symbol in ticker_map:
                t = ticker_map[symbol]
                price = float(t.get("lastPrice", 0))
                vol = float(t.get("volume", 0))
                if price > 0:
                    rows.append((symbol, price, vol, now, "Binance API", now))
                    
        if rows:
            print("  ✅ Using real Binance API data.")
    except Exception as e:
        print(f"  ⚠️ Binance API failed ({e}). Using sample data.")
        # Fallback to random if API fails
        for symbol in SYMBOLS:
            base_price = 50000 if "BTC" in symbol else 3000 if "ETH" in symbol else 100
            price = base_price * (1 + random.uniform(-0.05, 0.05))
            vol = random.uniform(1000, 50000)
            rows.append((symbol, round(price, 4), round(vol, 4), now, "Sample", now))

    if rows:
        execute_values(
            cur,
            """INSERT INTO silver.prices 
               (symbol, price, volume_24h, event_time, source, processed_at)
               VALUES %s""",
            rows
        )
        conn.commit()
        print(f"  🎯 Inserted {len(rows)} price records.")

# ── 3. Seed News (Real NewsAPI or Fallback) ─────────────────────────
def seed_news(conn):
    print("\n📰 Seeding silver.news...")
    cur = conn.cursor()
    cur.execute("TRUNCATE silver.news")
    
    rows = []
    now = datetime.now(timezone.utc)
    
    if NEWS_API_KEY:
        try:
            url = f"https://newsapi.org/v2/everything?q=cryptocurrency OR bitcoin OR ethereum&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}&pageSize=20"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                articles = resp.json().get("articles", [])
                for a in articles:
                    pub_str = a.get("publishedAt", "")
                    try:
                        pub_date = datetime.strptime(pub_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    except:
                        pub_date = now
                        
                    source = a.get("source", {}).get("name", "Unknown")
                    title = a.get("title", "")
                    if title and title != "[Removed]":
                        rows.append((
                            source, title, a.get("description", ""),
                            a.get("url", ""), pub_date, a.get("content", ""), now
                        ))
                print("  ✅ Using real NewsAPI data.")
        except Exception as e:
             print(f"  ⚠️ NewsAPI failed ({e}).")
    
    if not rows:
        print("  ⚠️ Using sample news data.")
        for i in range(15):
            rows.append((
                "CryptoNews", f"Sample Crypto Article {i}", f"This is a sample description {i}",
                "https://example.com", now - timedelta(hours=i), "Sample content", now
            ))

    if rows:
        execute_values(
            cur,
            """INSERT INTO silver.news 
               (source, title, description, url, published_at, content, ingested_at)
               VALUES %s""",
            rows
        )
        conn.commit()
        print(f"  🎯 Inserted {len(rows)} news records.")

# ── 4. Seed Social (Real RSS or Fallback) ───────────────────────────
def seed_social(conn):
    print("\n🗣️ Seeding silver.social...")
    cur = conn.cursor()
    cur.execute("TRUNCATE silver.social")
    
    rows = []
    now = datetime.now(timezone.utc)
    
    try:
        feed = feedparser.parse("https://cointelegraph.com/rss")
        for entry in feed.entries[:20]:
            try:
                pub_date = datetime(*entry.published_parsed[:6]).replace(tzinfo=timezone.utc)
            except:
                pub_date = now
                
            rows.append((
                "CoinTelegraph", entry.get("id", str(random.randint(1000, 9999))), 
                entry.get("title", ""), entry.get("summary", ""), 0, 0,
                int(pub_date.timestamp()), pub_date, entry.get("link", ""), "RSS", now
            ))
        print("  ✅ Using real RSS data.")
    except Exception as e:
        print(f"  ⚠️ RSS failed ({e}). Using sample social data.")
        for i in range(15):
            rows.append((
                "Reddit", f"t3_{i}", f"Sample Social Post {i}", "Text content", 
                random.randint(10, 500), random.randint(5, 50),
                int(now.timestamp()), now, "https://reddit.com", "Reddit", now
            ))

    if rows:
        execute_values(
            cur,
            """INSERT INTO silver.social 
               (subreddit, post_id, title, text, score, num_comments, created_utc, created_at, url, type, ingested_at)
               VALUES %s""",
            rows
        )
        conn.commit()
        print(f"  🎯 Inserted {len(rows)} social records.")

# ── 5. Seed News Sentiment (Simulated FinBERT) ──────────────────────
def seed_sentiment(conn):
    print("\n🧠 Seeding silver.news_sentiment (Simulated)...")
    cur = conn.cursor()
    cur.execute("TRUNCATE silver.news_sentiment RESTART IDENTITY")
    
    rows = []
    now = datetime.now(timezone.utc)
    
    headlines = [
        ("Surges past resistance", 0.85, "positive"),
        ("Faces regulatory concerns", -0.65, "negative"),
        ("Upgrade boosts efficiency", 0.72, "positive"),
        ("Sideways movement", 0.05, "neutral"),
        ("Investors increase holdings", 0.68, "positive"),
        ("Volatility concerns grow", -0.45, "negative"),
        ("Partnership announced", 0.55, "positive"),
        ("Volume hits monthly low", -0.30, "negative"),
    ]
    
    for symbol in ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT"]:
        for day_offset in range(30):
            pub_date = now - timedelta(days=day_offset)
            num_articles = random.randint(1, 4)
            for _ in range(num_articles):
                phrase, score, label = random.choice(headlines)
                title = f"{symbol.replace('USDT','')} {phrase}"
                noise_score = max(-1.0, min(1.0, score + random.uniform(-0.15, 0.15)))
                
                rows.append((
                    symbol, title, round(noise_score, 4), label, 
                    pub_date, "Simulated", now
                ))

    if rows:
        execute_values(
            cur,
            """INSERT INTO silver.news_sentiment 
               (symbol, title, sentiment_score, sentiment_label, published_at, source, ingested_at)
               VALUES %s""",
            rows, page_size=500
        )
        conn.commit()
        print(f"  🎯 Inserted {len(rows)} sentiment records.")

def main():
    print("=" * 60)
    print("🚀 CryptoPulse — Direct Supabase Seeder (Lightweight)")
    print("=" * 60)
    
    conn = get_connection()
    
    seed_historical(conn)
    seed_prices(conn)
    seed_news(conn)
    seed_social(conn)
    seed_sentiment(conn)
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ All data seeded to Silver layer successfully!")
    print("   Next: cd processing/dbt && dbt run")
    print("=" * 60)

if __name__ == "__main__":
    main()
