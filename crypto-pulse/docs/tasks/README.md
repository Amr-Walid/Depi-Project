# CryptoPulse — Task Dashboard

> Last reviewed: May 2026

---

## Task Files

| File | Owner |
|------|-------|
| [00_project_structure.md](./00_project_structure.md) | Project Structure & Data Flow |
| [01_amr_tasks.md](./01_amr_tasks.md) | Amr Walid — Lead Engineer |
| [02_yassin_tasks.md](./02_yassin_tasks.md) | Yassin Mahmoud — Spark / DataOps |
| [03_mostafa_tasks.md](./03_mostafa_tasks.md) | Mostafa Matar — Backend / Docker |
| [04_ahmed_tasks.md](./04_ahmed_tasks.md) | Ahmed Ayman — ML / Analyst |
| [05_karim_tasks.md](./05_karim_tasks.md) | Karim — dbt / Analytics |

---

## Progress Dashboard

### Amr Walid

| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| Progress | 100% | 95% |
| Status | Complete | Integration testing complete. News/Social RSS pipelines integrated. Final status report pending. |

### Yassin Mahmoud

| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| Progress | 100% | 100% |
| Status | Complete | Complete — Bronze streaming, Silver streaming processor, historical batch, News/Social consumers, Airflow DAGs. |

### Mostafa Matar

| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| Progress | 100% | 100% |
| Status | Complete | Complete — Full FastAPI backend with JWT auth, all CRUD endpoints, pytest test suite. |

### Ahmed Ayman

| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| Progress | 100% | 0% |
| Status | Complete — News producer and RSS social producer are operational and data flows to Azure. | ML tasks (FinBERT, LSTM, Notebooks) not started. |

### Karim

| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| Progress | 100% | 85% |
| Status | Complete | Staging and Gold dbt models written. Data tests written. `dbt run` and `dbt docs generate` pending execution. |

---

## Pipeline Dependency Chain

```
Amr (Azure infra + Kafka producers)
    |
    v
Yassin (bronze_consumer.py — Streaming) ✅
    |
    v
Yassin (silver_prices_processor.py — Streaming Upsert) ✅
    |
    v
Amr (sync_*_pg.py — Silver → PostgreSQL) ✅
    |
    v
Karim  (dbt staging + gold models) ⏳
    |
    v
Mostafa (FastAPI — data_service reads Gold layer) ✅

---

Amr (producer_news.py + producer_social_rss.py) ✅
    |
    v
Amr (bronze_news_consumer + bronze_social_consumer) ✅
    |
    v
Amr (silver_news_processor + silver_social_processor) ✅
    |
    v
Karim  (gold/market_sentiment.sql — data available now!) ⏳
    |
    v
Ahmed (FinBERT sentiment scoring — NOT STARTED) ❌
```

---

## Current Priorities

1. **Karim** — Execute `dbt run && dbt test` to materialize the Gold layer. News/Social data is now available.
2. **Ahmed** — Implement FinBERT sentiment model in notebooks and integrate as Spark UDF.
3. **Amr** — Complete final status report (Task 2.4). Execute `sync_news_pg.py` and `sync_social_pg.py` to populate PostgreSQL.
4. **Yassin** — All tasks complete.
5. **Mostafa** — All tasks complete.
