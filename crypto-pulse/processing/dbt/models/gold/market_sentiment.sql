{{ config(materialized='table') }}

WITH sentiment_base AS (
    SELECT
        DATE_TRUNC('day', published_at) AS sentiment_date,
        symbol,
        sentiment_score,
        sentiment_label
    FROM {{ ref('stg_news_sentiment') }}
    WHERE sentiment_score IS NOT NULL
)

SELECT
    sentiment_date,
    symbol,
    AVG(sentiment_score) AS avg_sentiment_score,
    COUNT(*) AS total_articles,
    SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) AS positive_count,
    SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) AS negative_count,
    SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) AS neutral_count,
    CASE
        WHEN AVG(sentiment_score) > 0.2 THEN 'Bullish'
        WHEN AVG(sentiment_score) < -0.2 THEN 'Bearish'
        ELSE 'Neutral'
    END AS market_mood
FROM sentiment_base
GROUP BY sentiment_date, symbol
ORDER BY sentiment_date DESC, symbol
