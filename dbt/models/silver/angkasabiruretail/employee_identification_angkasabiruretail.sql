{# silver_angkasabiruretail.employee_identification_angkasabiruretail: data employee_identification milik Angkasa Biru Retail (aturan pemetaan di stg_employee_identification_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_identification_angkasabiruretail') }}
