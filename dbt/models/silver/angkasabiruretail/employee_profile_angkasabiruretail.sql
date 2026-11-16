{# silver_angkasabiruretail.employee_profile_angkasabiruretail: data employee_profile milik Angkasa Biru Retail (aturan pemetaan di stg_employee_profile_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_profile_angkasabiruretail') }}
