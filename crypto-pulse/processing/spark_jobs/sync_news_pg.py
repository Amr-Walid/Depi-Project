import os
import logging
from pyspark.sql import SparkSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

from dotenv import load_dotenv

def get_azure_configs():
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if not os.path.exists(env_path):
        env_path = os.path.join("/opt", "spark-apps", ".env")
    load_dotenv(dotenv_path=env_path)
    return {
        "client_id": os.getenv("AZURE_CLIENT_ID", "").strip('"'),
        "client_secret": os.getenv("AZURE_CLIENT_SECRET", "").strip('"'),
        "tenant_id": os.getenv("AZURE_TENANT_ID", "").strip('"'),
        "storage_account": os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "stcryptopulsedev2").strip('"'),
        "container": os.getenv("AZURE_STORAGE_CONTAINER_NAME", "datalake").strip('"')
    }

def main():
    logger.info("Starting News Silver to PostgreSQL Sync Job")
    az = get_azure_configs()
    sa = az["storage_account"]
    
    spark = SparkSession.builder \
        .appName("SyncNewsToPostgres") \
        .config(f"fs.azure.account.auth.type.{sa}.dfs.core.windows.net", "OAuth") \
        .config(f"fs.azure.account.oauth.provider.type.{sa}.dfs.core.windows.net", "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider") \
        .config(f"fs.azure.account.oauth2.client.id.{sa}.dfs.core.windows.net", az["client_id"]) \
        .config(f"fs.azure.account.oauth2.client.secret.{sa}.dfs.core.windows.net", az["client_secret"]) \
        .config(f"fs.azure.account.oauth2.client.endpoint.{sa}.dfs.core.windows.net", f"https://login.microsoftonline.com/{az['tenant_id']}/oauth2/token") \
        .getOrCreate()
    
    # Azure ADLS Configuration
    storage_account = az["storage_account"]
    container = az["container"]
    adls_path = f"abfss://{container}@{storage_account}.dfs.core.windows.net/silver/news"
    
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
    
    pg_table = "silver.news"
    
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
