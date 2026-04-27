# CryptoPulse — Task Dashboard

> Last reviewed: April 2026

---

## Task Files

| File | Owner |
|------|-------|
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
| Progress | 100% | 80% |
| Status | Complete | README updated. Integration testing (Streaming path) complete. README + final report pending. |

### Yassin Mahmoud

| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| Progress | 100% | 100% |
| Status | Complete | Complete — Bronze streaming, Silver streaming processor (real-time Upsert), historical batch jobs, Airflow DAG all done. |

### Mostafa Matar

| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| Progress | 100% | 100% |
| Status | Complete | Complete — Full FastAPI backend with JWT auth, all CRUD endpoints, pytest test suite. |

### Ahmed Ayman

| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| Progress | 0% | 0% |
| Status | producer_news.py is an empty file. No work started. | All ML tasks pending. Blocking the news/sentiment path entirely. |

### Karim

| | Milestone 1 | Milestone 2 |
|--|------------|------------|
| Progress | 100% | 85% |
| Status | Complete | Staging and Gold dbt models written. Data test written. dbt docs and Airflow integration pending. |

---

## Pipeline Dependency Chain

```
Amr (Azure infra + Kafka producers)
    |
    v
Yassin (bronze_consumer.py — Streaming)
    |
    v
Yassin (silver_prices_processor.py — Streaming Upsert)
    |
    v
Karim  (dbt staging + gold models)
    |
    v
Mostafa (FastAPI — data_service reads Gold layer)

---

Ahmed (producer_news.py — NOT STARTED)
    |
    v
Yassin (silver news/social processing — blocked)
    |
    v
Karim  (gold/market_sentiment.sql — model written but no data yet)
```

---

## Current Priorities

1. **Ahmed** — Write `producer_news.py`. The file is completely empty. The entire news/sentiment path of the pipeline is blocked until this is done.
2. **Karim** — Run `dbt docs generate` to produce interactive documentation. Add dbt task to the Airflow DAG.
3. **Amr** — Complete the final status report (Task 2.4) and review open PRs.
4. **Yassin** — All tasks complete. Available to assist Ahmed or extend the Silver layer for news data.
5. **Mostafa** — All tasks complete.
