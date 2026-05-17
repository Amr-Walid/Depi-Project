# 🏗️ CryptoPulse — هيكل المشروع الكامل

> **آخر تحديث:** مايو 2026  
> **الفريق:** عمرو (Lead/Frontend) · ياسين (Spark/ML) · مصطفى (Backend/Docker) · كريم (dbt/Analytics)

---

## 📁 الهيكل الكامل للمشروع

```
crypto-pulse/
│
├── 📄 .env                         ← متغيرات البيئة الفعلية (لا تُرفع على GitHub)
├── 📄 .env.example                 ← قالب متغيرات البيئة [عمرو]
├── 📄 .gitignore                   ← ملفات مستثناة من Git [عمرو]
├── 📄 .dockerignore                ← ملفات مستثناة من Docker build [مصطفى]
├── 📄 Makefile                     ← اختصارات أوامر المشروع [مصطفى]
├── 📄 docker-compose.yml           ← تعريف كل خدمات Docker [مصطفى]
├── 📄 requirements.txt             ← مكتبات Python المطلوبة [مشترك]
├── 📄 README.md                    ← التوثيق الرئيسي للمشروع [عمرو]
│
├── 📁 .github/
│   └── 📁 workflows/               ← ملفات CI/CD (GitHub Actions) [عمرو]
│
├── 📁 ingestion/                   ← طبقة جلب البيانات
│   ├── 📁 producers/
│   │   ├── 📄 producer_binance.py      ← بيانات أسعار لحظية من Binance [عمرو] ✅
│   │   ├── 📄 producer_coingecko.py    ← بيانات سوق من CoinGecko [عمرو] ✅
│   │   ├── 📄 producer_news.py         ← أخبار العملات من NewsAPI [عمرو] ✅
│   │   └── 📄 producer_social_rss.py   ← مقالات رأي من RSS Feeds [عمرو] ✅
│   └── 📁 historical/
│       └── 📄 historical_fetcher.py    ← جلب بيانات تاريخية من Binance [عمرو] ✅
│
├── 📁 processing/
│   ├── 📁 spark_jobs/
│   │   ├── 📄 bronze_consumer.py           ← Spark Streaming → Bronze/prices [ياسين] ✅
│   │   ├── 📄 bronze_news_consumer.py      ← Spark Streaming → Bronze/news [عمرو] ✅
│   │   ├── 📄 bronze_social_consumer.py    ← Spark Streaming → Bronze/social [عمرو] ✅
│   │   ├── 📄 silver_prices_processor.py   ← Streaming → Silver Prices [ياسين] ✅
│   │   ├── 📄 silver_historical_processor.py ← Batch → Silver Historical [ياسين] ✅
│   │   ├── 📄 silver_news_processor.py     ← Batch → Silver News [عمرو] ✅
│   │   ├── 📄 silver_social_processor.py   ← Batch → Silver Social [عمرو] ✅
│   │   ├── 📄 sentiment_processor.py       ← FinBERT Sentiment Analysis [ياسين] ✅
│   │   ├── 📄 historical_loader.py         ← تحميل البيانات التاريخية → Bronze [ياسين] ✅
│   │   ├── 📄 sync_historical_pg.py        ← Sync Historical ADLS → Postgres [عمرو] ✅
│   │   ├── 📄 sync_prices_pg.py            ← Sync Prices ADLS → Postgres [عمرو] ✅
│   │   ├── 📄 sync_news_pg.py              ← Sync News ADLS → Postgres [عمرو] ✅
│   │   └── 📄 sync_social_pg.py            ← Sync Social ADLS → Postgres [عمرو] ✅
│   └── 📁 dbt/                     ← تحويلات الطبقة الذهبية
│       ├── 📄 dbt_project.yml          ← إعدادات مشروع dbt [كريم] ✅
│       ├── 📁 models/
│       │   ├── 📁 staging/
│       │   │   ├── 📄 stg_prices.sql, stg_historical.sql, stg_news.sql, stg_social.sql ✅
│       │   │   ├── 📄 stg_news_sentiment.sql  ← Staging للـ Sentiment [كريم] ✅
│       │   │   └── 📄 sources.yml              ← مع news_sentiment source [كريم] ✅
│       │   └── 📁 gold/
│       │       ├── 📄 daily_market_summary.sql, gold_daily_ohlcv.sql, gold_latest_prices.sql ✅
│       │       ├── 📄 market_sentiment.sql     ← FinBERT-based sentiment [كريم] ✅
│       │       ├── 📄 gold_dashboard_stats.sql ← Dashboard Stats Model [كريم] ✅
│       │       └── 📄 schema.yml              ← مع أوصاف Sentiment الجديدة ✅
│       └── 📁 tests/
│           ├── 📄 assert_low_price_less_than_high_price.sql ✅
│           ├── 📄 assert_no_duplicate_symbol_date.sql ✅
│           ├── 📄 assert_total_volume_positive.sql ✅
│           └── 📄 assert_sentiment_score_range.sql ← اختبار نطاق الـ Scores [كريم] ✅
│
├── 📁 dags/
│   ├── 📄 dag_historical_daily.py      ← DAG يومي للبيانات التاريخية [عمرو] ✅
│   └── 📄 dag_prices_frequent.py       ← DAG متكرر للبيانات اللحظية [عمرو] ✅
│
├── 📁 backend/
│   ├── 📁 app/
│   │   ├── 📄 main.py                  ← نقطة دخول FastAPI [مصطفى] ✅
│   │   ├── 📄 __init__.py
│   │   ├── 📁 routers/                 ← API Endpoints [مصطفى] ✅
│   │   ├── 📁 models/
│   │   │   └── 📄 schema.sql           ← مخطط قاعدة البيانات [كريم] ✅
│   │   └── 📁 services/                ← منطق الأعمال [مصطفى] ✅
│   │       ├── 📄 auth_service.py
│   │       ├── 📄 data_service.py          ← حقيقي من PostgreSQL (بدون Mock) ✅
│   │       └── 📄 alert_worker.py          ← Background Alert Service [مصطفى] ✅
│   └── 📁 tests/                   ← اختبارات API [مصطفى] ✅
│
├── 📁 spark-apps/                  ← بيئة Spark Docker
│   ├── 📄 Dockerfile.spark             ← صورة Docker لـ Spark + FinBERT [مصطفى/ياسين] ✅
│   └── 📄 bronze_consumer.py           ← نسخة تشغيل داخل Container [ياسين] ✅
│
├── 📄 Dockerfile.airflow               ← صورة Airflow مخصصة + PySpark [ياسين] ✅
│
├── 📁 ml/                          ← نماذج الذكاء الاصطناعي (FinBERT متكامل في Spark) ✅
├── 📁 notebooks/
│   ├── 📄 01-data-exploration.ipynb    ← تحليل استكشافي للبيانات [ياسين] ✅
│   ├── 📄 02-model-training.ipynb      ← تدريب نماذج ML [ياسين] ✅
│   ├── 📄 03-poc-dashboard.ipynb       ← Proof of Concept Dashboard ⏳
│   └── 📄 03-sentiment-dashboard.ipynb ← Sentiment Intelligence Dashboard [ياسين] ✅
│
├── 📁 data/
│   └── 📁 historical/              ← بيانات JSON المحفوظة محليًا [عمرو] ✅
│
├── 📁 docs/
│   ├── 📄 project_proposal.pdf         ← مقترح المشروع
│   ├── 📄 architecture.png             ← رسم البنية التحتية [عمرو] ✅
│   └── 📁 tasks/                   ← ← أنت هنا (ملفات التاسكات)
│
├── 📁 airflow/                     ← صورة Docker مخصصة للـ Airflow
│   └── 📄 Dockerfile                  ← Airflow + Docker CLI 27.4.1 + dbt [عمرو] ✅
│
├── 📁 frontend/                    ← واجهة المستخدم (Next.js 16 Dashboard) [عمرو] ✅
└── 📁 orchestration/               ← (محجوز للتوسع المستقبلي)
```

