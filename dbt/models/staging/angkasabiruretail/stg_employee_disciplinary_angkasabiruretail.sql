{#
  Mapping Angkasa Biru Retail: employee_disciplinary <- hukdis (endpoint lama):
    id_employee <- nik;  disciplinary_type <- hukdis_cat (apa adanya);  dt_disciplinary <- start_date;
    dt_disciplinary_end <- end_date;  is_aktif <- is_active.
#}
select
    {{ id_employee('angkasabiruretail', nip7(abr('hukdis', 'nik'))) }} as id_employee,
    {{ baku('angkasabiruretail', 'disciplinary_type', abr('hukdis', 'hukdis_cat')) }} as disciplinary_type,
    {{ ke_tanggal(abr('hukdis', 'start_date')) }} as dt_disciplinary,
    {{ ke_tanggal(abr('hukdis', 'end_date')) }}   as dt_disciplinary_end,
    {{ ke_boolean(abr('hukdis', 'is_active')) }}  as is_aktif,
    {{ kolom_teknis('angkasabiruretail') }}
from {{ source('raw_abr', 'hukdis') }} r
