import psycopg2
from urllib.parse import quote_plus

pwd = quote_plus("R1m@pi9bw123w123")
DSN = f"postgresql://postgres.idiidwhgddbxdbnpamag:{pwd}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require"

def main():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'silver' AND table_name = 'historical'
        ORDER BY ordinal_position
    """)
    cols = cur.fetchall()
    print("Database Columns:")
    for col in cols:
        print(f"  - {col[0]} ({col[1]})")
        
    cur.execute("SELECT MIN(open_time), MAX(open_time), COUNT(*) FROM silver.historical")
    stats = cur.fetchone()
    print("\nDatabase Stats:")
    print(f"  - Min time: {stats[0]}")
    print(f"  - Max time: {stats[1]}")
    print(f"  - Total rows: {stats[2]}")
    
    conn.close()

if __name__ == "__main__":
    main()
