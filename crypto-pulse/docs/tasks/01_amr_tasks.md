# Amr Walid — Team Lead & Lead Data Engineer

**Role:** Team Lead + Lead Data Engineer  
**Core Responsibility:** Project architecture, Azure infrastructure, Kafka producers, integration testing, and ensuring all pipeline components connect correctly.

---

## Milestone 1 — Project Foundation and Infrastructure

**Goal:** Build the skeleton of the entire project — GitHub repository, Azure resources, environment configuration, and core ingestion scripts.

---

### Task 1.1 — GitHub Repository Setup [COMPLETE]

**Files affected:** full `crypto-pulse/` directory structure

- [x] Created the GitHub repository
- [x] Established the full directory structure (ingestion, processing, dags, backend, ml, notebooks, docs, spark-apps)
- [x] Structured the project around the Medallion Architecture (Bronze → Silver → Gold)
- [x] Pushed initial files to main/dev branch

---

### Task 1.2 — Root Configuration Files [COMPLETE]

**Files:**
- `.gitignore`
- `.env.example`
- `requirements.txt`

- [x] Created `.gitignore` covering: `.env`, `__pycache__`, `*.pyc`, `data/historical/`, large model files
- [x] Created `.env.example` with all required variable names:
  - `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`
  - `AZURE_STORAGE_ACCOUNT_NAME`, `AZURE_STORAGE_CONTAINER_NAME`
  - `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_TOPIC_REALTIME_PRICES`
- [x] Created initial `requirements.txt`

---

### Task 1.3 — Azure Infrastructure [COMPLETE]

- [x] Created Resource Group: `rg-cryptopulse-dev`
- [x] Created Storage Account (ADLS Gen2): `stcryptopulsedev2`
- [x] Created Container: `datalake`
- [x] Created Service Principal: `sp-cryptopulse` with `Storage Blob Data Contributor` role
- [x] Shared credentials securely with the team

> Amr is the point of contact for any Azure access issues or credential errors.

---

### Task 1.4 — Ingestion Scripts [COMPLETE]

**Files:**
- `ingestion/producers/producer_binance.py`
- `ingestion/producers/producer_coingecko.py`
- `ingestion/historical/historical_fetcher.py`

- [x] `producer_binance.py` — WebSocket stream for 10 live crypto pairs → Kafka topic `crypto.realtime.prices`. Includes exponential backoff auto-reconnect logic.
- [x] `producer_coingecko.py` — Polls CoinGecko every 60s for top-100 market data → Kafka topic `crypto.market.data`. Handles HTTP 429 rate limiting.
- [x] `historical_fetcher.py` — Downloads OHLCV candlestick data from January 2021 for 20 coins using 5 concurrent workers. Output: `data/historical/<symbol>_raw_klines.json`

---

### Task 1.5 — Pull Request Review [ONGOING]

- [ ] Review all PRs before merging into `dev` or `main`
- [ ] Enforce that no `.env` file or real credentials are committed

---

## Milestone 2 — Integration, Documentation, and Validation

**Goal:** Shift from builder to architect. Ensure all components from every team member integrate correctly end-to-end.

---

### Task 2.1 — Architecture Diagram [COMPLETE]

**File:** `docs/architecture.png`

- [x] Created architecture diagram showing the full data flow:
  `APIs → Kafka → Spark (Bronze) → Spark (Silver) → dbt (Gold) → FastAPI → Frontend`
- [x] Uploaded to `docs/architecture.png`

---

### Task 2.2 — README.md Update [COMPLETE]

**File:** `README.md`

- [x] Full rewrite of the root README with accurate, file-by-file documentation of all pipeline components, Docker services, environment setup, and run instructions.

---

### Task 2.3 — Integration Testing [COMPLETE]

**What was done:**
- [x] Validated the complete real-time streaming path end-to-end:
  - [x] Binance producer → Kafka → `bronze_consumer.py` → ADLS Bronze (Delta)
  - [x] `silver_prices_processor.py` reads Bronze as a stream and writes cleaned, deduplicated data to Silver via Delta MERGE (Upsert)
- [x] Validated the complete News and Social streaming path end-to-end:
  - [x] RSS/NewsAPI producers → Kafka → `bronze_news_consumer.py` & `bronze_social_consumer.py` → ADLS Bronze (Delta)
  - [x] `silver_news_processor.py` & `silver_social_processor.py` formatting and cleansing
- [x] Resolved Kafka connectivity issue between Docker containers (changed bootstrap servers from `localhost:9092` to `kafka:29092` for internal services)
- [x] Resolved Spark Azure Auth issues (`ClientCredsTokenProvider` injection in Spark Session)
- [x] Resolved Docker image staleness issue (required `--build` flag to rebuild Spark image with updated Dockerfile)
- [x] Diagnosed and resolved Spark executor heartbeat timeout caused by running two concurrent Streaming jobs on a local WSL2 environment
- [x] dbt Gold layer integration test (completed)
- [x] FastAPI end-to-end test reading from Gold

