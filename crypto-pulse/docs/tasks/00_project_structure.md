# 🏗️ CryptoPulse — هيكل المشروع الكامل

> **آخر تحديث:** أبريل 2026  
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
│   │   └── 📄 producer_news.py         ← أخبار العملات من NewsAPI [أحمد] ⏳
│   └── 📁 historical/
│       └── 📄 historical_fetcher.py    ← جلب بيانات تاريخية من Binance [عمرو] ✅
│
├── 📁 processing/
│   ├── 📁 spark_jobs/
│   │   ├── 📄 bronze_consumer.py       ← Spark Streaming → Bronze Layer [ياسين] ✅
│   │   ├── 📄 silver_processor.py      ← Spark Batch → Silver Layer [ياسين] ⏳
│   │   └── 📄 historical_loader.py     ← تحميل البيانات التاريخية → Bronze [ياسين] ✅
│   └── 📁 dbt/                     ← تحويلات الطبقة الذهبية
│       ├── 📄 dbt_project.yml          ← إعدادات مشروع dbt [كريم] ✅
│       ├── 📁 models/                  ← نماذج dbt (Gold Layer) [كريم] ⏳
│       └── 📁 tests/                   ← اختبارات جودة البيانات [كريم] ❌
│
├── 📁 dags/
│   └── 📄 etl_pipeline_dag.py      ← DAG الرئيسي لـ Airflow [ياسين] ✅
│
├── 📁 backend/
│   ├── 📁 app/
│   │   ├── 📄 main.py                  ← نقطة دخول FastAPI [مصطفى] ✅
│   │   ├── 📄 __init__.py
│   │   ├── 📁 routers/                 ← API Endpoints [مصطفى] ❌
│   │   ├── 📁 models/
│   │   │   └── 📄 schema.sql           ← مخطط قاعدة البيانات [كريم] ✅
│   │   └── 📁 services/                ← منطق الأعمال [مصطفى] ❌
│   └── 📁 tests/                   ← اختبارات API [مصطفى] ❌
│
├── 📁 spark-apps/                  ← بيئة Spark Docker
│   ├── 📄 Dockerfile.spark             ← صورة Docker لـ Spark [مصطفى] ✅
│   └── 📄 bronze_consumer.py           ← نسخة تشغيل داخل Container [ياسين] ✅
│
├── 📁 ml/                          ← نماذج الذكاء الاصطناعي [أحمد] ❌
├── 📁 notebooks/
│   ├── 📄 01-data-exploration.ipynb    ← تحليل استكشافي للبيانات [أحمد] ⏳
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
Reddit API ────────────────────────────────────────── ┘
                                                        │
                                                        ▼
                                              Spark Structured Streaming
                                                        │
                                                        ▼
                                              Bronze Layer (ADLS Gen2)
                                              /bronze/prices/ | /news/ | /social/
                                                        │
                                                        ▼
                                              Silver Layer (Spark Batch)
                                              /silver/prices/ | /news/ | /social/
                                                        │
                                                        ▼
                                              Gold Layer (dbt models)
                                              /gold/coin_summary/ | /sentiment/
                                                        │
                                                        ▼
                                              FastAPI Backend
                                              /api/v1/coins/ | /auth/ | /prices/
                                                        │
                                                        ▼
                                              Frontend Dashboard
```

---

## ☁️ البنية التحتية على Azure

| المورد | الاسم | المستخدم |
|--------|-------|----------|
| Resource Group | rg-cryptopulse-dev | الكل |
| Storage Account (ADLS Gen2) | stcryptopulsedev | الكل |
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
| airflow-webserver | 8081 | واجهة Airflow |
| airflow-scheduler | — | Scheduler لتشغيل DAGs |
| spark-master | 7077 / 8082 | Spark Master Node |
| spark-worker | 8083 | Spark Worker Node |
| backend | 8000 | FastAPI Application |
