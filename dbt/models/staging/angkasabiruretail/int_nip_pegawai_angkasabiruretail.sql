{#
  Semesta NIP pegawai Angkasa Biru Retail yang membutuhkan id_employee, beserta TMT-nya.

  Angkasa Biru Retail memakai DUA nomor pegawai: id_employee (ID sistem baru, dipakai endpoint employee-profile,
  employee-personal-details, employee-address, employee-contracts) dan NIP lama 7 digit (dipakai semua endpoint lama
  sebagai `nik`/`code_member`, dan anehnya juga oleh kolom id_employee pada employee-assignment-histories,
  dan leave-histories). old_nip pada employee-profile adalah penghubung keduanya, jadi NIP lama dipakai
  sebagai kunci registri.
  TMT = employee-personal-details.dt_start_work (tanggal mulai bekerja).
#}
with nip as (
    select {{ abr('employee__profile', 'old_nip') }} as nip from {{ source('raw_abr', 'employee__profile') }} r
    union select {{ abr('employees', 'code_member') }} from {{ source('raw_abr', 'employees') }} r
    union select {{ nip7(abr('position_histories', 'nik')) }} from {{ source('raw_abr', 'position_histories') }} r
    union select {{ nip7(abr('educations', 'nik')) }} from {{ source('raw_abr', 'educations') }} r
    union select {{ nip7(abr('performances', 'nik')) }} from {{ source('raw_abr', 'performances') }} r
    union select {{ nip7(abr('hukdis', 'nik')) }} from {{ source('raw_abr', 'hukdis') }} r
    union select {{ nip7(abr('spouses', 'nik')) }} from {{ source('raw_abr', 'spouses') }} r
    union select {{ nip7(abr('childrens', 'nik')) }} from {{ source('raw_abr', 'childrens') }} r
    union select {{ nip7(abr('employee__assignment__histories', 'id_employee')) }} from {{ source('raw_abr', 'employee__assignment__histories') }} r
    union select {{ nip7(abr('leave__histories', 'id_employee')) }} from {{ source('raw_abr', 'leave__histories') }} r
    union select {{ abr('employee__address', 'old_nip') }} from {{ source('raw_abr', 'employee__address') }} r
    union select {{ abr('employee__contracts', 'old_nip') }} from {{ source('raw_abr', 'employee__contracts') }} r
),
tmt as (
    select {{ abr('employee__profile', 'old_nip', 'p') }} as nip,
           min({{ ke_tanggal(abr('employee__personal__details', 'dt_start_work', 'd')) }}) as dt_tmt
    from {{ source('raw_abr', 'employee__profile') }} p
    join {{ source('raw_abr', 'employee__personal__details') }} d
      on {{ abr('employee__personal__details', 'id_employee', 'd') }} = {{ abr('employee__profile', 'id_employee', 'p') }}
    group by 1
)
select
    cast('angkasabiruretail' as text) as source_system,
    n.nip,
    t.dt_tmt
from nip n
left join tmt t using (nip)
where n.nip is not null
