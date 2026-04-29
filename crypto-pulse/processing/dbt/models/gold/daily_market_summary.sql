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
)

SELECT
    symbol,
    date,
    open_price,
    high_price,
    low_price,
    close_price,
    total_volume
FROM historical_ohlcv
ORDER BY symbol, date DESC
