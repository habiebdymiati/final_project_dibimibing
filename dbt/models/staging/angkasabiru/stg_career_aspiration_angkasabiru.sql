{#
  Mapping AB (katalog BRD 5.1): career_aspiration <- Angkasa Biru TMS (sumber sistem talenta grup,
  BUKAN HRIS perusahaan). Endpoint lintas perusahaan raw_tms.career_aspirations disaring
  company_code = 'AB'; id pegawai pada baris TMS memakai penomoran sistem perusahaan ini.
  id_target_position dan id_target_job_family memakai kode master perusahaan ini (sama dengan
  position_master.id_position_master dan job_family.id_job_family), jadi dibawa apa adanya.
#}
{{ config(tags=['tms']) }}
select
    {{ id_employee('angkasabiru', tms('career_aspirations', 'id_employee')) }} as id_employee,
    lower({{ tms('career_aspirations', 'aspiration_source') }})   as aspiration_source,
    {{ tms('career_aspirations', 'id_target_position') }}         as id_target_position,
    {{ tms('career_aspirations', 'id_target_job_family') }}       as id_target_job_family,
    {{ ke_tanggal(tms('career_aspirations', 'dt_aspiration')) }}  as dt_aspiration,
    {{ tms('career_aspirations', 'aspiration_notes') }}           as aspiration_notes,
    cast('angkasabiru' as text) as dwh_source_system,
    r._batch_id         as dwh_batch_id,
    r._extracted_at     as dwh_extracted_at
from {{ source('raw_tms', 'career_aspirations') }} r
where {{ tms('career_aspirations', 'company_code') }} = 'AB'
