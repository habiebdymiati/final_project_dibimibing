{# silver_angkasabiruretail.employee_performance_history_angkasabiruretail: data employee_performance_history milik Angkasa Biru Retail (aturan pemetaan di stg_employee_performance_history_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_performance_history_angkasabiruretail') }}
