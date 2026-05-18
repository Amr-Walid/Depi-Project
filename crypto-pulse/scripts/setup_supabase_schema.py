"""
Setup Supabase Schema — Creates all required schemas and tables.

This script is IDEMPOTENT: safe to run multiple times.
It creates:
  - public: users, watchlists, alerts, portfolios, refresh_tokens, user_sessions
  - silver: historical, prices, news, social, news_sentiment
  - gold:   (created by dbt run)

Usage:
    python scripts/setup_supabase_schema.py
"""
import psycopg2
from urllib.parse import quote_plus
import os
import sys

# ── Connection ──────────────────────────────────────────────
# Try .env first, fallback to hardcoded
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

pwd = quote_plus(POSTGRES_PASSWORD)
DSN = f"postgresql://{POSTGRES_USER}:{pwd}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}?sslmode=require"


def get_connection():
    conn = psycopg2.connect(DSN)
    conn.autocommit = False
    return conn


def setup_schemas(conn):
    """Create required schemas."""
    cur = conn.cursor()
    for schema in ['silver', 'gold']:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    conn.commit()
    print("✅ Schemas created: silver, gold")


def setup_public_tables(conn):
    """Create public tables for auth and user features."""
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS watchlists (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            symbol VARCHAR(10) NOT NULL,
            added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            symbol VARCHAR(10) NOT NULL,
            condition VARCHAR(50) NOT NULL,
            threshold DECIMAL(18, 8) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            symbol VARCHAR(10) NOT NULL,
            quantity DECIMAL(18, 8) NOT NULL,
            avg_buy_price DECIMAL(18, 8) NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            token VARCHAR(512) UNIQUE NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            revoked BOOLEAN DEFAULT FALSE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            session_token VARCHAR(512) UNIQUE NOT NULL,
            ip_address VARCHAR(45),
            user_agent TEXT,
            last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    # Indexes (IF NOT EXISTS for idempotency)
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_watchlists_user_id ON watchlists(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_watchlists_symbol ON watchlists(symbol)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON alerts(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_symbol ON alerts(symbol)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_is_active ON alerts(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_portfolios_symbol ON portfolios(symbol)",
        "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token)",
    ]
    for idx in indexes:
        cur.execute(idx)

    conn.commit()
    print("✅ Public tables created: users, watchlists, alerts, portfolios, refresh_tokens, user_sessions")


def setup_silver_tables(conn):
    """Create silver layer tables matching what dbt staging views expect."""
    cur = conn.cursor()

    # ── silver.historical ──
    # Used by: stg_historical.sql → gold_daily_ohlcv → daily_market_summary
    # Columns: symbol, open_time, open, high, low, close, volume, year, month, day, processed_at
    cur.execute("""
        CREATE TABLE IF NOT EXISTS silver.historical (
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

    # ── silver.prices ──
    # Used by: stg_prices.sql → gold_latest_prices, daily_market_summary (today's data)
    # Columns: symbol, price, volume_24h, event_time, source, processed_at
    cur.execute("""
        CREATE TABLE IF NOT EXISTS silver.prices (
            symbol VARCHAR(20),
            price DECIMAL(18,8),
            volume_24h DECIMAL(24,8),
            event_time TIMESTAMP,
            source VARCHAR(50),
            processed_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_prices_symbol ON silver.prices(symbol)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_prices_event_time ON silver.prices(event_time)")

    # ── silver.news ──
    # Used by: stg_news.sql
    # Columns: source, title, description, url, published_at, content, ingested_at
    cur.execute("""
        CREATE TABLE IF NOT EXISTS silver.news (
            source VARCHAR(255),
            title TEXT,
            description TEXT,
            url TEXT,
            published_at TIMESTAMP,
            content TEXT,
            ingested_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_news_published_at ON silver.news(published_at)")

    # ── silver.social ──
    # Used by: stg_social.sql
    # Columns: subreddit, post_id, title, text, score, num_comments, created_utc, created_at, url, type, ingested_at
    cur.execute("""
        CREATE TABLE IF NOT EXISTS silver.social (
            subreddit VARCHAR(100),
            post_id VARCHAR(255),
            title TEXT,
            text TEXT,
            score INTEGER,
            num_comments INTEGER,
            created_utc BIGINT,
            created_at TIMESTAMP,
            url TEXT,
            type VARCHAR(20),
            ingested_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_social_created_at ON silver.social(created_at)")

    # ── silver.news_sentiment ──
    # Used by: stg_news_sentiment.sql → market_sentiment (Gold)
    # Columns: article_id, symbol, title, sentiment_score, sentiment_label, published_at, source, ingested_at
    cur.execute("""
        CREATE TABLE IF NOT EXISTS silver.news_sentiment (
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
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sentiment_published_at ON silver.news_sentiment(published_at)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sentiment_label ON silver.news_sentiment(sentiment_label)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sentiment_symbol ON silver.news_sentiment(symbol)")

    conn.commit()
    print("✅ Silver tables created: historical, prices, news, social, news_sentiment")


def verify_setup(conn):
    """Verify all tables exist and print status."""
    cur = conn.cursor()
    print("\n=== Schema Verification ===")

    tables = [
        "public.users", "public.watchlists", "public.alerts",
        "public.portfolios", "public.refresh_tokens",
        "silver.historical", "silver.prices", "silver.news",
        "silver.social", "silver.news_sentiment",
    ]

    for tbl in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {tbl}")
            count = cur.fetchone()[0]
            status = "✅" if count > 0 else "🔲 (empty)"
            print(f"  {status} {tbl}: {count} rows")
        except Exception as e:
            conn.rollback()
            print(f"  ❌ {tbl}: MISSING — {str(e).split(chr(10))[0]}")

    # Check gold schema exists
    cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'gold'")
    if cur.fetchone():
        print("  ✅ gold schema exists (tables created by dbt run)")
    else:
        print("  ❌ gold schema missing")


def main():
    print("=" * 60)
    print("🏗️  CryptoPulse — Supabase Schema Setup")
    print("=" * 60)

    conn = get_connection()

    print("\n🔧 Step 1: Creating schemas...")
    setup_schemas(conn)

    print("\n🔧 Step 2: Creating public tables...")
    setup_public_tables(conn)

    print("\n🔧 Step 3: Creating silver tables...")
    setup_silver_tables(conn)

    print("\n🔍 Step 4: Verifying setup...")
    verify_setup(conn)

    conn.close()

    print("\n" + "=" * 60)
    print("✅ Schema setup complete!")
    print("   Next: python scripts/seed_supabase_direct.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
