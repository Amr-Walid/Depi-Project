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
- [x] الكتابة إلى Bronze Layer بتنسيق **Delta Lake**:
  - المسار: `abfss://datalake@stcryptopulsedev.dfs.core.windows.net/bronze/prices`
  - Checkpoint: `abfss://...dfs.core.windows.net/checkpoints/bronze/prices`
  - trigger كل 30 ثانية

**🚀 تم ترقية التخزين إلى Delta Lake لضمان جودة البيانات.**

---

### ✅ Task 1.2 — كتابة محمل البيانات التاريخية (Historical Loader)

**الملف المطلوب إنشاؤه:** `processing/spark_jobs/historical_loader.py`

**ما يجب فعله:**
- [x] قراءة ملفات JSON الخام من `data/historical/`.
- [x] تحليل مصفوفة OHLCV وإضافة أعمدة `symbol` و `ingested_at`.
- [x] الكتابة إلى Bronze Layer بتنسيق **Delta Lake**.
- [x] استخدام `overwrite` mode لتجنب التكرار.

---

### ✅ Task 1.3 — إنشاء DAG لتشغيل Historical Loader

**الملف:** `dags/etl_pipeline_dag.py` *(حاليًا فارغ)*

**ما يجب فعله:**
- [x] إنشاء DAG شامل باسم `crypto_pulse_bronze_layer`.
- [x] تشغيل `historical_loader.py` عبر `BashOperator`.
- [x] إعداد الجدولة (Schedule) والـ Logging.

---

## 🚀 Milestone 2 — بناء خط أنابيب الطبقة الفضية (Silver Layer)

**الهدف:** تحويل البيانات الخام وغير المتجانسة في طبقة Bronze إلى بيانات نظيفة، موحدة، وجاهزة للتحليل.

---

### ✅ Task 2.1 — كتابة معالج الطبقة الفضية (Silver Processor)

**الملف:** `processing/spark_jobs/silver_processor.py`

**ما تم إنجازه:**
- [x] قراءة البيانات من Bronze Layer (Delta format):
  ```python
  spark.read.format("delta").load("abfss://.../bronze/prices")
  ```
- [x] تطبيق قواعد التنظيف الكاملة:
  - [x] **تحليل JSON:** استخراج الأعمدة باستخدام `from_json` مع Schema محدد
  - [x] **إزالة التكرارات:** `dropDuplicates(["symbol", "event_time"])`
  - [x] **فلترة DQ:** حذف الأسعار الصفر والسالبة والقيم الـ Null
  - [x] **توحيد الـ Timestamps:** تحويل Unix timestamp إلى UTC Timestamp
  - [x] **إضافة أعمدة Partitioning:** `year`, `month`, `day`
- [x] الكتابة إلى Silver Layer بـ **Delta MERGE (Upsert)**:
  - المسار: `abfss://datalake@stcryptopulsedev.dfs.core.windows.net/silver/prices`
  - Smart Merge: لو السجل موجود يُحدَّث، لو جديد يُضاف
  - Partitioning: `year`, `month`, `day`
- [x] تشغيل `OPTIMIZE` تلقائياً بعد الكتابة

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

### ✅ Task 2.2 — تحديث DAG للأتمتة الكاملة

**الملف:** `dags/etl_pipeline_dag.py`

**ما تم إنجازه:**
- [x] إضافة Task جديد لتشغيل `silver_processor.py`
- [x] إنشاء **Dependency Chain** الكاملة:
  ```python
  ingest_historical >> process_silver  # Silver لا تبدأ إلا بعد نجاح Bronze
  ```
- [x] تشغيل Silver بشكل دوري: `schedule_interval="@daily"`
- [ ] إضافة **Email/Slack alert** عند فشل أي مهمة (اختياري)

---

### ✅ Task 2.3 — التحويل إلى Delta Lake (مكتمل)

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
| 1.1 | Bronze Consumer (Streaming) | ✅ مكتمل (Delta) |
| 1.2 | Historical Loader (Batch) | ✅ مكتمل |
| 1.3 | DAG — Historical Load | ✅ مكتمل |
| 2.1 | Silver Processor (Cleaning + Delta MERGE) | ✅ مكتمل |
| 2.2 | DAG — Bronze >> Silver Chain | ✅ مكتمل |
| 2.3 | ترقية Bronze إلى Delta Format | ✅ مكتمل |

---

## 📂 ما يجب رفعه على GitHub (Deliverables)

**Milestone 1:**
- `processing/spark_jobs/bronze_consumer.py` ✅ (مرفوع)
- `processing/spark_jobs/historical_loader.py` ✅ (مرفوع)
- `dags/etl_pipeline_dag.py` ✅ (مرفوع)
- `spark-apps/Dockerfile.spark` ✅ (مرفوع)

**Milestone 2:**
- `processing/spark_jobs/silver_processor.py` ✅ (مرفوع - Delta MERGE كامل)
- `dags/etl_pipeline_dag.py` (نسخة كاملة مع Bronze >> Silver) ✅

---

## 🔧 التبعيات والاعتمادات

| يعتمد على | من | لماذا |
|-----------|-----|--------|
| Azure credentials | عمرو | للاتصال بـ ADLS Gen2 |
| `data/historical/*.json` | عمرو | لتشغيل historical_loader |
| Kafka running | مصطفى | لتشغيل bronze_consumer |
| Silver Layer جاهز | ياسين | كريم يحتاجها لـ dbt |
