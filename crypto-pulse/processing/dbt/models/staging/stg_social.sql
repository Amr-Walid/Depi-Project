{{ config(materialized='view') }}

SELECT
    subreddit,
    post_id,
    title,
    text,
    score,
    num_comments,
    created_at,
    url,
    type,
    ingested_at
FROM {{ source('silver', 'social') }}
WHERE title IS NOT NULL OR text IS NOT NULL