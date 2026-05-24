import os
import logging
from pyspark.sql import SparkSession

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
    logger.info("Starting Checkpoints Cleanup Job")
    az = get_azure_configs()
    sa = az["storage_account"]

    spark = SparkSession.builder \
        .appName("CleanupCheckpoints") \
        .config(f"fs.azure.account.auth.type.{sa}.dfs.core.windows.net", "OAuth") \
        .config(f"fs.azure.account.oauth.provider.type.{sa}.dfs.core.windows.net", "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider") \
        .config(f"fs.azure.account.oauth2.client.id.{sa}.dfs.core.windows.net", az["client_id"]) \
        .config(f"fs.azure.account.oauth2.client.secret.{sa}.dfs.core.windows.net", az["client_secret"]) \
        .config(f"fs.azure.account.oauth2.client.endpoint.{sa}.dfs.core.windows.net", f"https://login.microsoftonline.com/{az['tenant_id']}/oauth2/token") \
        .getOrCreate()

    try:
        sc = spark.sparkContext
        fs = sc._jvm.org.apache.hadoop.fs.FileSystem.get(sc._jsc.hadoopConfiguration())
        
        container = az["container"]
        path_str = f"abfss://{container}@{sa}.dfs.core.windows.net/checkpoints"
        checkpoint_path = sc._jvm.org.apache.hadoop.fs.Path(path_str)
        
        logger.info(f"Checking if path exists: {path_str}")
        if fs.exists(checkpoint_path):
            logger.info(f"Deleting path recursively: {path_str}")
            fs.delete(checkpoint_path, True)
            logger.info("Checkpoints deleted successfully!")
        else:
            logger.info("No checkpoints path found to delete.")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

    spark.stop()

if __name__ == "__main__":
    main()
