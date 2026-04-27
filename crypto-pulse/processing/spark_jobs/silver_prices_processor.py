"""
silver_prices_processor.py — Silver Layer: Realtime Prices Processor

Reads raw streaming price data from the Bronze layer (bronze/prices),
which was written by the Binance producer → Kafka → bronze_consumer pipeline.

The raw Bronze records contain a `raw_value` column that holds a JSON string
with the following schema (produced by producer_binance.py):
  {
    "symbol":     "BTCUSDT",
    "price":      68500.0,
    "volume_24h": 1234567.0,
    "timestamp":  1714231234567,   ← Unix ms from Binance event time
    "source":     "binance"
  }

This script:
  1. Reads the Bronze Delta table at bronze/prices.
  2. Detects incremental data (only rows newer than the last Silver record).
  3. Parses and validates the raw JSON values.
  4. Applies Data Quality (DQ) rules: drops nulls, zeroes, and duplicates.
  5. Enriches with derived columns: event_time (UTC), year/month/day/hour.
  6. Writes cleaned data to silver/prices in Delta Lake format.
  7. Runs OPTIMIZE for compaction.

Output Silver schema:
  symbol         STRING        — e.g. BTCUSDT
  price          DOUBLE        — current market price in USDT
  volume_24h     DOUBLE        — 24-hour rolling volume
  event_time     TIMESTAMP     — parsed from Binance Unix ms timestamp
  source         STRING        — always "binance"
  kafka_timestamp TIMESTAMP   — when Kafka received the message
  ingested_at    TIMESTAMP     — when bronze_consumer wrote to ADLS
  processed_at   TIMESTAMP     — when this script ran
  year           INT           — partition key
  month          INT           — partition key
  day            INT           — partition key
  hour           INT           — partition key

Usage (local spark-submit):
  spark-submit processing/spark_jobs/silver_prices_processor.py

Usage (via Airflow / docker):
  BashOperator pointing to this script inside the Spark container.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, current_timestamp,
    year, month, dayofmonth, hour,
    from_unixtime, to_timestamp
)
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, LongType
)


# =====================================================================
# Logging
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("SilverPricesProcessor")


# =====================================================================
# JSON schema of raw_value coming from producer_binance.py
# =====================================================================
BINANCE_PRICE_SCHEMA = StructType([
    StructField("symbol",     StringType(), True),
    StructField("price",      DoubleType(), True),
    StructField("volume_24h", DoubleType(), True),
    StructField("timestamp",  LongType(),   True),   # Unix ms
    StructField("source",     StringType(), True),
])


# =====================================================================
# Environment
# =====================================================================
def load_environment() -> dict:
    """Load and validate Azure credentials from .env."""
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if not os.path.exists(env_path):
        env_path = os.path.join("/opt", "spark-apps", ".env")

    load_dotenv(dotenv_path=env_path)

    config = {
        "azure_client_id":     os.getenv("AZURE_CLIENT_ID"),
        "azure_client_secret": os.getenv("AZURE_CLIENT_SECRET"),
        "azure_tenant_id":     os.getenv("AZURE_TENANT_ID"),
        "storage_account":     os.getenv("AZURE_STORAGE_ACCOUNT_NAME"),
        "container":           os.getenv("AZURE_STORAGE_CONTAINER_NAME", "datalake"),
    }

    required = ["azure_client_id", "azure_client_secret", "azure_tenant_id", "storage_account"]
    missing  = [k for k in required if not config[k]]
    if missing:
        logger.error(f"Missing environment variables: {missing}")
        sys.exit(1)

    logger.info(f"Environment loaded — storage account: {config['storage_account']}")
    return config


# =====================================================================
# Spark Session
# =====================================================================
def create_spark_session(config: dict) -> SparkSession:
    """Build a SparkSession with Azure ADLS Gen2 + Delta Lake support."""
    logger.info("Starting Spark session for Silver Prices processing...")
    sa = config["storage_account"]

    spark = (
        SparkSession.builder
        .appName("SilverPricesProcessor")
        .master("spark://spark-master:7077")
        .config("spark.jars.packages", ",".join([
            "org.apache.hadoop:hadoop-azure:3.3.4",
            "org.wildfly.openssl:wildfly-openssl:1.1.3.Final",
            "io.delta:delta-spark_2.12:3.2.0",
        ]))
        .config("spark.sql.extensions",        "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.databricks.delta.retentionDurationCheck.enabled", "false")
        # ── Azure OAuth2 / Service Principal ──
        .config(f"fs.azure.account.auth.type.{sa}.dfs.core.windows.net", "OAuth")
        .config(f"fs.azure.account.oauth.provider.type.{sa}.dfs.core.windows.net",
                "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider")
        .config(f"fs.azure.account.oauth2.client.id.{sa}.dfs.core.windows.net",
                config["azure_client_id"])
        .config(f"fs.azure.account.oauth2.client.secret.{sa}.dfs.core.windows.net",
                config["azure_client_secret"])
        .config(f"fs.azure.account.oauth2.client.endpoint.{sa}.dfs.core.windows.net",
                f"https://login.microsoftonline.com/{config['azure_tenant_id']}/oauth2/token")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")
    logger.info(f"Spark session ready (version {spark.version})")
    return spark


# =====================================================================
# Core Processing
# =====================================================================
def process_bronze_prices_to_silver(spark: SparkSession, config: dict) -> None:
    """
    Read raw price rows from bronze/prices, parse, clean, and write to silver/prices.
    Uses incremental loading — only processes rows newer than the latest Silver record.
    """
    container = config["container"]
    sa        = config["storage_account"]

    bronze_path = f"abfss://{container}@{sa}.dfs.core.windows.net/bronze/prices"
    silver_path = f"abfss://{container}@{sa}.dfs.core.windows.net/silver/prices"

    # ── Step 1: Read Bronze Delta table ──────────────────────────────
    logger.info(f"Step 1: Reading Bronze Delta table at {bronze_path}")
    try:
        bronze_df = spark.read.format("delta").load(bronze_path)
    except Exception as e:
        logger.error(f"Cannot read Bronze table at {bronze_path}: {e}")
        logger.error("Make sure bronze_consumer.py has run and written data first.")
        sys.exit(1)

    total_bronze = bronze_df.count()
    logger.info(f"  Bronze rows available: {total_bronze:,}")

    if total_bronze == 0:
        logger.warning("Bronze/prices is empty. Nothing to process. Exiting.")
        return

    # ── Step 2: Incremental load check ───────────────────────────────
    silver_exists      = False
    last_silver_time   = None

    try:
        last_silver_time = (
            spark.sql(f"SELECT MAX(kafka_timestamp) FROM delta.`{silver_path}`")
            .collect()[0][0]
        )
        silver_exists = True
        logger.info(f"  Silver table exists. Last kafka_timestamp: {last_silver_time}")
    except Exception:
        logger.info("  Silver table does not exist yet. Will perform full initial load.")

    # Filter only new Bronze rows not yet processed into Silver
    if silver_exists and last_silver_time is not None:
        source_df  = bronze_df.filter(col("kafka_timestamp") > last_silver_time)
        new_count  = source_df.count()
        if new_count == 0:
            logger.info("Silver/prices is already up to date. No new rows to process. Exiting.")
            return
        logger.info(f"  Incremental load: {new_count:,} new rows to process.")
    else:
        source_df = bronze_df
        logger.info(f"  Full load: {total_bronze:,} rows to process.")

    # ── Step 3: Parse raw_value JSON ─────────────────────────────────
    logger.info("Step 3: Parsing raw_value JSON from Binance Kafka messages...")
    parsed_df = source_df.withColumn(
        "parsed", from_json(col("raw_value"), BINANCE_PRICE_SCHEMA)
    ).select(
        # Fields from parsed JSON
        col("parsed.symbol").alias("symbol"),
        col("parsed.price").alias("price"),
        col("parsed.volume_24h").alias("volume_24h"),
        col("parsed.source").alias("source"),

        # Convert Binance Unix-ms timestamp → UTC Timestamp
        to_timestamp(
            from_unixtime(col("parsed.timestamp") / 1000)
        ).alias("event_time"),

        # Bronze metadata
        col("kafka_timestamp"),
        col("ingested_at"),

        # Processing time
        current_timestamp().alias("processed_at"),
    )

    # ── Step 4: Data Quality Rules ────────────────────────────────────
    logger.info("Step 4: Applying Data Quality rules...")
    cleaned_df = (
        parsed_df
        # Drop rows where critical fields are null
        .filter(col("symbol").isNotNull())
        .filter(col("price").isNotNull())
        .filter(col("event_time").isNotNull())
        # Drop zero or negative prices (bad data)
        .filter(col("price") > 0)
        # Drop zero or negative volumes
        .filter(col("volume_24h") > 0)
        # Deduplicate: same symbol at the same event_time from Binance
        .dropDuplicates(["symbol", "event_time"])
    )

    valid_count = cleaned_df.count()
    logger.info(f"  DQ Result: {valid_count:,} valid rows after cleaning "
                f"(dropped {source_df.count() - valid_count:,} rows).")

    if valid_count == 0:
        logger.warning("All rows were dropped by DQ rules. Nothing to write.")
        return

    # ── Step 5: Add partition columns ─────────────────────────────────
    logger.info("Step 5: Adding partition columns (year / month / day / hour)...")
    enriched_df = (
        cleaned_df
        .withColumn("year",  year(col("event_time")))
        .withColumn("month", month(col("event_time")))
        .withColumn("day",   dayofmonth(col("event_time")))
        .withColumn("hour",  hour(col("event_time")))
    )

    # ── Step 6: Write to Silver ───────────────────────────────────────
    if silver_exists:
        logger.info(f"Step 6: Appending {valid_count:,} rows to Silver at {silver_path}")
        (
            enriched_df.write
            .format("delta")
            .mode("append")
            .partitionBy("year", "month", "day", "hour")
            .save(silver_path)
        )
        logger.info("  Append completed.")
    else:
        logger.info(f"Step 6: Writing initial Silver table at {silver_path}")
        (
            enriched_df.write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .partitionBy("year", "month", "day", "hour")
            .save(silver_path)
        )
        logger.info("  Initial load completed.")

    # ── Step 7: Delta OPTIMIZE ────────────────────────────────────────
    logger.info("Step 7: Running Delta OPTIMIZE for better query performance...")
    spark.sql(f"OPTIMIZE delta.`{silver_path}`")
    logger.info("Silver Prices processing completed successfully.")
    logger.info(f"  Output path : {silver_path}")
    logger.info(f"  Rows written: {valid_count:,}")


# =====================================================================
# Entry Point
# =====================================================================
def main():
    logger.info("=" * 60)
    logger.info("  CryptoPulse — Silver Prices Processor")
    logger.info("  bronze/prices  ──►  silver/prices")
    logger.info("=" * 60)

    config = load_environment()
    spark  = create_spark_session(config)

    try:
        process_bronze_prices_to_silver(spark, config)
    except Exception as e:
        logger.error(f"Silver Prices Processor failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        spark.stop()
        logger.info("Spark session stopped.")


if __name__ == "__main__":
    main()
