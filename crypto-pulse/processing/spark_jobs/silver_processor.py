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
    if not os.path.exists(env_path):
        env_path = os.path.join("/opt", "spark-apps", ".env")
        
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
        .master("spark://spark-master:7077")
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
    
    bronze_path = f"abfss://{config['container']}@{config['storage_account']}.dfs.core.windows.net/bronze/historical"
    silver_path = f"abfss://{config['container']}@{config['storage_account']}.dfs.core.windows.net/silver/historical"

    # Step 1: Read all Bronze data
    logger.info(f"Step 1: Reading Bronze Delta table at {bronze_path}")
    bronze_df = spark.read.format("delta").load(bronze_path)

    # Step 2: Check if Silver exists and get last processed date
    try:
        last_silver_time = spark.sql(f"SELECT MAX(open_time) FROM delta.`{silver_path}`").collect()[0][0]
        silver_exists = True
        logger.info(f"Silver table found. Last processed open_time: {last_silver_time}")
    except Exception:
        last_silver_time = None
        silver_exists = False
        logger.info("Silver table does not exist. Will perform full initial load.")

    # Step 3: Filter only NEW data from Bronze
    if silver_exists and last_silver_time is not None:
        new_bronze_df = bronze_df.filter(col("open_time") > last_silver_time)
        new_count = new_bronze_df.count()
        if new_count == 0:
            logger.info("No new data found in Bronze. Silver is already up to date. Exiting.")
            return
        logger.info(f"Found {new_count} new rows to add to Silver.")
        source_df = new_bronze_df
    else:
        source_df = bronze_df
        logger.info(f"Full load: {source_df.count()} rows from Bronze.")

    # Step 4: Transform and Clean
    processed_df = (
        source_df
        .withColumn("year", year(col("open_time")))
        .withColumn("month", month(col("open_time")))
        .withColumn("day", day(col("open_time")))
        .withColumn("processed_at", current_timestamp())
        .filter((col("open") > 0) & (col("symbol").isNotNull()))
        .dropDuplicates(["symbol", "open_time"])
    )

    valid_count = processed_df.count()
    logger.info(f"Data Quality Check: {valid_count} valid rows after cleaning.")

    # Step 5: Write to Silver (append only new rows)
    if silver_exists:
        logger.info(f"Step 2: Appending new rows to Silver at {silver_path}")
        (
            processed_df.write
            .format("delta")
            .mode("append")
            .partitionBy("year")
            .save(silver_path)
        )
        logger.info("Append completed.")
    else:
        logger.info(f"Step 2: Writing initial Silver table at {silver_path}")
        (
            processed_df.write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .partitionBy("year")
            .save(silver_path)
        )
        logger.info("Initial load completed.")

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
