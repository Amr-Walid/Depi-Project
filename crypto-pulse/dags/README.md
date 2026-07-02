# Apache Airflow DAG Workflows

This directory houses the **Directed Acyclic Graphs (DAGs)** that orchestrate the pipeline executions for data synchronization, FinBERT sentiment scoring, and dbt analytic builds.

---

## Directory Structure

```
dags/
├── dag_historical_daily.py   # Daily batch DAG: history, sentiment, and core metrics
└── dag_prices_frequent.py    # 5-minute interval DAG: live price sync and dbt models
```

---

## DAG 1: `dag_historical_daily` (Daily Batch)

This DAG is scheduled to run once every day (`@daily`) and is responsible for pulling historical candles, syncing news/social feeds, running PySpark ML models, and materializing gold reporting tables.

### Workflow Sequence

```mermaid
graph TD
    A[fetch_historical_data] -->|Downloads raw candles| B[ingest_historical_to_bronze]
    B -->|Loads JSON to Delta| C[process_historical_to_silver]
    C -->|Cleans & Merges| D[sync_historical_to_postgres]
    D -->|JDBC Sync| E[sync_news_to_postgres]
    E -->|JDBC Sync| F[sync_social_to_postgres]
    F -->|JDBC Sync| G[run_sentiment_analysis]
    G -->|FinBERT UDF| H[run_dbt_gold]
```

---

## DAG 2: `dag_prices_frequent` (5-Minute Sync)

This DAG triggers every 5 minutes (`*/5 * * * *`) to keep the frontend dashboard updated with real-time price tickers.

### Workflow Sequence

```mermaid
graph TD
    A[sync_prices_to_postgres] -->|JDBC Sync 5m Stream| B[run_dbt_prices]
```

---

## Configuration Details

Both DAGs run via `BashOperator` but target execution on the separate `spark-master` container:
*   **Docker Execution**: Command syntax runs as `docker exec spark-master spark-submit ...`.
*   **JAR Preloading**: The custom Spark worker container contains all needed Azure Storage, Kafka connectors, and PostgreSQL JDBC driver JARs natively under `/opt/spark/jars/`.
*   **Environment Handling**: Credentials like database endpoints, passwords, and Azure client keys are populated via system env variables passed straight to the containers from `.env`.
