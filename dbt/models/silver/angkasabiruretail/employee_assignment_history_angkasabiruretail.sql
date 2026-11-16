{# silver_angkasabiruretail.employee_assignment_history_angkasabiruretail: data employee_assignment_history milik Angkasa Biru Retail (aturan pemetaan di stg_employee_assignment_history_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_assignment_history_angkasabiruretail') }}
