{# silver.employee_identification_angkasabiru: data employee_identification milik Angkasa Biru (aturan pemetaan di stg_employee_identification_angkasabiru). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_identification_angkasabiru') }}
