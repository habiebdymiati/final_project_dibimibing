{# silver.employee_family_member_angkasabiru: data employee_family_member milik Angkasa Biru (aturan pemetaan di stg_employee_family_member_angkasabiru). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_family_member_angkasabiru') }}
