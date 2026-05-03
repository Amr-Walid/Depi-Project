# Ahmed Ayman — Data Analyst & ML Engineer

**Role:** Data Analyst + AI/ML Engineer  
**Core Responsibility:** Enrich the pipeline with news and social sentiment data, and build intelligent models that differentiate the project.

> **UPDATE (May 2026):** Ahmed was removed from the project due to inactivity. The Data Engineering tasks (NewsAPI and RSS Social producers) he was supposed to do in Milestone 1 were actually handled by **Amr Walid**. Ahmed's remaining tasks are currently unassigned or marked as not started.

---

## Milestone 1 — Enrich the Data Pipeline with New Sources

**Goal:** Extend the data the project collects to include news headlines and social media sentiment, and perform exploratory data analysis on what is already available.

---

### Task 1.1 — News Producer [NOT STARTED]

**File:** `ingestion/producers/producer_news.py`

- [ ] Connected to NewsAPI using `NEWS_API_KEY`
- [ ] Searches for keywords: `"bitcoin"`, `"ethereum"`, `"crypto"`, `"cryptocurrency"`
- [ ] Fetches new articles every 15 minutes using the `schedule` library
- [ ] Sends each article as a JSON message to Kafka topic: `crypto.news`

**Expected message format:**
```json
{
  "source": "CoinDesk",
  "title": "Bitcoin hits new ATH...",
  "url": "https://...",
  "published_at": "2024-04-10T12:00:00Z",
  "content": "Full article text..."
}
```

**Implementation outline:**
```python
import requests, schedule, time, json, os
from confluent_kafka import Producer

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
KAFKA_TOPIC = "crypto.news"

def fetch_and_produce():
    url = f"https://newsapi.org/v2/everything?q=bitcoin+crypto&apiKey={NEWS_API_KEY}&pageSize=20"
    response = requests.get(url)
    articles = response.json().get("articles", [])
    for article in articles:
        producer.produce(KAFKA_TOPIC, value=json.dumps(article).encode())

schedule.every(15).minutes.do(fetch_and_produce)
```

---

### Task 1.2 — RSS Social Producer [NOT STARTED]

**File:** `ingestion/producers/producer_social_rss.py`

- [ ] Integrated `feedparser` to read standard RSS crypto feeds.
- [ ] Monitors feeds periodically for new articles.
- [ ] Streams new posts to Kafka topic: `crypto.social`

**Expected message format:**
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

**Library to use:** `praw` (Python Reddit API Wrapper)

---

### Task 1.3 — Environment Configuration Update [NOT STARTED]

- [ ] Added `NEWS_API_KEY` to `.env.example`.
- [ ] Added `feedparser`, `newsapi-python`, `schedule` to `requirements.txt`.

---

### Task 1.4 — Exploratory Data Analysis [NOT STARTED]

**File:** `notebooks/01-data-exploration.ipynb` — exists but is empty

- [ ] Read price data from ADLS Gen2 Silver layer
- [ ] Analyze price distributions, 24h volume over time, correlation matrix between coins, and daily/weekly seasonality patterns
- [ ] Once news data is available: analyze most active sources, article frequency over time, and word frequency
- [ ] Each notebook cell must include a markdown explanation of what it does and what it concludes

---

## Milestone 2 — AI/ML Models

**Goal:** Build intelligent models for sentiment analysis and price forecasting — this is what differentiates the project from a standard data pipeline.

---

### Task 2.1 — Sentiment Analysis Model (FinBERT) [NOT STARTED]

**File:** `notebooks/02-model-training.ipynb` — exists but is empty  
**Directory:** `ml/` — exists but is empty

**What needs to be done:**
- [ ] Read cleaned news and social text data from the Silver layer (after Yassin has implemented the Silver news/social processing)
- [ ] Apply the **FinBERT** financial sentiment model:
  ```python
  from transformers import pipeline
  sentiment_pipeline = pipeline("text-classification", model="ProsusAI/finbert")
  result = sentiment_pipeline("Bitcoin is surging to new highs!")
  # [{'label': 'positive', 'score': 0.97}]
  ```
- [ ] Apply to news headlines and Reddit post titles
- [ ] Generate a `sentiment_score` column (range -1 to 1) and a `sentiment_label` column
- [ ] Analyze the relationship between sentiment and price movement (does positive news precede price increases?)

---

### Task 2.2 — Price Forecasting Model (LSTM) [NOT STARTED]

**File:** `notebooks/02-model-training.ipynb` — second section

- [ ] Prepare training data from the Silver historical layer
- [ ] Create features: `rolling_mean_7d`, `rolling_std_7d`, `price_change_pct`, `volume_change_pct`
- [ ] Normalize data with MinMaxScaler
- [ ] Build and train an LSTM model (start with BTC only):
  ```python
  import tensorflow as tf
  model = tf.keras.Sequential([
      tf.keras.layers.LSTM(50, return_sequences=True, input_shape=(lookback, features)),
      tf.keras.layers.Dropout(0.2),
      tf.keras.layers.LSTM(50),
      tf.keras.layers.Dense(1)
  ])
  ```
- [ ] Evaluate with RMSE and plot actual vs predicted prices

---

### Task 2.3 — POC Dashboard Notebook [NOT STARTED]

**File:** `notebooks/03-poc-dashboard.ipynb` — exists but is empty

- [ ] Use `plotly` or `matplotlib` to create:
  - Interactive price chart per coin
  - Overall market sentiment indicator
  - Latest news list with sentiment scores
  - Cross-coin performance comparison
- [ ] This notebook serves as the proof-of-concept before a real frontend is built

---

### Task 2.4 — Integrate Models with the Spark Pipeline [NOT STARTED]

**Coordinate with Yassin and Mostafa:**
- [ ] Convert the FinBERT sentiment model to a Spark UDF so it can run at scale:
  ```python
  from pyspark.sql.functions import udf
  from pyspark.sql.types import StringType

  @udf(returnType=StringType())
  def get_sentiment(text):
      result = sentiment_pipeline(text[:512])
      return result[0]['label']
  ```
- [ ] Add this UDF to the Silver news/social processor
- [ ] Coordinate with Mostafa to add `GET /api/v1/market/sentiment` endpoint to the API

---

## Summary Table

| Task | Description | Status |
|------|-------------|--------|
| 1.1 | producer_news.py | Not started |
| 1.2 | producer_social_rss.py | Not started |
| 1.3 | Update .env.example and requirements.txt | Not started |
| 1.4 | EDA notebook | Not started |
| 2.1 | Sentiment Analysis — FinBERT | Not started |
| 2.2 | Price Forecasting — LSTM | Not started |
| 2.3 | POC Dashboard notebook | Not started — file is empty |
| 2.4 | Integrate models into Spark pipeline | Not started |

---

## Dependencies

| Depends on | From | Why |
|-----------|------|-----|
| Kafka running | Mostafa (Docker) | To send news and social messages |
| Silver Layer (news/social) | Yassin | To get clean data for model training |
| Azure credentials | Amr | To read from ADLS in notebooks |
| NewsAPI key | Ahmed (self) | Must register at newsapi.org |
| Reddit app credentials | Ahmed (self) | Must create app at reddit.com/prefs/apps |

---

## Reference Links

| Resource | URL |
|----------|-----|
| FinBERT Model | https://huggingface.co/ProsusAI/finbert |
| NewsAPI Docs | https://newsapi.org/docs |
| PRAW Documentation | https://praw.readthedocs.io |
| Reddit App Registration | https://www.reddit.com/prefs/apps |
