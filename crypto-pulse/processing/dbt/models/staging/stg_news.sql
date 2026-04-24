{{ config(materialized='view') }}

SELECT
    title,
    source,
    CAST(published_at AS TIMESTAMP) AS published_at,
    url,
    ingested_at
FROM {{ source('silver', 'bronze_news') }}
WHERE title IS NOT NULL