{{ config(
    materialized='incremental',
    unique_key=['symbol', 'date']
) }}

SELECT DISTINCT
    symbol,
    DATE(open_time) AS date,
    FIRST_VALUE(open) OVER (PARTITION BY symbol, DATE(open_time) ORDER BY open_time) AS open_price,
    MAX(high) OVER (PARTITION BY symbol, DATE(open_time)) AS high_price,
    MIN(low) OVER (PARTITION BY symbol, DATE(open_time)) AS low_price,
    LAST_VALUE(close) OVER (PARTITION BY symbol, DATE(open_time) ORDER BY open_time
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS close_price,
    SUM(volume) OVER (PARTITION BY symbol, DATE(open_time)) AS total_volume
FROM {{ ref('stg_historical') }}
{% if is_incremental() %}
WHERE DATE(open_time) >= (SELECT COALESCE(MAX(date), '1970-01-01') FROM {{ this }})
{% endif %}