{# silver.learning_history_angkasabiru: data learning_history milik angkasabiru (aturan pemetaan di stg_learning_history_angkasabiru). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_learning_history_angkasabiru') }}
