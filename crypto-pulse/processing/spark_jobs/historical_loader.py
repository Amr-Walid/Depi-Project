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
    logger.info("Starting Spark session for historical load...")
    sa = config["storage_account"]
    
    spark = (
        SparkSession.builder
        .appName("HistoricalLoader")
        .master("spark://spark-master:7077")
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



    final_df = None

    for file_name in json_files:
        symbol = file_name.split("_")[0].upper()
        file_path = os.path.join(historical_dir, file_name)
        logger.info(f"  Loading {symbol} from {file_name}")

        import json
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        df_data = []
        for item in data:
            df_data.append([str(x) for x in item[:12]])
            
        schema = [
            "raw_open_time", "raw_open", "raw_high", "raw_low", "raw_close", "raw_volume", 
            "raw_close_time", "quote_asset_volume", "number_of_trades", 
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ]
        from pyspark.sql.types import StructType, StructField, StringType
        spark_schema = StructType([StructField(name, StringType(), True) for name in schema])
        
        symbol_df = spark.createDataFrame(df_data, schema=spark_schema)

        # Extract fields from the array
        parsed_df = symbol_df.select(
            (col("raw_open_time").cast(LongType()) / 1000).cast("timestamp").alias("open_time"),
            col("raw_open").cast(DoubleType()).alias("open"),
            col("raw_high").cast(DoubleType()).alias("high"),
            col("raw_low").cast(DoubleType()).alias("low"),
            col("raw_close").cast(DoubleType()).alias("close"),
            col("raw_volume").cast(DoubleType()).alias("volume"),
            (col("raw_close_time").cast(LongType()) / 1000).cast("timestamp").alias("close_time"),
            col("quote_asset_volume").cast(DoubleType()).alias("quote_asset_volume"),
            col("number_of_trades").cast(LongType()).alias("number_of_trades"),
            col("taker_buy_base_asset_volume").cast(DoubleType()).alias("taker_buy_base_asset_volume"),
            col("taker_buy_quote_asset_volume").cast(DoubleType()).alias("taker_buy_quote_asset_volume"),
            lit(symbol).alias("symbol"),
            current_timestamp().alias("ingested_at")
        )

        if final_df is None:
            final_df = parsed_df
        else:
            final_df = final_df.union(parsed_df)

    if final_df:
        output_path = f"abfss://{config['container']}@{config['storage_account']}.dfs.core.windows.net/bronze/historical"
        
        # Create temporary view for the new data
        final_df.createOrReplaceTempView("source_data")
        
        try:
            logger.info(f"Performing Delta MERGE (Upsert) via Spark SQL to {output_path}")
            spark.sql(f"""
                MERGE INTO delta.`{output_path}` AS target
                USING source_data AS source
                ON target.symbol = source.symbol AND target.open_time = source.open_time
                WHEN MATCHED THEN UPDATE SET *
                WHEN NOT MATCHED THEN INSERT *
            """)
        except Exception as e:
            logger.info(f"Initial write or Delta table not found. Writing full load to {output_path}")
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
