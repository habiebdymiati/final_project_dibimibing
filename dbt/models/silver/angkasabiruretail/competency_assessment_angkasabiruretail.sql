{# silver.competency_assessment_angkasabiruretail: data competency_assessment milik angkasabiruretail (aturan pemetaan di stg_competency_assessment_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_competency_assessment_angkasabiruretail') }}
