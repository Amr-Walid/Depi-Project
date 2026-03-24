# Crypto-Pulse: Data Ingestion Layer

Welcome to **Crypto-Pulse**, a robust and scalable data ingestion system designed to feed real-time and historical cryptocurrency data into a modern data pipeline.

## 🚀 Overview

This repository contains the "arteries" of the Crypto-Pulse project, responsible for fetching data from multiple sources and delivering it to **Kafka** and **Google BigQuery**.

## 🏗️ Architecture

-   **Real-time Streaming**: Binance WebSocket integration for sub-second price updates.
-   **Periodic Market Data**: REST API integration with CoinGecko for market cap and volume tracking.
-   **Historical Batching**: Automated OHLCV data retrieval from Binance API stored directly in BigQuery.
-   **Messaging Backbone**: Apache Kafka for decoupling ingestion from processing.

## 📂 Project Structure

```bash
crypto-pulse/
├── ingestion/
│   ├── producers/           # Real-time and Periodic producers
│   │   ├── producer_binance.py
│   │   └── producer_coingecko.py
│   └── historical/        # Batch data fetchers
│       └── historical_fetcher.py
├── processing/             # Spark/Flink jobs (Planned)
├── orchestration/          # Airflow DAGs (Planned)
├── backend/                # API Layer (Planned)
├── frontend/               # Dashboard (Planned)
├── ml/                     # Model training (Planned)
├── infra/                  # Terraform/Docker files
├── requirements.txt        # Python dependencies
└── .env                    # Environment configurations
```

## 🛠️ Setup & Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Amr-Walid/Depi-Project.git
    cd Depi-Project
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r crypto-pulse/requirements.txt
    ```

3.  **Configure Environment**:
    Rename `.env` and fill in your API keys:
    ```bash
    cp crypto-pulse/.env crypto-pulse/.env.local
    ```

## 📈 Running the Services

### Real-time Price Streaming (Binance)
```bash
python crypto-pulse/ingestion/producers/producer_binance.py
```

### Market Data Fetching (CoinGecko)
```bash
python crypto-pulse/ingestion/producers/producer_coingecko.py
```

### Historical Data Ingestion (BigQuery)
```bash
python crypto-pulse/ingestion/historical/historical_fetcher.py
```

## 🤝 Contributing
This project is part of the DEPI (Digital Egypt Pioneers Initiative) program. Special thanks to the team members:
- **Amr Walid**: Data Ingestion
- **Mostafa**: Infrastructure & Docker

---
Built with ❤️ for the Crypto Community.
