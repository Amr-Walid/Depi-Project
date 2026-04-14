# 🤖 أحمد أيمن — Data Analyst & ML Engineer

> **الدور:** محلل البيانات + مهندس الذكاء الاصطناعي  
> **المسؤولية الجوهرية:** إثراء المشروع ببيانات المشاعر والأخبار، وبناء النماذج الذكية التي تميزنا

---

## 🏁 Milestone 1 — إثراء خط أنابيب البيانات بمصادر جديدة

**الهدف:** توسيع نطاق البيانات التي نجمعها لتشمل الأخبار والمشاعر العامة، وإجراء تحليل استكشافي لفهم هذه البيانات.

---

### ❌ Task 1.1 — كتابة منتج بيانات الأخبار (News Producer)

**الملف:** `ingestion/producers/producer_news.py` *(حاليًا فارغ)*

**ما يجب فعله:**
- [ ] الاتصال بـ NewsAPI (مفتاح API يضاف في `.env` كـ `NEWS_API_KEY`)
- [ ] البحث عن الكلمات الرئيسية: `"bitcoin"`, `"ethereum"`, `"crypto"`, `"cryptocurrency"`
- [ ] جلب المقالات الإخبارية الجديدة كل 15 دقيقة باستخدام `schedule`
- [ ] إرسال كل مقال كـ JSON إلى Kafka topic: `crypto.news`
- [ ] هيكل الرسالة المقترح:
  ```json
  {
    "source": "CoinDesk",
    "title": "Bitcoin hits new ATH...",
    "url": "https://...",
    "published_at": "2024-04-10T12:00:00Z",
    "content": "Full article text..."
  }
  ```
- [ ] معالجة الأخطاء: إذا فشل الاتصال بـ NewsAPI، يتم تسجيل الخطأ والمحاولة مرة أخرى

**مثال للكود الأساسي:**
```python
import requests
from kafka import KafkaProducer
import schedule, time, json, os

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
KAFKA_TOPIC = "crypto.news"

def fetch_and_produce():
    url = f"https://newsapi.org/v2/everything?q=bitcoin+crypto&apiKey={NEWS_API_KEY}&pageSize=20"
    response = requests.get(url)
    articles = response.json().get("articles", [])
    for article in articles:
        producer.send(KAFKA_TOPIC, value=json.dumps(article).encode())

schedule.every(15).minutes.do(fetch_and_produce)
```

---

### ❌ Task 1.2 — كتابة منتج بيانات Reddit (Social Producer)

**الملف المطلوب إنشاؤه:** `ingestion/producers/producer_reddit.py`

**لماذا Reddit؟** Twitter API أصبح مدفوعًا — Reddit مجاني ولديه مجتمع ضخم للعملات الرقمية.

**ما يجب فعله:**
- [ ] إنشاء تطبيق Reddit API (مجاني) والحصول على:
  - `REDDIT_CLIENT_ID`
  - `REDDIT_CLIENT_SECRET`
  - `REDDIT_USER_AGENT`
- [ ] مراقبة subreddits:
  - `r/CryptoCurrency` — أخبار عامة
  - `r/Bitcoin` — مجتمع البيتكوين
  - `r/ethereum` — مجتمع Ethereum
- [ ] إرسال المنشورات والتعليقات الجديدة إلى Kafka topic: `crypto.social`
- [ ] هيكل الرسالة المقترح:
  ```json
  {
    "subreddit": "CryptoCurrency",
    "post_id": "abc123",
    "title": "Why Bitcoin is rising...",
    "text": "Full post content...",
    "score": 1250,
    "num_comments": 89,
    "created_utc": 1712750400
  }
  ```
- [ ] استخدام مكتبة `praw` (Python Reddit API Wrapper):
  ```python
  import praw
  reddit = praw.Reddit(
      client_id=os.getenv("REDDIT_CLIENT_ID"),
      client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
      user_agent=os.getenv("REDDIT_USER_AGENT")
  )
  ```
- [ ] تشغيل بشكل مستمر (stream) أو كل 10 دقائق

---

### ⏳ Task 1.3 — تحديث ملفات الإعداد

**الملفات:**
- `.env.example` (في الجذر — تنسق مع عمرو)
- `requirements.txt`