---

### Task 2.4 — Final Status Report [COMPLETE]

- [x] Summary of progress per milestone
- [x] Problems encountered and how they were resolved
- [x] Next steps for the project

---

### Task 2.5 — Silver to PostgreSQL Sync Job [COMPLETE]

**Files:**
- `processing/spark_jobs/silver_to_postgres_sync.py`
- `dags/etl_pipeline_dag.py`
- `docker-compose.yml`
- `backend/app/models/schema.sql`

- [x] Created `silver_to_postgres_sync.py` to copy `silver/historical` and `silver/prices` from ADLS to PostgreSQL using PySpark and JDBC.
- [x] Updated `schema.sql` to initialize `silver` and `gold` schemas.
- [x] Updated `etl_pipeline_dag.py` to include the sync job and run `dbt run && dbt test` automatically afterwards.
- [x] Updated `docker-compose.yml` to install `dbt-postgres` in the Airflow environment and mount the dbt project folder.

---

### Task 2.6 — Airflow-Spark Orchestration Integration [COMPLETE]

**Files:**
- `airflow/Dockerfile`
- `docker-compose.yml`
- `dags/dag_prices_frequent.py`
- `dags/dag_historical_daily.py`
- `processing/spark_jobs/sync_prices_pg.py`

**What was done:**
- [x] Created `airflow/Dockerfile` — custom Airflow image with Docker CLI 27.4.1 (static binary) and pre-installed pip packages (dbt-core, dbt-postgres, requests, python-dotenv)
- [x] Updated `docker-compose.yml` to use custom Airflow build context (`./airflow`) with `user: "0:0"` for Docker socket access
- [x] Added `POSTGRES_HOST=postgres` environment variable to the backend service
- [x] Updated all DAG tasks to use `docker exec spark-master spark-submit` instead of local execution — Airflow acts as a lightweight orchestrator that triggers Spark jobs on the spark-master container
- [x] Removed `--packages` flags from all spark-submit commands since JARs are pre-installed in the Spark image
- [x] Converted `sync_prices_pg.py` from streaming to batch mode for Airflow compatibility (streaming is handled by dedicated background containers)
- [x] Added Delta Lake configuration (`spark.sql.extensions`, `spark.sql.catalog`) to all spark-submit commands

**Architecture Decision:** Airflow does NOT run Spark locally. Instead, it uses the Docker socket to execute `docker exec` commands on the already-running `spark-master` container. This keeps Airflow lightweight and avoids duplicate Java/Spark installations.

**Issues resolved:**
1. Docker socket permission denied → Fixed with `user: "0:0"`
2. Docker CLI version mismatch (API 1.41 vs 1.44) → Fixed with static binary 27.4.1
3. Airflow `_PIP_ADDITIONAL_REQUIREMENTS` failure as root → Fixed by baking packages in Dockerfile
4. Ivy cache write permission → Fixed with `--conf spark.jars.ivy=/tmp/.ivy2` (later removed by eliminating `--packages`)
5. Maven download failures → Fixed by using pre-installed JARs from Spark image
6. sync_prices_pg.py streaming hang → Fixed by converting to batch mode

---

## Summary Table

| Task | Description | Status |
|------|-------------|--------|
| 1.1 | GitHub repository structure | Complete |
| 1.2 | Root config files (.gitignore, .env.example) | Complete |
| 1.3 | Azure infrastructure (ADLS Gen2, Service Principal) | Complete |
| 1.4 | Ingestion scripts (Binance, CoinGecko, Historical) | Complete |
| 1.5 | Pull request review | Ongoing |
| 2.1 | Architecture diagram | Complete |
| 2.2 | README.md full rewrite | Complete |
| 2.3 | Integration testing (Streaming path) | Complete |
| 2.4 | Final status report | Complete |
| 2.5 | Silver to PostgreSQL Sync Job & DAG Update | Complete |
| 2.6 | Airflow-Spark Orchestration Integration | Complete |

---

## Deliverables

**Milestone 1 (complete):**
- `ingestion/producers/producer_binance.py`
- `ingestion/producers/producer_coingecko.py`
- `ingestion/historical/historical_fetcher.py`
- `.gitignore`, `.env.example`, `requirements.txt`

**Milestone 2 (complete):**
- `README.md` (complete)
- `docs/architecture.png` (complete)
- `airflow/Dockerfile` (complete — Docker CLI 27.4.1 + dbt + pip packages)
- Integration test results and final report (complete)
