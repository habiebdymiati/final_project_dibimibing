{#
  Mapping AB: employee_leave_history <- employee_leave_history.
  id_leave_history: sumber tidak menyediakan id -> kunci buatan DWH dari isi baris; baris kembar identik disatukan.
#}
select distinct
    {{ id_employee('angkasabiru', ab('employee_leave_history', 'id_employee')) }} as id_employee,
    coalesce({{ ab('employee_leave_history', 'id_leave_history') }}, 'AB-LEAVE-AB-' || md5(r._row_hash)) as id_leave_history,
    {{ baku('angkasabiru', 'leave_type', ab('employee_leave_history', 'leave_type')) }} as leave_type,
    {{ ke_tanggal(ab('employee_leave_history', 'dt_leave_start')) }}     as dt_leave_start,
    {{ ke_tanggal(ab('employee_leave_history', 'dt_leave_end')) }}       as dt_leave_end,
    {{ ke_desimal(ab('employee_leave_history', 'leave_duration_days')) }} as leave_duration_days,
    {{ baku('angkasabiru', 'leave_status', ab('employee_leave_history', 'leave_status')) }} as leave_status,
    {{ kolom_teknis('angkasabiru') }}
from {{ source('raw_ab', 'employee_leave_history') }} r
