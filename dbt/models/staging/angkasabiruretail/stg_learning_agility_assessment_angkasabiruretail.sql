{#
  Mapping ABR (katalog BRD 4.4): learning_agility_assessment <- Angkasa Biru LMS (sumber sistem grup,
  BUKAN HRIS perusahaan). Endpoint lintas perusahaan raw_lms.learning_agility_assessments disaring
  company_code = 'ABR'; id pegawai pada baris LMS memakai penomoran sistem perusahaan ini.
#}
{{ config(tags=['lms']) }}
select
    {{ id_employee('angkasabiruretail', nip7(lms('learning_agility_assessments', 'id_employee'))) }} as id_employee,
    {{ lms('learning_agility_assessments', 'assessment_period') }}              as assessment_period,
    {{ ke_desimal(lms('learning_agility_assessments', 'learning_agility_score')) }} as learning_agility_score,
    {{ ke_desimal(lms('learning_agility_assessments', 'mental_agility')) }}     as mental_agility,
    {{ ke_desimal(lms('learning_agility_assessments', 'people_agility')) }}     as people_agility,
    {{ ke_desimal(lms('learning_agility_assessments', 'change_agility')) }}     as change_agility,
    {{ ke_desimal(lms('learning_agility_assessments', 'results_agility')) }}    as results_agility,
    {{ ke_tanggal(lms('learning_agility_assessments', 'dt_assessment')) }}      as dt_assessment,
    cast('angkasabiruretail' as text) as dwh_source_system,
    r._batch_id         as dwh_batch_id,
    r._extracted_at     as dwh_extracted_at
from {{ source('raw_lms', 'learning_agility_assessments') }} r
where {{ lms('learning_agility_assessments', 'company_code') }} = 'ABR'
  and {{ lms('learning_agility_assessments', 'assessment_period') }} is not null
