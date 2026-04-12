<div align="center">

# 🚀 Crypto-Pulse

**A Highly Scalable, Real-Time & Historical Cryptocurrency Data Engineering Pipeline powered by Microsoft Azure.**

</div>

![Crypto Data Pipeline Architecture](docs/image_6b784b2e-b866-4bee-b431-226755eea123.png)

Welcome to **Crypto-Pulse**, an advanced end-to-end data engineering project designed to ingest, process, and analyze cryptocurrency market data in real time. Built on the **Microsoft Azure Stack** and following the industry-standard **Medallion Architecture (Bronze ➔ Silver ➔ Gold)**, this pipeline ensures data flows reliably from source APIs all the way to analytics-ready dashboards.

---

## 🧬 Pipeline Architecture Overview

The system is built around 4 main environments working together:

| Layer | Technology | Status |
|-------|-----------|--------|
| **Data Ingestion (Bronze)** | Python, Binance API, CoinGecko API, Apache Kafka | ✅ Complete |
| **Data Processing (Silver/Gold)** | Apache Spark, dbt, Azure Databricks | 🚧 In Progress |
| **Orchestration** | Apache Airflow | 🚧 In Progress |
| **Serving** | FastAPI, PostgreSQL, Power BI | 🔜 Planned |

### The Azure Medallion Layers:
- 🥉 **Bronze Layer:** Raw JSON data captured directly from APIs, stored as-is in **Azure Data Lake Storage Gen2 (ADLS Gen2)** following the *Schema-on-Read* principle.
- 🥈 **Silver Layer:** Data cleaned, typed, and normalized using **Apache Spark** running on **Azure Databricks**. Anomalies filtered, schemas enforced.
- 🥇 **Gold Layer:** Business-level aggregations, KPIs, and metrics ready for **Power BI** dashboards and ML model training, stored in Azure Synapse or Azure SQL.

---

## 📡 The Ingestion Layer

Three specialized Python agents in `ingestion/` power the Bronze layer:

### 🕰️ The Historian (`ingestion/historical/historical_fetcher.py`)
> *"Captures the past so we can learn from it."*

- **Does:** Downloads years of historical OHLCV (Open/High/Low/Close/Volume) candlestick data for the **Top 20 cryptocurrencies** starting from 2021.
- **How:** Uses `ThreadPoolExecutor` (5 parallel workers) to run concurrent Binance API calls, significantly reducing fetch time. Implements automatic **Retry Logic** for Rate Limit errors (HTTP 429).
- **Output:** Saves raw JSON arrays directly into `data/historical/<symbol>_raw_klines.json` — no transformation, no cleaning — ready for the Bronze layer.

### ⚡ The Live Reporter (`ingestion/producers/producer_binance.py`)
> *"Never misses a heartbeat of the market."*

- **Does:** Maintains a persistent, live connection to Binance to capture every price tick in real-time.
- **How:** Uses **WebSockets** for a continuous data stream with a **Bulletproof Auto-Reconnect** engine using exponential backoff (retries automatically if connection drops).
- **Output:** Publishes every price update immediately to the Kafka topic: `crypto.realtime.prices`.

### 📊 The Strategic Analyst (`ingestion/producers/producer_coingecko.py`)
> *"Surveys the entire market every 60 seconds."*

- **Does:** Periodically fetches macro-market data (Market Cap, Volume, Price Change %) for the **Top 100 coins**.
- **How:** Uses the `schedule` library to poll the CoinGecko REST API every 60 seconds.
- **Output:** Publishes market overview snapshots to the Kafka topic: `crypto.market.data`.

### 📰 The News Watcher (`ingestion/producers/producer_news.py`)
> *"Tracks what the world is saying about crypto."*

- **Status:** 🔜 Planned (Ahmed Ayman)
- **Goal:** Fetch news headlines and sentiment data from NewsAPI to correlate market movements with world events.

---

## ⚙️ Data Processing Layer

Located in `processing/`, this layer handles transforming raw Bronze data into business-ready insights.

### 🔥 Spark Jobs (`processing/spark_jobs/`)
- **`bronze_consumer.py`** (🚧 In Progress - Yassin): Reads raw data from Kafka using **Spark Structured Streaming**, writes it as Parquet to the **Bronze** container in Azure Data Lake Gen2.
- **`silver_processor.py`** (🔜 Planned - Yassin): Reads Bronze Parquet files, applies cleaning/transformation, and writes to the **Silver** container partitioned by date (`year/month/day`).

### 🧱 dbt Models (`processing/dbt/`)
- **Status:** 🔜 Planned
- **Goal:** Transform Silver data into Gold-layer aggregations (daily averages, volatility metrics, trending coins) using dbt on top of Azure Synapse.

