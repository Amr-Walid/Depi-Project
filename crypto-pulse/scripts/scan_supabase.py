"""Scan Supabase database: schemas, tables, row counts."""
import psycopg2
from urllib.parse import quote_plus

pwd = quote_plus("R1m@pi9bw123w123")
conn = psycopg2.connect(
    f"postgresql://postgres.idiidwhgddbxdbnpamag:{pwd}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require"
)
cur = conn.cursor()

# List schemas
cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('public','silver','gold') ORDER BY schema_name")
print("=== SCHEMAS ===")
for r in cur.fetchall():
    print(f"  {r[0]}")

# List tables per schema
for schema in ['public', 'silver', 'gold']:
    cur.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema}' AND table_type = 'BASE TABLE' ORDER BY table_name")
    tables = cur.fetchall()
    print(f"\n=== {schema.upper()} TABLES ({len(tables)}) ===")
    for t in tables:
        print(f"  {t[0]}")

# Row counts
print("\n=== ROW COUNTS ===")
check_tables = [
    "public.users", "public.alerts", "public.portfolios", "public.watchlists", "public.refresh_tokens",
    "silver.historical", "silver.prices", "silver.news", "silver.social", "silver.news_sentiment",
    "gold.daily_market_summary", "gold.market_sentiment", "gold.gold_daily_ohlcv",
    "gold.gold_latest_prices", "gold.gold_dashboard_stats",
]
for tbl in check_tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        count = cur.fetchone()[0]
        status = "OK" if count > 0 else "EMPTY"
        print(f"  {tbl}: {count} rows [{status}]")
    except Exception as e:
        conn.rollback()
        err = str(e).split('\n')[0]
        print(f"  {tbl}: MISSING [{err}]")

conn.close()
print("\n=== CONNECTION: OK ===")
