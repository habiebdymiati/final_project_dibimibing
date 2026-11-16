{# silver.employee_secondary_assignment_angkasabiru: data employee_secondary_assignment milik angkasabiru (aturan pemetaan di stg_employee_secondary_assignment_angkasabiru). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_secondary_assignment_angkasabiru') }}
