{# silver.job_function_abdestination: data job_function milik abdestination (aturan pemetaan di stg_job_function_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_job_function_abdestination') }}
