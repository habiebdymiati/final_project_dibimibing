{# silver_angkasabiruretail.employee_family_member_angkasabiruretail: data employee_family_member milik Angkasa Biru Retail (aturan pemetaan di stg_employee_family_member_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_family_member_angkasabiruretail') }}
