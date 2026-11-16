{#
  Mapping AB: employee_education_history <- employee_education_history.
  id_employee : kolom di raw bernama "id_emloyee" (salah ketik di API).
  id_education_history: sumber tidak menyediakan id -> kunci buatan DWH dari isi baris; baris kembar identik disatukan.
  final_score : hanya angka (koma desimal diterima); isian seperti "A"/"B" -> NULL.
#}
select distinct
    {{ id_employee('angkasabiru', ab('employee_education_history', ['id_employee', 'id_emloyee'])) }} as id_employee,
    coalesce({{ ab('employee_education_history', 'id_education_history') }}, 'AB-EDU-AB-' || md5(r._row_hash)) as id_education_history,
    {{ ab('employee_education_history', 'education_level_code') }}  as education_level_code,
    {{ baku('angkasabiru', 'education_degree_type', ab('employee_education_history', 'education_degree_type')) }} as education_degree_type,
    upper({{ ab('employee_education_history', 'institution_name') }}) as institution_name,
    {{ baku('angkasabiru', 'institution_country', ab('employee_education_history', 'institution_country')) }} as institution_country,
    upper({{ ab('employee_education_history', 'major') }}) as major,
    {{ ke_tanggal(ab('employee_education_history', 'dt_start')) }}  as dt_start,
    {{ ke_tanggal(ab('employee_education_history', 'dt_end')) }}    as dt_end,
    {{ ke_desimal(ab('employee_education_history', 'final_score')) }} as final_score,
    {{ kolom_teknis('angkasabiru') }}
from {{ source('raw_ab', 'employee_education_history') }} r
