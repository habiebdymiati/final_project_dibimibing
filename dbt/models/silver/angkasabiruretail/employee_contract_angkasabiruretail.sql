{# silver_angkasabiruretail.employee_contract_angkasabiruretail: data employee_contract milik Angkasa Biru Retail (aturan pemetaan di stg_employee_contract_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_contract_angkasabiruretail') }}
