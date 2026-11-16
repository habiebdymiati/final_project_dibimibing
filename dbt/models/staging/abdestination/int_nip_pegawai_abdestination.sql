{#
  Semesta NIP pegawai Angkasa Biru Destinasi beserta TMT-nya. API NATA RINJANI memakai satu pengenal
  (id_employee = new_nip = old_nip), jadi semesta = profiles + semua tabel anak yang membawa kunci pegawai.
  TMT = employee_identifications.dt_start_work.
#}
with nip as (
    select {{ abd('employee_profiles', 'new_nip') }} as nip from {{ source('raw_abd', 'employee_profiles') }} r
    union select {{ abd('employee_identifications', 'id_employee') }} from {{ source('raw_abd', 'employee_identifications') }} r
    union select {{ abd('employee_addresses', 'id_employee') }} from {{ source('raw_abd', 'employee_addresses') }} r
    union select {{ abd('employee_family_members', 'id_employee') }} from {{ source('raw_abd', 'employee_family_members') }} r
    union select {{ abd('employee_contracts', 'id_employee') }} from {{ source('raw_abd', 'employee_contracts') }} r
    union select {{ abd('employee_position_histories', 'new_nip') }} from {{ source('raw_abd', 'employee_position_histories') }} r
    union select {{ abd('employee_assignment_histories', 'id_employee') }} from {{ source('raw_abd', 'employee_assignment_histories') }} r
    union select {{ abd('employee_performance_histories', 'id_employee') }} from {{ source('raw_abd', 'employee_performance_histories') }} r
    union select {{ abd('employee_leave_histories', 'id_employee') }} from {{ source('raw_abd', 'employee_leave_histories') }} r
    union select {{ abd('employee_education_histories', 'id_employee') }} from {{ source('raw_abd', 'employee_education_histories') }} r
    union select {{ abd('learning_histories', 'id_employee') }} from {{ source('raw_abd', 'learning_histories') }} r
),
tmt as (
    select {{ abd('employee_identifications', 'id_employee') }} as nip,
           min({{ ke_tanggal(abd('employee_identifications', 'dt_start_work')) }}) as dt_tmt
    from {{ source('raw_abd', 'employee_identifications') }} r
    group by 1
)
select cast('abdestination' as text) as source_system, n.nip, t.dt_tmt
from nip n left join tmt t using (nip)
where n.nip is not null
