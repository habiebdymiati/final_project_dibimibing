{# Mapping ABD: job_function <- job_functions. #}
select
    {{ abd('job_functions', 'id_job_function') }}   as id_job_function,
    {{ abd('job_functions', 'fk_job_family_id') }}  as fk_job_family_id,
    upper({{ abd('job_functions', 'job_function_name') }}) as job_function_name,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'job_functions') }} r
where {{ abd('job_functions', 'id_job_function') }} is not null
