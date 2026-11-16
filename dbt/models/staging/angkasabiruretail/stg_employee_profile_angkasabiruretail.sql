{#
  Mapping Angkasa Biru Retail: employee_profile <- employee-profile, dilengkapi endpoint employees untuk penempatan.
    id_employee      = DWH Generate: VARCHAR dari registri (10 + 6 digit nomor urut menurut tanggal mulai bekerja), dicari lewat old_nip.
    old_nip          : apa adanya (NIP lama 7 digit, nol di depan dipertahankan).
    new_nip          : disamakan dengan old_nip (keputusan 07 Nov 2026). Kolom new_nip dari API tidak dipakai.
    area_name        <- employees.personnel_area_text (kode) dicari namanya di areas (code_area -> name_area).
    directorate_name <- employees.name_directorate;  org_group_name <- employees.name_group.
    band_name        : employees.band_name bila terisi; selama kosong diturunkan dari job_class pegawai lewat tangga band.
                       job_class di luar tangga (mis. 4B, 5) tidak punya band.
  Sambungan ke employees memakai old_nip = employees.code_member (employees memuat baris kembar identik -> disatukan).

  Pegawai yang hanya ada di endpoint employees (tidak dikirim employee-profile) ikut dimuat (keputusan 07 Nov 2026), dengan padanan:
    full_name <- personel_number (kolom ini berisi nama: sama dengan full_name pada semua pegawai yang ada di kedua endpoint),
    corporate_email <- email, employment_status <- status_aktif, photo_blob <- photo_blob, job_class <- person_grade.
  Harmonisasi: full_name huruf besar, email huruf kecil, employment_status aktif / tidak aktif.
#}
with pegawai as (
    select distinct on ({{ abr('employees', 'code_member', 'e') }})
        {{ abr('employees', 'code_member', 'e') }}         as nip,
        {{ abr('employees', 'personel_number', 'e') }}     as full_name,
        {{ abr('employees', 'email', 'e') }}               as corporate_email,
        {{ abr('employees', 'status_aktif', 'e') }}        as employment_status,
        {{ abr('employees', 'photo_blob', 'e') }}          as photo_blob,
        {{ abr('employees', 'person_grade', 'e') }}        as person_grade,
        {{ abr('employees', 'personnel_area_text', 'e') }} as kode_area,
        {{ abr('employees', 'name_directorate', 'e') }}    as directorate_name,
        {{ abr('employees', 'name_group', 'e') }}          as org_group_name,
        {{ abr('employees', 'band_name', 'e') }}           as band_name,
        e._batch_id, e._extracted_at
    from {{ source('raw_abr', 'employees') }} e
    where {{ abr('employees', 'code_member', 'e') }} is not null
    order by {{ abr('employees', 'code_member', 'e') }}, e._row_hash
),
area as (
    select {{ abr('areas', 'code_area', 'a') }} as kode_area, {{ abr('areas', 'name_area', 'a') }} as area_name
    from {{ source('raw_abr', 'areas') }} a
),
rinci as (
    select {{ abr('employee__personal__details', 'id_employee', 'd') }} as id_sistem,
           {{ abr('employee__personal__details', 'job_class', 'd') }}   as job_class
    from {{ source('raw_abr', 'employee__personal__details') }} d
),
profil as (
    select
        {{ abr('employee__profile', 'old_nip') }}           as old_nip,
        {{ abr('employee__profile', 'full_name') }}         as full_name,
        {{ abr('employee__profile', 'academic_title') }}    as academic_title,
        {{ abr('employee__profile', 'corporate_email') }}   as corporate_email,
        {{ abr('employee__profile', 'employment_status') }} as employment_status,
        {{ abr('employee__profile', 'photo_blob') }}        as photo_blob,
        d.job_class,
        r._batch_id, r._extracted_at
    from {{ source('raw_abr', 'employee__profile') }} r
    left join rinci d on d.id_sistem = {{ abr('employee__profile', 'id_employee') }}
    where {{ abr('employee__profile', 'old_nip') }} is not null
    union all
    select g.nip, g.full_name, cast(null as text), g.corporate_email, g.employment_status, g.photo_blob, g.person_grade,
           g._batch_id, g._extracted_at
    from pegawai g
    where not exists (select 1 from {{ source('raw_abr', 'employee__profile') }} p
                       where {{ abr('employee__profile', 'old_nip', 'p') }} = g.nip)
)
select
    {{ id_employee('angkasabiruretail', 'x.old_nip') }} as id_employee,
    x.old_nip                                  as old_nip,
    cast(x.old_nip as varchar)                 as new_nip,
    upper(x.full_name)                         as full_name,
    x.academic_title                           as academic_title,
    lower(x.corporate_email)                   as corporate_email,
    {{ baku('angkasabiruretail', 'employment_status', 'x.employment_status') }} as employment_status,
    x.photo_blob                               as photo_blob,
    a.area_name                                as area_name,
    g.directorate_name                         as directorate_name,
    g.org_group_name                           as org_group_name,
    coalesce(g.band_name, b.band_name)         as band_name,
    {{ kolom_teknis('angkasabiruretail', 'x') }}
from profil x
left join pegawai g on g.nip = x.old_nip
left join area a on a.kode_area = g.kode_area
left join {{ ref('ref_band_angkasabiruretail') }} b
       on {{ ke_int('x.job_class') }} between b.job_class_min and b.job_class_max
