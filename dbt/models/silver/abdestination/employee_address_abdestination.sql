{# silver.employee_address_abdestination: data employee_address milik abdestination (aturan pemetaan di stg_employee_address_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_address_abdestination') }}
