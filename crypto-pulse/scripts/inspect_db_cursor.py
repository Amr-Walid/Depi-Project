import psycopg2
from urllib.parse import quote_plus

pwd = quote_plus("R1m@pi9bw123w123")
DSN = f"postgresql://postgres.idiidwhgddbxdbnpamag:{pwd}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require"

def main():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute("SELECT * FROM silver.historical LIMIT 1")
    colnames = [desc[0] for desc in cur.description]
    print("Direct SELECT Column Names:")
    for col in colnames:
        print(f"  - {col}")
    conn.close()

if __name__ == "__main__":
    main()
