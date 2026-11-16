{# silver_angkasabiruretail.job_function_angkasabiruretail: data job_function milik Angkasa Biru Retail (aturan pemetaan di stg_job_function_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_job_function_angkasabiruretail') }}