---

## 🏷️ رموز الحالة

| الرمز | المعنى |
|-------|--------|
| ✅ | مكتمل وجاهز |
| ⏳ | بدأ ولم يكتمل بعد |
| ❌ | لم يبدأ بعد |

---

## 👥 ملفات التاسكات التفصيلية

| الملف | الشخص |
|-------|--------|
| [01_amr_tasks.md](./01_amr_tasks.md) | عمرو وليد — Team Lead, Data Engineer & Frontend |
| [02_yassin_tasks.md](./02_yassin_tasks.md) | ياسين محمود — DataOps, Spark & ML (FinBERT) |
| [03_mostafa_tasks.md](./03_mostafa_tasks.md) | مصطفى مطر — Backend, Alerts & Docker Environment |
| [05_karim_tasks.md](./05_karim_tasks.md) | كريم — Analytics Engineer (dbt) |
| [06_milestone3_plan.md](./06_milestone3_plan.md) | خطة عمل المرحلة الثالثة (Milestone 3) المجمعة |

---

## 🔗 تدفق البيانات (Data Flow)

```
Binance API ──────────────────────────────────────────┐
CoinGecko API ─────────────────────────────────────── ┤
NewsAPI ────────────────────────────────────────────── ┤─► Kafka Topics
RSS Feeds (CoinTelegraph, NewsBTC) ─────────────────── ┘
                                                        │
                                                        ▼
                                              Spark Structured Streaming
                                                        │
                                                        ▼
                                              Bronze Layer (ADLS Gen2) ✅
                                              /bronze/prices/ | /news/ | /social/ | /historical/
                                                        │
                                                        ▼
                                              Silver Layer (Spark Batch) ✅
                                              /silver/prices/ | /news/ | /social/ | /historical/
                                                        │
                                                        ▼
                                              Gold Layer (dbt models → Supabase) ✅
                                              /gold/daily_summary/ | /sentiment/ | /latest_prices/
                                                        │
                                                        ▼
                                              FastAPI Backend (→ Supabase Cloud) ✅
                                              /api/v1/coins/ | /market/sentiment/ | /alerts/
                                                        │
                                                        ▼
                                              Frontend Dashboard (Next.js 16) ✅
```

