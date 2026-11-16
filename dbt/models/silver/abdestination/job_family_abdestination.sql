{# silver.job_family_abdestination: data job_family milik abdestination (aturan pemetaan di stg_job_family_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_job_family_abdestination') }}
