{# silver.competency_assessment_abdestination: data competency_assessment milik abdestination (aturan pemetaan di stg_competency_assessment_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_competency_assessment_abdestination') }}
