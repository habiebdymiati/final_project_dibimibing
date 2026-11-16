{#
  Mapping Angkasa Biru Retail: employee_identification <- employee-personal-details (nama kolom sama dengan target).
  id_employee : kunci pegawai DWH dari registri; endpoint ini memakai ID sistem baru, jadi NIP lamanya diambil dari
                employee-profile (id_employee yang sama).
  mobile_phone: distandarkan berawalan 08.  job_class: apa adanya dari API (memuat kelas berhuruf seperti 4B).
  dt_retirement, dt_appointed_employee, dt_grade_start: dikirim API tetapi kosong -> NULL.
#}
select
    {{ id_employee('angkasabiruretail', abr('employee__profile', 'old_nip', 'p')) }} as id_employee,
    {{ abr('employee__personal__details', 'id_nik') }}          as id_nik,
    {{ hanya_angka(abr('employee__personal__details', 'id_npwp')) }} as id_npwp,
    upper({{ abr('employee__personal__details', 'birth_place') }}) as birth_place,
    {{ ke_tanggal(abr('employee__personal__details', 'dt_birth')) }}              as dt_birth,
    {{ ke_tanggal(abr('employee__personal__details', 'dt_start_work')) }}         as dt_start_work,
    {{ ke_tanggal(abr('employee__personal__details', 'dt_retirement')) }}         as dt_retirement,
    {{ ke_tanggal(abr('employee__personal__details', 'dt_appointed_employee')) }} as dt_appointed_employee,
    {{ ke_tanggal(abr('employee__personal__details', 'dt_grade_start')) }}        as dt_grade_start,
    {{ abr('employee__personal__details', 'employment_type') }} as employment_type,
    {{ abr('employee__personal__details', 'job_class') }}       as job_class,
    {{ baku('angkasabiruretail', 'gender', abr('employee__personal__details', 'gender')) }} as gender,
    {{ ke_ponsel(abr('employee__personal__details', 'mobile_phone')) }} as mobile_phone,
    lower({{ abr('employee__personal__details', 'corporate_email') }}) as corporate_email,
    {{ kolom_teknis('angkasabiruretail') }}
from {{ source('raw_abr', 'employee__personal__details') }} r
join {{ source('raw_abr', 'employee__profile') }} p
  on {{ abr('employee__profile', 'id_employee', 'p') }} = {{ abr('employee__personal__details', 'id_employee') }}
