{# silver.employee_assignment_history_abdestination: data employee_assignment_history milik abdestination (aturan pemetaan di stg_employee_assignment_history_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_assignment_history_abdestination') }}
