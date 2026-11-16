{#
  Mapping Angkasa Biru Retail: employee_position_history <- position_histories (endpoint lama):
    id_position_history <- id;  new_nip <- nik (NIP lama; nol di depan dikembalikan);  fk_position_variant_id <- position_code;
    position_name <- position_name;  job_class <- grade_name (hanya angka);  org_unit_name <- division_name;
    company_name <- perusahaan;  dt_position_start <- start_date;  dt_position_end <- end_date.
  position_type tidak punya sumber -> NULL.
#}
select
    {{ abr('position_histories', 'id') }}            as id_position_history,
    cast({{ nip7(abr('position_histories', 'nik')) }} as varchar) as new_nip,
    {{ abr('position_histories', 'position_code') }} as fk_position_variant_id,
    {{ abr('position_histories', 'position_name') }} as position_name,
    cast(null as text)                         as position_type,
    {{ ke_int(abr('position_histories', 'grade_name')) }} as job_class,
    {{ abr('position_histories', 'division_name') }} as org_unit_name,
    {{ baku('angkasabiruretail', 'company_name', abr('position_histories', 'perusahaan')) }} as company_name,
    {{ ke_tanggal(abr('position_histories', 'start_date')) }} as dt_position_start,
    {{ ke_tanggal(abr('position_histories', 'end_date')) }}   as dt_position_end,
    {{ kolom_teknis('angkasabiruretail') }}
from {{ source('raw_abr', 'position_histories') }} r
where {{ abr('position_histories', 'id') }} is not null
