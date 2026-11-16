{# Mapping ABD: position_master <- position_masters (nama kolom sama dengan target). #}
select
    {{ abd('position_masters', 'id_position_master') }}   as id_position_master,
    {{ abd('position_masters', 'position_master_name') }} as position_master_name,
    {{ abd('position_masters', 'fk_position_type_id') }}  as fk_position_type_id,
    {{ abd('position_masters', 'id_job_family') }}        as id_job_family,
    {{ abd('position_masters', 'id_job_function') }}      as id_job_function,
    {{ abd('position_masters', 'id_grade') }}             as id_grade,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'position_masters') }} r
where {{ abd('position_masters', 'id_position_master') }} is not null