**ما يجب فعله:**
- [ ] إضافة المفاتيح الجديدة إلى `.env.example`:
  ```env
  # NewsAPI
  NEWS_API_KEY=your_news_api_key_here
  
  # Reddit API
  REDDIT_CLIENT_ID=your_reddit_client_id
  REDDIT_CLIENT_SECRET=your_reddit_client_secret
  REDDIT_USER_AGENT=CryptoPulse/1.0 by YourUsername
  ```
- [ ] إضافة المكتبات الجديدة إلى `requirements.txt`:
  ```
  praw>=7.7.1
  schedule>=1.2.0
  newsapi-python>=0.2.7  # أو requests مباشرة
  ```

---

### ⏳ Task 1.4 — التحليل الاستكشافي للبيانات (EDA)

**الملف:** `notebooks/01-data-exploration.ipynb` *(موجود لكن يحتاج محتوى)*

**ما يجب فعله:**
- [ ] قراءة بيانات الأسعار من ADLS Gen2:
  ```python
  from azure.storage.filedatalake import DataLakeServiceClient
  # أو عبر PySpark
  df = spark.read.parquet("abfss://datalake@stcryptopulsedev.dfs.core.windows.net/bronze/prices")
  ```
- [ ] تحليل بيانات الأسعار:
  - [ ] توزيع الأسعار (distribution plots)
  - [ ] حجم التداول عبر الزمن
  - [ ] الارتباط بين العملات المختلفة (correlation matrix)
  - [ ] تحديد الأنماط الموسمية (daily, weekly patterns)
- [ ] تحليل بيانات الأخبار (بمجرد توفرها):
  - [ ] أكثر المصادر نشاطًا
  - [ ] توزيع الأخبار عبر الزمن
  - [ ] كلمات متكررة (word cloud)
- [ ] التوثيق: كل خلية يجب أن تشرح ماذا تفعل وماذا تستنتج

---

## 🚀 Milestone 2 — بناء نماذج الذكاء الاصطناعي (AI/ML)

**الهدف:** بناء نماذج ذكية لتحليل المشاعر والتنبؤ بالأسعار — هذا ما يميز مشروعنا.

---

### ❌ Task 2.1 — نموذج تحليل المشاعر (Sentiment Analysis)

**الملف:** `notebooks/02-model-training.ipynb` *(موجود لكن فارغ)*  
**المجلد:** `ml/` *(فارغ، مخصص لحفظ النماذج)*

**ما يجب فعله:**
- [ ] قراءة بيانات النصوص النظيفة من Silver Layer (بمجرد إنجاز ياسين لها)
- [ ] استخدام نموذج **FinBERT** المتخصص في التحليل المالي:
  ```python
  from transformers import pipeline
  sentiment_pipeline = pipeline(
      "text-classification",
      model="ProsusAI/finbert"
  )
  result = sentiment_pipeline("Bitcoin is surging to new highs!")
  # [{'label': 'positive', 'score': 0.97}]
  ```
- [ ] تطبيق النموذج على:
  - [ ] عناوين وملخصات الأخبار من `crypto.news`
  - [ ] منشورات Reddit من `crypto.social`
- [ ] إنشاء عمود `sentiment_score` (-1 إلى 1) و `sentiment_label`
- [ ] تحليل العلاقة بين المشاعر وحركة الأسعار:
  - [ ] هل الأخبار الإيجابية تسبق ارتفاع الأسعار؟
  - [ ] رسم بياني: Sentiment vs. Price Movement
- [ ] حفظ النتائج في:
  - ملف CSV مؤقت، أو
  - كتابة نتائج المشاعر إلى Silver Layer كعمود إضافي

---

### ❌ Task 2.2 — نموذج التنبؤ بالأسعار (Price Forecasting) — متقدم

**الملف:** `notebooks/02-model-training.ipynb` (قسم ثانٍ)

**ما يجب فعله:**
- [ ] تحضير البيانات للتدريب:
  - [ ] تحميل بيانات الأسعار التاريخية من Silver Layer
  - [ ] إنشاء features: `rolling_mean_7d`, `rolling_std_7d`, `price_change_%`, `volume_change_%`
  - [ ] تطبيع البيانات (MinMaxScaler)
- [ ] بناء نموذج LSTM (بداية بسيطة):
  ```python
  import tensorflow as tf
  model = tf.keras.Sequential([
      tf.keras.layers.LSTM(50, return_sequences=True, input_shape=(lookback, features)),
      tf.keras.layers.Dropout(0.2),
      tf.keras.layers.LSTM(50),
      tf.keras.layers.Dense(1)  # سعر الغد
  ])
  ```
