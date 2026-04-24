SELECT *
FROM {{ ref('daily_market_summary') }}
WHERE low_price > high_price