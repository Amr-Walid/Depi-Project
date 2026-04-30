import os
import logging
from pyspark.sql import SparkSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Historical Silver to PostgreSQL Sync Job")
    
    spark = SparkSession.builder \
        .appName("SyncHistoricalToPostgres") \
        .getOrCreate()
    
    azure_client_id = os.getenv("AZURE_CLIENT_ID")
    azure_tenant_id = os.getenv("AZURE_TENANT_ID")
    azure_client_secret = os.getenv("AZURE_CLIENT_SECRET")
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    container = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "datalake")
    
    if all([azure_client_id, azure_tenant_id, azure_client_secret, storage_account]):
        logger.info("Configuring Azure ADLS authentication...")
        spark.conf.set(f"fs.azure.account.auth.type.{storage_account}.dfs.core.windows.net", "OAuth")
        spark.conf.set(f"fs.azure.account.oauth.provider.type.{storage_account}.dfs.core.windows.net", "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider")
        spark.conf.set(f"fs.azure.account.oauth2.client.id.{storage_account}.dfs.core.windows.net", azure_client_id)
        spark.conf.set(f"fs.azure.account.oauth2.client.secret.{storage_account}.dfs.core.windows.net", azure_client_secret)
        spark.conf.set(f"fs.azure.account.oauth2.client.endpoint.{storage_account}.dfs.core.windows.net", f"https://login.microsoftonline.com/{azure_tenant_id}/oauth2/token")
    
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
    
    adls_path = f"abfss://{container}@{storage_account}.dfs.core.windows.net/silver/historical"
    pg_table = "silver.historical"
    
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
