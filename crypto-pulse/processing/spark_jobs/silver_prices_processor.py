"""
silver_prices_processor.py — Silver Layer: Realtime Prices Streaming Processor

Reads raw streaming price data from the Bronze layer (bronze/prices) continuously,
parses the JSON, cleans the data, and writes to silver/prices using Delta MERGE (Upsert).
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
from delta.tables import DeltaTable


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
    logger.info("Starting Spark session for Silver Prices Streaming...")
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
def process_bronze_prices_to_silver_stream(spark: SparkSession, config: dict) -> None:
    """
    Read raw price rows from bronze/prices as a STREAM, parse, clean, 
    and write to silver/prices continuously using micro-batches and Upsert.
    """
    container = config["container"]
    sa        = config["storage_account"]

    bronze_path = f"abfss://{container}@{sa}.dfs.core.windows.net/bronze/prices"
    silver_path = f"abfss://{container}@{sa}.dfs.core.windows.net/silver/prices"
    checkpoint_path = f"abfss://{container}@{sa}.dfs.core.windows.net/checkpoints/silver/prices"

    logger.info(f"Step 1: Reading Bronze Delta table as a STREAM at {bronze_path}")

    # ── 1. Read Stream ──────────────────────────────────────────────
    try:
        bronze_stream_df = spark.readStream.format("delta").load(bronze_path)
    except Exception as e:
        logger.error(f"Cannot read Bronze stream at {bronze_path}: {e}")
        sys.exit(1)

    # ── 2. Parse raw_value JSON ─────────────────────────────────────
    parsed_df = bronze_stream_df.withColumn(
        "parsed", from_json(col("raw_value"), BINANCE_PRICE_SCHEMA)
    ).select(
        col("parsed.symbol").alias("symbol"),
        col("parsed.price").alias("price"),
        col("parsed.volume_24h").alias("volume_24h"),
        col("parsed.source").alias("source"),
        to_timestamp(from_unixtime(col("parsed.timestamp") / 1000)).alias("event_time"),
        col("kafka_timestamp"),
        col("ingested_at"),
        current_timestamp().alias("processed_at"),
    )

    # ── 3. Data Quality Rules ───────────────────────────────────────
    cleaned_df = (
        parsed_df
        .filter(col("symbol").isNotNull())
        .filter(col("price").isNotNull())
        .filter(col("event_time").isNotNull())
        .filter(col("price") > 0)
        .filter(col("volume_24h") > 0)
        .dropDuplicates(["symbol", "event_time"])
    )

    # ── 4. Add partition columns ────────────────────────────────────
    enriched_df = (
        cleaned_df
        .withColumn("year",  year(col("event_time")))
        .withColumn("month", month(col("event_time")))
        .withColumn("day",   dayofmonth(col("event_time")))
        .withColumn("hour",  hour(col("event_time")))
    )

    # ── 5. ForeachBatch Function for Upsert (Merge) ─────────────────
    def upsert_to_silver(microBatchOutputDF, batchId):
        """
        Takes the micro-batch DataFrame and merges it into the Silver Delta Table.
        This ensures duplicate events (same symbol & time) are updated instead of appended twice.
        """
        count = microBatchOutputDF.count()
        logger.info(f"Processing micro-batch {batchId} with {count} records...")
        
        if count == 0:
            return

        # Check if the Delta table exists on Azure
        if DeltaTable.isDeltaTable(spark, silver_path):
            deltaTable = DeltaTable.forPath(spark, silver_path)
            
            # Perform Upsert
            (
                deltaTable.alias("target")
                .merge(
                    microBatchOutputDF.alias("updates"),
                    "target.symbol = updates.symbol AND target.event_time = updates.event_time"
                )
                .whenMatchedUpdateAll()
                .whenNotMatchedInsertAll()
                .execute()
            )
            logger.info(f"Micro-batch {batchId} merged successfully.")
        else:
            # If table doesn't exist, create it by writing the first batch
            logger.info("Silver table does not exist. Initializing table...")
            (
                microBatchOutputDF.write
                .format("delta")
                .mode("overwrite")
                .partitionBy("year", "month", "day", "hour")
                .save(silver_path)
            )
            logger.info("Silver table created successfully.")

    # ── 6. Write Stream ─────────────────────────────────────────────
    logger.info("Step 2: Starting Streaming Query to Silver...")
    
    query = (
        enriched_df.writeStream
        .format("delta")
        .foreachBatch(upsert_to_silver)
        .outputMode("update")
        .option("checkpointLocation", checkpoint_path)
        .trigger(processingTime="30 seconds")
        .queryName("silver_prices_stream")
        .start()
    )

    logger.info("Silver Prices Processor is now running in STREAMING mode.")
    logger.info("It will continuously read from Bronze and Upsert to Silver.")
    logger.info("Press Ctrl+C to stop gracefully.")
    
    # Block until manually stopped
    query.awaitTermination()


# =====================================================================
# Entry Point
# =====================================================================
def main():
    logger.info("=" * 60)
    logger.info("  CryptoPulse — Silver Prices Processor (STREAMING)")
    logger.info("  bronze/prices  ──►  silver/prices (Real-time Upsert)")
    logger.info("=" * 60)

    config = load_environment()
    spark  = create_spark_session(config)

    try:
        process_bronze_prices_to_silver_stream(spark, config)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Stopping gracefully...")
    except Exception as e:
        logger.error(f"Silver Prices Processor failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        spark.stop()
        logger.info("Spark session stopped.")


if __name__ == "__main__":
    main()
