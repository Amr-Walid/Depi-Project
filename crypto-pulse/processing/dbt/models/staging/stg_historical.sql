{{ config(materialized='view') }}

SELECT
    symbol,
    open_time,
    open,
    high,
    low,
    close,
    volume,
    year,
    month,
    day,
    processed_at
FROM {{ source('silver', 'historical') }}
WHERE open IS NOT NULL
  AND open > 0