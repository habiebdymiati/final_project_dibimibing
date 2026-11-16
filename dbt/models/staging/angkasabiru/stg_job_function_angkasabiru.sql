{#
  Mapping AB: job_function <- job_functions (id_job_function, job_function_name).
  fk_job_family_id tidak ada di mapping; kolom bernama sama ada di raw -> dibawa.
#}
select
    {{ ab('job_functions', 'id_job_function') }}   as id_job_function,
    {{ ab('job_functions', 'fk_job_family_id') }}  as fk_job_family_id,
    upper({{ ab('job_functions', 'job_function_name') }}) as job_function_name,
    {{ kolom_teknis('angkasabiru') }}
from {{ source('raw_ab', 'job_functions') }} r
where {{ ab('job_functions', 'id_job_function') }} is not null
