{# silver.employee_identification_abdestination: data employee_identification milik abdestination (aturan pemetaan di stg_employee_identification_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_identification_abdestination') }}
