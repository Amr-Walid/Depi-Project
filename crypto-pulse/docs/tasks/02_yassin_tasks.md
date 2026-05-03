# Yassin Mahmoud — DataOps & Spark Engineer

**Role:** Data Processing Engineer  
**Core Responsibility:** Transform raw data from Kafka into clean, structured data in Azure Data Lake — across both real-time streaming and historical batch paths.

---

## Milestone 1 — Bronze Layer Pipeline

**Goal:** Build the entry point for all project data. Every message arriving from Kafka must be captured reliably in Azure as-is.

---

### Task 1.1 — Streaming Consumer (Bronze) [COMPLETE]

**Files:**
- `processing/spark_jobs/bronze_consumer.py`
- `spark-apps/bronze_consumer.py` (copy mounted into Docker)

**What was done:**
- [x] Reads from Kafka topic `crypto.realtime.prices` via `spark.readStream`
- [x] Configures SparkSession with Azure ADLS Gen2 OAuth2 authentication using a Service Principal (`ClientCredsTokenProvider`)
- [x] Casts binary Kafka value to String and preserves all Kafka metadata columns: `kafka_key`, `raw_value`, `topic`, `partition`, `offset`, `kafka_timestamp`, `ingested_at`
- [x] Writes to ADLS path `bronze/prices` in **Delta Lake** format
- [x] Checkpoint stored at `checkpoints/bronze/prices`
- [x] Trigger: every 30 seconds
- [x] Stream uses `failOnDataLoss=false` to handle Kafka offset gaps after restarts

---

### Task 1.2 — Historical Loader (Batch) [COMPLETE]

**File:** `processing/spark_jobs/historical_loader.py`

**What was done:**
- [x] Reads raw OHLCV JSON files from `data/historical/`
- [x] Parses the raw arrays, adds `symbol` and `ingested_at` columns
- [x] Writes to `bronze/historical` in Delta format using overwrite mode

---

### Task 1.3 — Airflow DAGs for Historical and Prices Pipelines [COMPLETE]

**Files:** 
- `dags/dag_historical_daily.py`
- `dags/dag_prices_frequent.py`

**What was done:**
- [x] Created `dag_historical_daily` running `@daily` for the historical batch workload.
- [x] Created `dag_prices_frequent` running every 5 minutes for micro-batch sync and dbt updates.
- [x] Replaced the old monolithic `etl_pipeline_dag.py` to prevent streaming tasks from blocking batch DAGs.
- [x] **Verified (May 2026):** DAGs successfully orchestrate Spark jobs via Docker socket on the `spark-master` container. ✅

---

## Milestone 2 — Silver Layer Pipeline

**Goal:** Transform the raw Bronze data into cleaned, typed, deduplicated, and partitioned data ready for analytics.

---

### Task 2.1 — Silver Prices Processor — Real-time Streaming [COMPLETE]

**File:** `processing/spark_jobs/silver_prices_processor.py`

**What was done:**
- [x] Reads the Bronze Delta table as a continuous stream (`spark.readStream.format("delta")`)
- [x] Parses `raw_value` JSON using a defined schema: `symbol`, `price`, `volume_24h`, `timestamp`, `source`
- [x] Converts Unix millisecond timestamp to UTC `TimestampType`
- [x] Applies Data Quality filters:
  - Removes rows with null `symbol`, null `price`, null `event_time`
  - Removes rows where `price <= 0` or `volume_24h <= 0`
  - Drops duplicates on `(symbol, event_time)`
- [x] Adds partition columns: `year`, `month`, `day`, `hour`
- [x] Uses `foreachBatch` to apply a **Delta MERGE (Upsert)** per micro-batch:
  - If a row with matching `(symbol, event_time)` already exists → UPDATE
  - If new → INSERT
- [x] Creates the Silver Delta table automatically on the first batch if it does not exist
- [x] Trigger: every 30 seconds
- [x] Checkpoint: `checkpoints/silver/prices`
- [x] Validated end-to-end: data flows from Binance → Kafka → Bronze → Silver on Azure ADLS Gen2

---

### Task 2.2 — Silver Historical Processor — Batch [COMPLETE]

**File:** `processing/spark_jobs/silver_historical_processor.py`

**What was done:**
- [x] Reads from `bronze/historical` (Delta batch read)
- [x] Applies type casting, null filtering, and deduplication
- [x] Writes to `silver/historical` partitioned by symbol and date

---

### Task 2.3 — Delta Lake Upgrade [COMPLETE]

- [x] Both Bronze and Silver layers use Delta Lake format
- [x] SparkSession configured with `DeltaSparkSessionExtension` and `DeltaCatalog`
- [x] Delta JARs pre-installed in the custom Spark Docker image (`delta-spark_2.12:3.2.0`, `delta-storage:3.2.0`)

---

## Summary Table

