{{ config(materialized='table') }}

WITH latest_prices AS (
    SELECT DISTINCT ON (symbol)
        symbol,
        latest_price,
        latest_volume_24h,
        last_updated
    FROM {{ ref('gold_latest_prices') }}
    ORDER BY symbol, last_updated DESC
),

latest_sentiment AS (
    SELECT DISTINCT ON (symbol)
        symbol,
        avg_sentiment_score,
        market_mood,
        sentiment_date
    FROM {{ ref('market_sentiment') }}
    ORDER BY symbol, sentiment_date DESC
)

SELECT
    COALESCE(lp.symbol, ls.symbol) AS symbol,
    lp.latest_price,
    lp.latest_volume_24h,
    lp.last_updated,
    ls.avg_sentiment_score,
    ls.market_mood,
    ls.sentiment_date AS last_sentiment_update,
    COUNT(CASE WHEN lp.latest_price > 1 THEN 1 END) OVER () AS active_coins
FROM latest_prices lp
FULL OUTER JOIN latest_sentiment ls ON lp.symbol = ls.symbol
ORDER BY lp.latest_price DESC NULLS LAST