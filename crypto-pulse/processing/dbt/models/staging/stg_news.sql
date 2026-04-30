{{ config(materialized='view') }}

SELECT
    title,
    source,
    description,
    published_at,
    url,
    content,
    ingested_at
FROM {{ source('silver', 'news') }}
WHERE title IS NOT NULL