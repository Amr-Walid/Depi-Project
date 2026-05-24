import psycopg2
from urllib.parse import quote_plus

pwd = quote_plus("R1m@pi9bw123w123")
DSN = f"postgresql://postgres.idiidwhgddbxdbnpamag:{pwd}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require"

def main():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT n.nspname, c.relname, a.attname
        FROM pg_attribute a
        JOIN pg_class c ON a.attrelid = c.oid
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE c.relname = 'historical'
          AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY n.nspname, a.attnum
    """)
    cols = cur.fetchall()
    print("All tables named 'historical' in Supabase:")
    for col in cols:
         print(f"  - Schema: {col[0]}, Table: {col[1]}, Column: {col[2]}")
        
    conn.close()

if __name__ == "__main__":
    main()
