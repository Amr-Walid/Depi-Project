# Milestone 3 — The Final Product 🚀

> **آخر تحديث:** مايو 2026
> **الفريق:** عمرو (Lead/Frontend) · ياسين (ML/Spark) · مصطفى (Backend) · كريم (dbt/Analytics)
> **هدف المايلستون:** تحويل الـ Pipeline الجاهز إلى منتج نهائي متكامل بواجهة رسومية وذكاء اصطناعي

---

## 📊 تحليل الفجوات (Gap Analysis) — بناءً على مراجعة الكود بالكامل

بعد فحص **كل ملف** في البروجكت (13 Spark job, 5 API routers, 5 dbt Gold models, docker-compose.yml, schema.sql, الـ DAGs)، تم اكتشاف التالي:

### فجوات مكتشفة:

| # | الفجوة | الملف المتأثر | الخطورة |
|---|--------|--------------|---------|
| 1 | `data_service.py` لا يزال يحتوي على `MOCK_BASE_PRICES` (سطر 38-59) و `import random` (سطر 1) — كود قديم غير مستخدم | `backend/app/services/data_service.py` | منخفضة |
| 2 | `market_sentiment.sql` يستخدم keywords بدائية (`bull`, `bear`, `crash`) بدلاً من FinBERT scores حقيقية | `processing/dbt/models/gold/market_sentiment.sql` | عالية |
| 3 | مجلد `frontend/` فارغ — يحتوي فقط على `.gitkeep` | `frontend/` | عالية |
| 4 | مجلد `ml/` فارغ — يحتوي فقط على `.gitkeep` | `ml/` | عالية |
| 5 | الـ Notebooks موجودة لكنها **فارغة أو بدائية جداً** | `notebooks/*.ipynb` | متوسطة |
| 6 | الـ Alert CRUD API موجود لكن **لا يوجد محرك يراقب الأسعار** | `backend/app/routers/alerts.py` | متوسطة |
| 7 | لا يوجد endpoint لجلب الـ Sentiment في الـ API | `backend/app/routers/coins.py` | متوسطة |
| 8 | `schema.sql` لا يحتوي على جدول لـ sentiment scores | `backend/app/models/schema.sql` | متوسطة |
| 9 | `docker-compose.yml` لا يحتوي على service للـ Frontend | `docker-compose.yml` | عالية |

---

## 🔗 ترتيب التنفيذ (Dependency Chain)

```
المرحلة A (يبدأوا في نفس الوقت):
├── عمرو: Frontend Setup (Template + Cleaning)
├── ياسين: FinBERT Spark Script
├── كريم: dbt sentiment models جديدة
└── مصطفى: Alert Worker + Sentiment Endpoint

المرحلة B (بعد ما ياسين وكريم يخلصوا):
├── مصطفى: يربط الـ Sentiment Endpoint بالـ Gold tables الجديدة
└── عمرو: يربط الـ Frontend بالـ API endpoints

المرحلة C (بعد ما الكل يخلص):
└── عمرو: Cloud Deployment على Azure + Final Testing
```

---

## 👤 عمرو وليد — Frontend + Deployment

### Task 3.1 — اختيار وتنظيف قالب Next.js [NOT STARTED]

**المجلد:** `frontend/`

- [ ] البحث عن قالب Crypto Dashboard مناسب (مفتوح المصدر) من GitHub أو Vercel Templates
- [ ] تشغيل القالب محلياً والتأكد إنه شغال: `npx create-next-app@latest ./frontend --use-npm`
- [ ] إزالة الصفحات والمكونات غير المطلوبة من القالب
- [ ] إعداد هيكل المجلدات:
  ```
  frontend/
  ├── app/              ← Next.js App Router
  │   ├── layout.tsx
  │   ├── page.tsx      ← الصفحة الرئيسية (Dashboard)
  │   ├── login/
  │   │   └── page.tsx  ← شاشة تسجيل الدخول
  │   └── coin/
  │       └── [symbol]/
  │           └── page.tsx  ← صفحة تفاصيل عملة
  ├── components/
  │   ├── Navbar.tsx
  │   ├── CoinTable.tsx
  │   ├── PriceChart.tsx
  │   ├── MarketOverview.tsx
  │   └── SentimentGauge.tsx
  ├── lib/
  │   └── api.ts        ← Helper functions للتعامل مع الـ Backend API
  ├── Dockerfile
  └── package.json
  ```

