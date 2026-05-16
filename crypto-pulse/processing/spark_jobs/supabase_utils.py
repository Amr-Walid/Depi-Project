"""
Supabase connection utilities for Spark JDBC jobs.
Centralizes Supabase-specific connection settings with SSL support.
"""
import os

def get_supabase_jdbc_config():
    """
    Returns JDBC URL and properties for Supabase connection.
    Automatically adds sslmode=require which is mandatory for Supabase.
    """
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT", "5432")
    db   = os.getenv("POSTGRES_DB", "postgres")
    user = os.getenv("POSTGRES_USER", "postgres")
    pwd  = os.getenv("POSTGRES_PASSWORD")

    # Construct JDBC URL with SSL parameter
    jdbc_url = (
        f"jdbc:postgresql://{host}:{port}/{db}"
        f"?sslmode=require"
    )
    
    # JDBC Properties for the Spark write/read action
    jdbc_props = {
        "user": user,
        "password": pwd,
        "driver": "org.postgresql.Driver",
        "sslmode": "require",
    }
    
    return jdbc_url, jdbc_props
