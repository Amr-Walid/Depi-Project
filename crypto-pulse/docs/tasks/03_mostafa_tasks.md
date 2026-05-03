# Mostafa Matar — Backend Engineer & Docker Environment Owner

**Role:** Backend Engineer + Owner of the entire local development environment  
**Core Responsibility:** Docker infrastructure that runs all services, and the REST API that serves users.

---

## Milestone 1 — Docker Infrastructure and Backend Foundation

**Goal:** Deliver a working local development environment. Any team member runs `make up` and every service starts correctly.

---

### Task 1.1 — Docker Compose Setup [COMPLETE]

**File:** `docker-compose.yml`

**What was done:**
- [x] Defined `zookeeper` service (Kafka coordination)
- [x] Defined `kafka` service with dual listener configuration:
  - `INTERNAL://kafka:29092` — for Docker services (Spark, Airflow)
  - `EXTERNAL://localhost:9092` — for the Python producer running on the host
- [x] Defined `kafka-init-topics` container that auto-creates 4 topics on startup: `crypto.realtime.prices`, `crypto.market.data`, `crypto.news`, `crypto.social`
- [x] Defined `kafka-ui` on port 8080
- [x] Defined `postgres:15` with a mounted `schema.sql` that auto-initializes the database schema
- [x] Defined `airflow-webserver` on port 8081 using a **custom Dockerfile** (`airflow/Dockerfile`) with Docker CLI 27.4.1 and pre-installed pip packages (dbt-core, dbt-postgres)
- [x] Defined `airflow-scheduler` — triggers Spark jobs via `docker exec` on the spark-master container through the Docker socket
- [x] Defined `spark-master` and `spark-worker` using the custom `crypto-pulse-spark:3.5.0` image
- [x] Defined background streaming containers: `streaming-bronze-prices`, `streaming-bronze-news`, `streaming-bronze-social`, and `streaming-silver-prices` to run Spark structured streaming continuously without blocking Airflow
- [x] Defined `backend` FastAPI container on port 8000 with `POSTGRES_HOST=postgres`
- [x] Configured shared bridge network `crypto-net` for all services
- [x] All containers that need Azure credentials receive them via `env_file: .env`
- [x] All Spark and Airflow containers have `KAFKA_BOOTSTRAP_SERVERS=kafka:29092` set correctly for internal networking
- [x] Both Airflow containers run as `user: "0:0"` to access the Docker socket at `/var/run/docker.sock`

---

### Task 1.2 — Makefile [COMPLETE]

**File:** `Makefile`

- [x] `make up` — `docker compose up -d`
- [x] `make down` — `docker compose down`
- [x] `make logs` — `docker compose logs -f`
- [x] `make restart` — down + up
- [x] `make rebuild-backend` — rebuilds only the backend image
- [x] `make test` — runs pytest inside the backend container
- [x] `make shell-backend` — opens a shell inside the backend container
- [x] `make spark-submit` — shortcut for running a Spark job

---

### Task 1.3 — Custom Spark Dockerfile [COMPLETE]

**File:** `spark-apps/Dockerfile.spark`

- [x] Extends `apache/spark:3.5.0`
- [x] Installs Python packages: `python-dotenv==1.0.1`, `delta-spark==3.2.0`
- [x] Downloads all required JARs directly into `/opt/spark/jars/`:
  - Azure: `hadoop-azure:3.3.4`, `wildfly-openssl:1.1.3.Final`, `azure-storage-blob`, `azure-storage-common`, `azure-core`, `azure-core-http-netty`, `azure-identity`, `msal4j`
  - Kafka: `spark-sql-kafka-0-10_2.12:3.5.0`, `kafka-clients:3.5.1`, `spark-token-provider-kafka-0-10_2.12:3.5.0`, `commons-pool2:2.11.1`
  - Delta: `delta-spark_2.12:3.2.0`, `delta-storage:3.2.0`

---

### Task 1.4 — Backend Dockerfile [COMPLETE]

**File:** `backend/Dockerfile`

- [x] Created `backend/Dockerfile` for building the FastAPI container
- [x] Created `backend/requirements.txt`
- [x] Created `backend/.dockerignore`

---

### Task 1.5 — Backend Application Skeleton [COMPLETE]

**Files:** `backend/app/main.py`, routers, models, services, schemas

- [x] `main.py` — FastAPI app with CORS middleware, startup event to create DB tables, health check endpoints (`/` and `/health`), and all routers registered
- [x] All `__init__.py` files created for proper module structure

---

## Milestone 2 — Full REST API

**Goal:** Build a secure, functional API that the frontend can use to authenticate users and retrieve data.

---

### Task 2.1 — Authentication System [COMPLETE]

**Files:**
- `backend/app/routers/auth.py`
- `backend/app/services/auth_service.py`
- `backend/app/models/user.py`, `refresh_token.py`
- `backend/app/schemas/auth.py`

