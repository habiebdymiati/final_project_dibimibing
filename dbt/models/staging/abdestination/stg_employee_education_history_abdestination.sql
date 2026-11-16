{# Mapping ABD: employee_education_history <- employee_education_histories (jenjang sudah baku). #}
select distinct
    {{ id_employee('abdestination', abd('employee_education_histories', 'id_employee')) }} as id_employee,
    {{ abd('employee_education_histories', 'id_education_history') }}   as id_education_history,
    {{ abd('employee_education_histories', 'education_level_code') }}   as education_level_code,
    {{ abd('employee_education_histories', 'education_degree_type') }}  as education_degree_type,
    upper({{ abd('employee_education_histories', 'institution_name') }}) as institution_name,
    {{ abd('employee_education_histories', 'institution_country') }}    as institution_country,
    upper({{ abd('employee_education_histories', 'major') }})           as major,
    {{ ke_tanggal(abd('employee_education_histories', 'dt_start')) }}   as dt_start,
    {{ ke_tanggal(abd('employee_education_histories', 'dt_end')) }}     as dt_end,
    {{ ke_desimal(abd('employee_education_histories', 'final_score')) }} as final_score,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'employee_education_histories') }} r
where {{ abd('employee_education_histories', 'id_education_history') }} is not null
