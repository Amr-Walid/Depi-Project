SELECT *
FROM {{ ref('market_sentiment') }}
WHERE avg_sentiment_score < -1 OR avg_sentiment_score > 1