---

### Task 3.2 — شاشة تسجيل الدخول (Login Page) [NOT STARTED]

**الملف:** `frontend/app/login/page.tsx`

- [ ] إنشاء فورم بسيط (Email + Password)
- [ ] ربط الفورم بالـ API: `POST /api/v1/auth/login`
- [ ] تخزين الـ `access_token` و `refresh_token` في `localStorage` أو `cookies`
- [ ] إضافة زر "Create Account" يستدعي: `POST /api/v1/auth/signup`
- [ ] Redirect للـ Dashboard بعد تسجيل الدخول الناجح

---

### Task 3.3 — لوحة التحكم الرئيسية (Dashboard) [NOT STARTED]

**الملف:** `frontend/app/page.tsx`

- [ ] عرض بطاقات (Cards) في الأعلى:
  - Total Market Cap (من `GET /api/v1/market/overview` → `total_market_cap`)
  - Total Volume 24h (من نفس الـ endpoint → `total_volume_24h`)
  - BTC Dominance (من نفس الـ endpoint → `btc_dominance`)
  - Active Coins (من نفس الـ endpoint → `active_coins`)
- [ ] جدول عملات تفاعلي (من `GET /api/v1/coins`):
  - الأعمدة: Symbol, Name, Price, 24h Change%, Volume
  - كل صف يكون clickable → يوديك لـ `/coin/BTCUSDT`
- [ ] عرض Top 5 Gainers و Top 5 Losers (من `market/overview` → `top_gainers`, `top_losers`)
- [ ] مؤشر Sentiment Gauge (من `GET /api/v1/market/sentiment` — Endpoint جديد يبنيه مصطفى)

---

### Task 3.4 — صفحة تفاصيل العملة (Coin Detail Page) [NOT STARTED]

**الملف:** `frontend/app/coin/[symbol]/page.tsx`

- [ ] رسم بياني (Chart) يعرض أسعار الـ OHLCV:
  - مصدر البيانات: `GET /api/v1/coins/BTCUSDT/prices?days=30`
  - مكتبة الرسم: **Recharts** أو **Lightweight Charts** (TradingView)
- [ ] جدول يعرض الـ Daily Summary (Open, High, Low, Close, Volume)
- [ ] أزرار لتغيير الفترة الزمنية: 7 أيام / 30 يوم / 90 يوم / سنة

---

### Task 3.5 — إضافة Frontend للـ Docker Compose [NOT STARTED]

**الملف:** `docker-compose.yml`

- [ ] إنشاء `frontend/Dockerfile`:
  ```dockerfile
  FROM node:18-alpine
  WORKDIR /app
  COPY package*.json ./
  RUN npm install
  COPY . .
  RUN npm run build
  CMD ["npm", "start"]
  ```
- [ ] إضافة service جديدة في `docker-compose.yml`:
  ```yaml
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
    networks:
      - crypto-net
  ```

---

### Task 3.6 — النشر على Azure (Cloud Deployment) [NOT STARTED]

- [ ] إنشاء Azure VM (Ubuntu 22.04, Standard_B2s)
- [ ] تثبيت Docker و Docker Compose على الـ VM
- [ ] نسخ `.env` و `docker-compose.yml` إلى الـ VM
- [ ] `docker compose up -d --build` على الـ VM
- [ ] فتح البورتات في Azure NSG:
  - Port 3000 (Frontend)
  - Port 8000 (API)
  - Port 8081 (Airflow — اختياري)
- [ ] اختبار الوصول من المتصفح: `http://<VM-IP>:3000`

---

## 👤 ياسين محمود — FinBERT + Spark Integration

