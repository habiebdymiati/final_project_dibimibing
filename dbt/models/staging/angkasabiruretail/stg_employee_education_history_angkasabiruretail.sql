{#
  Mapping Angkasa Biru Retail: employee_education_history <- educations (endpoint lama):
    id_employee <- nik;  education_level_code <- level_education;  institution_name <- university_name;
    institution_country <- kota_negara (kosong di API);  major <- major_name;  dt_start <- start_date;  dt_end <- end_date;
    final_score <- ipk.
  id_education_history: sumber tidak menyediakan id -> kunci buatan DWH dari isi baris; baris kembar identik disatukan.
  education_level_code dan education_degree_type diseragamkan dari level_education ke kode dan jenjang Angkasa Biru (seed map_nilai_angkasabiruretail).
#}
select distinct
    {{ id_employee('angkasabiruretail', nip7(abr('educations', 'nik'))) }} as id_employee,
    'AB-EDU-ABR-' || md5(r._row_hash)       as id_education_history,
    {{ baku('angkasabiruretail', 'education_level_code', abr('educations', 'level_education')) }} as education_level_code,
    {{ baku('angkasabiruretail', 'education_degree_type', abr('educations', 'level_education')) }} as education_degree_type,
    upper({{ abr('educations', 'university_name') }}) as institution_name,
    {{ abr('educations', 'kota_negara') }}         as institution_country,
    upper({{ abr('educations', 'major_name') }}) as major,
    {{ ke_tanggal(abr('educations', 'start_date')) }} as dt_start,
    {{ ke_tanggal(abr('educations', 'end_date')) }}   as dt_end,
    {{ ke_desimal(abr('educations', 'ipk')) }}        as final_score,
    {{ kolom_teknis('angkasabiruretail') }}
from {{ source('raw_abr', 'educations') }} r
