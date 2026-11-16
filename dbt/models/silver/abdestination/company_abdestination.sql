{# silver.company_abdestination: data company milik abdestination (aturan pemetaan di stg_company_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_company_abdestination') }}
