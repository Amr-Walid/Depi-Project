import os
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Silver News Processor Job")

    spark = SparkSession.builder \
        .appName("SilverNewsProcessor") \
        .getOrCreate()

    # ADLS Configuration
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    container = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "datalake")
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
