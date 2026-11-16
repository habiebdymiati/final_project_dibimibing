{# silver.position_competency_requirement_abdestination: data position_competency_requirement milik abdestination (aturan pemetaan di stg_position_competency_requirement_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_position_competency_requirement_abdestination') }}
