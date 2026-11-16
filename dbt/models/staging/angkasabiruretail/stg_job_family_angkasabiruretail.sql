{# Mapping Angkasa Biru Retail: job_family <- job_families (id_job_family <- code_job_family, job_family_name <- name_job_family). #}
select
    {{ abr('job_families', 'code_job_family') }} as id_job_family,
    upper({{ abr('job_families', 'name_job_family') }}) as job_family_name,
    {{ kolom_teknis('angkasabiruretail') }}
from {{ source('raw_abr', 'job_families') }} r
where {{ abr('job_families', 'code_job_family') }} is not null
