{#
  Mapping Angkasa Biru Retail: position_master <- positions (endpoint lama):
    id_position_master <- code_position, position_master_name <- name_position, fk_position_type_id <- code_position_type,
    id_job_family <- code_job_family, id_grade <- grade_min. id_job_function tidak punya sumber -> NULL.
  code_position kembar di sumber (10 kode) disatukan: diutamakan baris berstatus aktif.
#}
select
    id_position_master, position_master_name, fk_position_type_id, id_job_family, id_job_function, id_grade,
    dwh_source_system, dwh_batch_id, dwh_extracted_at
from (
    select distinct on ({{ abr('positions', 'code_position') }})
        {{ abr('positions', 'code_position') }}      as id_position_master,
        {{ abr('positions', 'name_position') }}      as position_master_name,
        {{ abr('positions', 'code_position_type') }} as fk_position_type_id,
        {{ abr('positions', 'code_job_family') }}    as id_job_family,
        cast(null as text)                     as id_job_function,
        {{ abr('positions', 'grade_min') }}          as id_grade,
        {{ kolom_teknis('angkasabiruretail') }}
    from {{ source('raw_abr', 'positions') }} r
    where {{ abr('positions', 'code_position') }} is not null
    order by {{ abr('positions', 'code_position') }}, ({{ abr('positions', 'status_aktif') }} = 'aktif') desc nulls last, r._row_hash
) x
