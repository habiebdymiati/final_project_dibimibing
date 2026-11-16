{# Mapping Angkasa Biru Retail: job_function <- job-function (nama kolom sama dengan target; API baru mengirim satu baris). #}
select
    {{ abr('job__function', 'id_job_function') }}   as id_job_function,
    {{ abr('job__function', 'fk_job_family_id') }}  as fk_job_family_id,
    upper({{ abr('job__function', 'job_function_name') }}) as job_function_name,
    {{ kolom_teknis('angkasabiruretail') }}
from {{ source('raw_abr', 'job__function') }} r
where {{ abr('job__function', 'id_job_function') }} is not null
