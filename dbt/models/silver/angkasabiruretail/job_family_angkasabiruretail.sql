{# silver_angkasabiruretail.job_family_angkasabiruretail: data job_family milik Angkasa Biru Retail (aturan pemetaan di stg_job_family_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_job_family_angkasabiruretail') }}
