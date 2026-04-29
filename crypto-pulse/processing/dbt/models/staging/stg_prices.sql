{{ config(materialized='view') }}

SELECT
    symbol,
    price,
    volume_24h AS volume,
    event_time,
    source,
    processed_at
FROM {{ source('silver_prices', 'prices') }}
WHERE price IS NOT NULL
  AND price > 0
