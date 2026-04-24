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
    schedule_interval=None,  # Manual trigger for Milestone 1
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['crypto', 'bronze', 'milestone1'],
) as dag:

    # Task 1: Load Historical Data (Batch)
    ingest_historical = BashOperator(
        task_id='ingest_historical_data',
        bash_command='python3 /opt/airflow/jobs/historical_loader.py',
    )

    # Task 3: Process Silver Layer (Cleaning & Normalization)
    process_silver = BashOperator(
        task_id='process_silver_data',
        bash_command='python3 /opt/airflow/jobs/silver_processor.py',
    )

    ingest_historical >> process_silver
