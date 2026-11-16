{#
  Mapping AP (katalog BRD 2.10): employee_secondary_assignment <- employee_assignment_history (turunan).
  Katalog menandai seluruh field "DWH Generated / turunan" dari riwayat penugasan; field yang tidak punya
  sumber AP (fk_position_variant_id, job_class, org_unit_name, company_name, dt_assignment_letter) NULL.
#}
select
    'AB-ASG-AB-' || {{ ab('employee_assignment_history', 'id_assignment_history') }} as id_secondary_assignment,
    {{ id_employee('angkasabiru', ab('employee_assignment_history', 'id_employee')) }} as id_employee,
    cast(null as text)                                                  as fk_position_variant_id,
    {{ ab('employee_assignment_history', 'assignment_position') }}      as position_name,
    cast(null as text)                                                  as job_class,
    cast(null as text)                                                  as org_unit_name,
    cast(null as text)                                                  as company_name,
    {{ baku('angkasabiru', 'assignment_name', ab('employee_assignment_history', 'assignment_name')) }} as secondary_assignment_type,
    {{ ab('employee_assignment_history', 'assignment_letter_number') }} as assignment_letter_number,
    cast(null as date)                                                  as dt_assignment_letter,
    {{ ke_tanggal(ab('employee_assignment_history', 'dt_assignment_start')) }} as dt_assignment_start,
    {{ ke_tanggal(ab('employee_assignment_history', 'dt_assignment_end')) }}   as dt_assignment_end,
    {{ kolom_teknis('angkasabiru') }}
from {{ source('raw_ab', 'employee_assignment_history') }} r
where {{ ab('employee_assignment_history', 'id_assignment_history') }} is not null
