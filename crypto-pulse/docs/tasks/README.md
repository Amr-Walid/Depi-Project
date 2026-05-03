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

| | Milestone 1 | Milestone 2 | Milestone 3 |
|--|------------|------------|------------|
| Progress | 100% | 100% | 0% |
| Status | Complete | Complete ✅ | Frontend (Next.js Template) + Azure Deployment |

### Yassin Mahmoud

| | Milestone 1 | Milestone 2 | Milestone 3 |
|--|------------|------------|------------|
| Progress | 100% | 100% | 0% |
| Status | Complete | Complete ✅ | FinBERT Integration + Notebooks |

### Mostafa Matar

| | Milestone 1 | Milestone 2 | Milestone 3 |
|--|------------|------------|------------|
| Progress | 100% | 100% | 0% |
| Status | Complete | Complete ✅ | Sentiment API + Alert Worker + Cleanup |

### Ahmed Ayman — ❌ REMOVED FROM PROJECT

| | Milestone 1 | Milestone 2 | Milestone 3 |
|--|------------|------------|------------|
| Progress | 0% | 0% | 0% |
| Status | Not started | Not started | Not started |

> Ahmed was removed from the team due to inactivity. His Milestone 1 tasks (News & Social Producers) were actually implemented by **Amr Walid** and added to Amr's Milestone 2. His remaining ML tasks have been redistributed to Yassin and Karim.

### Karim

| | Milestone 1 | Milestone 2 | Milestone 3 |
|--|------------|------------|------------|
| Progress | 100% | 100% | 0% |
| Status | Complete | Complete ✅ | dbt Sentiment Models + Dashboard Stats |

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
Karim  (dbt staging + gold models) ✅
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
Yassin (FinBERT sentiment_processor.py) ⏳  ← NEW (Milestone 3)
    |
    v
Karim  (gold/market_sentiment.sql — FinBERT scores) ⏳  ← NEW (Milestone 3)
    |
    v
Mostafa (GET /api/v1/market/sentiment) ⏳  ← NEW (Milestone 3)
    |
    v
Amr (Frontend Dashboard — Next.js) ⏳  ← NEW (Milestone 3)
```

---

## Milestone 3 Task Files

| File | Owner |
|------|-------|
| [06_milestone3_plan.md](./06_milestone3_plan.md) | Detailed plan with code samples for all tasks |

---

## Current Priorities

1. **✅ Airflow Automation** — DONE.
2. **✅ End-to-End Pipeline Testing** — DONE.
3. **✅ Backend API Testing** — DONE.
4. **⏳ Yassin** — FinBERT integration in Spark + Notebooks.
5. **⏳ Karim** — dbt sentiment models + dashboard stats.
6. **⏳ Mostafa** — Sentiment API endpoint + Alert Worker.
7. **⏳ Amr** — Frontend Dashboard (Next.js) + Azure Deployment.
