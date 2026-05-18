"""
Seed the Silver Layer in Supabase — following the Medallion Pipeline correctly.

Flow: JSON files → Parse (simulates Bronze) → Clean & Transform (Silver) → INSERT into silver.historical
Then: dbt run → builds Gold tables from Silver views

This respects the project's Medallion Architecture: Bronze → Silver → Gold
"""
import json
import os
import glob
from datetime import datetime, timezone
from urllib.parse import quote_plus
import psycopg2
from psycopg2.extras import execute_values

# ── Connection ──────────────────────────────────────────────
pwd = quote_plus("R1m@pi9bw123w123")
DSN = f"postgresql://postgres.idiidwhgddbxdbnpamag:{pwd}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require"

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "historical")


def get_connection():
    conn = psycopg2.connect(DSN)
    conn.autocommit = False
    return conn


def check_silver_table_columns(conn):
    """Check existing silver.historical columns and return them."""
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_schema = 'silver' AND table_name = 'historical'
        ORDER BY ordinal_position
    """)
    cols = [r[0] for r in cur.fetchall()]
    return cols


def ensure_silver_tables(conn):
    """Make sure silver.historical has the right columns for dbt stg_historical to work."""
    cur = conn.cursor()
    
    existing_cols = check_silver_table_columns(conn)
    print(f"  Existing silver.historical columns: {existing_cols}")
    
    # The dbt stg_historical.sql reads: symbol, open_time, open, high, low, close, volume, year, month, day, processed_at
    # We need to DROP and recreate if columns don't match
    needed_cols = {'symbol', 'open_time', 'open', 'high', 'low', 'close', 'volume', 'year', 'month', 'day', 'processed_at'}
    
    if not needed_cols.issubset(set(existing_cols)):
        print("  ⚠️  Recreating silver.historical with correct columns for dbt...")
        cur.execute("DROP TABLE IF EXISTS silver.historical CASCADE")
        cur.execute("""
            CREATE TABLE silver.historical (
                symbol VARCHAR(20) NOT NULL,
                open_time TIMESTAMP NOT NULL,
                open DECIMAL(18,8),
                high DECIMAL(18,8),
                low DECIMAL(18,8),
                close DECIMAL(18,8),
                volume DECIMAL(24,8),
                year INTEGER,
                month INTEGER,
                day INTEGER,
                processed_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hist_symbol ON silver.historical(symbol)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hist_open_time ON silver.historical(open_time)")
        conn.commit()
        print("  ✅ silver.historical recreated with correct columns")
    else:
        print("  ✅ silver.historical columns are correct")
    
    # Also ensure silver.news_sentiment has the right columns for stg_news_sentiment
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_schema = 'silver' AND table_name = 'news_sentiment'
        ORDER BY ordinal_position
    """)
    sentiment_cols = [r[0] for r in cur.fetchall()]
    print(f"  Existing silver.news_sentiment columns: {sentiment_cols}")
    
    needed_sentiment = {'article_id', 'symbol', 'sentiment_score', 'sentiment_label', 'published_at', 'ingested_at'}
    if not needed_sentiment.issubset(set(sentiment_cols)):
        print("  ⚠️  Recreating silver.news_sentiment with correct columns for dbt...")
        cur.execute("DROP TABLE IF EXISTS silver.news_sentiment CASCADE")
        cur.execute("""
            CREATE TABLE silver.news_sentiment (
                article_id SERIAL PRIMARY KEY,
                symbol VARCHAR(20),
                title TEXT,
                sentiment_score DECIMAL(5, 4),
                sentiment_label VARCHAR(20),
                published_at TIMESTAMP,
                source VARCHAR(255),
                ingested_at TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()
        print("  ✅ silver.news_sentiment recreated with correct columns")
    else:
        print("  ✅ silver.news_sentiment columns are correct")
    
    # Ensure silver.prices table has correct columns for stg_prices
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_schema = 'silver' AND table_name = 'prices'
        ORDER BY ordinal_position
    """)
    prices_cols = [r[0] for r in cur.fetchall()]
    print(f"  Existing silver.prices columns: {prices_cols}")
    
    needed_prices = {'symbol', 'price', 'volume_24h', 'event_time', 'source', 'processed_at'}
    if not needed_prices.issubset(set(prices_cols)):
        print("  ⚠️  Recreating silver.prices with correct columns for dbt...")
        cur.execute("DROP TABLE IF EXISTS silver.prices CASCADE")
        cur.execute("""
            CREATE TABLE silver.prices (
                symbol VARCHAR(20),
                price DECIMAL(18,8),
                volume_24h DECIMAL(24,8),
                event_time TIMESTAMP,
                source VARCHAR(50),
                processed_at TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()
        print("  ✅ silver.prices recreated")
    else:
        print("  ✅ silver.prices columns are correct")


def seed_silver_historical(conn):
    """
    Read JSON kline files → parse → clean → insert into silver.historical.
    Simulates: historical_loader.py (Bronze) + silver_historical_processor.py (Silver) + sync_historical_pg.py (Sync)
    """
    cur = conn.cursor()
    
    # Clear existing data
    cur.execute("TRUNCATE silver.historical")
    conn.commit()
    
    json_files = sorted(glob.glob(os.path.join(DATA_DIR, "*_raw_klines.json")))
    print(f"\n📂 Found {len(json_files)} JSON files in data/historical/")
    
    total_rows = 0
    
    for filepath in json_files:
        filename = os.path.basename(filepath)
        symbol = filename.replace("_raw_klines.json", "").upper()
        
        with open(filepath, "r") as f:
            klines = json.load(f)
        
        # Parse Binance kline format:
        # [open_time, open, high, low, close, volume, close_time, quote_volume, trade_count, ...]
        rows = []
        for k in klines:
            open_time_ms = int(k[0])
            open_time = datetime.fromtimestamp(open_time_ms / 1000, tz=timezone.utc)
            
            open_price = float(k[1])
            high_price = float(k[2])
            low_price = float(k[3])
            close_price = float(k[4])
            volume = float(k[5])
            
            # Quality filters (matching silver_historical_processor.py logic)
            if open_price <= 0 or high_price <= 0 or low_price <= 0 or close_price <= 0:
                continue
            if low_price > high_price:
                continue
            
            rows.append((
                symbol,
                open_time,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                open_time.year,
                open_time.month,
                open_time.day,
                datetime.now(timezone.utc),
            ))
        
        # Batch insert
        if rows:
            execute_values(
                cur,
                """INSERT INTO silver.historical 
                   (symbol, open_time, open, high, low, close, volume, year, month, day, processed_at)
                   VALUES %s""",
                rows,
                page_size=500
            )
            conn.commit()
        
        total_rows += len(rows)
        print(f"  ✅ {symbol}: {len(rows)} klines loaded")
    
    print(f"\n📊 Total silver.historical rows: {total_rows}")
    return total_rows


def seed_silver_news_sentiment(conn):
    """
    Insert sample sentiment data into silver.news_sentiment.
    Simulates: sentiment_processor.py (FinBERT analysis of news)
    """
    import random
    cur = conn.cursor()
    
    cur.execute("TRUNCATE silver.news_sentiment RESTART IDENTITY")
    conn.commit()
    
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
               "ADAUSDT", "DOGEUSDT", "DOTUSDT", "LINKUSDT", "AVAXUSDT"]
    
    # Generate 30 days of sentiment data
    rows = []
    now = datetime.now(timezone.utc)
    
    headlines = [
        ("Bitcoin surges past resistance level", 0.85, "positive"),
        ("Crypto market faces regulatory concerns", -0.65, "negative"),
        ("Ethereum upgrade boosts network efficiency", 0.72, "positive"),
        ("Analysts predict sideways movement", 0.05, "neutral"),
        ("Institutional investors increase holdings", 0.68, "positive"),
        ("Market volatility concerns grow", -0.45, "negative"),
        ("New partnership announced for blockchain", 0.55, "positive"),
        ("Trading volume hits monthly low", -0.30, "negative"),
        ("Bullish sentiment dominates social media", 0.60, "positive"),
        ("Central bank policies impact crypto markets", -0.15, "neutral"),
    ]
    
    for day_offset in range(30):
        pub_date = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        pub_date = pub_date.replace(day=max(1, now.day - day_offset))
        try:
            pub_date = now.replace(day=now.day - day_offset)
        except ValueError:
            pub_date = now.replace(month=now.month - 1, day=28 - day_offset + now.day)
        
        # 3-5 articles per symbol per day
        for symbol in symbols:
            num_articles = random.randint(3, 5)
            for _ in range(num_articles):
                title, score, label = random.choice(headlines)
                # Add some noise
                score = max(-1.0, min(1.0, score + random.uniform(-0.15, 0.15)))
                
                rows.append((
                    symbol,
                    f"{title} - {symbol}",
                    round(score, 4),
                    label,
                    pub_date,
                    "NewsAPI",
                    datetime.now(timezone.utc),
                ))
    
    if rows:
        execute_values(
            cur,
            """INSERT INTO silver.news_sentiment 
               (symbol, title, sentiment_score, sentiment_label, published_at, source, ingested_at)
               VALUES %s""",
            rows,
            page_size=500
        )
        conn.commit()
    
    print(f"\n📰 Inserted {len(rows)} sentiment records into silver.news_sentiment")
    return len(rows)


def verify_silver(conn):
    """Verify Silver layer is populated."""
    cur = conn.cursor()
    print("\n=== Silver Layer Verification ===")
    
    for tbl in ['silver.historical', 'silver.news_sentiment']:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        count = cur.fetchone()[0]
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {tbl}: {count} rows")
    
    # Show sample of historical
    cur.execute("SELECT DISTINCT symbol FROM silver.historical ORDER BY symbol")
    symbols = [r[0] for r in cur.fetchall()]
    print(f"  📊 Coins in silver.historical: {len(symbols)} — {', '.join(symbols[:5])}...")
    
    cur.execute("SELECT MIN(open_time), MAX(open_time) FROM silver.historical")
    mn, mx = cur.fetchone()
    print(f"  📅 Date range: {mn} → {mx}")


def main():
    print("=" * 60)
    print("🏗️  CryptoPulse — Silver Layer Seeding Script")
    print("   Flow: JSON → Parse (Bronze) → Clean (Silver) → Supabase")
    print("=" * 60)
    
    conn = get_connection()
    
    # Step 1: Ensure tables have correct schema
    print("\n🔧 Step 1: Ensuring Silver table schemas...")
    ensure_silver_tables(conn)
    
    # Step 2: Seed silver.historical from JSON klines
    print("\n📦 Step 2: Seeding silver.historical (Bronze → Silver pipeline)...")
    seed_silver_historical(conn)
    
    # Step 3: Seed silver.news_sentiment (simulates FinBERT)
    print("\n🧠 Step 3: Seeding silver.news_sentiment (FinBERT pipeline)...")
    seed_silver_news_sentiment(conn)
    
    # Step 4: Verify
    verify_silver(conn)
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Silver Layer complete! Now run:")
    print("   cd processing/dbt && dbt run && dbt test")
    print("   This will build the Gold Layer from Silver.")
    print("=" * 60)


if __name__ == "__main__":
    main()
