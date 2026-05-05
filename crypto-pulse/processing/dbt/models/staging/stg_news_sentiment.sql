{{ config(materialized='view') }}

SELECT
    article_id,
    symbol,
    sentiment_score,
    sentiment_label,
    published_at,
    ingested_at
FROM {{ source('silver', 'news_sentiment') }}
WHERE sentiment_score IS NOT NULL