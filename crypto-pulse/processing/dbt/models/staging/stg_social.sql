{{ config(materialized='view') }}

SELECT
    text,
    platform,
    author_id,
    CAST(created_at AS TIMESTAMP) AS created_at,
    likes,
    shares,
    ingested_at
FROM {{ source('silver', 'bronze_social') }}
WHERE text IS NOT NULL