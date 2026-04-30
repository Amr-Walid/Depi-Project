import os
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, LongType

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
    logger.info("Starting Bronze News Consumer Job")
    az = get_azure_configs()
    sa = az["storage_account"]

    spark = SparkSession.builder \
        .appName("BronzeNewsConsumer") \
        .config(f"fs.azure.account.auth.type.{sa}.dfs.core.windows.net", "OAuth") \
        .config(f"fs.azure.account.oauth.provider.type.{sa}.dfs.core.windows.net", "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider") \
        .config(f"fs.azure.account.oauth2.client.id.{sa}.dfs.core.windows.net", az["client_id"]) \
        .config(f"fs.azure.account.oauth2.client.secret.{sa}.dfs.core.windows.net", az["client_secret"]) \
        .config(f"fs.azure.account.oauth2.client.endpoint.{sa}.dfs.core.windows.net", f"https://login.microsoftonline.com/{az['tenant_id']}/oauth2/token") \
        .getOrCreate()

    # Kafka Configuration
    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_topic = os.getenv("KAFKA_TOPIC_NEWS", "crypto.news")

    # ADLS Configuration
    storage_account = az["storage_account"]
    container = az["container"]
    output_path = f"abfss://{container}@{storage_account}.dfs.core.windows.net/bronze/news"
    checkpoint_path = f"abfss://{container}@{storage_account}.dfs.core.windows.net/checkpoints/bronze_news"

    # Schema for NewsAPI payload (Matching Ahmed's producer)
    news_schema = StructType([
        StructField("source", StringType(), True),
        StructField("author", StringType(), True),
        StructField("title", StringType(), True),
        StructField("description", StringType(), True),
        StructField("url", StringType(), True),
        StructField("published_at", StringType(), True),
        StructField("content", StringType(), True),
        StructField("timestamp", LongType(), True)
    ])

    # Read from Kafka
    logger.info(f"Reading from Kafka topic: {kafka_topic}")
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("subscribe", kafka_topic) \
        .option("startingOffsets", "earliest") \
        .load()

    # Parse JSON and add ingestion timestamp
    parsed_df = kafka_df.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col("value"), news_schema).alias("data")) \
        .select("data.*") \
        .withColumn("ingested_at", current_timestamp())

    # Write to Bronze (Delta format)
    logger.info(f"Writing to Bronze path: {output_path}")
    query = parsed_df.writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("checkpointLocation", checkpoint_path) \
        .start(output_path)

    query.awaitTermination()

if __name__ == "__main__":
    main()
