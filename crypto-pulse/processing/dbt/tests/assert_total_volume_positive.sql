SELECT *
FROM {{ ref('daily_market_summary') }}
WHERE total_volume <= 0