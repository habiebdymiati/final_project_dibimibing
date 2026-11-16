{# Mapping AB: job_family <- job_families (id_job_family, job_family_name). #}
select
    {{ ab('job_families', 'id_job_family') }}   as id_job_family,
    upper({{ ab('job_families', 'job_family_name') }}) as job_family_name,
    {{ kolom_teknis('angkasabiru') }}
from {{ source('raw_ab', 'job_families') }} r
where {{ ab('job_families', 'id_job_family') }} is not null
