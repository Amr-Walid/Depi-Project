# 🌟 كريم — Analytics Engineer (dbt & Gold Layer)

> **الدور:** مهندس التحليلات — محول البيانات النظيفة إلى رؤى تجارية  
> **المسؤولية الجوهرية:** بناء الطبقة الذهبية (Gold Layer) باستخدام dbt، وتصميم قاعدة البيانات

---

## 🏁 Milestone 1 — تأسيس البنية التحتية والمخطط (Foundations)

**الهدف:** إعداد قاعدة البيانات وتجهيز بيئة العمل لـ dbt لتكون جاهزة بمجرد توفر البيانات.

---

### ✅ Task 1.1 — تصميم مخطط قاعدة البيانات (PostgreSQL)

**الملف:** `backend/app/models/schema.sql`

**ما تم إنجازه:**
- [x] إنشاء جدول `users`:
  ```sql
  CREATE TABLE users (
      id SERIAL PRIMARY KEY,
      email VARCHAR(255) UNIQUE NOT NULL,
      password_hash VARCHAR(255) NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );
  ```
- [x] إنشاء جدول `watchlists` (قوائم المراقبة):
  ```sql
  CREATE TABLE watchlists (
      id SERIAL PRIMARY KEY,
      user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
      symbol VARCHAR(10) NOT NULL,
      added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );
  ```
- [x] إنشاء جدول `alerts` (تنبيهات الأسعار):
  ```sql
  CREATE TABLE alerts (
      id SERIAL PRIMARY KEY,
      user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
      symbol VARCHAR(10) NOT NULL,
      condition VARCHAR(50) NOT NULL,   -- 'above' | 'below'
      threshold DECIMAL(18, 8) NOT NULL,
      is_active BOOLEAN DEFAULT TRUE
  );
  ```
- [x] إنشاء جدول `portfolios` (المحافظ الاستثمارية):
  ```sql
  CREATE TABLE portfolios (
      id SERIAL PRIMARY KEY,
      user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
      symbol VARCHAR(10) NOT NULL,
      quantity DECIMAL(18, 8) NOT NULL,
      avg_buy_price DECIMAL(18, 8) NOT NULL
  );
  ```

**⚠️ ما تم إضافته:**
- [x] `refresh_tokens` جدول لتخزين JWT Refresh Tokens
- [x] `user_sessions` للتتبع (اختياري)
- [x] إضافة indexes على الأعمدة المستخدمة كثيرًا (مثل `user_id`, `symbol`)

---

### ✅ Task 1.2 — إعداد مشروع dbt

**الملف:** `processing/dbt/dbt_project.yml`

**ما تم إنجازه:**
- [x] ملء `dbt_project.yml` بالإعدادات الأساسية والـ materialization
- [x] إعداد هيكل المجلدات (staging, gold, models)
- [x] إضافة `dbt-spark` و `dbt-postgres` إلى `requirements.txt`
- [x] إنشاء ملف `.gitignore` خاص بـ dbt لاستثناء ملفات الـ target والـ packages


---

---

## 🚀 Milestone 2 — بناء النماذج، جودة البيانات، والتوثيق

**الهدف:** تحويل البيانات النظيفة في Silver Layer إلى جداول تحليلية (Gold) وضمان موثوقيتها وتوثيقها.

---

### ⏳ Task 2.1 — بناء نماذج Bronze (Staging)

**المجلد:** `processing/dbt/models/`

**ما يجب فعله:**
- [x] إنشاء `models/staging/` لقراءة البيانات الخام من Silver:
  ```
  processing/dbt/models/
  ├── staging/
  │   ├── stg_prices.sql        ← قراءة silver/prices
  │   ├── stg_news.sql          ← قراءة silver/news
  │   └── stg_social.sql        ← قراءة silver/social
  └── gold/
      └── ...
  ```
- [x] مثال `models/staging/stg_prices.sql`:
  ```sql
  {{ config(materialized='view') }}
  
  SELECT
      symbol,
      CAST(price AS DECIMAL(18, 8)) AS price,
      CAST(volume AS DECIMAL(18, 8)) AS volume,
      CAST(kafka_timestamp AS TIMESTAMP) AS event_time,
      ingested_at
  FROM {{ source('silver', 'prices') }}
  WHERE price IS NOT NULL
    AND price > 0
  ```
- [x] إنشاء `models/sources.yml` لتعريف مصادر البيانات (Silver Layer)
- [x] إنشاء ملفات الـ `.sql` لكل مصدر (prices, news, social)


---

### ⏳ Task 2.2 — بناء نماذج Gold (التحليلية)

**المجلد:** `processing/dbt/models/gold/`

**ما يجب فعله:**

**الجدول 1: `gold/coin_daily_summary.sql`**
- [x] إنشاء الهيكل الأولي للجدول (Placeholder)
- [x] كتابة المنطق الفعلي للحسابات بناءً على الـ Staging Models
  ```sql
  {{ config(materialized='table') }}
  
  SELECT
      symbol,
      DATE_TRUNC('day', event_time) AS trading_date,
      MIN(price)    AS day_low,
      MAX(price)    AS day_high,
      FIRST(price)  AS day_open,
      LAST(price)   AS day_close,
      SUM(volume)   AS total_volume,
      AVG(price)    AS avg_price,
      COUNT(*)      AS tick_count
  FROM {{ ref('stg_prices') }}
  GROUP BY symbol, DATE_TRUNC('day', event_time)
  ```

