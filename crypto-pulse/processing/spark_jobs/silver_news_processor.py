import os
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp

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
    logger.info("Starting Silver News Processor")
    az = get_azure_configs()
    sa = az["storage_account"]

    spark = SparkSession.builder \
        .appName("SilverNewsProcessor") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config(f"fs.azure.account.auth.type.{sa}.dfs.core.windows.net", "OAuth") \
        .config(f"fs.azure.account.oauth.provider.type.{sa}.dfs.core.windows.net", "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider") \
        .config(f"fs.azure.account.oauth2.client.id.{sa}.dfs.core.windows.net", az["client_id"]) \
        .config(f"fs.azure.account.oauth2.client.secret.{sa}.dfs.core.windows.net", az["client_secret"]) \
        .config(f"fs.azure.account.oauth2.client.endpoint.{sa}.dfs.core.windows.net", f"https://login.microsoftonline.com/{az['tenant_id']}/oauth2/token") \
        .getOrCreate()

    # ADLS Configuration
    storage_account = az["storage_account"]
    container = az["container"]
    input_path = f"abfss://{container}@{storage_account}.dfs.core.windows.net/bronze/news"
    output_path = f"abfss://{container}@{storage_account}.dfs.core.windows.net/silver/news"

    try:
        logger.info(f"Reading from Bronze: {input_path}")
        bronze_df = spark.read.format("delta").load(input_path)

        # Transformation: Convert published_at string to Timestamp
        silver_df = bronze_df.select(
            col("source"),
            col("title"),
            col("description"),
            col("url"),
            to_timestamp(col("published_at")).alias("published_at"),
            col("content"),
            col("ingested_at")
        ).filter(col("title").isNotNull())

        # Write to Silver (Delta) - Using Overwrite for simplicity in batch sync
        logger.info(f"Writing to Silver: {output_path}")
        silver_df.write.format("delta") \
            .mode("overwrite") \
            .save(output_path)
            
        logger.info("Successfully processed News to Silver")
    except Exception as e:
        logger.error(f"Error processing News: {str(e)}")

    spark.stop()

if __name__ == "__main__":
    main()