### Task 3.1 — تجهيز بيئة FinBERT في Spark Docker Image [NOT STARTED]

**الملف:** `spark-apps/Dockerfile.spark`

- [ ] إضافة مكتبات Python المطلوبة للـ Image:
  ```dockerfile
  RUN pip install transformers torch --no-cache-dir
  ```
- [ ] إعادة بناء الـ Image: `docker compose build spark-master`
- [ ] اختبار إن المكتبات موجودة:
  ```bash
  docker exec spark-master python -c "from transformers import pipeline; print('OK')"
  ```

> **ملاحظة:** مكتبة `torch` كبيرة (~2GB). لو الجهاز ضعيف، ممكن نستخدم `torch-cpu` بدلاً منها.

---

### Task 3.2 — إنشاء Sentiment Processor Script [NOT STARTED]

**الملف:** `processing/spark_jobs/sentiment_processor.py`

هذا السكريبت يقرأ من `silver.news` و `silver.social` في PostgreSQL، يمرر العناوين على FinBERT، ويكتب النتيجة.

- [ ] إنشاء الملف `processing/spark_jobs/sentiment_processor.py`
- [ ] قراءة البيانات من PostgreSQL:
  ```python
  news_df = spark.read.jdbc(url=jdbc_url, table="silver.news", properties=jdbc_properties)
  social_df = spark.read.jdbc(url=jdbc_url, table="silver.social", properties=jdbc_properties)
  ```
- [ ] تطبيق FinBERT كـ UDF:
  ```python
  from transformers import pipeline
  from pyspark.sql.functions import udf
  from pyspark.sql.types import FloatType, StringType

  sentiment_model = pipeline("text-classification", model="ProsusAI/finbert")

  @udf(returnType=FloatType())
  def get_sentiment_score(text):
      if not text or len(text.strip()) == 0:
          return 0.0
      result = sentiment_model(text[:512])
      label = result[0]['label']
      score = result[0]['score']
      if label == 'positive':
          return score
      elif label == 'negative':
          return -score
      return 0.0

  @udf(returnType=StringType())
  def get_sentiment_label(text):
      if not text or len(text.strip()) == 0:
          return 'neutral'
      result = sentiment_model(text[:512])
      return result[0]['label']
  ```
- [ ] إضافة الأعمدة الجديدة:
  ```python
  enriched_news = news_df.withColumn("sentiment_score", get_sentiment_score("title")) \
                         .withColumn("sentiment_label", get_sentiment_label("title"))
  ```
- [ ] كتابة النتيجة في جدول جديد في PostgreSQL:
  ```python
  enriched_news.write.jdbc(url=jdbc_url, table="silver.news_sentiment", mode="overwrite", properties=jdbc_properties)
  ```

---

### Task 3.3 — إضافة جدول Sentiment في قاعدة البيانات [NOT STARTED]

**الملف:** `backend/app/models/schema.sql`

- [ ] إضافة الجدول التالي (بالتنسيق مع كريم):
  ```sql
  CREATE TABLE IF NOT EXISTS silver.news_sentiment (
      source VARCHAR(255),
      title TEXT,
      url TEXT,
      published_at TIMESTAMP,
      sentiment_score DECIMAL(5, 4),   -- من -1.0 إلى 1.0
      sentiment_label VARCHAR(20),      -- positive / negative / neutral
      ingested_at TIMESTAMP DEFAULT NOW()
  );

  CREATE INDEX idx_news_sentiment_date ON silver.news_sentiment(published_at);
  CREATE INDEX idx_news_sentiment_label ON silver.news_sentiment(sentiment_label);
  ```

---

### Task 3.4 — إضافة Sentiment Job للـ Airflow DAG [NOT STARTED]

**الملف:** `dags/dag_historical_daily.py`

- [ ] إضافة تاسك جديد بعد `sync_news_to_postgres`:
  ```python
  run_sentiment = BashOperator(
      task_id='run_sentiment_analysis',
      bash_command=(
          'docker exec spark-master '
          '/opt/spark/bin/spark-submit '
          '--conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension '
          '--conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog '
          '/opt/spark/jobs/sentiment_processor.py'
      ),
  )
  ```