**الجدول 2: `gold/market_sentiment.sql`**
- [x] يجمع درجات المشاعر من الأخبار والـ Reddit:
  ```sql
  {{ config(materialized='table') }}
  
  SELECT
      DATE_TRUNC('hour', published_at) AS sentiment_hour,
      AVG(sentiment_score) AS avg_sentiment,
      COUNT(*) AS article_count,
      SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) AS positive_count,
      SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) AS negative_count
  FROM {{ ref('stg_news') }}
  GROUP BY DATE_TRUNC('hour', published_at)
  ```

**الجدول 3: `gold/coin_performance_ranking.sql`** (اختياري)
- [ ] ترتيب العملات حسب الأداء اليومي والأسبوعي

---

### ❌ Task 2.3 — كتابة اختبارات جودة البيانات

**المجلد:** `processing/dbt/tests/`

**ما يجب فعله:**
- [x] إنشاء `tests/schema.yml` (أو `gold/schema.yml`) لتعريف اختبارات تلقائية:
  ```yaml
  version: 2
  models:
    - name: coin_daily_summary
      columns:
        - name: symbol
          tests:
            - not_null
            - accepted_values:
                values: ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', ...]
        - name: day_close
          tests:
            - not_null
            - dbt_utils.expression_is_true:
                expression: "day_close > 0"
        - name: trading_date
          tests:
            - not_null
            - unique
  ```
- [x] إضافة اختبارات مخصصة (singular tests):
  - [x] التأكد من أن `day_low <= day_high` دائمًا
  - [ ] التأكد من أن `total_volume > 0`
  - [ ] التأكد من عدم وجود تكرارات في البيانات اليومية

---

### ❌ Task 2.4 — توثيق النماذج

**ما يجب فعله:**
- [x] إضافة وصف لكل نموذج في `schema.yml`:
  ```yaml
  models:
    - name: coin_daily_summary
      description: |
        جدول يحتوي على ملخص يومي لكل عملة رقمية.
        يشمل: فتح، إغلاق، أعلى، أدنى سعر، وحجم التداول.
      columns:
        - name: symbol
          description: "رمز العملة مثل BTCUSDT"
        - name: day_close
          description: "سعر الإغلاق في نهاية اليوم"
  ```
- [ ] تشغيل `dbt docs generate` لإنشاء توثيق تفاعلي

---

### ❌ Task 2.5 — تشغيل dbt مع Airflow

**بالتنسيق مع ياسين:**
- [ ] إضافة Task في `dags/etl_pipeline_dag.py` لتشغيل dbt:
  ```python
  from airflow.operators.bash import BashOperator
  
  run_dbt = BashOperator(
      task_id='run_dbt_gold_models',
      bash_command='cd /opt/dbt && dbt run --models gold.*',
  )
  
  # التسلسل: Bronze → Silver → dbt Gold
  bronze_task >> silver_task >> run_dbt
  ```

---

## 📋 ملخص الحالة

| Task | الوصف | الحالة |
|------|--------|--------|
| 1.1 | schema.sql (PostgreSQL tables) | ✅ مكتمل |
| 1.2 | إعداد dbt_project.yml | ✅ مكتمل |
| 2.1 | Staging Models (stg_prices, stg_news) | ✅ مكتمل |
| 2.2 | Gold Models (daily_summary, sentiment) | ✅ مكتمل |
| 2.3 | اختبارات جودة البيانات | ✅ مكتمل |
| 2.4 | توثيق النماذج | ⏳ قيد التنفيذ |
| 2.5 | تكامل dbt مع Airflow DAG | ❌ لم يبدأ |

---

## 📂 ما يجب رفعه على GitHub (Deliverables)

Milestone 1 (Complete):
- `backend/app/models/schema.sql` ✅
- `processing/dbt/dbt_project.yml` ✅
- `processing/dbt/.gitignore` ✅

Milestone 2 (In Progress):
- `processing/dbt/models/staging/sources.yml` ✅
- `processing/dbt/models/gold/daily_market_summary.sql` ✅
- `processing/dbt/models/staging/stg_prices.sql` ✅
- `processing/dbt/models/staging/stg_news.sql` ✅
- `processing/dbt/models/staging/stg_social.sql` ✅
- `processing/dbt/models/gold/market_sentiment.sql` ✅
- `processing/dbt/models/gold/schema.yml` ✅
- `processing/dbt/tests/assert_low_price_less_than_high_price.sql` ✅
- تحديثات على `dags/etl_pipeline_dag.py`

**❌ لا ترفع أبدًا:**
- `profiles.yml` (يحتوي credentials)
- `dbt_packages/` (مثل node_modules في npm)
- `target/` (نتائج التشغيل المحلية)

---

## 🔧 التبعيات والاعتمادات

| يعتمد على | من | لماذا |
|-----------|-----|--------|
| Silver Layer جاهز | ياسين | كريم لا يستطيع البدء بدون بيانات Silver |
| Sentiment scores | أحمد | مطلوب لبناء `gold/market_sentiment.sql` |
| Gold Layer جاهز | كريم نفسه | مصطفى يحتاجها لبناء Data Endpoints في الـ API |
| Azure credentials | عمرو | للاتصال بـ ADLS Gen2 من dbt |

---

## 📚 مصادر مفيدة

| المورد | الرابط |
|--------|--------|
| dbt Documentation | https://docs.getdbt.com |
| dbt-spark Adapter | https://docs.getdbt.com/docs/core/connect-data-platform/spark-setup |
| dbt Best Practices | https://docs.getdbt.com/guides/best-practices |
| Medallion Architecture | https://www.databricks.com/glossary/medallion-architecture |
