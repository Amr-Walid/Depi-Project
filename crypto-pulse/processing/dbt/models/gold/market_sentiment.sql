{{ config(materialized='table') }}

WITH news_sentiment AS (
    SELECT
        DATE_TRUNC('day', published_at) AS sentiment_date,
        'news' AS source_type,
        COUNT(*) AS total_mentions,
        COUNT(*) AS positive_count,
        0 AS negative_count
    FROM {{ ref('stg_news') }}
    WHERE title ILIKE '%bull%' OR title ILIKE '%surge%' OR title ILIKE '%rally%'
    GROUP BY DATE_TRUNC('day', published_at)

    UNION ALL

    SELECT
        DATE_TRUNC('day', published_at) AS sentiment_date,
        'news' AS source_type,
        COUNT(*) AS total_mentions,
        0 AS positive_count,
        COUNT(*) AS negative_count
    FROM {{ ref('stg_news') }}
    WHERE title ILIKE '%bear%' OR title ILIKE '%drop%' OR title ILIKE '%crash%'
    GROUP BY DATE_TRUNC('day', published_at)
),

social_sentiment AS (
    SELECT
        DATE_TRUNC('day', created_at) AS sentiment_date,
        'social' AS source_type,
        COUNT(*) AS total_mentions,
        COUNT(*) AS positive_count,
        0 AS negative_count
    FROM {{ ref('stg_social') }}
    WHERE text ILIKE '%bull%' OR text ILIKE '%moon%' OR text ILIKE '%gem%'
    GROUP BY DATE_TRUNC('day', created_at)

    UNION ALL

    SELECT
        DATE_TRUNC('day', created_at) AS sentiment_date,
        'social' AS source_type,
        COUNT(*) AS total_mentions,
        0 AS positive_count,
        COUNT(*) AS negative_count
    FROM {{ ref('stg_social') }}
    WHERE text ILIKE '%bear%' OR text ILIKE '%fud%' OR text ILIKE '%dump%'
    GROUP BY DATE_TRUNC('day', created_at)
),

combined AS (
    SELECT * FROM news_sentiment
    UNION ALL
    SELECT * FROM social_sentiment
)

SELECT
    sentiment_date,
    source_type,
    SUM(total_mentions) AS mentions,
    SUM(positive_count) AS positive_mentions,
    SUM(negative_count) AS negative_mentions,
CASE 
    WHEN SUM(total_mentions) = 0 THEN NULL
    ELSE (SUM(positive_count) - SUM(negative_count)) * 100.0 / SUM(total_mentions)
END AS sentiment_score
FROM combined
GROUP BY sentiment_date, source_type
ORDER BY sentiment_date DESC