- [ ] تحديث الـ Dependency Chain:
  ```python
  sync_news_postgres >> sync_social_postgres >> run_sentiment >> run_dbt_gold
  ```

---

### Task 3.5 — ملء Notebook التحليل الاستكشافي [NOT STARTED]

**الملف:** `notebooks/01-data-exploration.ipynb`

- [ ] إضافة خلايا تقرأ من PostgreSQL:
  - توزيع الأسعار لكل عملة (Histogram)
  - حجم التداول اليومي (Line Chart)
  - Correlation Matrix بين العملات
  - عدد الأخبار مع الوقت
- [ ] كل خلية تحتوي على شرح Markdown يوضح ماذا يفعل الكود وما هي الاستنتاجات

---

### Task 3.6 — ملء Notebook تدريب النموذج [NOT STARTED]

**الملف:** `notebooks/02-model-training.ipynb`

- [ ] شرح نموذج FinBERT وكيفية عمله
- [ ] عرض نتائج الـ Sentiment Analysis على عينة من الأخبار
- [ ] Confusion matrix أو Classification report
- [ ] رسم بياني يوضح العلاقة بين sentiment score وتغير السعر

---

## 👤 مصطفى مطر — Backend Updates + Alert Worker

### Task 3.1 — إنشاء Sentiment API Endpoint [NOT STARTED]

**الملف:** `backend/app/routers/coins.py`

- [ ] إضافة endpoint جديد:
  ```python
  @router.get("/market/sentiment")
  def market_sentiment(db: Session = Depends(get_db)):
      """Get current market sentiment from FinBERT analysis."""
  ```
- [ ] الـ Endpoint يقرأ من `gold.market_sentiment` (الجدول اللي كريم هيحدثه)
- [ ] يرجع:
  ```json
  {
    "overall_score": 0.65,
    "overall_label": "Bullish",
    "positive_pct": 60,
    "negative_pct": 25,
    "neutral_pct": 15,
    "article_count": 150,
    "last_updated": "2026-05-03T00:00:00Z"
  }
  ```

---

### Task 3.2 — تحديث Pydantic Schema للـ Sentiment [NOT STARTED]

**الملف:** `backend/app/schemas/coins.py`

- [ ] إضافة schema جديد:
  ```python
  class SentimentOverview(BaseModel):
      overall_score: float
      overall_label: str
      positive_pct: float
      negative_pct: float
      neutral_pct: float
      article_count: int
      last_updated: str
  ```

---

### Task 3.3 — تحديث data_service.py [NOT STARTED]

**الملف:** `backend/app/services/data_service.py`

- [ ] **حذف** `MOCK_BASE_PRICES` (سطر 37-59) و `import random` (سطر 1) — كود قديم غير مستخدم
- [ ] إضافة function `get_market_sentiment(db)`:
  ```python
  def get_market_sentiment(db: Session) -> dict:
      query = text("""
          SELECT
              AVG(sentiment_score) as avg_score,
              COUNT(*) as total,
              SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive,
              SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative,
              SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral
          FROM silver.news_sentiment
          WHERE published_at >= NOW() - INTERVAL '7 days'
      """)
      result = db.execute(query).fetchone()
      # ... format and return
  ```

---

### Task 3.4 — بناء Alert Worker (Background Service) [NOT STARTED]

**الملف:** `backend/app/services/alert_worker.py`

