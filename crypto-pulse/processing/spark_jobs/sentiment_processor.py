import os
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, FloatType, TimestampType
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Set transformers cache to a writable directory
os.environ["TRANSFORMERS_CACHE"] = "/tmp"
os.environ["HF_HOME"] = "/tmp"

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
    logger.info("Starting Sentiment Analysis Processor (FinBERT)")
    az = get_azure_configs()
    sa = az["storage_account"]
    
    spark = SparkSession.builder \
        .appName("SentimentProcessor") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config(f"fs.azure.account.auth.type.{sa}.dfs.core.windows.net", "OAuth") \
        .config(f"fs.azure.account.oauth.provider.type.{sa}.dfs.core.windows.net", "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider") \
        .config(f"fs.azure.account.oauth2.client.id.{sa}.dfs.core.windows.net", az["client_id"]) \
        .config(f"fs.azure.account.oauth2.client.secret.{sa}.dfs.core.windows.net", az["client_secret"]) \
        .config(f"fs.azure.account.oauth2.client.endpoint.{sa}.dfs.core.windows.net", f"https://login.microsoftonline.com/{az['tenant_id']}/oauth2/token") \
        .getOrCreate()

    # --- Setup Sentiment Analysis via Hugging Face ---
    # Note: transformers and torch must be installed on all Spark workers.
    # We load the model inside the UDF to ensure it's available on workers.
    
    sentiment_schema = StructType([
        StructField("score", FloatType(), False),
        StructField("label", StringType(), False)
    ])

    @udf(returnType=sentiment_schema)
    def analyze_sentiment_udf(text):
        if not text or text.strip() == "":
            return (0.0, "neutral")
        
        try:
            # We import inside to handle serialization correctly across workers
            from transformers import pipeline
            # The model will be cached on each worker after first run
            classifier = pipeline("sentiment-analysis", model="ProsusAI/finbert", device=-1)
            
            # Limit text to 512 tokens to avoid transformer limits
            result = classifier(text[:512])[0]
            return (float(result['score']), result['label'])
        except Exception as e:
            return (0.0, f"error: {str(e)}")

    # --- Paths ---
    container = az["container"]
    news_adls_path = f"abfss://{container}@{sa}.dfs.core.windows.net/silver/news"
    checkpoint_path = f"abfss://{container}@{sa}.dfs.core.windows.net/checkpoints/sentiment/news"
    
    # --- PostgreSQL Setup ---
    pg_host = os.getenv("POSTGRES_HOST", "postgres")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_db = os.getenv("POSTGRES_DB", "cryptopulse")
    pg_user = os.getenv("POSTGRES_USER", "admin")
    pg_password = os.getenv("POSTGRES_PASSWORD", "admin123")
    
    jdbc_url = f"jdbc:postgresql://{pg_host}:{pg_port}/{pg_db}"
    jdbc_properties = {
        "user": pg_user,
        "password": pg_password,
        "driver": "org.postgresql.Driver"
    }
    target_pg_table = "silver.news_sentiment"

    try:
        logger.info(f"Reading News from Delta (Batch): {news_adls_path}")
        df = spark.read.format("delta").load(news_adls_path)

        # Apply sentiment analysis
        sentiment_df = df.withColumn("sentiment", analyze_sentiment_udf(col("title"))) \
                         .select(
                             col("title"),
                             col("symbol"),
                             col("published_at"),
                             col("sentiment.score").alias("sentiment_score"),
                             col("sentiment.label").alias("sentiment_label"),
                             col("source"),
                             current_timestamp().alias("ingested_at")
                         )

        logger.info(f"Writing {sentiment_df.count()} sentiment results to Postgres...")
        sentiment_df.write.jdbc(
            url=jdbc_url,
            table=target_pg_table,
            mode="append",
            properties=jdbc_properties
        )
        logger.info("Batch Sentiment Analysis Complete.")

    except Exception as e:
        logger.error(f"Sentiment Analysis Error: {str(e)}")

if __name__ == "__main__":
    main()
