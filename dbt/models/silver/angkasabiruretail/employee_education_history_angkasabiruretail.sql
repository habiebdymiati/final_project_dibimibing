{# silver_angkasabiruretail.employee_education_history_angkasabiruretail: data employee_education_history milik Angkasa Biru Retail (aturan pemetaan di stg_employee_education_history_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_education_history_angkasabiruretail') }}
