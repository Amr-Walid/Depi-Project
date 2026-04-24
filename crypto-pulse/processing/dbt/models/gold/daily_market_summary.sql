{{ config(materialized='table') }}

WITH prices AS (
    SELECT
        symbol,
        DATE_TRUNC('day', event_time) AS date,
        FIRST_VALUE(price) OVER (
            PARTITION BY symbol, DATE_TRUNC('day', event_time)
            ORDER BY event_time
        ) AS open_price,
        MAX(price) OVER (
            PARTITION BY symbol, DATE_TRUNC('day', event_time)
        ) AS high_price,
        MIN(price) OVER (
            PARTITION BY symbol, DATE_TRUNC('day', event_time)
        ) AS low_price,
        LAST_VALUE(price) OVER (
            PARTITION BY symbol, DATE_TRUNC('day', event_time)
            ORDER BY event_time
        ) AS close_price,
        SUM(volume) OVER (
            PARTITION BY symbol, DATE_TRUNC('day', event_time)
        ) AS total_volume
    FROM {{ ref('stg_prices') }}
)

SELECT DISTINCT
    symbol,
    date,
    open_price,
    high_price,
    low_price,
    close_price,
    total_volume
FROM prices
