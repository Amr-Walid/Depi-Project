# 🏗️ CryptoPulse — هيكل المشروع الكامل

> **آخر تحديث:** مايو 2026  
> **الفريق:** عمرو (Lead) · ياسين (Spark) · مصطفى (Backend/Docker) · أحمد (ML/Analyst) · كريم (dbt/Analytics)

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
│   │   ├── 📄 producer_news.py         ← أخبار العملات من NewsAPI [أحمد/عمرو] ✅
│   │   └── 📄 producer_social_rss.py   ← مقالات رأي من RSS Feeds [أحمد/عمرو] ✅
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
│   │   ├── 📄 historical_loader.py         ← تحميل البيانات التاريخية → Bronze [ياسين] ✅
│   │   ├── 📄 sync_historical_pg.py        ← Sync Historical ADLS → Postgres [عمرو] ✅
│   │   ├── 📄 sync_prices_pg.py            ← Sync Prices ADLS → Postgres [عمرو] ✅
│   │   ├── 📄 sync_news_pg.py              ← Sync News ADLS → Postgres [عمرو] ✅
│   │   └── 📄 sync_social_pg.py            ← Sync Social ADLS → Postgres [عمرو] ✅
│   └── 📁 dbt/                     ← تحويلات الطبقة الذهبية
│       ├── 📄 dbt_project.yml          ← إعدادات مشروع dbt [كريم] ✅
│       ├── 📁 models/                  ← نماذج dbt (Gold Layer) [كريم] ✅
│       └── 📁 tests/                   ← اختبارات جودة البيانات [كريم] ✅
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
│   └── 📁 tests/                   ← اختبارات API [مصطفى] ✅
│
├── 📁 spark-apps/                  ← بيئة Spark Docker
│   ├── 📄 Dockerfile.spark             ← صورة Docker لـ Spark [مصطفى] ✅
│   └── 📄 bronze_consumer.py           ← نسخة تشغيل داخل Container [ياسين] ✅
│
├── 📁 ml/                          ← نماذج الذكاء الاصطناعي [أحمد] ❌ (FinBERT لم يُطبق)
├── 📁 notebooks/
│   ├── 📄 01-data-exploration.ipynb    ← تحليل استكشافي للبيانات [أحمد] ❌
│   ├── 📄 02-model-training.ipynb      ← تدريب نماذج ML [أحمد] ❌
│   └── 📄 03-poc-dashboard.ipynb       ← لوحة معلومات تجريبية [أحمد] ❌
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
├── 📁 frontend/                    ← واجهة المستخدم (مرحلة لاحقة) ❌
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
| [01_amr_tasks.md](./01_amr_tasks.md) | عمرو وليد — Team Lead & Lead Data Engineer |
| [02_yassin_tasks.md](./02_yassin_tasks.md) | ياسين محمود — DataOps & Spark Engineer |
| [03_mostafa_tasks.md](./03_mostafa_tasks.md) | مصطفى مطر — Backend & Docker Environment |
| [04_ahmed_tasks.md](./04_ahmed_tasks.md) | أحمد أيمن — Data Analyst & ML Engineer |
| [05_karim_tasks.md](./05_karim_tasks.md) | كريم — Analytics Engineer (dbt) |

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
                                              Gold Layer (dbt models) ✅
                                              /gold/daily_summary/ | /sentiment/ | /latest_prices/
                                                        │
                                                        ▼
                                              FastAPI Backend ✅
                                              /api/v1/coins/ | /auth/ | /prices/
                                                        │
                                                        ▼
                                              Frontend Dashboard ❌
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
| postgres | 5432 | قاعدة بيانات Airflow + Backend |
| airflow-webserver | 8081 | واجهة Airflow (صورة مخصصة + Docker CLI) |
| airflow-scheduler | — | Scheduler — ينفذ Spark jobs عبر `docker exec` |
| spark-master | 7077 / 8082 | Spark Master Node |
| spark-worker | 8083 | Spark Worker Node |
| streaming-bronze-prices | — | Kafka → Bronze/prices (مستمر 24/7) |
| streaming-bronze-news | — | Kafka → Bronze/news (مستمر 24/7) |
| streaming-bronze-social | — | Kafka → Bronze/social (مستمر 24/7) |
| streaming-silver-prices | — | Bronze → Silver/prices (مستمر 24/7) |
| backend | 8000 | FastAPI Application |
