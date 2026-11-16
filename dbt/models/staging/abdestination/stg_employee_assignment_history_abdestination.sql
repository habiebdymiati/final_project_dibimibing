{# Mapping ABD: employee_assignment_history <- employee_assignment_histories (nilai assignment_name sudah baku). #}
select
    {{ id_employee('abdestination', abd('employee_assignment_histories', 'id_employee')) }} as id_employee,
    {{ abd('employee_assignment_histories', 'id_assignment_history') }}      as id_assignment_history,
    {{ abd('employee_assignment_histories', 'assignment_name') }}            as assignment_name,
    {{ abd('employee_assignment_histories', 'assignment_position') }}        as assignment_position,
    {{ abd('employee_assignment_histories', 'assignment_letter_number') }}   as assignment_letter_number,
    {{ abd('employee_assignment_histories', 'assignment_letter_blob') }}     as assignment_letter_blob,
    {{ ke_tanggal(abd('employee_assignment_histories', 'dt_assignment_start')) }} as dt_assignment_start,
    {{ ke_tanggal(abd('employee_assignment_histories', 'dt_assignment_end')) }}   as dt_assignment_end,
    {{ ke_int(abd('employee_assignment_histories', 'assignment_duration_months')) }} as assignment_duration_months,
    {{ abd('employee_assignment_histories', 'description') }}                as description,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'employee_assignment_histories') }} r
where {{ abd('employee_assignment_histories', 'id_assignment_history') }} is not null