| Task | Description | Status |
|------|-------------|--------|
| 1.1 | Bronze Consumer — Kafka to Delta Streaming | Complete |
| 1.2 | Historical Loader — JSON to Bronze (Batch) | Complete |
| 1.3 | Airflow DAGs — Decoupled Historical + Prices pipelines | Complete |
| 1.4 | Bronze News & Social Consumers — Kafka to Delta | Complete |
| 2.1 | Silver Prices Processor — Real-time Streaming + Delta MERGE | Complete |
| 2.2 | Silver Historical Processor — Batch | Complete |
| 2.3 | Delta Lake format on all layers | Complete |
| 2.4 | Silver News & Social Processors — Cleansing & formatting | Complete & Verified ✅ |

---

## Deliverables

**Milestone 1:**
- `processing/spark_jobs/bronze_consumer.py`
- `processing/spark_jobs/historical_loader.py`
- `processing/spark_jobs/bronze_news_consumer.py`
- `processing/spark_jobs/bronze_social_consumer.py`
- `dags/dag_historical_daily.py`
- `dags/dag_prices_frequent.py`
- `spark-apps/Dockerfile.spark`

**Milestone 2:**
- `processing/spark_jobs/silver_prices_processor.py` (Streaming + Delta MERGE)
- `processing/spark_jobs/silver_historical_processor.py` (Batch)
- `processing/spark_jobs/silver_news_processor.py`
- `processing/spark_jobs/silver_social_processor.py`

---

## Dependencies

| Depends on | From | Why |
|-----------|------|-----|
| Azure credentials | Amr | To authenticate with ADLS Gen2 |
| `data/historical/*.json` | Amr | To run historical_loader |
| Kafka running | Mostafa (Docker) | To run bronze_consumer |
| Silver Layer ready | Yassin (self) | Karim needs it for dbt models |

---

## Milestone 3 — FinBERT Sentiment Integration + Notebooks

**Goal:** دمج نموذج FinBERT داخل Spark لتحليل مشاعر الأخبار، وملء دفاتر التحليل (Notebooks) بالرسوم البيانية والاستنتاجات.

> **ملاحظة:** التفاصيل الكاملة لكل التاسكات موجودة في [06_milestone3_plan.md](./06_milestone3_plan.md)

---

### Task 3.1 — تجهيز بيئة FinBERT في Spark Docker Image [NOT STARTED]

**الملف:** `spark-apps/Dockerfile.spark`

- [ ] إضافة `transformers` و `torch` (أو `torch-cpu`) للـ Dockerfile
- [ ] إعادة بناء الـ Image: `docker compose build spark-master`
- [ ] اختبار إن المكتبات تعمل داخل الـ Container

### Task 3.2 — إنشاء Sentiment Processor Script [NOT STARTED]

**الملف الجديد:** `processing/spark_jobs/sentiment_processor.py`

- [ ] قراءة `silver.news` و `silver.social` من PostgreSQL
- [ ] تطبيق FinBERT كـ Spark UDF على عمود `title`
- [ ] إضافة أعمدة: `sentiment_score` (float, -1 to 1) و `sentiment_label` (string)
- [ ] كتابة النتيجة في `silver.news_sentiment` (mode=overwrite)
- [ ] إضافة `spark.stop()` في النهاية للتوافق مع Airflow

### Task 3.3 — إضافة جدول Sentiment في schema.sql [NOT STARTED]

**الملف:** `backend/app/models/schema.sql`

- [ ] إضافة `CREATE TABLE IF NOT EXISTS silver.news_sentiment` مع أعمدة sentiment_score و sentiment_label
- [ ] إضافة indexes على `published_at` و `sentiment_label`

### Task 3.4 — إضافة Sentiment Job للـ Airflow DAG [NOT STARTED]

**الملف:** `dags/dag_historical_daily.py`

- [ ] إضافة BashOperator `run_sentiment_analysis` يشغل `sentiment_processor.py` عبر `docker exec`
- [ ] وضعه بعد `sync_news_postgres` وقبل `run_dbt_gold`

### Task 3.5 — ملء Notebook التحليل الاستكشافي [NOT STARTED]

**الملف:** `notebooks/01-data-exploration.ipynb`

- [ ] قراءة بيانات الأسعار من PostgreSQL وعرض توزيعاتها
- [ ] Correlation Matrix بين العملات
- [ ] حجم التداول اليومي مع الوقت
- [ ] شرح Markdown لكل خلية

### Task 3.6 — ملء Notebook تدريب النموذج [NOT STARTED]

**الملف:** `notebooks/02-model-training.ipynb`

- [ ] شرح نموذج FinBERT وطريقة عمله
- [ ] عرض نتائج الـ Sentiment على عينة من الأخبار
- [ ] رسم العلاقة بين Sentiment Score وتغير السعر

---

| Task | Description | Status |
|------|-------------|--------|
| 3.1 | تجهيز بيئة FinBERT في Docker | Not started |
| 3.2 | إنشاء Sentiment Processor Script | Not started |
| 3.3 | إضافة جدول Sentiment في schema.sql | Not started |
| 3.4 | إضافة Sentiment Job للـ Airflow DAG | Not started |
| 3.5 | ملء Notebook التحليل الاستكشافي | Not started |
| 3.6 | ملء Notebook تدريب النموذج | Not started |
