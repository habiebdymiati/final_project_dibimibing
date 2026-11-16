{# silver.competency_assessment_angkasabiru: data competency_assessment milik angkasabiru (aturan pemetaan di stg_competency_assessment_angkasabiru). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_competency_assessment_angkasabiru') }}
