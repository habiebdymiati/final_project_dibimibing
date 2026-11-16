{# silver.learning_history_abdestination: data learning_history milik abdestination (aturan pemetaan di stg_learning_history_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_learning_history_abdestination') }}
