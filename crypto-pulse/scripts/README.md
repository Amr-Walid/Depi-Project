# 📜 Utility & Automation Scripts Directory

This directory contains a suite of automation, seeding, validation, database inspection, and orchestrator runner scripts used to manage the **Crypto-Pulse** pipeline lifecycle.

---

## 📂 Directory Structure & Script Index

Here is a summary of all utility scripts:

| Script Name | Language | Purpose | Key Actions |
| :--- | :---: | :--- | :--- |
| **`run_pipeline_spark_sequential.sh`**| Shell | Sequential Runner | Coordinates WSL/Host paths, runs Spark tasks sequentially to prevent container OOMs, and opens the frontend browser on startup. |
| **`run_pipeline.sh`** | Shell | Pipeline Start | Launches all Spark streaming consumers in Docker container backdrops. |
| **`setup_supabase_schema.py`** | Python | DB Initialization | Sets up database schemas (`public`, `silver`, `gold`) and tables on Supabase Cloud. |
| **`seed_supabase_direct.py`** | Python | Database Seeding | Seeds PostgreSQL with sample dataset rows for testing backend endpoints. |
| **`seed_silver_layer.py`** | Python | Delta Seeding | Populates Bronze/Silver Delta tables on ADLS Gen2 with local historical data. |
| **`generate_dashboard_html.py`**| Python | Visual Generator | Reads PostgreSQL metrics and compiles a standalone, styled HTML dashboard file. |
| **`inspect_db_schema.py`** | Python | DB Verification | Checks tables structures, columns data types, and primary key constraints in the Supabase db. |
| **`inspect_db_stats.py`** | Python | Metrics Inspect | Counts records, records ranges, and table sizes in PostgreSQL schemas. |
| **`inspect_db_catalog.py`** | Python | DB Catalog | Scans all available table namespaces in the relational target. |
| **`inspect_db_cursor.py`** | Python | Raw DB Access | Runs arbitrary read queries on PostgreSQL using raw connections. |
| **`scan_supabase.py`** | Python | Cloud Scan | Quick healthcheck verification for the Supabase Cloud instance. |
| **`test_sentiment.py`** | Python | ML Sandbox | Local sandbox verifying the FinBERT classifier on mock headlines. |

---

## 🏃‍♂️ Key Execution Workflows

### 1. Launching the Sequential Pipeline (`run_pipeline_spark_sequential.sh`)
This shell script is optimized for local environments to prevent Docker memory overflow:
*   Initializes files synchronization.
*   Triggers historical fetch, loading, processing, and Postgres database syncing sequentially.
*   Executes FinBERT sentiment batch scripts.
*   Triggers dbt builds and testing.
*   Launches your system browser directly to the dashboard server.

Run from the root or scripts directory:
```bash
bash scripts/run_pipeline_spark_sequential.sh
```

### 2. Seeding Supabase (`seed_supabase_direct.py`)
To seed the Supabase database with base tables and mock histories:
```bash
python scripts/seed_supabase_direct.py
```

### 3. Database Inspect (`inspect_db_stats.py`)
To print current table row counts and ingestion timelines:
```bash
python scripts/inspect_db_stats.py
```
