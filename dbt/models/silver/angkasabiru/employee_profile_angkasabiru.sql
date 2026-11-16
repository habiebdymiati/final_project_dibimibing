{# silver.employee_profile_angkasabiru: data employee_profile milik Angkasa Biru (aturan pemetaan di stg_employee_profile_angkasabiru). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_profile_angkasabiru') }}
