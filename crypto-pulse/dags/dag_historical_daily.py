from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'crypto-pulse-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'dag_historical_daily',
    default_args=default_args,
    description='Daily Batch Pipeline: Fetch, Process, Sync, and dbt Gold Layer for Historical Data',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['crypto', 'historical', 'batch', 'dbt'],
) as dag:

    # All JARs (delta, hadoop-azure, postgresql, kafka) are pre-installed in the Spark image.
    # No --packages needed — faster and no network dependency.

    # 1. Fetch Historical OHLCV Data from Binance API
    fetch_historical = BashOperator(
        task_id='fetch_historical_data',
        bash_command='python3 /opt/airflow/ingestion/historical/historical_fetcher.py',
    )

    # 2. Load Historical JSON → Bronze/historical (Delta)
    ingest_historical = BashOperator(
        task_id='ingest_historical_to_bronze',
        bash_command=(
            'docker exec spark-master '
            '/opt/spark/bin/spark-submit '
            '--conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension '
            '--conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog '
            '/opt/spark/jobs/historical_loader.py'
        ),
    )

    # 3. Historical Bronze → Silver/historical (Delta)
    process_historical_silver = BashOperator(
        task_id='process_historical_to_silver',
        bash_command=(
            'docker exec spark-master '
            '/opt/spark/bin/spark-submit '
            '--conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension '
            '--conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog '
            '/opt/spark/jobs/silver_historical_processor.py'
        ),
    )

    # 4. Sync Silver Historical Data from ADLS to PostgreSQL
    sync_historical_postgres = BashOperator(
        task_id='sync_historical_to_postgres',
        bash_command=(
            'docker exec spark-master '
            '/opt/spark/bin/spark-submit '
            '--conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension '
            '--conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog '
            '/opt/spark/jobs/sync_historical_pg.py'
        ),
    )

    # 5. Sync News & Social Data from ADLS to PostgreSQL
    sync_news_postgres = BashOperator(
        task_id='sync_news_to_postgres',
        bash_command=(
            'docker exec spark-master '
            '/opt/spark/bin/spark-submit '
            '--conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension '
            '--conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog '
            '/opt/spark/jobs/sync_news_pg.py'
        ),
    )

    sync_social_postgres = BashOperator(
        task_id='sync_social_to_postgres',
        bash_command=(
            'docker exec spark-master '
            '/opt/spark/bin/spark-submit '
            '--conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension '
            '--conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog '
            '/opt/spark/jobs/sync_social_pg.py'
        ),
    )

    # 6. Run dbt to generate Gold Layer (Full Models)
    run_dbt_gold = BashOperator(
        task_id='run_dbt_gold',
        bash_command='export POSTGRES_HOST=postgres && cd /opt/airflow/dbt && /home/airflow/.local/bin/dbt deps && /home/airflow/.local/bin/dbt run --select gold_daily_ohlcv daily_market_summary && /home/airflow/.local/bin/dbt test --select gold_daily_ohlcv daily_market_summary',
    )

    # Dependency Chain
    fetch_historical >> ingest_historical >> process_historical_silver >> sync_historical_postgres >> sync_news_postgres >> sync_social_postgres >> run_dbt_gold
