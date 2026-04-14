# ⚡ ياسين محمود — DataOps & Spark Engineer

> **الدور:** مهندس معالجة البيانات — العمود الفقري لخط الأنابيب  
> **المسؤولية الجوهرية:** تحويل البيانات الخام من Kafka إلى بيانات نظيفة ومنظمة في Azure Data Lake

---

## 🏁 Milestone 1 — بناء خط أنابيب الطبقة البرونزية (Bronze Layer)

**الهدف:** إنشاء "بوابة الدخول" لجميع بيانات المشروع، والتأكد من أن كل معلومة تصل من Kafka يتم تخزينها بشكل خام وموثوق في Azure.

---

### ✅ Task 1.1 — كتابة مستهلك البث المباشر (Streaming Consumer)

**الملف:** `processing/spark_jobs/bronze_consumer.py`  
*(نسخة للتشغيل في docker: `spark-apps/bronze_consumer.py`)*

**ما تم إنجازه:**
- [x] الاتصال بـ Kafka وقراءة topic: `crypto.realtime.prices`
- [x] إعداد SparkSession مع Azure ADLS Gen2 عبر OAuth2 / Service Principal
  - تكوين `fs.azure.account.auth.type` بـ OAuth
  - تكوين `ClientCredsTokenProvider`
  - ربط `client_id`, `client_secret`, `tenant_id`
- [x] تحويل الـ Binary Kafka value إلى STRING مع الحفاظ على الـ metadata:
  - `kafka_key`, `raw_value`, `topic`, `partition`, `offset`, `kafka_timestamp`, `ingested_at`
- [x] الكتابة إلى Bronze Layer بتنسيق **Parquet**:
  - المسار: `abfss://datalake@stcryptopulsedev.dfs.core.windows.net/bronze/prices`
  - Checkpoint: `abfss://...dfs.core.windows.net/checkpoints/bronze/prices`
  - trigger كل 30 ثانية
- [x] إدارة نقاط التفتيش (Checkpointing) لضمان عدم فقدان رسائل عند إعادة التشغيل
- [x] معالجة الأخطاء (KeyboardInterrupt, Exception) وإيقاف Spark بشكل نظيف

**⚠️ ملاحظة مهمة:** النسخة الحالية تستخدم **Parquet** وليس **Delta Lake** — التحويل لـ Delta مطلوب في نسخة قادمة.

---

### ❌ Task 1.2 — كتابة محمل البيانات التاريخية (Historical Loader)

**الملف المطلوب إنشاؤه:** `processing/spark_jobs/historical_loader.py`

**ما يجب فعله:**
- [ ] قراءة ملفات JSON الخام من `data/historical/` (التي أنشأها `historical_fetcher.py`)
- [ ] تحليل بنية الـ JSON (مصفوفة OHLCV من Binance):
  ```python
  # كل سجل: [open_time, open, high, low, close, volume, close_time, ...]
  ```
- [ ] تحويلها إلى DataFrame منظم مع أعمدة واضحة
- [ ] الكتابة إلى Bronze Layer كـ **Batch Job** (مرة واحدة وليس streaming):
  - المسار: `abfss://datalake@stcryptopulsedev.dfs.core.windows.net/bronze/historical`
  - التنسيق: Delta Lake (أو Parquet كبداية)
  - Partitioning: `year`, `month`, `day`
- [ ] استخدام `overwrite` mode لتجنب التكرار عند إعادة التشغيل

---

### ⏳ Task 1.3 — إنشاء DAG لتشغيل Historical Loader

**الملف:** `dags/etl_pipeline_dag.py` *(حاليًا فارغ)*

**ما يجب فعله:**
- [ ] إنشاء DAG أساسي في Airflow:
  ```python
  from airflow import DAG
  from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
  ```
- [ ] تشغيل `historical_loader.py` كـ SparkSubmitOperator
- [ ] إعداد schedule_interval مناسب (مثلاً `@once` للتحميل الأول)
- [ ] إضافة logging واضح لكل خطوة

---

## 🚀 Milestone 2 — بناء خط أنابيب الطبقة الفضية (Silver Layer)

**الهدف:** تحويل البيانات الخام وغير المتجانسة في طبقة Bronze إلى بيانات نظيفة، موحدة، وجاهزة للتحليل.

---

### ❌ Task 2.1 — كتابة معالج الطبقة الفضية (Silver Processor)

**الملف المطلوب:** `processing/spark_jobs/silver_processor.py` *(حاليًا فارغ)*

