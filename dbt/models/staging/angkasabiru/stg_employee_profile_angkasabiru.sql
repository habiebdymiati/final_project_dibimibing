{#
  Mapping AB: employee_profile <- employee_profile, kecuali:
    id_employee       = DWH Generate: VARCHAR 8 digit dari registri (10 + 6 digit nomor urut menurut tahun masuk / TMT karyawan)
    new_nip           : VARCHAR, apa adanya dari API (NIP adalah pengenal, bukan bilangan).
    area_name         <- NAMA area: positions.area dari varian posisi TERAKHIR pegawai (per new_nip), dicari di
                         branches (CODE_AREA -> NAME_AREA) (keputusan 06 Nov 2026)
  employment_status : kolom di raw bernama "employee_status".
  old_nip           : apa adanya dari API (teks; di sumber berisi huruf/tanda hubung dan nol di depan).
  photo_blob        : mapping merujuk kolom employee_profile yang belum dikirim API -> NULL sampai kolomnya ada.
  directorate_name, org_group_name, band_name: mapping merujuk kolom employee_profile yang belum dikirim API.
                      Selama belum dikirim, diisi dari posisi terkini pegawai (keputusan 06 Nov 2026, rinciannya di
                      int_posisi_terkini_angkasabiru): direktorat lewat kode posisi (cadangan: nama posisi),
                      group lewat kode posisi, band dari job_class lewat tangga band.
                      Begitu API mengirim kolomnya, nilai API yang dipakai.
  area_name, directorate_name, org_group_name: kosong dari API -> nominatif 8 September 2026 (int_nominatif_angkasabiru).
#}
select
    {{ id_employee('angkasabiru', ab('employee_profile', 'new_nip')) }} as id_employee,
    {{ ab('employee_profile', 'old_nip') }}                          as old_nip,
    cast({{ ab('employee_profile', 'new_nip') }} as varchar)         as new_nip,
    upper({{ ab('employee_profile', 'full_name') }}) as full_name,
    {{ ab('employee_profile', 'academic_title') }}                   as academic_title,
    lower({{ ab('employee_profile', 'corporate_email') }}) as corporate_email,
    {{ baku('angkasabiru', 'employment_status', ab('employee_profile', ['employment_status', 'employee_status'])) }} as employment_status,
    {{ ab('employee_profile', 'photo_blob') }}                       as photo_blob,
    t.area_name                                                      as area_name,
    {{ baku('angkasabiru', 'directorate_name', "coalesce(" ~ ab('employee_profile', 'directorate_name') ~ ", t.directorate_name)") }} as directorate_name,
    coalesce({{ ab('employee_profile', 'org_group_name') }}, t.org_group_name)     as org_group_name,
    coalesce({{ ab('employee_profile', 'band_name') }}, b.band_name) as band_name,
    {{ kolom_teknis('angkasabiru') }}
from {{ source('raw_ab', 'employee_profile') }} r
left join {{ ref('int_posisi_terkini_angkasabiru') }} t
       on t.new_nip = {{ ab('employee_profile', 'new_nip') }}
left join {{ ref('ref_band_angkasabiru') }} b
       on b.source_system = 'angkasabiru'
      and {{ ke_int('t.job_class') }} between b.job_class_min and b.job_class_max
where {{ ab('employee_profile', 'new_nip') }} is not null
