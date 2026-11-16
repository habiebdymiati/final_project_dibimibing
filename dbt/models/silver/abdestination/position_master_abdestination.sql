{# silver.position_master_abdestination: data position_master milik abdestination (aturan pemetaan di stg_position_master_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_position_master_abdestination') }}
