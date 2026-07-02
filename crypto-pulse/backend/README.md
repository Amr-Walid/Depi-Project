<div align="center">

# Crypto-Pulse Backend & REST API

### The High-Performance Core Built on FastAPI & Supabase PostgreSQL

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql)](https://www.postgresql.org)
[![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=json-web-tokens)](https://jwt.io)
[![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest)](https://docs.pytest.org)

</div>

---

## Table of Contents
1. [Overview](#-overview)
2. [Current Status](#-current-status-june-2026)
3. [Architecture & Folder Structure](#-architecture--folder-structure)
4. [Database & Schema Design](#-database--schema-design)
5. [API Endpoint Documentation](#-api-endpoint-documentation)
6. [Security & JWT Rotation Flow](#-security--jwt-rotation-flow)
7. [Alert Worker Background Daemon](#-alert-worker-background-daemon)
8. [Installation & Local Setup](#-installation--local-setup)
9. [Automated Test Suite](#-automated-test-suite)

---

## Overview

The backend of **Crypto-Pulse** is a production-grade REST API built using **FastAPI** and **SQLAlchemy (ORM)**. It serves live and historical cryptocurrency data to the user, runs background workers to track real-time price alerts, manages portfolio allocations, watchlists, and maintains strict token-based user authentication.

---

## Current Status (June 2026)

All backend features are fully implemented, verified, and integrated:
- **JWT Authentication**: Full user signup/login flows with secure refresh token rotation.
- **Production Data Delivery**: Endpoints feed live and historical OHLCV data directly from dbt Gold layers on Supabase Cloud PostgreSQL.
- **Sentiment Analytics**: Dedicated endpoint serves sentiment reports backed by FinBERT results with automatic fallbacks.
- **Robust Alert Daemon**: The alert worker service monitors prices and alerts user portfolios.
- **High Test Coverage**: 50 automated unit and integration tests passing.

---

## Architecture & Folder Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point, CORS middleware, and routers
│   ├── config.py            # Central config & validation (via Pydantic BaseSettings)
│   ├── database.py          # SQLAlchemy connection engine & DB session factory
│   ├── routers/             # API Endpoints (segmented by resource area)
│   │   ├── auth.py          # Signup, Login, Profile, JWT Refresh
│   │   ├── coins.py         # Coins list, Historical Prices, Market Overview, Sentiment
│   │   ├── watchlists.py    # CRUD for user-specific Watchlists
│   │   ├── alerts.py        # CRUD for Price Alerts
│   │   └── portfolios.py    # CRUD for Portfolio Holdings
│   ├── models/              # SQLAlchemy Database Models
│   │   ├── schema.sql       # SQL database initialization schema
│   │   ├── user.py, alert.py, portfolio.py, watchlist.py, refresh_token.py
│   ├── schemas/             # Pydantic (v2) Request/Response Schemas
│   └── services/            # Core business logic handlers
│       ├── auth_service.py  # Password hashing (bcrypt) & JWT operations
│       ├── data_service.py  # Query builder interfacing Postgres views/tables
│       └── alert_worker.py  # Background price polling and alert trigger daemon
├── tests/                   # Automated pytest suite (50 test scenarios)
├── Dockerfile               # Production multi-stage build manifest
└── requirements.txt         # Package dependencies
```

---

## Database & Schema Design

The backend communicates with a remote **Supabase Cloud PostgreSQL** instance (`aws-0-eu-west-1.pooler.supabase.com`). 

```
                                  DATABASE LAYOUT
 ┌──────────────────────────┐    ┌──────────────────────────┐    ┌──────────────────────────┐
 │      public Schema       │    │      silver Schema       │    │       gold Schema        │
 ├──────────────────────────┤    ├──────────────────────────┤    ├──────────────────────────┤
 │ • users                  │    │ • news                   │    │ • daily_market_summary   │
 │ • refresh_tokens         │    │ • social                 │    │ • market_sentiment       │
 │ • user_sessions          │    │ • news_sentiment         │    │ • gold_dashboard_stats   │
 │ • watchlists             │    │   (Populated by Spark)   │    │   (Materialized by dbt)  │
 │ • alerts                 │    └──────────────────────────┘    └──────────────────────────┘
 │ • portfolios             │
 └──────────────────────────┘
```

The database structures are partitioned as follows:
*   `public`: User accounts, session metrics, configurations, watchlists, portfolio listings, and user-defined price alerts.
*   `silver`: Ingested news headlines and RSS feeds (synchronized by Spark streaming jobs).
*   `gold`: Business intelligence data, daily OHLCV aggregations, and sentiment indexes (materialized by dbt).

---

## API Endpoint Documentation

### Authentication (`/api/v1/auth`)
Authentication endpoints are stateless, JWT-based, and enforce rotation:

| Endpoint | Method | Input Schema | Output Description |
| :--- | :---: | :--- | :--- |
| `/api/v1/auth/signup` | `POST` | `UserCreate` (email, password, name) | Creates user, returns Access + Refresh Token pair. |
| `/api/v1/auth/login` | `POST` | `OAuth2PasswordRequestForm` | Verifies password; issues Access + Refresh Tokens. |
| `/api/v1/auth/refresh` | `POST` | `TokenRefreshRequest` | Rotates Refresh Token; invalidates previous session. |
| `/api/v1/auth/me` | `GET` | *Bearer Token Header* | Retrieves profile details of the authenticated caller. |

### Market & Coin Endpoints (`/api/v1`)
Retrieve data from the data lakehouse warehouse tables:

| Endpoint | Method | Parameters | Description |
| :--- | :---: | :--- | :--- |
| `/api/v1/coins` | `GET` | *None* | Lists all 20 tracked cryptocurrencies (e.g. BTC, ETH). |
| `/api/v1/coins/{symbol}/summary` | `GET` | `symbol` (e.g., `BTCUSDT`) | Fetch latest daily OHLCV summary from `gold.daily_market_summary`. |
| `/api/v1/coins/{symbol}/prices` | `GET` | `symbol`, `days` (default 30) | Historical price candles (1 to 365 days range). |
| `/api/v1/market/overview` | `GET` | *None* | Aggregated stats: total volume, BTC dominance index, top gainers/losers. |
| `/api/v1/market/sentiment` | `GET` | *None* | Real-time sentiment score (FinBERT analysis) with fallbacks. |

### Portfolio, Watchlists & Alerts (Authentication Required)
User CRUD endpoints:

| Endpoint | Method | Path/Description |
| :--- | :---: | :--- |
| `/api/v1/watchlists` | `GET`/`POST`/`DELETE` | Retrieve, add, or delete tickers from personal watchlists. |
| `/api/v1/alerts` | `GET`/`POST`/`DELETE` | Set or remove price alerts (`above` or `below` thresholds). |
| `/api/v1/portfolios` | `GET`/`POST`/`DELETE` | Fetch and update portfolio allocations (calculates net profit/loss). |

---

## Security & JWT Rotation Flow

To mitigate replay attacks and session theft, the backend implements **Refresh Token Rotation**:

```
[ Client ]                        [ Backend API ]                       [ Supabase DB ]
    │                                    │                                     │
    │ ─── 1. POST /auth/refresh ───────► │                                     │
    │      (with OLD Refresh Token)      │                                     │
    │                                    │ ─── 2. Lookup & Verify Token ─────► │
    │                                    │ ◄─── 3. Token is Valid & Active ────│
    │                                    │                                     │
    │                                    │ ─── 4. Revoke OLD Token ──────────► │
    │                                    │ ─── 5. Store NEW Token ───────────► │
    │                                    │                                     │
    │ ◄── 6. Return NEW Access+Refresh ─ │                                     │
```

*   **Access Token Lifespan**: 30 minutes.
*   **Refresh Token Lifespan**: 7 days.
*   **Safety Trigger**: If a client attempts to use a revoked/old refresh token, the backend triggers an immediate lockout of all sessions for that user as a precaution.

---

## Alert Worker Background Daemon

The `alert_worker.py` script is a lightweight background worker that runs concurrently with the API:

```text
               ┌──────────────────────────────────────┐
               │         ALERT WORKER DAEMON          │
               └──────────────────┬───────────────────┘
                                  │ Polls every 60s
                                  ▼
               ┌──────────────────────────────────────┐
               │    Query Active Alerts from DB       │
               └──────────────────┬───────────────────┘
                                  │
                                  ▼
               ┌──────────────────────────────────────┐
               │ Query Latest Prices from Gold Layer  │
               └──────────────────┬───────────────────┘
                                  │
                                  ▼
                      Did any Price cross
                      the Alert threshold?
                        /            \
                     YES              NO
                     /                  \
                    ▼                    ▼
        ┌───────────────────────┐   ┌───────────────┐
        │ Trigger Alert Notification│   │   Do Nothing  │
        │  & Mark Alert INACTIVE │   └───────────────┘
        └───────────────────────┘
```

---

## Installation & Local Setup

### Prerequisites
*   Python 3.10+
*   A running PostgreSQL instance (or Supabase URL credentials)

### Steps
1.  Navigate to the backend folder:
    ```bash
    cd backend
    ```
2.  Initialize virtual environment:
    ```bash
    python -m venv venv
    venv\Scripts\activate      # Windows
    source venv/bin/activate   # Linux/macOS
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Copy and fill the `.env` settings:
    ```bash
    cp .env.example .env
    ```
5.  Launch the server:
    ```bash
    uvicorn app.main:app --reload --port 8000
    ```

Navigate to `http://localhost:8000/docs` to access the interactive Swagger documentation.

---

## Automated Test Suite

A complete testing suite is implemented in `tests/` utilizing `pytest` and SQLite for rapid testing cycles (without mock data overlays).

Execute tests locally:
```bash
pytest tests/ -v
```

All 50 unit and integration tests are verified.