**ما يجب فعله:**
- [ ] قراءة البيانات من Bronze Layer:
  ```python
  spark.read.format("parquet").load("abfss://.../bronze/prices")
  ```
- [ ] تطبيق قواعد التنظيف:
  - [ ] **إزالة التكرارات:** `dropDuplicates(["kafka_key", "kafka_timestamp"])`
  - [ ] **معالجة القيم المفقودة:** `fillna()` أو حذف الصفوف الناقصة حسب الأعمدة الحرجة
  - [ ] **توحيد الـ Timestamps:** تحويل كل التواريخ إلى UTC
  - [ ] **تحليل JSON:** استخراج الأعمدة من `raw_value`:
    ```python
    from pyspark.sql.functions import from_json, col
    schema = StructType([...])  # تعريف schema لبيانات الأسعار
    df = df.withColumn("data", from_json(col("raw_value"), schema))
    ```
  - [ ] **توحيد أسماء الأعمدة:** `price` بدلاً من `p` أو `last_price`
- [ ] الكتابة إلى Silver Layer:
  - المسار: `abfss://datalake@stcryptopulsedev.dfs.core.windows.net/silver/prices`
  - التنسيق: **Delta Lake** (مطلوب لدعم Upserts)
  - Partitioning: `year`, `month`, `day`
  - Output Mode: `overwrite` أو `merge` (Delta UPSERT)

**مثال هيكل Silver:**
```
silver/
├── prices/
│   ├── year=2024/month=04/day=10/
│   └── ...
└── news/
    └── ...
```

---

### ❌ Task 2.2 — تحديث DAG للأتمتة الكاملة

**الملف:** `dags/etl_pipeline_dag.py`

**ما يجب فعله:**
- [ ] إضافة Task جديد لتشغيل `silver_processor.py`
- [ ] إنشاء **Dependency Chain**:
  ```python
  bronze_task >> silver_task  # Silver لا تبدأ إلا بعد نجاح Bronze
  ```
- [ ] تشغيل Silver بشكل دوري (مثلاً كل ساعة): `schedule_interval="@hourly"`
- [ ] إضافة **Email/Slack alert** عند فشل أي مهمة (اختياري)

---

### ❌ Task 2.3 — التحويل إلى Delta Lake (تحديث Bronze Consumer)

**الملف:** `processing/spark_jobs/bronze_consumer.py`

**ما يجب فعله:**
- [ ] إضافة Delta Lake packages إلى SparkSession:
  ```python
  "io.delta:delta-spark_2.12:3.1.0"
  ```
- [ ] تفعيل Delta extensions:
  ```python
  .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
  .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
  ```
- [ ] تغيير format من `"parquet"` إلى `"delta"`

---

## 📋 ملخص الحالة

| Task | الوصف | الحالة |
|------|--------|--------|
| 1.1 | Bronze Consumer (Streaming) | ✅ مكتمل (Parquet) |
| 1.2 | Historical Loader (Batch) | ❌ لم يبدأ |
| 1.3 | DAG — Historical Load | ⏳ ملف فارغ |
| 2.1 | Silver Processor (Cleaning) | ❌ ملف فارغ |
| 2.2 | DAG — Bronze >> Silver Chain | ❌ لم يبدأ |
| 2.3 | ترقية Bronze إلى Delta Format | ❌ لم يبدأ |

---

## 📂 ما يجب رفعه على GitHub (Deliverables)

**Milestone 1:**
- `processing/spark_jobs/bronze_consumer.py` ✅ (مرفوع)
- `processing/spark_jobs/historical_loader.py` ← **الأولوية الأولى الآن**
- `dags/etl_pipeline_dag.py` (نسخة أولى للـ historical)
- `spark-apps/Dockerfile.spark` ✅ (مرفوع)

**Milestone 2:**
- `processing/spark_jobs/silver_processor.py` ← **الأولوية الثانية**
- `dags/etl_pipeline_dag.py` (نسخة كاملة مع Bronze >> Silver)
- تحديثات على `requirements.txt` لإضافة `pyspark`, `delta-spark`

---

## 🔧 التبعيات والاعتمادات

| يعتمد على | من | لماذا |
|-----------|-----|--------|
| Azure credentials | عمرو | للاتصال بـ ADLS Gen2 |
| `data/historical/*.json` | عمرو | لتشغيل historical_loader |
| Kafka running | مصطفى | لتشغيل bronze_consumer |
| Silver Layer جاهز | ياسين | كريم يحتاجها لـ dbt |