---

## 🎼 Orchestration (`dags/`)

- **`etl_pipeline_dag.py`**: An Apache Airflow DAG (🚧 In Progress - Mostafa) that schedules and sequences the entire pipeline:
  - Triggers historical fetcher nightly.
  - Monitors Spark jobs.
  - Alerts on failures.

---

## 🗄️ Backend & Database

Located in `backend/app/`:

- **`main.py`**: FastAPI application entry point.
- **`models/schema.sql`**: PostgreSQL schema defining the tables for users, watchlists, alerts, and portfolios (✅ Complete - Karim Ahmed).
- **`routers/`**: API route handlers (🔜 Planned).
- **`services/`**: Business logic services (🔜 Planned).

---

## 📂 Repository Structure

```text
crypto-pulse/
├── ingestion/                          # Bronze layer data agents
│   ├── historical/
│   │   └── historical_fetcher.py       ✅ Fetches years of OHLCV data
│   └── producers/
│       ├── producer_binance.py         ✅ Real-time WebSocket price stream
│       ├── producer_coingecko.py       ✅ Periodic market data poller
│       └── producer_news.py            🔜 News & sentiment fetcher
│
├── processing/                         # Silver & Gold layer jobs
│   ├── spark_jobs/
│   │   ├── bronze_consumer.py          🚧 Kafka → Azure Bronze (Parquet)
│   │   └── silver_processor.py         🔜 Bronze → Silver (Cleaned)
│   └── dbt/                            🔜 Silver → Gold (Aggregations)
│
├── backend/                            # REST API
│   └── app/
│       ├── main.py                     🔜 FastAPI entrypoint
│       ├── models/schema.sql           ✅ PostgreSQL schema
│       ├── routers/                    🔜 API routes
│       └── services/                   🔜 Business logic
│
├── dags/
│   └── etl_pipeline_dag.py             🚧 Airflow orchestration DAG
│
├── data/historical/                    📦 Local Bronze JSON files (20 coins)
├── docs/                               📖 Architecture diagrams & docs
├── ml/                                 🔜 ML models (Azure ML)
├── notebooks/                          📔 EDA Jupyter notebooks
├── frontend/                           🔜 Web Dashboard
├── docker-compose.yml                  🐳 Local: Kafka, Spark, Airflow, Postgres
├── Makefile                            ⚡ make up / make down / make logs
├── requirements.txt                    📦 Python dependencies
├── .env.example                        🔑 Environment variables template
└── README.md                           📖 This file
```

---

## 🛠️ Setup & Installation

### Prerequisites
- **Python 3.10+**
- **Docker** and **Docker Compose**
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/Amr-Walid/Depi-Project.git
cd Depi-Project/crypto-pulse
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with your Azure credentials and API keys
```

### 3. Start Local Infrastructure (One Command!)
```bash
make up
# This starts: Kafka, Zookeeper, Spark, Airflow, PostgreSQL, Kafka-UI
```

### 4. Install Python Dependencies
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

---

## 🚀 Running the Pipeline

```bash
# 1. Pull historical data for all 20 cryptocurrencies (Bronze Layer)
python ingestion/historical/historical_fetcher.py

# 2. Start real-time price streaming to Kafka
python ingestion/producers/producer_binance.py

# 3. Start periodic market data polling (every 60s)
python ingestion/producers/producer_coingecko.py
```

**Useful Docker commands:**
```bash
make up       # Start all services
make down     # Stop all services
make logs     # Follow live logs
make restart  # Restart everything
```

---

## 🤝 The Team

Crypto-Pulse is proudly developed as a capstone project for the **DEPI (Digital Egypt Pioneers Initiative)** program — Microsoft Azure Data Engineering Track.

| Name | Role | Milestone 1 Status |
|------|------|-------------------|
| 🧑‍💻 **Amr Walid** | Data Ingestion & Bronze Layer Lead | ✅ Complete |
| 🧑‍💻 **Mostafa Matar** | Infrastructure & DevOps (Docker/Airflow) | ✅ Complete |
| 🧑‍💻 **Karim Ahmed** | Database Engineering & PostgreSQL Schema | ✅ Complete |
| 🧑‍💻 **Yassin Mahmoud** | Data Processing (Spark/Databricks) | 🚧 In Progress |
| 🧑‍💻 **Ahmed Ayman** | Data Analysis & News API Research | 🚧 In Progress |

---

<div align="center">
  <b>Built with ❤️ for Data Engineering & The Crypto Ecosystem — DEPI 2024.</b>
</div>