- [ ] تدريب على Bitcoin أولاً (BTCUSDT)
- [ ] تقييم الأداء:
  ```python
  from sklearn.metrics import mean_squared_error
  rmse = mean_squared_error(y_test, predictions, squared=False)
  print(f"RMSE: {rmse}")
  ```
- [ ] رسم: Actual vs. Predicted prices

---

### ❌ Task 2.3 — لوحة معلومات تجريبية (POC Dashboard)

**الملف:** `notebooks/03-poc-dashboard.ipynb` *(موجود لكن فارغ)*

**ما يجب فعله:**
- [ ] استخدام مكتبة `plotly` أو `matplotlib` لإنشاء:
  - [ ] رسم بياني تفاعلي لأسعار العملات
  - [ ] مؤشر المشاعر العام للسوق
  - [ ] قائمة بأحدث الأخبار مع درجة مشاعرها
  - [ ] مقارنة بين أداء العملات المختلفة
- [ ] هذا الـ Notebook يُستخدم كـ "proof of concept" قبل بناء Frontend حقيقي

---

### ❌ Task 2.4 — دمج النماذج مع خط الأنابيب

**ما يجب فعله (بالتنسيق مع ياسين):**
- [ ] تحويل نموذج Sentiment Analysis إلى Spark UDF:
  ```python
  from pyspark.sql.functions import udf
  @udf(returnType=StringType())
  def get_sentiment(text):
      result = sentiment_pipeline(text[:512])
      return result[0]['label']
  ```
- [ ] إضافة هذا الـ UDF إلى `silver_processor.py` لتطبيقه على بيانات الأخبار تلقائيًا
- [ ] التنسيق مع مصطفى لإضافة endpoint جديد في API:
  - `GET /api/v1/market/sentiment` — يعرض درجة المشاعر الحالية

---

## 📋 ملخص الحالة

| Task | الوصف | الحالة |
|------|--------|--------|
| 1.1 | producer_news.py | ❌ ملف فارغ |
| 1.2 | producer_reddit.py | ❌ لم يُنشأ |
| 1.3 | تحديث .env.example و requirements.txt | ❌ لم يبدأ |
| 1.4 | العمل على notebooks/01 (EDA) | ⏳ ملف موجود فارغ |
| 2.1 | نموذج Sentiment Analysis (FinBERT) | ❌ لم يبدأ |
| 2.2 | نموذج التنبؤ بالأسعار (LSTM) | ❌ لم يبدأ |
| 2.3 | لوحة POC Dashboard في Notebook | ❌ ملف فارغ |
| 2.4 | دمج النماذج مع Spark Pipeline | ❌ لم يبدأ |

---

## 📂 ما يجب رفعه على GitHub (Deliverables)

**Milestone 1:**
- `ingestion/producers/producer_news.py` ← **الأولوية الأولى الآن**
- `ingestion/producers/producer_reddit.py` ← **الأولوية الثانية**
- تحديثات على `requirements.txt` (praw, schedule, newsapi-python)
- إبلاغ عمرو بالمفاتيح الجديدة لإضافتها في `.env.example`

**Milestone 2:**
- `notebooks/02-model-training.ipynb` (مكتمل مع نتائج موثقة)
- `notebooks/03-poc-dashboard.ipynb`
- `ml/` — أي كود مساعد لتحميل وتشغيل النماذج
- **لا ترفع ملفات نماذج ضخمة** — فقط الكود الذي يحمل النموذج من HuggingFace

---

## 🔧 التبعيات والاعتمادات

| يعتمد على | من | لماذا |
|-----------|-----|--------|
| Kafka running | مصطفى | لإرسال بيانات الأخبار والـ Reddit |
| Silver Layer (News/Social) | ياسين | للحصول على البيانات النظيفة لتدريب النماذج |
| Azure credentials | عمرو | للقراءة من ADLS في الـ notebooks |
| NewsAPI Key | أحمد نفسه | يجب التسجيل وإبلاغ عمرو بالمفتاح |
| Reddit App | أحمد نفسه | يجب إنشاء التطبيق على reddit.com/prefs/apps |

---

## 📚 مصادر مفيدة

| المورد | الرابط |
|--------|--------|
| FinBERT Model | https://huggingface.co/ProsusAI/finbert |
| NewsAPI Docs | https://newsapi.org/docs |
| PRAW Docs | https://praw.readthedocs.io |
| Reddit App Registration | https://www.reddit.com/prefs/apps |
