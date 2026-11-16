{# Mapping ABD: job_family <- job_families. #}
select
    {{ abd('job_families', 'id_job_family') }}   as id_job_family,
    upper({{ abd('job_families', 'job_family_name') }}) as job_family_name,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'job_families') }} r
where {{ abd('job_families', 'id_job_family') }} is not null
