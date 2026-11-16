{# silver.learning_history_angkasabiruretail: data learning_history milik angkasabiruretail (aturan pemetaan di stg_learning_history_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_learning_history_angkasabiruretail') }}
