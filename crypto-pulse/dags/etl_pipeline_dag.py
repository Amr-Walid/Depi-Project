from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# Default arguments for the DAG
default_args = {
    'owner': 'yassin',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    'crypto_pulse_bronze_layer',
    default_args=default_args,
    description='Orchestrates the Bronze layer ingestion (Historical & Streaming)',
    schedule_interval='@daily',  # Runs once a day automatically
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['crypto', 'bronze', 'milestone1'],
) as dag:

    # Task 1: Fetch Historical Data from Binance (Incremental)
    fetch_historical = BashOperator(
        task_id='fetch_historical_data',
        bash_command='python3 /opt/airflow/ingestion/historical/historical_fetcher.py',
    )

    # Task 2: Load Historical Data to Bronze (Batch)
    ingest_historical = BashOperator(
        task_id='ingest_historical_data',
        bash_command='python3 /opt/airflow/jobs/historical_loader.py',
    )

    # Task 3: Process Silver Layer (Cleaning & Normalization)
    process_silver = BashOperator(
        task_id='process_silver_data',
        bash_command='python3 /opt/airflow/jobs/silver_processor.py',
    )

    fetch_historical >> ingest_historical >> process_silver
