{# silver.employee_contract_angkasabiru: data employee_contract milik Angkasa Biru (aturan pemetaan di stg_employee_contract_angkasabiru). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_contract_angkasabiru') }}
