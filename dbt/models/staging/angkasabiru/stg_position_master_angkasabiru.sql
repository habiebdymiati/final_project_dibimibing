{#
  Mapping AB: position_master <- position_master (id_position_master, position_master_name, id_job_family,
  id_job_function, id_grade). fk_position_type_id tidak ada di mapping; kolom bernama sama ada di raw -> dibawa.
#}
select
    {{ ab('position_master', 'id_position_master') }}   as id_position_master,
    {{ ab('position_master', 'position_master_name') }} as position_master_name,
    {{ ab('position_master', 'fk_position_type_id') }}  as fk_position_type_id,
    {{ ab('position_master', 'id_job_family') }}        as id_job_family,
    {{ ab('position_master', 'id_job_function') }}      as id_job_function,
    {{ ab('position_master', 'id_grade') }}             as id_grade,
    {{ kolom_teknis('angkasabiru') }}
from {{ source('raw_ab', 'position_master') }} r
where {{ ab('position_master', 'id_position_master') }} is not null
