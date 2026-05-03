from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'crypto-pulse-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
}

with DAG(
    'dag_prices_frequent',
    default_args=default_args,
    description='Frequent Micro-Batch Pipeline: Sync and dbt Gold Layer for Real-time Prices',
    schedule_interval=timedelta(minutes=5),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=['crypto', 'prices', 'realtime', 'dbt'],
) as dag:

    # 1. Sync Silver Prices Data from ADLS to PostgreSQL
    # Note: bronze_consumer.py and silver_prices_processor.py are running continuously in background containers.
    # This task just copies the latest state from Silver ADLS to PostgreSQL.
    sync_prices_postgres = BashOperator(
        task_id='sync_prices_to_postgres',
        bash_command=(
            'docker exec spark-master '
            '/opt/spark/bin/spark-submit '
            '--conf spark.jars.ivy=/tmp/.ivy2 '
            '--packages io.delta:delta-spark_2.12:3.2.0,'
            'org.apache.hadoop:hadoop-azure:3.3.4,'
            'org.wildfly.openssl:wildfly-openssl:1.1.3.Final,'
            'org.postgresql:postgresql:42.6.0 '
            '/opt/spark/jobs/sync_prices_pg.py'
        ),
    )

    # 2. Run dbt to generate Gold Layer (Prices Models)
    run_dbt_prices = BashOperator(
        task_id='run_dbt_prices',
        bash_command='export POSTGRES_HOST=postgres && cd /opt/airflow/dbt && /home/airflow/.local/bin/dbt run --select gold_latest_prices daily_market_summary',
    )

    # Dependency Chain
    sync_prices_postgres >> run_dbt_prices
