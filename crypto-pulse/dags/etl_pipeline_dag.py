from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# ──────────────────────────────────────────────────────────
# Default arguments shared across all tasks
# ──────────────────────────────────────────────────────────
default_args = {
    'owner': 'crypto-pulse-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# ──────────────────────────────────────────────────────────
# DAG Definition
# Runs once daily to ingest and process all data layers.
#
# Pipeline:
#   fetch_historical
#       └──► ingest_historical_to_bronze
#                └──► process_historical_to_silver
#
#   process_realtime_prices_to_silver  (runs independently daily)
# ──────────────────────────────────────────────────────────
with DAG(
    'crypto_pulse_etl_pipeline',
    default_args=default_args,
    description='Full ETL pipeline: Fetch → Bronze → Silver (Historical + Prices)',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['crypto', 'bronze', 'silver', 'etl'],
) as dag:

    # ── Task 1: Fetch Historical OHLCV Data from Binance API ──
    fetch_historical = BashOperator(
        task_id='fetch_historical_data',
        bash_command='python3 /opt/airflow/ingestion/historical/historical_fetcher.py',
    )

    # ── Task 2: Load Historical JSON → Bronze/historical (Delta) ──
    ingest_historical = BashOperator(
        task_id='ingest_historical_to_bronze',
        bash_command=(
            'spark-submit '
            '--master spark://spark-master:7077 '
            '--packages io.delta:delta-spark_2.12:3.2.0,'
            'org.apache.hadoop:hadoop-azure:3.3.4,'
            'org.wildfly.openssl:wildfly-openssl:1.1.3.Final '
            '/opt/airflow/jobs/historical_loader.py'
        ),
    )

    # ── Task 3: Historical Bronze → Silver/historical (Delta) ──
    process_historical_silver = BashOperator(
        task_id='process_historical_to_silver',
        bash_command=(
            'spark-submit '
            '--master spark://spark-master:7077 '
            '--packages io.delta:delta-spark_2.12:3.2.0,'
            'org.apache.hadoop:hadoop-azure:3.3.4,'
            'org.wildfly.openssl:wildfly-openssl:1.1.3.Final '
            '/opt/airflow/jobs/silver_historical_processor.py'
        ),
    )

    # ── Task 4: Realtime Bronze/prices → Silver/prices (Delta) ──
    # Processes the raw Kafka price messages that bronze_consumer.py wrote.
    # Runs independently from the historical chain.
    process_prices_silver = BashOperator(
        task_id='process_realtime_prices_to_silver',
        bash_command=(
            'spark-submit '
            '--master spark://spark-master:7077 '
            '--packages io.delta:delta-spark_2.12:3.2.0,'
            'org.apache.hadoop:hadoop-azure:3.3.4,'
            'org.wildfly.openssl:wildfly-openssl:1.1.3.Final '
            '/opt/airflow/jobs/silver_prices_processor.py'
        ),
    )

    # ── Dependency Chain ──────────────────────────────────────
    # Historical pipeline (sequential):
    fetch_historical >> ingest_historical >> process_historical_silver

    # Prices pipeline (independent — runs daily in parallel):
    process_prices_silver

