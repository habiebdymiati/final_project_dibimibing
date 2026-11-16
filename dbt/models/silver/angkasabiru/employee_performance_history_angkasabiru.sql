{# silver.employee_performance_history_angkasabiru: data employee_performance_history milik Angkasa Biru (aturan pemetaan di stg_employee_performance_history_angkasabiru). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_performance_history_angkasabiru') }}