**Endpoints implemented:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/signup` | POST | Register a new user. Hashes password with bcrypt. Returns JWT access + refresh tokens. |
| `/api/v1/auth/login` | POST | Authenticate with email + password. Returns tokens. |
| `/api/v1/auth/refresh` | POST | Exchange a valid refresh token for a new token pair. Old token is revoked (token rotation). |
| `/api/v1/auth/me` | GET | Returns the authenticated user's profile. Requires Bearer token. |

**Security implementation:**
- Passwords hashed with `bcrypt` via `passlib`
- JWT tokens signed with HS256 using a secret key from `.env`
- Refresh token rotation: each `/refresh` call revokes the old token and issues a new one
- `get_current_user` dependency guards all protected endpoints

---

### Task 2.2 — Data Endpoints [COMPLETE]

**Files:**
- `backend/app/routers/coins.py`
- `backend/app/routers/watchlists.py`
- `backend/app/routers/alerts.py`
- `backend/app/routers/portfolios.py`
- `backend/app/services/data_service.py`

**Endpoints implemented:**
- `GET /api/v1/coins` — List all available coins
- `GET /api/v1/coins/{coin_id}/summary` — Analytical summary for a coin
- `GET /api/v1/coins/{coin_id}/prices` — Historical price data
- `GET /api/v1/market/overview` — Market-wide overview

**Full CRUD for:**
- Watchlists — user-scoped coin watchlists
- Alerts — price threshold alerts per user
- Portfolios — position tracking (symbol, quantity, average buy price)

`data_service.py` connects to Azure ADLS Gen2 using the Service Principal and reads from the Gold layer tables produced by dbt in PostgreSQL.
- [x] **Verified (May 2026):** API correctly serves real OHLCV and market overview data from the `gold.daily_market_summary` table. ✅

---

### Task 2.3 — API Test Suite [COMPLETE]

**Files:** `backend/tests/test_auth.py`, `test_coins.py`, `test_watchlists.py`, `test_alerts.py`, `test_portfolios.py`, `conftest.py`

- [x] `conftest.py` sets up a `TestClient` with an in-memory test database
- [x] Auth tests: valid signup (201), duplicate email (400), wrong password (401), accessing protected endpoint without token (403)
- [x] Data endpoint tests: `GET /api/v1/coins` with valid token (200)

---

## Summary Table

| Task | Description | Status |
|------|-------------|--------|
| 1.1 | docker-compose.yml — all services | Complete |
| 1.2 | Makefile | Complete |
| 1.3 | Spark Dockerfile with pre-installed JARs | Complete |
| 1.4 | Backend Dockerfile | Complete |
| 1.5 | Backend app skeleton | Complete |
| 2.1 | JWT Authentication system | Complete |
| 2.2 | Data endpoints (coins, watchlists, alerts, portfolios) | Complete & Verified ✅ |
| 2.3 | pytest test suite | Complete |

---

## Service URLs

| Service | Port | URL |
|---------|------|-----|
| FastAPI Swagger | 8000 | http://localhost:8000/docs |
| FastAPI Health | 8000 | http://localhost:8000/health |
| Kafka UI | 8080 | http://localhost:8080 |
| Airflow | 8081 | http://localhost:8081 |
| Spark Master | 8082 | http://localhost:8082 |

---

## Milestone 3 — Sentiment API + Alert Worker + Code Cleanup

**Goal:** إضافة Endpoint للـ Sentiment، بناء محرك تنبيهات يعمل في الخلفية، وتنظيف الكود القديم.

> **ملاحظة:** التفاصيل الكاملة لكل التاسكات موجودة في [06_milestone3_plan.md](./06_milestone3_plan.md)

---

### Task 3.1 — إنشاء Sentiment API Endpoint [NOT STARTED]

**الملف:** `backend/app/routers/coins.py`

- [ ] إضافة `GET /api/v1/market/sentiment`
- [ ] يقرأ من `gold.market_sentiment` أو `silver.news_sentiment`
- [ ] يرجع: `overall_score`, `overall_label`, `positive_pct`, `negative_pct`, `article_count`

### Task 3.2 — تحديث Pydantic Schema للـ Sentiment [NOT STARTED]

**الملف:** `backend/app/schemas/coins.py`

- [ ] إضافة `SentimentOverview` schema جديد

### Task 3.3 — تحديث data_service.py [NOT STARTED]

**الملف:** `backend/app/services/data_service.py`

- [ ] حذف `import random` (سطر 1) — كود قديم
- [ ] حذف `MOCK_BASE_PRICES` (سطر 37-59) — كود Mock غير مستخدم
- [ ] إضافة function `get_market_sentiment(db)` يقرأ من PostgreSQL

### Task 3.4 — بناء Alert Worker (Background Service) [NOT STARTED]

**الملف الجديد:** `backend/app/services/alert_worker.py`

- [ ] Worker يلف كل دقيقة يقرأ أحدث الأسعار من `gold.daily_market_summary`
- [ ] يقارن بجدول `alerts` (condition: above/below)
- [ ] يطبع تنبيه ويعطل الـ Alert (`is_active = FALSE`)

### Task 3.5 — إضافة Alert Worker للـ Docker Compose [NOT STARTED]

**الملف:** `docker-compose.yml`

- [ ] إضافة service `alert-worker` يستخدم نفس `backend/Dockerfile`
- [ ] يشتغل كـ: `python -m app.services.alert_worker`

### Task 3.6 — تنظيف الـ Backend Code [NOT STARTED]

**الملف:** `backend/app/services/data_service.py`

- [ ] التأكد إن كل الـ Endpoints بترجع داتا حقيقية من PostgreSQL فقط
- [ ] إزالة أي references للـ Mock data

---

| Task | Description | Status |
|------|-------------|--------|
| 3.1 | Sentiment API Endpoint | Not started |
| 3.2 | Pydantic Schema للـ Sentiment | Not started |
| 3.3 | تحديث data_service.py | Not started |
| 3.4 | Alert Worker | Not started |
| 3.5 | Alert Worker في Docker | Not started |
| 3.6 | تنظيف الـ Backend Code | Not started |
