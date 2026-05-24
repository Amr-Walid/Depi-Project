import psycopg2
from urllib.parse import quote_plus

pwd = quote_plus("R1m@pi9bw123w123")
DSN = f"postgresql://postgres.idiidwhgddbxdbnpamag:{pwd}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require"

def main():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute("SELECT MIN(open_time), MAX(open_time), COUNT(*) FROM silver.historical")
    row = cur.fetchone()
    print("Supabase PG stats for silver.historical:")
    print(f"  - Min open_time: {row[0]}")
    print(f"  - Max open_time: {row[1]}")
    print(f"  - Total rows: {row[2]}")
    conn.close()

if __name__ == "__main__":
    main()
