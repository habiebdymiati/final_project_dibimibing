{# Mapping ABD (katalog BRD 4.5): competency_assessment <- competency_assessments (dilengkapi mock). #}
select
    {{ id_employee('abdestination', abd('competency_assessments', 'id_employee')) }} as id_employee,
    {{ abd('competency_assessments', 'assessment_period') }}           as assessment_period,
    {{ ke_desimal(abd('competency_assessments', 'job_fit_score')) }}   as job_fit_score,
    cast(null as text)                                                     as assessment_result,
    {{ ke_desimal(abd('competency_assessments', 'competency_gap')) }}  as competency_gap,
    {{ abd('competency_assessments', 'assessment_method') }}           as assessment_method,
    {{ ke_tanggal(abd('competency_assessments', 'dt_assessment')) }}   as dt_assessment,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'competency_assessments') }} r
where {{ abd('competency_assessments', 'assessment_period') }} is not null
