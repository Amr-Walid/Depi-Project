# 🚀 Crypto-Pulse Backend & API Guide

Welcome to the backend component of the **Crypto-Pulse** project. This directory contains the FastAPI application responsible for serving data to users, handling authentication, and managing user-specific features like watchlists, portfolios, and price alerts.

**Database:** Supabase Cloud PostgreSQL (`aws-0-eu-west-1.pooler.supabase.com`)

---

## ✅ Current Status (May 2026)

All 3 milestones are **complete**. The backend is fully operational and serving **real data** from the Gold layer (dbt) on Supabase Cloud PostgreSQL.

- ✅ JWT Authentication with refresh token rotation
- ✅ All data endpoints serve real OHLCV data from `gold.daily_market_summary`
- ✅ Market sentiment endpoint with Gold → Silver → Neutral fallback
- ✅ Alert Worker background service (60s polling interval)
- ✅ 50 automated tests passing

---

## 🔐 Authentication (`/api/v1/auth`)

JWT Authentication with **Refresh Token Rotation**:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/signup` | POST | Register a new user. Returns access + refresh tokens. |
| `/api/v1/auth/login` | POST | Authenticate with email + password. Returns tokens. |
| `/api/v1/auth/refresh` | POST | Exchange a valid refresh token for a new token pair. Old token is revoked. |
| `/api/v1/auth/me` | GET | Returns the profile of the currently authenticated user. |

---

## 📊 Data & Market APIs (`/api/v1`)

All data endpoints read from the **Gold layer** (dbt materialized tables) in Supabase Cloud PostgreSQL.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/coins` | GET | List all 20 supported coins with name and active status. |
| `/api/v1/coins/{symbol}/summary` | GET | Daily OHLCV summary for a specific coin from `gold.daily_market_summary`. |
| `/api/v1/coins/{symbol}/prices` | GET | Historical price data (1–365 days) from Gold layer. |
| `/api/v1/market/overview` | GET | Market-wide stats: total volume, BTC dominance, top gainers/losers. |
| `/api/v1/market/sentiment` | GET | Market sentiment from FinBERT analysis. Falls back: Gold → Silver → Neutral. |

### User Features (Protected)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/watchlists` | CRUD | Manage user coin watchlists. |
| `/api/v1/alerts` | CRUD | Price alert management (above/below threshold). |
| `/api/v1/portfolios` | CRUD | Portfolio position tracking (symbol, quantity, buy price). |

---

## 🏗️ Architecture

```
backend/
├── app/
│   ├── main.py              ← FastAPI entry point, CORS, router registration
│   ├── config.py            ← Centralized config (reads from .env, URL-encodes Supabase password)
│   ├── database.py          ← SQLAlchemy engine + session (connected to Supabase Cloud)
│   ├── routers/             ← API Endpoints
│   │   ├── auth.py          ← JWT auth endpoints
│   │   ├── coins.py         ← Coin data + market overview + sentiment
│   │   ├── watchlists.py    ← User watchlists CRUD
│   │   ├── alerts.py        ← Price alerts CRUD
│   │   └── portfolios.py    ← Portfolio positions CRUD
│   ├── models/              ← SQLAlchemy ORM models
│   │   ├── schema.sql       ← Full DB schema (auto-creates tables on startup)
│   │   ├── user.py, alert.py, portfolio.py, watchlist.py, refresh_token.py
│   ├── schemas/             ← Pydantic v2 request/response schemas
│   └── services/            ← Business logic
│       ├── auth_service.py  ← Password hashing + JWT logic
│       ├── data_service.py  ← Reads from Gold/Silver layer in PostgreSQL (NO mock data)
│       └── alert_worker.py  ← Background alert polling service
├── tests/                   ← pytest test suite (50 tests)
├── Dockerfile               ← Docker image for FastAPI
└── requirements.txt         ← Python dependencies
```

---

## 🔔 Alert Worker

A background service that monitors price alerts:

- Runs every **60 seconds**
- Reads latest prices from `gold.daily_market_summary`
- Compares with active alerts in the `alerts` table
- Supports `above` and `below` conditions
- Deactivates triggered alerts
- Handles missing tables and DB errors gracefully

**Docker Compose service:**
```yaml
alert-worker:
  build: ./backend
  command: python -m app.services.alert_worker
  env_file: .env
  environment:
    POSTGRES_HOST: ${POSTGRES_HOST}
  restart: unless-stopped
```

---

## 🚀 Running the API

### Option 1 — Local Development (without Docker)

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables (or create backend/.env)
# The backend reads POSTGRES_* variables from the root .env or backend/.env

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Option 2 — Docker Compose (full stack)

```bash
# From project root
make up
# or: docker compose up -d --build
```

**Interactive docs:** http://localhost:8000/docs

---

## 🧪 Testing

```bash
cd backend

# Run all tests (uses in-memory SQLite, no Docker needed)
python -m pytest tests/ -q

# Run specific test file
python -m pytest tests/test_sentiment.py -q
```

**Latest results:** `50 passed, 3 warnings in 22.08s`

---

## 🔗 Database Configuration

The backend connects to **Supabase Cloud PostgreSQL** using environment variables:

```env
POSTGRES_HOST=aws-0-eu-west-1.pooler.supabase.com
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres.idiidwhgddbxdbnpamag
POSTGRES_PASSWORD=your_supabase_password
```

`config.py` automatically URL-encodes the password (handles special characters like `@`) and constructs the connection string with `sslmode=require`.

---

## 📋 Database Schema

Managed in `app/models/schema.sql`:

- **`public` schema:** `users`, `refresh_tokens`, `user_sessions`, `watchlists`, `alerts`, `portfolios`
- **`silver` schema:** `news`, `social`, `news_sentiment` (populated by Spark sync jobs)
- **`gold` schema:** `daily_market_summary`, `market_sentiment` (materialized by dbt)

Tables are auto-created on application startup via `create_tables()`.
