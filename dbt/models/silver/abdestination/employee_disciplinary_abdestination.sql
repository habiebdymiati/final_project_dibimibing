{# silver.employee_disciplinary_abdestination: data employee_disciplinary milik abdestination (aturan pemetaan di stg_employee_disciplinary_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_disciplinary_abdestination') }}
