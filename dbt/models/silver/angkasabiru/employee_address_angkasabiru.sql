{# silver.employee_address_angkasabiru: data employee_address milik Angkasa Biru (aturan pemetaan di stg_employee_address_angkasabiru). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_address_angkasabiru') }}
