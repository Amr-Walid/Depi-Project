# Karim — Analytics Engineer (dbt & Gold Layer)

**Role:** Analytics Engineer  
**Core Responsibility:** Build the Gold Layer using dbt — transforming clean Silver data into business-level aggregations and metrics that the API and dashboards consume.

---

## Milestone 1 — Database Schema and dbt Project Setup

**Goal:** Set up the PostgreSQL schema that the entire backend depends on, and configure the dbt project so it is ready to run as soon as Silver data is available.

---

### Task 1.1 — PostgreSQL Schema Design [COMPLETE]

**File:** `backend/app/models/schema.sql`

This file is mounted into the PostgreSQL container on startup and auto-executes to create all tables.

**Tables created:**

`users`
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

`watchlists`
```sql
CREATE TABLE watchlists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

`alerts`
```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    condition VARCHAR(50) NOT NULL,  -- 'above' | 'below'
    threshold DECIMAL(18, 8) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);
```

`portfolios`
```sql
CREATE TABLE portfolios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    quantity DECIMAL(18, 8) NOT NULL,
    avg_buy_price DECIMAL(18, 8) NOT NULL
);
```

`refresh_tokens` — stores JWT refresh tokens for rotation security

- [x] All tables created with appropriate foreign keys and `ON DELETE CASCADE`
- [x] Indexes added on `user_id` and `symbol` columns used in frequent queries

---

### Task 1.2 — dbt Project Setup [COMPLETE]

**File:** `processing/dbt/dbt_project.yml`

- [x] `dbt_project.yml` configured with project name `crypto_pulse_dbt`, correct model paths, and materialization strategy:
  - `staging` models → materialized as **Views**
  - `gold` models → materialized as **Tables**
- [x] Directory structure created: `models/staging/`, `models/gold/`, `tests/`
- [x] `dbt` `.gitignore` created to exclude `target/` and `dbt_packages/`

---

## Milestone 2 — dbt Models, Data Quality, and Documentation

**Goal:** Transform Silver Layer data into business-level Gold tables, ensure data quality with tests, and document the models.

---

### Task 2.1 — Staging Models [COMPLETE]

**Directory:** `processing/dbt/models/staging/`

Staging models are thin transformation views sitting directly on Silver data. They cast types and apply basic quality filters.

**`stg_prices.sql`** — reads from `silver.bronze_historical_prices`:
```sql
{{ config(materialized='view') }}

SELECT
    symbol,
    CAST(price AS DECIMAL(18, 8)) AS price,
    CAST(volume AS DECIMAL(18, 8)) AS volume,
    CAST(timestamp AS TIMESTAMP) AS event_time,
    ingested_at
FROM {{ source('silver', 'bronze_historical_prices') }}
WHERE price IS NOT NULL
  AND price > 0
```

**`stg_news.sql`** — reads cleaned news data from Silver

**`stg_social.sql`** — reads cleaned social/Reddit data from Silver

**`sources.yml`** — defines the Silver layer as a dbt source so models can reference it with `{{ source('silver', ...) }}`

---

### Task 2.2 — Gold Models [COMPLETE]

**Directory:** `processing/dbt/models/gold/`

Gold models are materialized as tables for fast query performance by the API.

**`daily_market_summary.sql`** — computes OHLCV per coin per day using window functions:
```sql
{{ config(materialized='table') }}

WITH prices AS (
    SELECT
        symbol,
        DATE_TRUNC('day', event_time) AS date,
        FIRST_VALUE(price) OVER (PARTITION BY symbol, DATE_TRUNC('day', event_time) ORDER BY event_time) AS open_price,
        MAX(price)         OVER (PARTITION BY symbol, DATE_TRUNC('day', event_time)) AS high_price,
        MIN(price)         OVER (PARTITION BY symbol, DATE_TRUNC('day', event_time)) AS low_price,
        LAST_VALUE(price)  OVER (PARTITION BY symbol, DATE_TRUNC('day', event_time) ORDER BY event_time) AS close_price,
        SUM(volume)        OVER (PARTITION BY symbol, DATE_TRUNC('day', event_time)) AS total_volume
    FROM {{ ref('stg_prices') }}
)

