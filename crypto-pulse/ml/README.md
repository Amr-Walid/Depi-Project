# Machine Learning Layer (Sentiment Analysis)

This directory is reserved for hosting and configuring the NLP (Natural Language Processing) models utilized within the **Crypto-Pulse** data lakehouse.

---

## The Core Model: FinBERT

To analyze market news sentiment, the pipeline implements **FinBERT** (`ProsusAI/finbert`), a specialized Natural Language Processing model:

*   **Architecture**: Built on top of the bidirectional BERT (Bidirectional Encoder Representations from Transformers) language model.
*   **Domain Tuning**: Pre-trained on **TRC20** financial news corpora and fine-tuned on the **Financial PhraseBank** dataset.
*   **Classification Targets**: Categorizes text chunks into three sentiment labels with corresponding confidence scores:
    *   **Positive** (bullish market cues)
    *   **Negative** (bearish market cues)
    *   **Neutral** (unbiased facts/statements)

---

## PySpark UDF Integration Architecture

To run NLP inference at scale, FinBERT is wrapped in a **PySpark User Defined Function (UDF)** inside `processing/spark_jobs/sentiment_processor.py`.

```
                    ┌─────────────────────────┐
                    │      Driver Node        │
                    │                         │
                    │   Defines UDF Schema    │
                    └────────────┬────────────┘
                                 │
                 UDF Broadcasted to Executors
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Spark Executor Worker  │
                    ├─────────────────────────┤
                    │   • Imports transformers│
                    │   • Downloads Model     │
                    │     (Cached to /tmp)    │
                    │   • Runs CPU Inference  │
                    └─────────────────────────┘
```

### Execution Details:
1.  **Lazy Model Instantiation**: The `transformers.pipeline` loading logic is enclosed directly inside the UDF body. This prevents serialization errors during Spark task distribution and ensures that workers instantiate the classifier only once locally.
2.  **Worker Caching**: Environment paths `TRANSFORMERS_CACHE` and `HF_HOME` are explicitly set to write to `/tmp` in the workers, where the pre-trained weights are cached locally upon the first execution.
3.  **Token Ceiling Safeguard**: News headlines are sliced to a maximum of `512` characters (`text[:512]`) before being passed to the classifier pipeline. This prevents token overflow issues.

---

## Database Output Schema

The UDF outputs a structured schema mapped to the `silver.news_sentiment` table in Supabase Cloud PostgreSQL:

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `title` | `VARCHAR` | The raw article title analyzed. |
| `symbol` | `VARCHAR` | The target coin symbol (`BTC`, `ETH`, `XRP`, `SHIB`, or `Other`). |
| `published_at` | `TIMESTAMP` | Article publication timestamp. |
| `sentiment_score` | `FLOAT` | Classifier confidence score (ranging from `0.0` to `1.0`). |
| `sentiment_label` | `VARCHAR` | Predicted label (`positive`, `negative`, `neutral`). |
| `source` | `VARCHAR` | News outlet source (NewsAPI, RSS feed name). |
| `ingested_at` | `TIMESTAMP` | Ingestion timestamp. |
