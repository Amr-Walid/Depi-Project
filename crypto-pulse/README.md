<div align="center">

# Crypto-Pulse

### A Real-Time & Historical Cryptocurrency Data Engineering Pipeline on Microsoft Azure

*DEPI — Digital Egypt Pioneers Initiative · Microsoft Azure Data Engineering Track*

</div>

---

![Full Pipeline Architecture](docs/architecture_full_pipeline.png)

Crypto-Pulse is a production-grade, end-to-end data engineering project that ingests live and historical cryptocurrency market data, **news headlines**, and **social sentiment** from RSS feeds, processes it through a layered data lakehouse (Medallion Architecture on Azure ADLS Gen2), syncs it to PostgreSQL, transforms it via dbt, and exposes it via a secured REST API.

The system handles four distinct data streams:
- **Real-time prices** — Binance WebSocket → Kafka → Spark Streaming → Delta Lake
- **Market data** — CoinGecko REST API → Kafka
- **Crypto news** — NewsAPI → Kafka → Spark → Delta Lake
- **Social sentiment** — RSS feeds (CoinTelegraph, NewsBTC, Bitcoin.com) → Kafka → Spark → Delta Lake
- **Historical OHLCV** — Binance Klines API → local JSON → Spark Batch → Delta Lake

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Repository Structure](#2-repository-structure)
3. [Layer 1 — Data Ingestion](#3-layer-1--data-ingestion)
4. [Layer 2 — Bronze Layer (Raw Storage)](#4-layer-2--bronze-layer)
5. [Layer 3 — Silver Layer (Cleaned & Structured)](#5-layer-3--silver-layer)
6. [Layer 4 — Gold Layer (dbt Analytics)](#6-layer-4--gold-layer-dbt)
7. [Backend API (FastAPI)](#7-backend-api-fastapi)
8. [Orchestration (Airflow)](#8-orchestration-airflow)
9. [Docker Infrastructure](#9-docker-infrastructure)
10. [Environment Configuration](#10-environment-configuration)
11. [Running the Project](#11-running-the-project)
12. [Team](#12-team)

---

## 1. Architecture Overview

All 4 pipelines follow the same **Medallion Architecture** flow:

```
┌─────────────────┐     ┌──────────┐     ┌──────────────────────┐     ┌──────────────────────┐     ┌──────────┐     ┌───────────┐     ┌─────────┐
│   DATA SOURCES  │     │  KAFKA   │     │    BRONZE LAYER      │     │    SILVER LAYER      │     │   SYNC   │     │ GOLD (dbt)│     │   API   │
│                 │     │          │     │   (Raw — Delta)      │     │  (Clean — Delta)     │     │  → PG    │     │           │     │         │
├─────────────────┤     ├──────────┤     ├──────────────────────┤     ├──────────────────────┤     ├──────────┤     ├───────────┤     ├─────────┤
│                 │     │          │     │                      │     │                      │     │          │     │           │     │         │
│ 🔴 Binance WS   │────►│ .prices  │────►│ bronze_consumer      │────►│ silver_prices_proc   │────►│sync_price│────►│gold_ohlcv │────►│ /coins  │
│   (Streaming)   │     │          │     │                      │     │  (Delta MERGE)       │     │          │     │gold_latest│     │ /prices │
│                 │     │          │     │                      │     │                      │     │          │     │daily_mkt  │     │ /market │
├─────────────────┤     ├──────────┤     ├──────────────────────┤     ├──────────────────────┤     ├──────────┤     │           │     │         │
│ 🟡 Binance API  │────►│ (batch)  │────►│ historical_loader    │────►│ silver_hist_proc     │────►│sync_hist │────►│           │     │         │
│   (Daily)       │     │          │     │                      │     │                      │     │          │     │           │     │         │
├─────────────────┤     ├──────────┤     ├──────────────────────┤     ├──────────────────────┤     ├──────────┤     ├───────────┤     │         │
│ 🟢 NewsAPI      │────►│ .news    │────►│ bronze_news_consumer │────►│ silver_news_proc     │────►│sync_news │────►│market_    │     │         │
│   (15 min)      │     │          │     │                      │     │                      │     │          │     │sentiment  │     │         │
├─────────────────┤     ├──────────┤     ├──────────────────────┤     ├──────────────────────┤     ├──────────┤     │           │     │         │
│ 🔵 RSS Feeds    │────►│ .social  │────►│ bronze_social_cons   │────►│ silver_social_proc   │────►│sync_socl │────►│           │     │         │
│   (10 min)      │     │          │     │                      │     │                      │     │          │     │           │     │         │
└─────────────────┘     └──────────┘     └──────────────────────┘     └──────────────────────┘     └──────────┘     └───────────┘     └─────────┘
                                                  │                            │                                          │
                                                  ▼                            ▼                                          ▼
                                         Azure ADLS Gen2               Azure ADLS Gen2                             PostgreSQL
                                         (stcryptopulsedev2)           (stcryptopulsedev2)                        (localhost:5432)
```

### Pipeline Summary

| # | Pipeline | Source | Kafka Topic | Type | Frequency |
|---|----------|--------|-------------|------|-----------|
| 1 | Real-Time Prices | Binance WebSocket | `crypto.realtime.prices` | Streaming 24/7 | Every 30s micro-batch |
| 2 | Historical OHLCV | Binance Klines API | — (batch) | Batch | Daily via Airflow |
| 3 | Crypto News | NewsAPI | `crypto.news` | Hybrid | Every 15 minutes |
| 4 | Social Sentiment | RSS Feeds | `crypto.social` | Hybrid | Every 10 minutes |

### Infrastructure at a Glance

| Component | Count |
|-----------|-------|
| Spark Jobs | 13 |
| Docker Containers | 15 |
| Airflow DAGs | 2 |
| dbt Models | 8 (4 staging + 4 gold) |
| API Endpoints | 10+ |

---

## 2. Repository Structure

```
crypto-pulse/
│
├── ingestion/                         Data ingestion agents (producers)
│   ├── producers/
│   │   ├── producer_binance.py        Live WebSocket price stream → Kafka
│   │   ├── producer_coingecko.py      Periodic market data polling → Kafka
│   │   ├── producer_news.py           News headlines via NewsAPI → Kafka
│   │   └── producer_social_rss.py     Social sentiment via RSS → Kafka
│   └── historical/
│       └── historical_fetcher.py      Batch OHLCV download → data/historical/
│
├── processing/                        All data transformation jobs
│   ├── spark_jobs/                    (13 Spark jobs)
│   │   ├── bronze_consumer.py         Kafka → Bronze/prices (Streaming)
│   │   ├── bronze_news_consumer.py    Kafka → Bronze/news (Streaming)
│   │   ├── bronze_social_consumer.py  Kafka → Bronze/social (Streaming)
│   │   ├── historical_loader.py       JSON → Bronze/historical (Batch)
│   │   ├── silver_prices_processor.py Bronze → Silver/prices (Streaming+Upsert)
│   │   ├── silver_historical_processor.py  Bronze → Silver/historical (Batch)
│   │   ├── silver_news_processor.py   Bronze → Silver/news (Batch)
│   │   ├── silver_social_processor.py Bronze → Silver/social (Batch)
│   │   ├── sync_prices_pg.py          Silver/prices → PostgreSQL (JDBC)
│   │   ├── sync_historical_pg.py      Silver/historical → PostgreSQL (JDBC)
│   │   ├── sync_news_pg.py            Silver/news → PostgreSQL (JDBC)
│   │   └── sync_social_pg.py          Silver/social → PostgreSQL (JDBC)
│   └── dbt/
│       ├── dbt_project.yml            dbt project configuration
│       ├── models/
│       │   ├── staging/               Views that cast and clean Silver data
│       │   │   ├── stg_prices.sql, stg_historical.sql
│       │   │   ├── stg_news.sql, stg_social.sql
│       │   │   └── sources.yml
│       │   └── gold/                  Materialized tables with business metrics
│       │       ├── gold_daily_ohlcv.sql, gold_latest_prices.sql
│       │       ├── daily_market_summary.sql, market_sentiment.sql
│       │       └── schema.yml
│       └── tests/
│           └── assert_low_price_less_than_high_price.sql
│
├── backend/                           REST API (FastAPI)
│   └── app/
│       ├── main.py                    FastAPI entry point, CORS, router registration
│       ├── config.py, database.py     Settings + SQLAlchemy engine
│       ├── models/                    ORM models + schema.sql
│       ├── schemas/                   Pydantic request/response schemas
│       ├── routers/                   auth, coins, watchlists, alerts, portfolios
│       ├── services/                  auth_service.py, data_service.py
│       └── tests/                     pytest test suite
│
├── dags/
│   ├── dag_historical_daily.py        @daily — Historical + News/Social sync + dbt
│   └── dag_prices_frequent.py         Every 5min — Prices sync + dbt
│
├── spark-apps/
│   ├── Dockerfile.spark               Custom Spark 3.5.0 with Azure+Kafka+Delta JARs
│   └── .env.example
│
├── data/historical/                   Raw JSON OHLCV files (20 coins, from Jan 2021)
├── docs/                              Architecture diagram, proposal, task files
├── notebooks/                         EDA, Model Training, POC Dashboard (pending)
├── ml/                                FinBERT sentiment models (pending)
├── docker-compose.yml                 15 containerized services
├── Makefile                           Shortcut commands
├── requirements.txt
└── .env.example
```

---

## 3. Layer 1 — Data Ingestion

### `ingestion/producers/producer_binance.py`

**Status:** Complete

Connects to Binance via a persistent WebSocket (`wss://stream.binance.com:9443/ws`) and subscribes to the combined ticker stream for 10 currency pairs: BTC, ETH, BNB, XRP, ADA, SOL, DOT, DOGE, MATIC, LINK (all against USDT).

For every tick received, it transforms the raw Binance payload into a clean, normalized message and publishes it to the Kafka topic `crypto.realtime.prices`:

```json
{
  "symbol": "BTCUSDT",
  "price": 68500.0,
  "volume_24h": 12345.6,
  "timestamp": 1712750400000,
  "source": "binance"
}
```

The connection is wrapped in an outer `while True` loop with **exponential backoff** (1s → 2s → 4s → ... → max 60s) to guarantee automatic reconnection after any network failure or WebSocket drop.

### `ingestion/producers/producer_coingecko.py`

**Status:** Complete

Polls the CoinGecko REST API every 60 seconds using the `schedule` library to retrieve market-wide data (market cap, total volume, 24h price change) for the top 100 coins by market cap. Handles HTTP 429 rate-limit errors gracefully. Publishes snapshots to the Kafka topic `crypto.market.data`.

### `ingestion/historical/historical_fetcher.py`

**Status:** Complete

Downloads multi-year OHLCV (Open, High, Low, Close, Volume) candlestick data for 20 cryptocurrencies starting from January 2021. Uses `ThreadPoolExecutor` with 5 parallel workers for concurrent downloads and includes retry logic for rate-limited requests. Output: raw JSON arrays saved to `data/historical/<SYMBOL>_raw_klines.json`. No transformation is applied at this stage — schema-on-read.

### `ingestion/producers/producer_news.py` & `producer_social_rss.py`

**Status:** Complete

Fetches global cryptocurrency news headlines from NewsAPI and specialized crypto publications via RSS feeds (e.g., CoinTelegraph, NewsBTC, Bitcoin.com). Data is continuously published to the `crypto.news` and `crypto.social` Kafka topics for downstream sentiment analysis using FinBERT.

---

## 4. Layer 2 — Bronze Layer

**Location on Azure:** `abfss://datalake@<ACCOUNT>.dfs.core.windows.net/bronze/`

**Format:** Delta Lake

The Bronze layer stores all raw data exactly as received — no transformation, no filtering. This guarantees a complete audit trail and allows reprocessing if the downstream logic changes.

### `processing/spark_jobs/bronze_consumer.py`

**Type:** Spark Structured Streaming (continuous, never exits)

Reads from the Kafka topic `crypto.realtime.prices` using `spark.readStream`. For every message, it extracts the Kafka metadata alongside the raw JSON payload and writes it to Azure Data Lake Storage Gen2 as a Delta stream.

Columns written:

| Column | Description |
|--------|-------------|
| `kafka_key` | Kafka message key (cast to String) |
| `raw_value` | Raw JSON string from Binance — unchanged |
| `topic` | Kafka topic name |
| `partition` | Kafka partition number |
| `offset` | Kafka message offset |
| `kafka_timestamp` | Timestamp from Kafka broker |
| `ingested_at` | Server-side ingestion timestamp (current_timestamp) |

**Trigger:** every 30 seconds  
**Checkpoint:** `abfss://.../checkpoints/bronze/prices`  
**Authentication:** Azure OAuth2 Service Principal via `ClientCredsTokenProvider`

### `processing/spark_jobs/historical_loader.py`

**Type:** Spark Batch Job (run once or scheduled)

Reads all raw JSON files from `data/historical/`, parses the OHLCV arrays, adds `symbol` and `ingested_at` metadata columns, and writes them in Delta format to `bronze/historical` on ADLS Gen2.

### `processing/spark_jobs/bronze_news_consumer.py` & `bronze_social_consumer.py`

**Type:** Spark Structured Streaming

Reads from `crypto.news` and `crypto.social` topics. Casts payloads matching the specific schema of NewsAPI and RSS sources, adding ingestion timestamps, and writing to ADLS Gen2 `bronze/news` and `bronze/social` respectively using the Delta format. Uses Azure OAuth2 client credentials injected into the Spark Session builder.

---

## 5. Layer 3 — Silver Layer

**Location on Azure:** `abfss://datalake@<ACCOUNT>.dfs.core.windows.net/silver/`

**Format:** Delta Lake (with partitioning)

The Silver layer contains cleaned, typed, deduplicated, and enriched data. It is the source of truth for all downstream analytics and API queries.

### `processing/spark_jobs/silver_prices_processor.py`

**Type:** Spark Structured Streaming (continuous, never exits)

Reads from the Bronze Delta table as a stream (`spark.readStream.format("delta")`). For each micro-batch it:

1. Parses the `raw_value` JSON column using a defined schema (`symbol`, `price`, `volume_24h`, `timestamp`, `source`).
2. Converts Unix millisecond timestamps to proper UTC `TimestampType`.
3. Applies Data Quality filters: removes null symbols, null/zero/negative prices, and null timestamps.
4. Drops duplicate events based on `(symbol, event_time)`.
5. Adds partition columns: `year`, `month`, `day`, `hour`.
6. Executes a **Delta MERGE (Upsert)** into the Silver table: if a row with the same `(symbol, event_time)` already exists it is updated, otherwise it is inserted.

The Merge strategy prevents any duplicates from appearing in Silver even if the Bronze consumer re-processes old Kafka offsets after a restart.

**Trigger:** every 30 seconds  
**Output path:** `silver/prices` partitioned by `year/month/day/hour`  
**Checkpoint:** `checkpoints/silver/prices`

### `processing/spark_jobs/silver_historical_processor.py`

**Type:** Spark Batch Job

Reads from `bronze/historical`, applies the same cleaning rules (type casting, null filtering, deduplication) and writes the output to `silver/historical` partitioned by symbol and date.

### `processing/spark_jobs/silver_news_processor.py` & `silver_social_processor.py`

**Type:** Spark Batch/Streaming

Reads from the respective `bronze/` directories, normalizes the deeply nested schemas, standardizes string representations of `published_at` to proper UTC `TimestampType`, and applies deduplication filters. Saves cleanly into `silver/news` and `silver/social`.

---

## 6. Layer 4 — Gold Layer (dbt)

**Owner:** Karim Ahmed  
**Tool:** dbt (Data Build Tool)  
**Project name:** `crypto_pulse_dbt`

The Gold layer contains business-level aggregations and metrics built on top of the Silver data. It uses dbt models compiled and executed against the target warehouse (Azure Synapse or PostgreSQL).

### Staging Models (materialized as Views)

These are thin transformation views that sit directly on top of Silver data.

**`models/staging/stg_prices.sql`**  
Casts Silver price data to clean types (`DECIMAL(18,8)` for price and volume, `TIMESTAMP` for event time) and filters out null/zero prices.

**`models/staging/stg_news.sql`** and **`models/staging/stg_social.sql`**  
Same pattern applied to news and social data streams.

### Gold Models (materialized as Tables)

**`models/gold/daily_market_summary.sql`**  
Computes OHLCV (Open, High, Low, Close, Volume) aggregates per coin per day using window functions. Output columns: `symbol`, `date`, `open_price`, `high_price`, `low_price`, `close_price`, `total_volume`.

**`models/gold/market_sentiment.sql`**  
Aggregates sentiment signals from the news and social streams.

### Tests

`tests/assert_low_price_less_than_high_price.sql` — a custom data test that asserts data integrity: `low_price` must always be less than or equal to `high_price` in `daily_market_summary`.

---

## 7. Backend API (FastAPI)

**Owner:** Mostafa Matar  
**Base URL:** `http://localhost:8000`  
**Interactive Docs:** `http://localhost:8000/docs`

The backend is a full-featured REST API built with FastAPI and SQLAlchemy, backed by a PostgreSQL database. It auto-creates all database tables on startup via `create_tables()`.

### Authentication — `routers/auth.py`

All user data is isolated by identity. The system uses JWT with **refresh token rotation** (each refresh issues a new refresh token and revokes the old one).

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/signup` | POST | Register a new user. Returns access + refresh tokens. Password hashed with bcrypt. |
| `/api/v1/auth/login` | POST | Authenticate with email + password. Returns tokens. |
| `/api/v1/auth/refresh` | POST | Exchange a valid refresh token for a new token pair. Old token is revoked. |
| `/api/v1/auth/me` | GET | Returns the profile of the currently authenticated user. Requires Bearer token. |

### Coin Data — `routers/coins.py`

Serves live and historical price data fetched from the Silver/Gold layer.

### Watchlists — `routers/watchlists.py`

Full CRUD for user-defined coin watchlists. Each list is scoped to the authenticated user.

### Alerts — `routers/alerts.py`

Allows users to configure price alerts (e.g., "notify me when BTC > $70,000"). Stored in PostgreSQL.

### Portfolios — `routers/portfolios.py`

Tracks user portfolio positions (coin, quantity, buy price). Calculates current value against live prices.

### Database Schema (`models/schema.sql`)

PostgreSQL tables: `users`, `refresh_tokens`, `watchlists`, `alerts`, `portfolios`.

---

## 8. Orchestration (Airflow)

The orchestration is split into two independent DAGs to separate batch processing from frequent micro-batch updates. **Note:** The continuous streaming jobs (`bronze_consumer.py` and `silver_prices_processor.py`) run as standalone background Docker containers and are not managed by Airflow.

### DAG 1: `dag_historical_daily`
**Schedule:** `@daily`  
Orchestrates the full historical + news/social batch pipeline.

```text
fetch_historical_data
        │
        ▼
ingest_historical_to_bronze
        │
        ▼
process_historical_to_silver
        │
        ▼
sync_historical_to_postgres
        │
        ▼
sync_news_to_postgres
        │
        ▼
sync_social_to_postgres
        │
        ▼
run_dbt_gold
```

### DAG 2: `dag_prices_frequent`
**Schedule:** Every 5 minutes  
Orchestrates the near real-time synchronization and modeling for live prices.

```text
sync_prices_to_postgres
        │
        ▼
run_dbt_prices
```

---

## 9. Docker Infrastructure

All services communicate over a shared Docker bridge network named `crypto-net`.

| Container | Image | Port | Role |
|-----------|-------|------|------|
| `zookeeper` | `confluentinc/cp-zookeeper:7.0.0` | 2181 | Kafka coordination |
| `kafka` | `confluentinc/cp-kafka:7.0.0` | 9092 (ext), 29092 (int) | Event streaming |
| `kafka-init-topics` | (same as kafka) | — | Auto-creates 4 topics on startup |
| `kafka-ui` | `provectuslabs/kafka-ui` | 8080 | Visual Kafka management |
| `postgres` | `postgres:15` | 5432 | Relational database for API + dbt |
| `airflow-webserver` | `apache/airflow:2.7.3` | 8081 | DAG management UI |
| `airflow-scheduler` | `apache/airflow:2.7.3` | — | DAG execution engine |
| `spark-master` | `crypto-pulse-spark:3.5.0` (custom) | 7077, 8082 | Spark cluster master |
| `spark-worker` | `crypto-pulse-spark:3.5.0` (custom) | 8083 | Spark executor (2 cores, 4GB RAM) |
| `streaming-bronze-prices` | `crypto-pulse-spark:3.5.0` | — | Kafka → Bronze/prices (continuous) |
| `streaming-bronze-news` | `crypto-pulse-spark:3.5.0` | — | Kafka → Bronze/news (continuous) |
| `streaming-bronze-social` | `crypto-pulse-spark:3.5.0` | — | Kafka → Bronze/social (continuous) |
| `streaming-silver-prices` | `crypto-pulse-spark:3.5.0` | — | Bronze → Silver/prices (continuous) |
| `backend` | Custom (from `backend/Dockerfile`) | 8000 | FastAPI REST API |

**Kafka topic auto-creation:** The `kafka-init-topics` container runs once on startup and creates: `crypto.realtime.prices`, `crypto.market.data`, `crypto.news`, `crypto.social`.

**Kafka networking:** The Kafka broker is configured with dual listeners:
- `EXTERNAL://localhost:9092` — for the Python producer running on the host machine.
- `INTERNAL://kafka:29092` — for all Docker services (Spark, Airflow) communicating within the network.

### Custom Spark Image — `spark-apps/Dockerfile.spark`

Extends `apache/spark:3.5.0` and pre-installs all required JARs and Python packages:

- Python: `python-dotenv==1.0.1`, `delta-spark==3.2.0`
- JARs (downloaded into `/opt/spark/jars/`):
  - `hadoop-azure:3.3.4` + `wildfly-openssl:1.1.3.Final` — ADLS Gen2 connectivity
  - `azure-storage-blob`, `azure-storage-common`, `azure-core`, `azure-identity`, `msal4j` — Azure SDK
  - `spark-sql-kafka-0-10_2.12:3.5.0`, `kafka-clients:3.5.1`, `commons-pool2:2.11.1` — Kafka connector
  - `delta-spark_2.12:3.2.0`, `delta-storage:3.2.0` — Delta Lake

---

## 10. Environment Configuration

Copy `.env.example` to `.env` and fill in your credentials. This file is mounted into all containers that need Azure or Kafka access.

```env
# Azure Service Principal (for ADLS Gen2 authentication)
AZURE_CLIENT_ID=<your-service-principal-client-id>
AZURE_CLIENT_SECRET=<your-service-principal-secret>
AZURE_TENANT_ID=<your-tenant-id>
AZURE_STORAGE_ACCOUNT_NAME=stcryptopulsedev2
AZURE_STORAGE_CONTAINER_NAME=datalake
NEWS_API_KEY=<your-newsapi-key>

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092           # Use this for the host-side Python producer
KAFKA_TOPIC_REALTIME_PRICES=crypto.realtime.prices

# PostgreSQL (used by the FastAPI backend)
POSTGRES_URL=postgresql://admin:admin123@postgres:5432/cryptopulse
```

> **Important:** The Spark and Airflow jobs running **inside Docker** use `kafka:29092` (the internal listener), not `localhost:9092`. This is configured automatically via the `KAFKA_BOOTSTRAP_SERVERS=kafka:29092` environment variable set in `docker-compose.yml` for those services. You do not need to change your `.env` file for this.

---

## 11. Running the Project

### Prerequisites

- Docker Desktop (with WSL2 backend on Windows)
- Python 3.10+
- A configured Azure subscription with an ADLS Gen2 storage account and a service principal

### Step 1 — Clone and Configure

```bash
git clone https://github.com/Amr-Walid/Depi-Project.git
cd Depi-Project/crypto-pulse
cp .env.example .env
# Open .env and fill in your Azure credentials
```

### Step 2 — Build and Start All Services

On the first run, this will build the custom Spark Docker image. Subsequent runs will be faster.

```bash
make up
# or: docker compose up -d --build
```

Wait approximately 30 seconds for Kafka and Postgres to fully initialize.

### Step 2.5 — Initialize Airflow (First Time Only)

If this is your first time running the project, you must initialize the Airflow database and create an admin user:

```bash
# 1. Create Airflow internal tables
docker compose exec airflow-webserver airflow db migrate

# 2. Create the Admin user for the Web UI
docker compose exec airflow-webserver airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin
```

You can now access the Airflow UI at `http://localhost:8081` using `admin` / `admin`.

### Step 3 — Run the Real-Time Streaming Pipeline

Open three separate terminal tabs and run one command per tab. All three must run simultaneously.

**Tab 1 — Binance Producer (runs on the host, outside Docker)**
```bash
source venv/bin/activate
python ingestion/producers/producer_binance.py
```

**Tab 2 — Bronze Consumer (runs inside Spark container)**
```bash
docker exec -it spark-master /opt/spark/bin/spark-submit /opt/spark/jobs/bronze_consumer.py
```

**Tab 3 — Silver Prices Processor (runs inside Spark container)**
```bash
docker exec -it spark-master /opt/spark/bin/spark-submit /opt/spark/jobs/silver_prices_processor.py
```

### Step 3.5 — Run the News & Social Sentiment Pipeline

Open two more terminals:

**Tab 4 — News Producer (runs on host)**
```bash
source venv/bin/activate
python ingestion/producers/producer_news.py
```

**Tab 5 — RSS Social Producer (runs on host)**
```bash
source venv/bin/activate
python ingestion/producers/producer_social_rss.py
```

**Then start the Bronze consumers inside Spark:**
```bash
docker exec -it spark-master /opt/spark/bin/spark-submit /opt/spark/jobs/bronze_news_consumer.py
docker exec -it spark-master /opt/spark/bin/spark-submit /opt/spark/jobs/bronze_social_consumer.py
```

**Process Bronze to Silver:**
```bash
docker exec -it spark-master /opt/spark/bin/spark-submit /opt/spark/jobs/silver_news_processor.py
docker exec -it spark-master /opt/spark/bin/spark-submit /opt/spark/jobs/silver_social_processor.py
```

> **Note for local testing:** Running two Spark Structured Streaming jobs simultaneously is resource-intensive. If you experience Spark executor heartbeat timeouts, stop Airflow first:
> ```bash
> docker compose stop airflow-webserver airflow-scheduler
> ```

### Step 4 — Run the Batch Historical Pipeline

```bash
# Download raw OHLCV data (runs on host)
python ingestion/historical/historical_fetcher.py

# Load raw JSON into Bronze (runs in Spark)
docker exec -it spark-master /opt/spark/bin/spark-submit /opt/spark/jobs/historical_loader.py

# Process Bronze historical into Silver (runs in Spark)
docker exec -it spark-master /opt/spark/bin/spark-submit /opt/spark/jobs/silver_historical_processor.py
```

### Step 5 — Sync Silver to PostgreSQL

```bash
# Sync all Silver layers to PostgreSQL for dbt to consume
docker exec -it spark-master /opt/spark/bin/spark-submit --packages org.postgresql:postgresql:42.6.0,io.delta:delta-spark_2.12:3.2.0,org.apache.hadoop:hadoop-azure:3.3.4 /opt/spark/jobs/sync_historical_pg.py
docker exec -it spark-master /opt/spark/bin/spark-submit --packages org.postgresql:postgresql:42.6.0,io.delta:delta-spark_2.12:3.2.0,org.apache.hadoop:hadoop-azure:3.3.4 /opt/spark/jobs/sync_prices_pg.py
docker exec -it spark-master /opt/spark/bin/spark-submit --packages org.postgresql:postgresql:42.6.0,io.delta:delta-spark_2.12:3.2.0,org.apache.hadoop:hadoop-azure:3.3.4 /opt/spark/jobs/sync_news_pg.py
docker exec -it spark-master /opt/spark/bin/spark-submit --packages org.postgresql:postgresql:42.6.0,io.delta:delta-spark_2.12:3.2.0,org.apache.hadoop:hadoop-azure:3.3.4 /opt/spark/jobs/sync_social_pg.py
```

### Step 6 — Build Gold Layer via dbt

After the Silver data is synced to PostgreSQL, you can trigger dbt to build the analytics tables.

```bash
docker compose exec -e POSTGRES_HOST=postgres airflow-webserver bash -c "cd /opt/airflow/dbt && dbt deps && dbt run"

# Run data quality tests
docker compose exec -e POSTGRES_HOST=postgres airflow-webserver bash -c "cd /opt/airflow/dbt && dbt test"

# Generate documentation
docker compose exec -e POSTGRES_HOST=postgres airflow-webserver bash -c "cd /opt/airflow/dbt && dbt docs generate"
```

### Step 7 — Access the Backend API

The FastAPI backend starts automatically with `make up`. No manual step is needed.

```
http://localhost:8000/docs      Swagger interactive API documentation
http://localhost:8000/redoc     ReDoc alternative documentation view
```

### Useful Commands

```bash
make up        # Start all services
make down      # Stop and remove all containers
make logs      # Follow live logs from all containers
make restart   # Restart everything
```

| Service UI | URL |
|------------|-----|
| Kafka UI (topic browser) | http://localhost:8080 |
| Airflow (DAG management) | http://localhost:8081 |
| Spark Master (job monitor) | http://localhost:8082 |
| FastAPI (Swagger docs) | http://localhost:8000/docs |

---

## 12. Team

| Name | Role | Responsibilities |
|------|------|-----------------|
| **Amr Walid** | Team Lead & Lead Data Engineer | Azure infrastructure, ingestion scripts, Kafka producers, orchestration, News/Social integration |
| **Yassin Mahmoud** | DataOps & Spark Engineer | Bronze consumer, Silver streaming processor, historical batch jobs, Airflow DAG |
| **Mostafa Matar** | Backend Engineer & Docker Owner | FastAPI backend, JWT auth, PostgreSQL schema, Docker Compose, CI/CD |
| **Karim Ahmed** | Analytics Engineer | dbt project setup, staging models, gold aggregations, data tests |
| **Ahmed Ayman** | Data Analyst & ML Engineer | Sentiment analysis (FinBERT), ML notebooks |

---

<div align="center">
Built for the <b>DEPI — Digital Egypt Pioneers Initiative</b> · Microsoft Azure Data Engineering Track · 2025–2026
</div>
