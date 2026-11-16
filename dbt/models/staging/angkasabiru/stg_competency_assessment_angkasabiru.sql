{#
  Mapping AP (katalog BRD 4.5): competency_assessment <- competency_assessment.
  Endpoint tidak ada di API asli ("AP — tidak ada" di katalog) -> dilengkapi instance tiruan (mock).
#}
select
    {{ id_employee('angkasabiru', ab('competency_assessment', 'id_employee')) }} as id_employee,
    {{ ab('competency_assessment', 'assessment_period') }}           as assessment_period,
    {{ ke_desimal(ab('competency_assessment', 'job_fit_score')) }}   as job_fit_score,
    cast(null as text)                                               as assessment_result,
    {{ ke_desimal(ab('competency_assessment', 'competency_gap')) }}  as competency_gap,
    {{ ab('competency_assessment', 'assessment_method') }}           as assessment_method,
    {{ ke_tanggal(ab('competency_assessment', 'dt_assessment')) }}   as dt_assessment,
    {{ kolom_teknis('angkasabiru') }}
from {{ source('raw_ab', 'competency_assessment') }} r
where {{ ab('competency_assessment', 'assessment_period') }} is not null
