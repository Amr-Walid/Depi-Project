import os
import logging
from pyspark.sql import SparkSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Historical Silver to PostgreSQL Sync Job")
    
    spark = SparkSession.builder \
        .appName("SyncHistoricalToPostgres") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
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
    
    from supabase_utils import get_supabase_jdbc_config
    jdbc_url, jdbc_properties = get_supabase_jdbc_config()
    
    adls_path = f"abfss://{container}@{storage_account}.dfs.core.windows.net/silver/historical"
    pg_table = "silver.historical"
    
    try:
        logger.info(f"Reading from ADLS: {adls_path}")
        df = spark.read.format("delta").load(adls_path)
        
        # Incremental Load Logic
        try:
            logger.info(f"Checking for max open_time in PostgreSQL table: {pg_table}")
            max_date_df = spark.read.jdbc(
                url=jdbc_url,
                table=f"(SELECT MAX(open_time) as max_date FROM {pg_table}) as tmp",
                properties=jdbc_properties
            )
            max_date = max_date_df.collect()[0]["max_date"]
            
            if max_date:
                logger.info(f"Max open_time found: {max_date}. Filtering new records...")
                from pyspark.sql.functions import col
                df = df.filter(col("open_time") > max_date)
            else:
                logger.info("Table exists but is empty. Performing full load.")
        except Exception as e:
            logger.info("Table does not exist or max date could not be fetched. Performing full load.")
        
        if df.isEmpty():
            logger.info("No new records to sync.")
        else:
            logger.info(f"Writing {df.count()} records to PostgreSQL table: {pg_table} (mode: append)")
            df.write.jdbc(
                url=jdbc_url,
                table=pg_table,
                mode="append",
                properties=jdbc_properties
            )
            logger.info(f"Successfully synced {pg_table}")
            
    except Exception as e:
        logger.error(f"Error syncing table {pg_table}: {str(e)}")
            
    spark.stop()

if __name__ == "__main__":
    main()