- [ ] إنشاء سكريبت يعمل كـ Background Worker:
  ```python
  import time
  from sqlalchemy import text
  from app.database import SessionLocal

  def check_alerts():
      db = SessionLocal()
      # 1. جلب أحدث الأسعار من gold.daily_market_summary
      prices = db.execute(text("""
          SELECT DISTINCT ON (symbol) symbol, close_price
          FROM gold.daily_market_summary
          ORDER BY symbol, date DESC
      """)).fetchall()

      price_map = {row.symbol: float(row.close_price) for row in prices}

      # 2. جلب التنبيهات النشطة
      alerts = db.execute(text("""
          SELECT id, user_id, symbol, condition, threshold
          FROM alerts WHERE is_active = TRUE
      """)).fetchall()

      # 3. المقارنة والتنبيه
      for alert in alerts:
          current_price = price_map.get(alert.symbol)
          if not current_price:
              continue
          triggered = False
          if alert.condition == 'above' and current_price >= float(alert.threshold):
              triggered = True
          elif alert.condition == 'below' and current_price <= float(alert.threshold):
              triggered = True

          if triggered:
              print(f"🔔 ALERT TRIGGERED: {alert.symbol} is {alert.condition} {alert.threshold} (current: {current_price})")
              # تعطيل التنبيه بعد إطلاقه
              db.execute(text("UPDATE alerts SET is_active = FALSE WHERE id = :id"), {"id": alert.id})
              db.commit()

      db.close()

  if __name__ == "__main__":
      while True:
          check_alerts()
          time.sleep(60)
  ```

---

### Task 3.5 — إضافة Alert Worker للـ Docker Compose [NOT STARTED]

**الملف:** `docker-compose.yml`

- [ ] إضافة service جديدة:
  ```yaml
  alert-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: alert-worker
    depends_on:
      - postgres
    environment:
      - POSTGRES_HOST=postgres
    command: python -m app.services.alert_worker
    networks:
      - crypto-net
  ```

---

### Task 3.6 — تنظيف الـ Backend Code [NOT STARTED]

**الملف:** `backend/app/services/data_service.py`

- [ ] حذف `import random` (سطر 1)
- [ ] حذف قاموس `MOCK_BASE_PRICES` بالكامل (سطر 37-59) — كود Mock قديم لم يعد مستخدماً
- [ ] التأكد إن كل الـ Endpoints بترجع داتا حقيقية من PostgreSQL فقط

---

## 👤 كريم أحمد — dbt Gold Models + Analytics

### Task 3.1 — تحديث market_sentiment.sql بأعمدة FinBERT [NOT STARTED]

**الملف:** `processing/dbt/models/gold/market_sentiment.sql`

- [ ] **استبدال** المنطق الحالي (keyword-based: `ILIKE '%bull%'`) بقراءة مباشرة من `silver.news_sentiment`:
  ```sql
  {{ config(materialized='table') }}

  WITH sentiment_data AS (
      SELECT
          DATE_TRUNC('day', published_at) AS sentiment_date,
          sentiment_score,
          sentiment_label
      FROM {{ source('silver', 'news_sentiment') }}
      WHERE published_at IS NOT NULL
  )

  SELECT
      sentiment_date,
      AVG(sentiment_score) AS avg_sentiment_score,
      COUNT(*) AS article_count,
      SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) AS positive_count,
      SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) AS negative_count,
      SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) AS neutral_count,
      CASE
          WHEN AVG(sentiment_score) > 0.2 THEN 'Bullish'
          WHEN AVG(sentiment_score) < -0.2 THEN 'Bearish'
          ELSE 'Neutral'
      END AS market_mood
  FROM sentiment_data
  GROUP BY sentiment_date
  ORDER BY sentiment_date DESC
  ```

---

### Task 3.2 — تحديث sources.yml [NOT STARTED]

**الملف:** `processing/dbt/models/staging/sources.yml`

- [ ] إضافة جدول الـ Sentiment الجديد:
  ```yaml
  - name: news_sentiment
    description: "News articles enriched with FinBERT sentiment scores"
  ```

---

### Task 3.3 — إنشاء Staging Model للـ Sentiment [NOT STARTED]

**الملف:** `processing/dbt/models/staging/stg_news_sentiment.sql`

- [ ] إنشاء View بسيط:
  ```sql
  {{ config(materialized='view') }}

  SELECT
      source,
      title,
      published_at,
      CAST(sentiment_score AS DECIMAL(5, 4)) AS sentiment_score,
      sentiment_label,
      ingested_at
  FROM {{ source('silver', 'news_sentiment') }}
  WHERE sentiment_score IS NOT NULL
  ```

