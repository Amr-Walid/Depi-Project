# 🚀 Crypto-Pulse Backend & API Guide

Welcome to the backend component of the **Crypto-Pulse** project. This directory contains the FastAPI application responsible for serving data to users, handling authentication, and managing user-specific features like watchlists and portfolios.

This document serves as a comprehensive guide to what has been implemented so far (Milestone 2) and exactly how to integrate this backend with the data engineering pipeline (Bronze/Silver/Gold layers) once they are finalized.

---

## 🎯 Milestone 2: What Has Been Implemented

We have successfully built a fully functioning, production-ready REST API with the following core features:

### 1. Security & Authentication (`/api/v1/auth`)
- **JWT Authentication:** Implemented secure login, signup, and profile retrieval using JSON Web Tokens.
- **Refresh Token Rotation:** Access tokens expire in 30 minutes for security. Refresh tokens are stored in the database and expire in 7 days. When a refresh token is used, it is revoked and replaced with a new pair.
- **Password Hashing:** Uses `bcrypt` (via `passlib`) with a strict truncation fallback to resolve compatibility issues with the latest `bcrypt` Rust implementation.

### 2. User Features APIs (Protected Endpoints)
- **Watchlists (`/api/v1/watchlists`):** CRUD endpoints for users to manage the coins they are tracking.
- **Alerts (`/api/v1/alerts`):** CRUD endpoints for users to set price alerts (e.g., 'above' 70,000 or 'below' 60,000).
- **Portfolios (`/api/v1/portfolios`):** CRUD endpoints for users to manage their crypto positions (quantity and average buy price).

### 3. Data & Market APIs (`/api/v1/coins`)
- **Supported Coins:** Fetches all coins actively tracked by the pipeline.
- **Coin Summaries:** Daily OHLCV summaries and 24h volume.
- **Historical Prices:** Up to 365 days of historical price data per coin.
- **Market Overview:** Global metrics like total market cap and top gainers/losers.
- *(Note: These endpoints currently use a **Mock Data Strategy** — see "Future Integration" below).*

### 4. Infrastructure & Testing
- **Automated Database Initialization:** When running `make up`, PostgreSQL automatically executes `app/models/schema.sql` to initialize all tables (`users`, `watchlists`, etc.) without manual intervention.
- **100% Test Coverage:** 47 automated tests written using `pytest`. Tests run in ~15 seconds using an isolated, in-memory SQLite database (`test.db`). 

---

## 🏗️ Architecture Overview

The backend strictly follows a layered architecture to separate concerns:

- **`models/`**: SQLAlchemy ORM models. These define how Python interacts with our PostgreSQL tables.
- **`schemas/`**: Pydantic v2 models. These strictly validate incoming request bodies and format outgoing JSON responses. They also auto-generate our Swagger documentation.
- **`services/`**: The core business logic.
  - `auth_service.py`: Password hashing and JWT logic.
  - `data_service.py`: Connects to data sources to serve the coin endpoints.
- **`routers/`**: The FastAPI endpoints. These functions receive the HTTP request, pass data to the services, and return the response.

---

## 🧪 Testing and Development

### Running the API locally
The API is fully integrated into the project's Docker Compose setup.
```bash
# Start all services, including the backend and PostgreSQL
make up

# Rebuild only the backend if you change dependencies
make rebuild-backend
```
Once running, interactive API documentation is available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### Running the Tests
Tests use a local SQLite database and do not require Docker to be running.
```bash
# Run tests locally (fastest)
make test-local

# Or run tests inside the Docker container
make test
```

---

## 🔮 Future Integration: When Gold & Silver Layers are Complete

Currently, the data endpoints in `app/services/data_service.py` return realistic, dynamically generated **Mock Data**. This allows the Frontend team to start building the dashboard immediately because the API contract (the JSON structure) is finalized.

When **Karim and Yassin** complete the Silver and Gold layers, you need to swap the mock data generator with real database queries. You will **not** need to touch the `routers` or `schemas`. **Only `data_service.py` will change.**

### Scenario A: Gold Layer is in PostgreSQL
If `dbt` materializes the Gold tables (like `coin_daily_summary`) into the shared PostgreSQL database:
1. Create new SQLAlchemy models in `app/models/` mirroring the dbt tables.
2. Update the router to pass the `db: Session` dependency into `data_service.py`.
3. Update `data_service.py` to run SQLAlchemy queries:
   ```python
   def get_coin_summary(symbol: str, db: Session):
       return db.query(CoinDailySummary).filter(CoinDailySummary.symbol == symbol).first()
   ```

### Scenario B: Gold Layer is in Azure Data Lake (Parquet/Delta)
If the data resides as Parquet/Delta files in ADLS Gen2:
1. Install Azure SDKs: `pip install azure-storage-file-datalake pandas` (and add to `requirements.txt`).
2. Add Azure connection logic to `data_service.py` using credentials from `.env`.
3. Read and convert the Parquet files into the JSON list expected by the API:
   ```python
   def get_coin_prices(symbol: str, days: int):
       # 1. Download/Read Parquet from ADLS Gen2
       # 2. Filter by symbol and days using Pandas/Polars
       # 3. Return as a list of dictionaries
       pass
   ```

By isolating this logic inside `data_service.py`, the transition from Mock Data to Real Data will be entirely seamless for the Frontend.

---

## 🚦 Current Status of Data Layers (Post-Rebase)

As of the latest rebase from `main` (which brought in 26 new commits):

1. **Silver Layer**: The code (`silver_processor.py`) is complete and uses Spark to write Delta tables to Azure Data Lake incrementally.
2. **Gold Layer**: The `dbt` SQL models (`daily_market_summary.sql` etc.) have been written by Karim, **but the Airflow orchestration to run them is not yet complete.**

**Conclusion:** We cannot switch away from Mock Data yet. The Gold tables do not physically exist in the database because the pipeline hasn't been executed. Once the Data Engineering team confirms the pipeline is fully running and the tables are populated, the Backend team can execute the transition steps outlined above.
