SELECT symbol, date, COUNT(*) AS cnt
FROM {{ ref('daily_market_summary') }}
GROUP BY symbol, date
HAVING COUNT(*) > 1