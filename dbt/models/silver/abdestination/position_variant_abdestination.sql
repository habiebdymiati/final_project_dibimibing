{# silver.position_variant_abdestination: data position_variant milik abdestination (aturan pemetaan di stg_position_variant_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_position_variant_abdestination') }}
