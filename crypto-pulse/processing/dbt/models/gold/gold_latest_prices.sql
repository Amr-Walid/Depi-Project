{{ config(materialized='table') }}

WITH ranked_prices AS (
    SELECT
        symbol,
        price AS latest_price,
        volume AS latest_volume_24h,
        event_time AS last_updated,
        ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY event_time DESC) AS rn
    FROM {{ ref('stg_prices') }}
)

SELECT
    symbol,
    latest_price,
    latest_volume_24h,
    last_updated
FROM ranked_prices
WHERE rn = 1