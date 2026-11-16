{# silver.employee_contract_abdestination: data employee_contract milik abdestination (aturan pemetaan di stg_employee_contract_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_contract_abdestination') }}
