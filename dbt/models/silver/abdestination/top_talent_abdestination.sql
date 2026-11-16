{# silver.top_talent_abdestination: data top_talent milik abdestination (aturan pemetaan di stg_top_talent_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_top_talent_abdestination') }}
