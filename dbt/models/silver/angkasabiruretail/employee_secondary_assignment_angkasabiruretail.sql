{# silver.employee_secondary_assignment_angkasabiruretail: data employee_secondary_assignment milik angkasabiruretail (aturan pemetaan di stg_employee_secondary_assignment_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_secondary_assignment_angkasabiruretail') }}