SELECT DISTINCT symbol, date, open_price, high_price, low_price, close_price, total_volume
FROM prices
```

**`market_sentiment.sql`** — aggregates sentiment scores per hour from news data:
```sql
{{ config(materialized='table') }}

SELECT
    DATE_TRUNC('hour', published_at) AS sentiment_hour,
    AVG(sentiment_score)             AS avg_sentiment,
    COUNT(*)                         AS article_count,
    SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) AS positive_count,
    SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) AS negative_count
FROM {{ ref('stg_news') }}
GROUP BY DATE_TRUNC('hour', published_at)
```

> ✅ **Update (May 2026):** `market_sentiment.sql` now has data to work with. The `producer_news.py` and `producer_social_rss.py` are both operational and data has been confirmed in `silver/news` and `silver/social` on ADLS Gen2. The keyword-based logic in `market_sentiment.sql` is a placeholder — FinBERT scores (Ahmed's task) will replace the `positive_count`/`negative_count` logic once implemented.

---

### Task 2.3 — Data Quality Tests [COMPLETE]

**File:** `processing/dbt/tests/assert_low_price_less_than_high_price.sql`

A custom singular test that asserts data integrity — `low_price` must always be less than or equal to `high_price` in `daily_market_summary`. dbt will flag any failing rows as a test failure.

- [x] Custom test for `low_price <= high_price` written and committed
- [x] Additional tests created and run successfully:
  - Assert `total_volume > 0`
  - Assert no duplicate `(symbol, date)` combinations in `daily_market_summary`

---

### Task 2.4 — Model Documentation [COMPLETE]

**Files:** `processing/dbt/models/gold/schema.yml`

- [x] `schema.yml` created with column descriptions for Gold models
- [x] Run `dbt docs generate` to produce the interactive HTML documentation site
- [x] Host or share the docs output with the team (tested via `dbt docs serve`)

---

### Task 2.5 — Airflow Integration [COMPLETE & VERIFIED ✅]

**Coordinated with Yassin & Amr:**
- [x] Added a dbt task to `dags/dag_historical_daily.py`:
  ```python
  run_dbt_historical = BashOperator(
      task_id='run_dbt_historical',
      bash_command='cd /opt/airflow/dbt && dbt run --select gold_daily_ohlcv daily_market_summary && dbt test',
  )
  ```
- [x] Added a dbt task to `dags/dag_prices_frequent.py`:
  ```python
  run_dbt_prices = BashOperator(
      task_id='run_dbt_prices',
      bash_command='cd /opt/airflow/dbt && dbt run --select gold_latest_prices daily_market_summary',
  )
  ```
- [x] **Verified (May 2026):** dbt runs successfully within Airflow DAGs and populates Gold tables in PostgreSQL. Confirmed **37,304 records** created in `gold.daily_market_summary`.

---

## Summary Table

| Task | Description | Status |
|------|-------------|--------|
| 1.1 | PostgreSQL schema (users, watchlists, alerts, portfolios, refresh_tokens) | Complete |
| 1.2 | dbt project setup and configuration | Complete |
| 2.1 | Staging models (stg_prices, stg_news, stg_social, sources.yml) | Complete |
| 2.2 | Gold models (daily_market_summary, market_sentiment) | Complete |
| 2.3 | Data quality tests | Complete |
| 2.4 | Model documentation | Complete |
| 2.5 | dbt integration with Airflow DAGs | Complete & Verified ✅ |

---

## Deliverables

**Milestone 1 (complete):**
- `backend/app/models/schema.sql`
- `processing/dbt/dbt_project.yml`
- `processing/dbt/.gitignore`

**Milestone 2 (complete):**
- `processing/dbt/models/staging/sources.yml`
- `processing/dbt/models/staging/stg_prices.sql`
- `processing/dbt/models/staging/stg_news.sql`
- `processing/dbt/models/staging/stg_social.sql`
- `processing/dbt/models/gold/daily_market_summary.sql`
- `processing/dbt/models/gold/market_sentiment.sql`
- `processing/dbt/models/gold/schema.yml`
- `processing/dbt/tests/assert_low_price_less_than_high_price.sql`

**Do not commit:**
- `profiles.yml` — contains database credentials
- `dbt_packages/` — equivalent to node_modules, auto-installed
- `target/` — local build artifacts

---

## Dependencies

| Depends on | From | Why |
|-----------|------|-----|
| Silver layer ready | Yassin | dbt cannot run without Silver data as input |
| Sentiment scores | Ahmed | Required to populate `gold/market_sentiment.sql` |
| Gold layer ready | Karim (self) | Mostafa needs it to build the data API endpoints |
| Azure credentials | Amr | To connect dbt to ADLS Gen2 |

---

## Reference Links

| Resource | URL |
|----------|-----|
| dbt Documentation | https://docs.getdbt.com |
| dbt Spark Adapter | https://docs.getdbt.com/docs/core/connect-data-platform/spark-setup |
| dbt Best Practices | https://docs.getdbt.com/guides/best-practices |
| Medallion Architecture | https://www.databricks.com/glossary/medallion-architecture |

---

## Milestone 3 — dbt Sentiment Models + Dashboard Analytics

**Goal:** تحديث نماذج الـ Sentiment لتستخدم أرقام FinBERT الحقيقية بدلاً من الكلمات المفتاحية، وإنشاء نماذج جديدة لدعم الـ Frontend Dashboard.

> **ملاحظة:** التفاصيل الكاملة لكل التاسكات موجودة في [06_milestone3_plan.md](./06_milestone3_plan.md)

---

### Task 3.1 — تحديث market_sentiment.sql بأعمدة FinBERT [NOT STARTED]

**الملف:** `processing/dbt/models/gold/market_sentiment.sql`

- [ ] استبدال المنطق الحالي (keyword-based: `ILIKE '%bull%'`) بقراءة مباشرة من `silver.news_sentiment`
- [ ] حساب `avg_sentiment_score`, `positive_count`, `negative_count`, `neutral_count`
- [ ] إضافة عمود `market_mood` (Bullish / Bearish / Neutral) بناءً على المتوسط

### Task 3.2 — تحديث sources.yml [NOT STARTED]

**الملف:** `processing/dbt/models/staging/sources.yml`

- [ ] إضافة جدول `news_sentiment` كـ source جديد

### Task 3.3 — إنشاء Staging Model للـ Sentiment [NOT STARTED]

**الملف الجديد:** `processing/dbt/models/staging/stg_news_sentiment.sql`

- [ ] View بسيط يقرأ من `silver.news_sentiment`
- [ ] يعمل CAST للـ sentiment_score كـ `DECIMAL(5, 4)`
- [ ] يفلتر الصفوف اللي فيها `sentiment_score IS NOT NULL`

### Task 3.4 — إنشاء Gold Model للـ Dashboard Stats [NOT STARTED]

**الملف الجديد:** `processing/dbt/models/gold/gold_dashboard_stats.sql`

- [ ] يجمع كل الإحصائيات في استعلام واحد
- [ ] `active_coins`, `total_volume_24h`, `overall_sentiment`

### Task 3.5 — إضافة اختبارات جودة بيانات جديدة [NOT STARTED]

**المجلد:** `processing/dbt/tests/`

- [ ] `assert_sentiment_score_range.sql` — التأكد إن الـ scores في نطاق -1 إلى 1
- [ ] تحديث `schema.yml` بأوصاف الأعمدة الجديدة

### Task 3.6 — تحديث الـ dbt DAG في Airflow [NOT STARTED]

**الملف:** `dags/dag_historical_daily.py`

- [ ] تحديث أمر dbt ليشمل كل الـ Models الجديدة: `dbt run && dbt test`

---

| Task | Description | Status |
|------|-------------|--------|
| 3.1 | تحديث market_sentiment.sql | Not started |
| 3.2 | تحديث sources.yml | Not started |
| 3.3 | Staging Model للـ Sentiment | Not started |
| 3.4 | Gold Dashboard Stats Model | Not started |
| 3.5 | اختبارات جودة بيانات جديدة | Not started |
| 3.6 | تحديث الـ dbt DAG | Not started |
