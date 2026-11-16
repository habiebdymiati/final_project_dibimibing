{# silver.job_family_angkasabiru: data job_family milik Angkasa Biru (aturan pemetaan di stg_job_family_angkasabiru). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_job_family_angkasabiru') }}
