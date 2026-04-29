{{ config(
    materialized='incremental',
    unique_key=['symbol', 'date']
) }}

SELECT
    symbol,
    DATE(open_time) AS date,
    MIN(open) AS open_price,
    MAX(high) AS high_price,
    MIN(low) AS low_price,
    MAX(close) AS close_price,
    SUM(volume) AS total_volume
FROM {{ ref('stg_historical') }}
GROUP BY symbol, DATE(open_time)