---

### Task 3.4 — إنشاء Gold Model للـ Dashboard Stats [NOT STARTED]

**الملف:** `processing/dbt/models/gold/gold_dashboard_stats.sql`

- [ ] إنشاء موديل يجمع كل الإحصائيات في استعلام واحد للـ Frontend:
  ```sql
  {{ config(materialized='table') }}

  WITH latest_prices AS (
      SELECT * FROM {{ ref('gold_latest_prices') }}
  ),
  market_summary AS (
      SELECT
          COUNT(DISTINCT symbol) as active_coins,
          SUM(total_volume) as total_volume_24h
      FROM {{ ref('daily_market_summary') }}
      WHERE date = (SELECT MAX(date) FROM {{ ref('daily_market_summary') }})
  ),
  sentiment AS (
      SELECT
          AVG(avg_sentiment_score) as overall_sentiment
      FROM {{ ref('market_sentiment') }}
      WHERE sentiment_date >= CURRENT_DATE - INTERVAL '7 days'
  )

  SELECT
      ms.active_coins,
      ms.total_volume_24h,
      s.overall_sentiment,
      CURRENT_TIMESTAMP as generated_at
  FROM market_summary ms
  CROSS JOIN sentiment s
  ```

---

### Task 3.5 — إضافة اختبارات جودة بيانات جديدة [NOT STARTED]

**المجلد:** `processing/dbt/tests/`

- [ ] إنشاء `assert_sentiment_score_range.sql`:
  ```sql
  -- يتأكد إن كل الـ sentiment scores في النطاق المقبول (-1 إلى 1)
  SELECT *
  FROM {{ ref('market_sentiment') }}
  WHERE avg_sentiment_score < -1 OR avg_sentiment_score > 1
  ```
- [ ] تحديث `schema.yml` بأوصاف الأعمدة الجديدة

---

### Task 3.6 — تحديث الـ dbt DAG في Airflow [NOT STARTED]

**الملف:** `dags/dag_historical_daily.py`

- [ ] تحديث أمر dbt ليشمل الـ Models الجديدة:
  ```python
  bash_command='export POSTGRES_HOST=postgres && cd /opt/airflow/dbt && '
               '/home/airflow/.local/bin/dbt run && '
               '/home/airflow/.local/bin/dbt test'
  ```

---

## 📅 الجدول الزمني المقترح

| الأسبوع | عمرو | ياسين | مصطفى | كريم |
|---------|-------|--------|--------|------|
| **1** | Task 3.1-3.2 (Template + Login) | Task 3.1-3.2 (Docker + FinBERT Script) | Task 3.1-3.3 (Sentiment API + cleanup) | Task 3.1-3.3 (dbt models + sources) |
| **2** | Task 3.3-3.4 (Dashboard + Coin Page) | Task 3.3-3.4 (DB Schema + DAG) | Task 3.4-3.5 (Alert Worker + Docker) | Task 3.4-3.5 (Dashboard Stats + Tests) |
| **3** | Task 3.5-3.6 (Docker + Azure Deploy) | Task 3.5-3.6 (Notebooks) | Task 3.6 (Final cleanup) | Task 3.6 (dbt DAG update) |

---

## ✅ معايير النجاح (Definition of Done)

| # | المعيار |
|---|--------|
| 1 | الـ Frontend يعمل على `http://localhost:3000` ويعرض Dashboard كامل |
| 2 | شاشة Login تعمل وتحصل على Token من الـ API |
| 3 | الـ Charts تعرض أسعار حقيقية من Gold Layer |
| 4 | الـ Sentiment Gauge يعرض رقم حقيقي من FinBERT (مش keywords) |
| 5 | الـ Alert Worker يكتشف ويطبع تنبيهات عند كسر سعر محدد |
| 6 | الـ Notebooks مليئة بتحليلات ورسوم بيانية |
| 7 | المشروع متاح على Azure VM عبر رابط عام |
| 8 | `dbt test` ينجح بدون أخطاء |
