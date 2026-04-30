{{ config(materialized='table') }}

WITH historical_ohlcv AS (
    SELECT
        symbol,
        date,
        open_price,
        high_price,
        low_price,
        close_price,
        total_volume
    FROM {{ ref('gold_daily_ohlcv') }}
    WHERE date < CURRENT_DATE
),
today_from_stream AS (
    SELECT DISTINCT
        symbol,
        CURRENT_DATE AS date,
        FIRST_VALUE(price) OVER (PARTITION BY symbol ORDER BY event_time) AS open_price,
        MAX(price) OVER (PARTITION BY symbol) AS high_price,
        MIN(price) OVER (PARTITION BY symbol) AS low_price,
        LAST_VALUE(price) OVER (PARTITION BY symbol ORDER BY event_time
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS close_price,
        LAST_VALUE(volume) OVER (PARTITION BY symbol ORDER BY event_time
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS total_volume
    FROM {{ ref('stg_prices') }}
    WHERE DATE(event_time) = CURRENT_DATE
),
combined AS (
    SELECT * FROM historical_ohlcv
    UNION ALL
    SELECT * FROM today_from_stream
)
SELECT DISTINCT
    symbol,
    date,
    open_price,
    high_price,
    low_price,
    close_price,
    total_volume
FROM combined
ORDER BY symbol, date DESC
