{# Mapping ABD: employee_performance_history <- employee_performance_histories (skor 0-100 langsung dari API). #}
select
    {{ id_employee('abdestination', abd('employee_performance_histories', 'id_employee')) }} as id_employee,
    {{ abd('employee_performance_histories', 'id_performance_history') }}      as id_performance_history,
    {{ ke_int(abd('employee_performance_histories', 'period_year')) }}         as period_year,
    {{ ke_desimal(abd('employee_performance_histories', 'performance_score')) }} as performance_score,
    {{ abd('employee_performance_histories', 'performance_rating') }}          as performance_rating,
    {{ ke_desimal(abd('employee_performance_histories', 'pct_kpi_achievement')) }} as pct_kpi_achievement,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'employee_performance_histories') }} r
where {{ abd('employee_performance_histories', 'id_performance_history') }} is not null
