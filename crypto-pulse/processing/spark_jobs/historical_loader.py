"""
historical_loader.py - Historical Data Loader

Reads raw historical JSON files from Binance ingestion,
parses them into a structured schema, and writes them to the
Bronze layer in Azure Data Lake Gen2 using Delta Lake format.
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_timestamp, from_unixtime
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, LongType, ArrayType
)

# =====================================================================
# Logging Configuration
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("HistoricalLoader")


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
    logger.info("Starting Spark session for historical load...")
    sa = config["storage_account"]
    
    spark = (
        SparkSession.builder
        .appName("HistoricalLoader")
        .config("spark.jars.packages", ",".join([
            "org.apache.hadoop:hadoop-azure:3.3.4",
            "org.wildfly.openssl:wildfly-openssl:1.1.3.Final",
            "io.delta:delta-spark_2.12:3.2.0"
        ]))
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config(f"fs.azure.account.auth.type.{sa}.dfs.core.windows.net", "OAuth")
        .config(f"fs.azure.account.oauth.provider.type.{sa}.dfs.core.windows.net", "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider")
        .config(f"fs.azure.account.oauth2.client.id.{sa}.dfs.core.windows.net", config["azure_client_id"])
        .config(f"fs.azure.account.oauth2.client.secret.{sa}.dfs.core.windows.net", config["azure_client_secret"])
        .config(f"fs.azure.account.oauth2.client.endpoint.{sa}.dfs.core.windows.net", f"https://login.microsoftonline.com/{config['azure_tenant_id']}/oauth2/token")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark


def process_historical_files(spark, config):
    """Read local JSON files and transform to Delta."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    historical_dir = os.path.join(project_root, "data", "historical")
    
    if not os.path.exists(historical_dir):
        logger.error(f"Historical directory not found: {historical_dir}")
        return

    json_files = [f for f in os.listdir(historical_dir) if f.endswith(".json")]
    if not json_files:
        logger.warning("No historical JSON files found.")
        return

    logger.info(f"Processing {len(json_files)} files...")

    # Define schema for the list of lists in JSON
    # Binance Kline: list of [open_time, open, high, low, close, volume, close_time, quote_asset_vol, trades, buy_base, buy_quote, ignore]
    raw_schema = ArrayType(ArrayType(StringType()))

    final_df = None

    for file_name in json_files:
        symbol = file_name.split("_")[0].upper()
        file_path = os.path.join(historical_dir, file_name)
        logger.info(f"  Loading {symbol} from {file_name}")

        # Read JSON file into a single-column DataFrame containing the array
        raw_json_df = spark.read.option("multiline", "true").json(file_path)
        
        # Explode the outer list to get rows of klines
        from pyspark.sql.functions import explode
        klines_df = raw_json_df.select(explode(col("element")).alias("kline"))

        # Extract fields from the array
        parsed_df = klines_df.select(
            (col("kline")[0].cast(LongType()) / 1000).cast("timestamp").alias("open_time"),
            col("kline")[1].cast(DoubleType()).alias("open"),
            col("kline")[2].cast(DoubleType()).alias("high"),
            col("kline")[3].cast(DoubleType()).alias("low"),
            col("kline")[4].cast(DoubleType()).alias("close"),
            col("kline")[5].cast(DoubleType()).alias("volume"),
            (col("kline")[6].cast(LongType()) / 1000).cast("timestamp").alias("close_time"),
            col("kline")[7].cast(DoubleType()).alias("quote_asset_volume"),
            col("kline")[8].cast(LongType()).alias("number_of_trades"),
            col("kline")[9].cast(DoubleType()).alias("taker_buy_base_asset_volume"),
            col("kline")[10].cast(DoubleType()).alias("taker_buy_quote_asset_volume"),
            lit(symbol).alias("symbol"),
            current_timestamp().alias("ingested_at")
        )

        if final_df is None:
            final_df = parsed_df
        else:
            final_df = final_df.union(parsed_df)

    if final_df:
        output_path = f"abfss://{config['container']}@{config['storage_account']}.dfs.core.windows.net/bronze/historical"
        logger.info(f"Writing all historical data to Delta at {output_path}")
        
        (
            final_df.write
            .format("delta")
            .mode("overwrite")
            .partitionBy("symbol")
            .save(output_path)
        )
        logger.info("Historical data ingestion completed successfully.")


def main():
    config = load_environment()
    spark = create_spark_session(config)
    try:
        process_historical_files(spark, config)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
