{#
  Semesta NIP pegawai Angkasa Biru yang membutuhkan id_employee, beserta TMT-nya.
  NIP dikumpulkan dari berkas referensi TMT dan dari setiap tabel raw yang membawa kunci pegawai, supaya
  baris anak (cuti, pembelajaran, dst.) milik pegawai yang tidak ada di employee_profile tetap punya ID.
  TMT diambil dari berkas referensi "Data Tanggal Lahir Angkasa Biru Indonesia.csv" (kolom Tmt karyawan).
#}
with nip as (
    select nullif(btrim(new_nip), '') as nip from {{ source('ref_ab', 'tmt_karyawan_angkasabiru') }}
    union select {{ ab('employee_profile', 'new_nip') }} from {{ source('raw_ab', 'employee_profile') }} r
    union select {{ ab('employee_identification', 'id_employee') }} from {{ source('raw_ab', 'employee_identification') }} r
    union select {{ ab('employee_address', ['id_employee', 'nik_new']) }} from {{ source('raw_ab', 'employee_address') }} r
    union select {{ ab('employee_family_member', 'id_employee') }} from {{ source('raw_ab', 'employee_family_member') }} r
    union select {{ ab('employee_assignment_history', 'id_employee') }} from {{ source('raw_ab', 'employee_assignment_history') }} r
    union select {{ ab('employee_performance', 'id_employee') }} from {{ source('raw_ab', 'employee_performance') }} r
    union select {{ ab('employee_leave_history', 'id_employee') }} from {{ source('raw_ab', 'employee_leave_history') }} r
    union select {{ ab('employee_education_history', ['id_employee', 'id_emloyee']) }} from {{ source('raw_ab', 'employee_education_history') }} r
),
tmt as (
    select nullif(btrim(new_nip), '') as nip, min(public.try_date(tmt_karyawan)) as dt_tmt
    from {{ source('ref_ab', 'tmt_karyawan_angkasabiru') }}
    group by 1
)
select
    cast('angkasabiru' as text) as source_system,
    n.nip,
    t.dt_tmt
from nip n
left join tmt t using (nip)
where n.nip is not null