---

## ☁️ البنية التحتية على Azure

| المورد | الاسم | المستخدم |
|--------|-------|----------|
| Resource Group | rg-cryptopulse-dev | الكل |
| Storage Account (ADLS Gen2) | stcryptopulsedev2 | الكل |
| Container | datalake | الكل |
| Service Principal | sp-cryptopulse | عمرو (يوفره للفريق) |

---

## 🐳 خدمات Docker

| الخدمة | Port | الوصف |
|--------|------|--------|
| zookeeper | 2181 | إدارة Kafka |
| kafka | 9092 | Message Broker |
| kafka-ui | 8080 | واجهة مراقبة Kafka |
| postgres | 5432 | قاعدة بيانات Airflow (محلي) — Backend يستخدم Supabase Cloud |
| airflow-webserver | 8081 | واجهة Airflow (صورة مخصصة + Docker CLI) |
| airflow-scheduler | — | Scheduler — ينفذ Spark jobs عبر `docker exec` |
| spark-master | 7077 / 8082 | Spark Master Node |
| spark-worker | 8083 | Spark Worker Node |
| streaming-bronze-prices | — | Kafka → Bronze/prices (مستمر 24/7) |
| streaming-bronze-news | — | Kafka → Bronze/news (مستمر 24/7) |
| streaming-bronze-social | — | Kafka → Bronze/social (مستمر 24/7) |
| streaming-silver-prices | — | Bronze → Silver/prices (مستمر 24/7) |
| backend | 8000 | FastAPI Application (→ Supabase Cloud) |
| alert-worker | — | خدمة التنبيهات في الخلفية ✅ |
| frontend | 3000 | واجهة Next.js 16 (Dashboard) ✅ |
