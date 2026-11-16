{# silver_angkasabiruretail.employee_address_angkasabiruretail: data employee_address milik Angkasa Biru Retail (aturan pemetaan di stg_employee_address_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_address_angkasabiruretail') }}
