"""
silver_processor.py - Silver Layer Processing Job

Reads raw data from the Bronze layer in Azure ADLS Gen2, 
applies cleaning, schema parsing, and normalization,
and writes the cleaned data to the Silver layer in Delta format.
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, current_timestamp, 
    year, month, day
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, LongType
)
from delta.tables import DeltaTable

# =====================================================================
# Logging Configuration
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("SilverProcessor")


def load_environment():
    """Load and validate environment variables."""
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    load_dotenv(dotenv_path=env_path)

    config = {
        "azure_client_id": os.getenv("AZURE_CLIENT_ID"),
        "azure_client_secret": os.getenv("AZURE_CLIENT_SECRET"),
        "azure_tenant_id": os.getenv("AZURE_TENANT_ID"),
        "storage_account": os.getenv("AZURE_STORAGE_ACCOUNT_NAME"),
        "container": os.getenv("AZURE_STORAGE_CONTAINER_NAME", "datalake"),
    }

    missing = [k for k in ["azure_client_id", "azure_client_secret", "azure_tenant_id", "storage_account"] if not config[k]]
    if missing:
        logger.error(f"Missing environment variables: {missing}")
        sys.exit(1)

    return config


def create_spark_session(config):
    """Start Spark with Azure and Delta support."""
    logger.info("Starting Spark session for Silver Layer processing (Milestone 2)...")
    sa = config["storage_account"]
    
    spark = (
        SparkSession.builder
        .appName("SilverProcessor")
        .config("spark.jars.packages", ",".join([
            "org.apache.hadoop:hadoop-azure:3.3.4",
            "org.wildfly.openssl:wildfly-openssl:1.1.3.Final",
            "io.delta:delta-spark_2.12:3.2.0"
        ]))
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.databricks.delta.retentionDurationCheck.enabled", "false")
        .config(f"fs.azure.account.auth.type.{sa}.dfs.core.windows.net", "OAuth")
        .config(f"fs.azure.account.oauth.provider.type.{sa}.dfs.core.windows.net", "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider")
        .config(f"fs.azure.account.oauth2.client.id.{sa}.dfs.core.windows.net", config["azure_client_id"])
        .config(f"fs.azure.account.oauth2.client.secret.{sa}.dfs.core.windows.net", config["azure_client_secret"])
        .config(f"fs.azure.account.oauth2.client.endpoint.{sa}.dfs.core.windows.net", f"https://login.microsoftonline.com/{config['azure_tenant_id']}/oauth2/token")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark


def process_bronze_to_silver(spark, config):
    """Read from Bronze, transform with DQ, and Upsert to Silver."""
    
    bronze_path = f"abfss://{config['container']}@{config['storage_account']}.dfs.core.windows.net/bronze/prices"
    silver_path = f"abfss://{config['container']}@{config['storage_account']}.dfs.core.windows.net/silver/prices"
    
    logger.info(f"Step 1: Reading raw data from Bronze Delta table at {bronze_path}")
    bronze_df = spark.read.format("delta").load(bronze_path)
    initial_count = bronze_df.count()
    logger.info(f"Total rows found in Bronze: {initial_count}")

    # Define Schema for JSON parsing
    json_schema = StructType([
        StructField("symbol", StringType(), True),
        StructField("price", DoubleType(), True),
        StructField("volume_24h", DoubleType(), True),
        StructField("timestamp", LongType(), True),
        StructField("source", StringType(), True)
    ])
    
    # Transform and Clean
    processed_df = (
        bronze_df
        .withColumn("data", from_json(col("raw_value"), json_schema))
        .select(
            col("data.symbol").alias("symbol"),
            col("data.price").alias("price"),
            col("data.volume_24h").alias("volume_24h"),
            (col("data.timestamp") / 1000).cast("timestamp").alias("event_time"),
            col("data.source").alias("source"),
            col("kafka_timestamp"),
            current_timestamp().alias("processed_at")
        )
        # 1. Data Quality: Filter out negative or zero prices
        .filter((col("price") > 0) & (col("symbol").isNotNull()))
        # 2. Add partitioning columns
        .withColumn("year", year(col("event_time")))
        .withColumn("month", month(col("event_time")))
        .withColumn("day", day(col("event_time")))
        # 3. Deduplication within the batch
        .dropDuplicates(["symbol", "event_time"])
    )
    
    valid_count = processed_df.count()
    dropped_count = initial_count - valid_count
    logger.info(f"Data Quality Check: {valid_count} valid rows, {dropped_count} rows dropped.")

    # Step 5: Upsert to Silver using MERGE
    logger.info(f"Step 2: Performing Delta MERGE (Upsert) into {silver_path}")
    
    # Check if Silver table exists to perform MERGE, otherwise write new
    if DeltaTable.isDeltaTable(spark, silver_path):
        silver_table = DeltaTable.forPath(spark, silver_path)
        
        (
            silver_table.alias("target")
            .merge(
                processed_df.alias("source"),
                "target.symbol = source.symbol AND target.event_time = source.event_time"
            )
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute()
        )
        logger.info("Delta MERGE completed.")
    else:
        logger.info("Silver table does not exist. Performing initial write.")
        (
            processed_df.write
            .format("delta")
            .mode("overwrite")
            .partitionBy("year", "month", "day")
            .save(silver_path)
        )

    # Step 6: Maintenance - OPTIMIZE
    logger.info("Step 3: Running Delta OPTIMIZE for better query performance.")
    spark.sql(f"OPTIMIZE delta.`{silver_path}`")
    logger.info("Silver Layer processing completed successfully.")


def main():
    config = load_environment()
    spark = create_spark_session(config)
    try:
        process_bronze_to_silver(spark, config)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
