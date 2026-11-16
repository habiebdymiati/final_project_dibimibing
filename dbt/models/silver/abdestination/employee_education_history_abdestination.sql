{# silver.employee_education_history_abdestination: data employee_education_history milik abdestination (aturan pemetaan di stg_employee_education_history_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_education_history_abdestination') }}
