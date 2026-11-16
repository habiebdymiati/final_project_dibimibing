{# silver.job_function_angkasabiru: data job_function milik Angkasa Biru (aturan pemetaan di stg_job_function_angkasabiru). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_job_function_angkasabiru') }}
