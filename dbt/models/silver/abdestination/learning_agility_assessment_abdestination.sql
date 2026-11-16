{# silver.learning_agility_assessment_abdestination: dari Angkasa Biru LMS (aturan pemetaan di stg_learning_agility_assessment_abdestination). #}
{{ config(tags=['lms']) }}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_learning_agility_assessment_abdestination') }}
