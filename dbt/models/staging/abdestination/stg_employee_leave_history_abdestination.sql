{# Mapping ABD: employee_leave_history <- employee_leave_histories (nilai sudah baku Cuti/Izin). #}
select
    {{ id_employee('abdestination', abd('employee_leave_histories', 'id_employee')) }} as id_employee,
    {{ abd('employee_leave_histories', 'id_leave_history') }}       as id_leave_history,
    {{ abd('employee_leave_histories', 'leave_type') }}             as leave_type,
    {{ ke_tanggal(abd('employee_leave_histories', 'dt_leave_start')) }} as dt_leave_start,
    {{ ke_tanggal(abd('employee_leave_histories', 'dt_leave_end')) }}   as dt_leave_end,
    {{ ke_desimal(abd('employee_leave_histories', 'leave_duration_days')) }} as leave_duration_days,
    {{ abd('employee_leave_histories', 'leave_status') }}           as leave_status,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'employee_leave_histories') }} r
where {{ abd('employee_leave_histories', 'id_leave_history') }} is not null
