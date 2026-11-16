{# silver.employee_profile_abdestination: data employee_profile milik abdestination (aturan pemetaan di stg_employee_profile_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_profile_abdestination') }}
