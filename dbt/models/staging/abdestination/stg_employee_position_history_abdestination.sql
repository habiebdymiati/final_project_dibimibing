{# Mapping ABD: employee_position_history <- employee_position_histories (nama kolom sama dengan target). #}
select
    {{ abd('employee_position_histories', 'id_position_history') }}    as id_position_history,
    cast({{ abd('employee_position_histories', 'new_nip') }} as varchar) as new_nip,
    {{ abd('employee_position_histories', 'fk_position_variant_id') }} as fk_position_variant_id,
    {{ abd('employee_position_histories', 'position_name') }}          as position_name,
    {{ abd('employee_position_histories', 'position_type') }}          as position_type,
    {{ ke_int(abd('employee_position_histories', 'job_class')) }}      as job_class,
    {{ abd('employee_position_histories', 'org_unit_name') }}          as org_unit_name,
    {{ abd('employee_position_histories', 'company_name') }}           as company_name,
    {{ ke_tanggal(abd('employee_position_histories', 'dt_position_start')) }} as dt_position_start,
    {{ ke_tanggal(abd('employee_position_histories', 'dt_position_end')) }}   as dt_position_end,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'employee_position_histories') }} r
where {{ abd('employee_position_histories', 'id_position_history') }} is not null
