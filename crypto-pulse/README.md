<div align="center">
  <h1>🚀 Crypto-Pulse</h1>
  <p><b>A Highly Scalable, Real-Time & Historical Cryptocurrency Data Engineering Pipeline powered by Microsoft Azure.</b></p>
  <br>
  <img src="docs/architecture.png" alt="Crypto Data Pipeline Architecture Preview" width="100%">
</div>

<br>

Welcome to **Crypto-Pulse**, an advanced data engineering project built from the ground up to ingest, process, and analyze cryptocurrency market data. Built entirely with the **Microsoft Azure Stack**, this pipeline ensures data is reliably captured, elegantly transformed, and robustly served for analytics and machine learning utilizing the **Medallion Architecture (Bronze ➔ Silver ➔ Gold)**.

---

## 🧬 Project Architecture & The Azure Medallion Approach

Crypto-Pulse is designed around a decoupled, event-driven architecture utilizing local engines that smoothly integrate into Azure's ecosystem:

1. **🥉 Bronze Layer (Ingestion):** Local python agents capture raw JSON data directly from APIs (Schema-on-Read). This data is ultimately destined for **Azure Data Lake Storage Gen2 (ADLS Gen2)**.
2. **🥈 Silver Layer (Processing):** Uses **Azure Databricks** or **Azure Synapse Analytics** to read the Bronze data, clean it, enforce schemas, and filter anomalies.
3. **🥇 Gold Layer (Serving):** Highly aggregated business-level tables stored in Azure Synapse or Azure SQL, optimized for fast queries and native **Microsoft Power BI** Dashboards.

---

## 📡 The Ingestion Layer (Agents)

Currently, our robust **Data Ingestion Layer** operates via three distinct and specialized Python agents located in `ingestion/`. 

### 1. The Historian 🕰️ (`historical_fetcher.py`)
* **Goal:** Downloads years of historical candlestick data (OHLCV) from Binance.
* **Mechanics:** Utilizes `ThreadPoolExecutor` to concurrently pull thousands of records per second for the top 20 cryptocurrencies.
* **Storage:** Dumps raw arrays directly into `.json` files inside `/data/historical/`, preserving the exact raw payload, ready to be ingested by **Azure Data Factory (ADF)** into the Data Lake.

### 2. The Live Reporter ⚡ (`producer_binance.py`)
* **Goal:** Streams real-time, millisecond-level price and volume updates.
* **Mechanics:** Subscribes to Binance **WebSockets**. Features a **Bulletproof Auto-Reconnect** engine with exponential backoff.
* **Destination:** Pushes messages immediately to a **Kafka** topic (which maps natively to **Azure Event Hubs**): `crypto.realtime.prices`.

### 3. The Strategic Analyst 📊 (`producer_coingecko.py`)
* **Goal:** Periodically surveys the entire cryptocurrency market for macro-economic overviews.
* **Mechanics:** Utilizes the `schedule` library to hit the CoinGecko REST API every 60 seconds, snagging the top 100 coins by Market Capitalization.
* **Destination:** Pushes summarized market health messages to the Kafka topic: `crypto.market.data`.

---

## 📂 Repository Structure

The project is structured to scale across multiple tracking environments:

```text
crypto-pulse/
├── ingestion/          # Source fetchers, REST API callers, WebSocket producers
│   ├── historical/     # Batch scripts (historical_fetcher.py)
│   └── producers/      # Real-time Kafka producers (Binance, CoinGecko)
├── processing/         # Azure Databricks / Pyspark Jobs (In-Progress by Yassin)
├── data/               # Local Bronze Layer JSONs (pre-ADLS upload)
├── dags/               # Apache Airflow orchestration scripts
├── orchestration/      # Data Factory / Airflow configurations 
├── backend/            # Future API Layer for serving data 
├── frontend/           # Future Analytics Dashboard
├── ml/                 # Machine Learning models (Azure Machine Learning) 
├── notebooks/          # Exploratory Data Analysis (EDA) Jupyter notebooks
├── docs/               # Architecture diagrams and deep-dive documentation
├── docker-compose.yml  # Local Kafka & Zookeeper testing
├── requirements.txt    # Python dependencies
└── .env                # Secrets and Azure Connection Strings
```

---

## 🛠️ Setup & Installation

### 1. Prerequisites
Ensure you have the following installed on your machine:
- **Python 3.10+**
- **Docker** and **Docker Compose**
- **Git**

### 2. Clone the Repository
```bash
git clone https://github.com/Amr-Walid/Depi-Project.git
cd Depi-Project/crypto-pulse
```

### 3. Environment Variables
Copy the example environment file and fill in your details (You will place your Azure Connection Strings here later).
```bash
cp .env.example .env
```

### 4. Start Local Infrastructure
Boot up the core local messaging backbone (Kafka) for testing before routing to Azure Event Hubs.
```bash
docker-compose up -d
```

### 5. Install Python Dependencies
```bash
python -m venv venv
# Windows: venv\Scripts\activate 
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
```

---

## 🚀 Running the Ingestion Agents

**Fetch Historical Data (Local ➔ Bronze Azure Blob):**
```bash
python ingestion/historical/historical_fetcher.py
```

**Start the Real-time Price Streamer (Local ➔ Azure Event Hubs):**
```bash
python ingestion/producers/producer_binance.py
```

**Start the Market Data Poller:**
```bash
python ingestion/producers/producer_coingecko.py
```

---

## 🤝 The Team

Crypto-Pulse is proudly developed as a capstone project for the **DEPI (Digital Egypt Pioneers Initiative)** program, leveraging the Microsoft Azure Data Engineering track.

- 🧑‍💻 **Amr Walid** — Data Ingestion & Bronze Layer Architecture
- 🧑‍💻 **Yassin** — Data Processing (Databricks) & Azure Silver Layer
- 🧑‍💻 **Mostafa** — Infrastructure, Azure Architecture & Orchestration
- 🧑‍💻 **Karim Ahmed** — Database Engineering & Backend Schemas
- 🧑‍💻 **Ahmed Ayman** — Data Analysis & API Research

---
<div align="center">
  <b>Built with ❤️ for Data Engineering & The Crypto Ecosystem.</b>
</div>
