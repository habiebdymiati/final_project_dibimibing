{# silver.learning_agility_assessment_angkasabiru: dari Angkasa Biru LMS (aturan pemetaan di stg_learning_agility_assessment_angkasabiru). #}
{{ config(tags=['lms']) }}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_learning_agility_assessment_angkasabiru') }}
