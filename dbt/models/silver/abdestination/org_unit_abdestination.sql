{# silver.org_unit_abdestination: data org_unit milik abdestination (aturan pemetaan di stg_org_unit_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_org_unit_abdestination') }}
