{# silver.employee_family_member_abdestination: data employee_family_member milik abdestination (aturan pemetaan di stg_employee_family_member_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_employee_family_member_abdestination') }}
