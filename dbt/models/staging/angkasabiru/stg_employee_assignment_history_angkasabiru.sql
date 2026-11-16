{#
  Mapping AB: employee_assignment_history <- employee_assignment_history.
  assignment_letter_number tidak ada di mapping; kolom bernama sama ada di raw -> dibawa.
  assignment_letter_blob dan description tidak ada di mapping maupun raw -> NULL.
#}
select
    {{ id_employee('angkasabiru', ab('employee_assignment_history', 'id_employee')) }} as id_employee,
    {{ ab('employee_assignment_history', 'id_assignment_history') }}    as id_assignment_history,
    {{ baku('angkasabiru', 'assignment_name', ab('employee_assignment_history', 'assignment_name')) }} as assignment_name,
    {{ ab('employee_assignment_history', 'assignment_position') }}      as assignment_position,
    {{ ab('employee_assignment_history', 'assignment_letter_number') }} as assignment_letter_number,
    {{ ab('employee_assignment_history', 'assignment_letter_blob') }}   as assignment_letter_blob,
    {{ ke_tanggal(ab('employee_assignment_history', 'dt_assignment_start')) }} as dt_assignment_start,
    {{ ke_tanggal(ab('employee_assignment_history', 'dt_assignment_end')) }}   as dt_assignment_end,
    {{ ke_int(ab('employee_assignment_history', 'assignment_duration_months')) }} as assignment_duration_months,
    {{ ab('employee_assignment_history', 'description') }}              as description,
    {{ kolom_teknis('angkasabiru') }}
from {{ source('raw_ab', 'employee_assignment_history') }} r
where {{ ab('employee_assignment_history', 'id_assignment_history') }} is not null
