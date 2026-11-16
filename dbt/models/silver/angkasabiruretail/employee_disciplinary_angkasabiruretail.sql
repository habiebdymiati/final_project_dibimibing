{# silver_angkasabiruretail.employee_disciplinary_angkasabiruretail: data employee_disciplinary milik Angkasa Biru Retail (aturan pemetaan di stg_employee_disciplinary_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_disciplinary_angkasabiruretail') }}
