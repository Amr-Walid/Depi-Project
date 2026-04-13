"""
bronze_consumer.py - Bronze Layer Consumer

Consumes real-time cryptocurrency price data from Kafka,
and writes it as raw Parquet to the Bronze layer in Azure Data Lake Gen2.

This script is the core of the Bronze layer creation in the CryptoPulse
data lakehouse architecture.

Usage:
    spark-submit --packages org.apache.hadoop:hadoop-azure:3.3.4,\
    org.wildfly.openssl:wildfly-openssl:1.1.3.Final,\
    org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
    bronze_consumer.py
"""

import os
import sys
import logging
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp, lit
from pyspark.sql.types import StringType

# =====================================================================
# Logging Configuration
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("BronzeConsumer")


def load_environment():
    """
    Load environment variables from .env file.
    Returns a dict of all required configuration values.
    """
    # Load .env file (search upward from the current working directory)
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    load_dotenv(dotenv_path=env_path)

    config = {
        # Azure Service Principal
        "azure_client_id": os.getenv("AZURE_CLIENT_ID"),
        "azure_client_secret": os.getenv("AZURE_CLIENT_SECRET"),
        "azure_tenant_id": os.getenv("AZURE_TENANT_ID"),
        # Azure Data Lake
        "storage_account": os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "stcryptopulsedev"),
        "container": os.getenv("AZURE_STORAGE_CONTAINER_NAME", "datalake"),
        # Kafka
        "kafka_bootstrap_servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        "kafka_topic": os.getenv("KAFKA_TOPIC_REALTIME_PRICES", "crypto.realtime.prices"),
    }

    # Strip any surrounding quotes from env values
    for key, value in config.items():
        if value and isinstance(value, str):
            config[key] = value.strip('"').strip("'")

    # Validate required credentials
    missing = [k for k in ["azure_client_id", "azure_client_secret", "azure_tenant_id"] if not config[k]]
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        logger.error("Please ensure your .env file contains AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID")
        sys.exit(1)

    logger.info("Environment variables loaded successfully")
    logger.info(f"  Storage Account : {config['storage_account']}")
    logger.info(f"  Container       : {config['container']}")
    logger.info(f"  Kafka Servers   : {config['kafka_bootstrap_servers']}")
    logger.info(f"  Kafka Topic     : {config['kafka_topic']}")

    return config


def create_spark_session(config):
    """
    Create and configure a SparkSession with:
    - Azure Data Lake Gen2 (ADLS Gen2) connectivity via OAuth2 / Service Principal
    - Required Hadoop-Azure and Kafka connector packages
    """
    logger.info("Starting Spark session...")

    storage_account = config["storage_account"]

    spark = (
        SparkSession.builder
        .appName("BronzeConsumer")
        .config(
            "spark.jars.packages",
            ",".join([
                "org.apache.hadoop:hadoop-azure:3.3.4",
                "org.wildfly.openssl:wildfly-openssl:1.1.3.Final",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0",
            ]),
        )
        # ── Delta Lake (optional, for future use) ──
        # .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        # .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        # ── Azure ADLS Gen2 - OAuth2 / Service Principal ──
        .config(
            f"fs.azure.account.auth.type.{storage_account}.dfs.core.windows.net",
            "OAuth",
        )
        .config(
            f"fs.azure.account.oauth.provider.type.{storage_account}.dfs.core.windows.net",
            "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
        )
        .config(
            f"fs.azure.account.oauth2.client.id.{storage_account}.dfs.core.windows.net",
            config["azure_client_id"],
        )
        .config(
            f"fs.azure.account.oauth2.client.secret.{storage_account}.dfs.core.windows.net",
            config["azure_client_secret"],
        )
        .config(
            f"fs.azure.account.oauth2.client.endpoint.{storage_account}.dfs.core.windows.net",
            f"https://login.microsoftonline.com/{config['azure_tenant_id']}/oauth2/token",
        )
        .getOrCreate()
    )

    # Reduce Spark's own verbose logging
    spark.sparkContext.setLogLevel("WARN")

    logger.info(f"Spark session created successfully (version {spark.version})")
    return spark


def read_from_kafka(spark, config):
    """
    Read a streaming DataFrame from a Kafka topic.
    The value column is cast to STRING for downstream processing.
    """
    kafka_servers = config["kafka_bootstrap_servers"]
    kafka_topic = config["kafka_topic"]

    logger.info(f"Reading from Kafka topic '{kafka_topic}' at {kafka_servers}...")

    kafka_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_servers)
        .option("subscribe", kafka_topic)
        .option("startingOffsets", "latest")
        .option("failOnDataLoss", "false")
        .load()
    )

    # Cast the binary Kafka value to a human-readable STRING
    # and keep metadata columns (key, topic, partition, offset, timestamp)
    raw_df = kafka_df.select(
        col("key").cast(StringType()).alias("kafka_key"),
        col("value").cast(StringType()).alias("raw_value"),
        col("topic"),
        col("partition"),
        col("offset"),
        col("timestamp").alias("kafka_timestamp"),
        current_timestamp().alias("ingested_at"),
    )

    logger.info("Kafka stream DataFrame created successfully")
    return raw_df


def write_to_bronze(raw_df, config):
    """
    Write the raw streaming DataFrame to the Bronze layer in ADLS Gen2
    as Parquet files using structured streaming with micro-batch triggers.
    """
    storage_account = config["storage_account"]
    container = config["container"]

    # Construct ADLS Gen2 paths
    bronze_path = (
        f"abfss://{container}@{storage_account}.dfs.core.windows.net"
        f"/bronze/prices"
    )
    checkpoint_path = (
        f"abfss://{container}@{storage_account}.dfs.core.windows.net"
        f"/checkpoints/bronze/prices"
    )

    logger.info(f"Writing to Bronze layer...")
    logger.info(f"  Output path     : {bronze_path}")
    logger.info(f"  Checkpoint path : {checkpoint_path}")

    query = (
        raw_df.writeStream
        .format("parquet")
        .outputMode("append")
        .option("path", bronze_path)
        .option("checkpointLocation", checkpoint_path)
        .trigger(processingTime="30 seconds")
        .queryName("bronze_prices_stream")
        .start()
    )

    logger.info("Bronze streaming query started successfully")
    logger.info(f"  Query ID   : {query.id}")
    logger.info(f"  Query Name : {query.name}")

    return query


def main():
    """
    Main entry point for the Bronze Consumer.

    Pipeline:
        Kafka Topic  ──►  Spark Structured Streaming  ──►  Bronze Layer (Parquet on ADLS Gen2)
    """
    logger.info("=" * 60)
    logger.info("  CryptoPulse - Bronze Consumer Starting")
    logger.info("=" * 60)

    # Step 1: Load configuration from .env
    config = load_environment()

    # Step 2: Create Spark session with Azure connectivity
    spark = create_spark_session(config)

    try:
        # Step 3: Read from Kafka
        raw_df = read_from_kafka(spark, config)

        # Step 4: Write to Bronze layer in ADLS Gen2
        query = write_to_bronze(raw_df, config)

        logger.info("Bronze Consumer is running. Waiting for termination...")
        logger.info("Press Ctrl+C to stop gracefully.")

        # Block until the query is terminated (manually or by error)
        query.awaitTermination()

    except KeyboardInterrupt:
        logger.info("Received shutdown signal. Stopping gracefully...")
    except Exception as e:
        logger.error(f"Bronze Consumer encountered an error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Stopping Spark session...")
        spark.stop()
        logger.info("Bronze Consumer stopped.")


if __name__ == "__main__":
    main()
