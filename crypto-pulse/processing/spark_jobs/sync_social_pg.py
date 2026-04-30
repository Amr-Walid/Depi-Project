import os
import logging
from pyspark.sql import SparkSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Social Silver to PostgreSQL Sync Job")
    
    spark = SparkSession.builder \
        .appName("SyncSocialToPostgres") \
        .getOrCreate()
    
    # Azure ADLS Configuration
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    container = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "datalake")
    adls_path = f"abfss://{container}@{storage_account}.dfs.core.windows.net/silver/social"
    
    # PostgreSQL Configuration
    pg_host = os.getenv("POSTGRES_HOST", "postgres")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_db = os.getenv("POSTGRES_DB", "cryptopulse")
    pg_user = os.getenv("POSTGRES_USER", "admin")
    pg_password = os.getenv("POSTGRES_PASSWORD", "admin123")
    
    jdbc_url = f"jdbc:postgresql://{pg_host}:{pg_port}/{pg_db}"
    jdbc_properties = {
        "user": pg_user,
        "password": pg_password,
        "driver": "org.postgresql.Driver"
    }
    
    pg_table = "silver.social"
    
    try:
        logger.info(f"Reading from ADLS: {adls_path}")
        df = spark.read.format("delta").load(adls_path)
        
        logger.info(f"Writing to PostgreSQL table: {pg_table}")
        df.write.jdbc(
            url=jdbc_url,
            table=pg_table,
            mode="overwrite",
            properties=jdbc_properties
        )
        logger.info(f"Successfully synced {pg_table}")
    except Exception as e:
        logger.error(f"Error syncing table {pg_table}: {str(e)}")
            
    spark.stop()

if __name__ == "__main__":
    main()
