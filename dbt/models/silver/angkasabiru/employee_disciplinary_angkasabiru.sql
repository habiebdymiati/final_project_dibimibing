{# silver.employee_disciplinary_angkasabiru: data employee_disciplinary milik Angkasa Biru (aturan pemetaan di stg_employee_disciplinary_angkasabiru). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_disciplinary_angkasabiru') }}
