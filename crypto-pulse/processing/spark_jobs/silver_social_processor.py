import os
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_unixtime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Silver Social Processor Job")

    spark = SparkSession.builder \
        .appName("SilverSocialProcessor") \
        .getOrCreate()

    # ADLS Configuration
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    container = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "datalake")
    input_path = f"abfss://{container}@{storage_account}.dfs.core.windows.net/bronze/social"
    output_path = f"abfss://{container}@{storage_account}.dfs.core.windows.net/silver/social"

    try:
        logger.info(f"Reading from Bronze: {input_path}")
        bronze_df = spark.read.format("delta").load(input_path)

        # Transformation: Convert created_utc to proper created_at timestamp
        silver_df = bronze_df.select(
            col("subreddit"),
            col("post_id"),
            col("title"),
            col("text"),
            col("score"),
            col("num_comments"),
            col("created_utc"),
            from_unixtime(col("created_utc")).cast("timestamp").alias("created_at"),
            col("url"),
            col("type"),
            col("ingested_at")
        ).filter(col("title").isNotNull() | col("text").isNotNull())

        # Write to Silver (Delta)
        logger.info(f"Writing to Silver: {output_path}")
        silver_df.write.format("delta") \
            .mode("overwrite") \
            .save(output_path)
            
        logger.info("Successfully processed Social to Silver")
    except Exception as e:
        logger.error(f"Error processing Social: {str(e)}")

    spark.stop()

if __name__ == "__main__":
    main()
