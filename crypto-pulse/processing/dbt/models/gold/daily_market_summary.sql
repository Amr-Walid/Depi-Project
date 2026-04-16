{{ config(materialized='table') }}

SELECT 
    'BTC' AS symbol,
    CURRENT_DATE AS date,
    50000 AS close_price