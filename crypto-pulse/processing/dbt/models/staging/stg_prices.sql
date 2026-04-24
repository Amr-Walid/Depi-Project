{{ config(materialized='view') }}

SELECT
    symbol,
    CAST(price AS DECIMAL(18, 8)) AS price,
    CAST(volume AS DECIMAL(18, 8)) AS volume,
    CAST(timestamp AS TIMESTAMP) AS event_time,
    ingested_at
FROM {{ source('silver', 'bronze_historical_prices') }}
WHERE price IS NOT NULL
  AND price > 0