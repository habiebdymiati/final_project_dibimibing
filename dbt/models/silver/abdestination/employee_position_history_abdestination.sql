{# silver.employee_position_history_abdestination: data employee_position_history milik abdestination (aturan pemetaan di stg_employee_position_history_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_position_history_abdestination') }}
