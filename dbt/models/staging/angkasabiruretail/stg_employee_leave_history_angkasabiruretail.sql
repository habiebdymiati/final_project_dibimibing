{#
  Mapping Angkasa Biru Retail: employee_leave_history <- leave-histories (nama kolom sama dengan target; API baru mengirim satu baris).
  id_employee: kolom id_employee endpoint ini berisi NIP LAMA -> dipetakan ke kunci pegawai DWH.
#}
select
    {{ id_employee('angkasabiruretail', nip7(abr('leave__histories', 'id_employee'))) }} as id_employee,
    {{ abr('leave__histories', 'id_leave_history') }} as id_leave_history,
    {{ baku('angkasabiruretail', 'leave_type', abr('leave__histories', 'leave_type')) }} as leave_type,
    {{ ke_tanggal(abr('leave__histories', 'dt_leave_start')) }} as dt_leave_start,
    {{ ke_tanggal(abr('leave__histories', 'dt_leave_end')) }}   as dt_leave_end,
    {{ ke_desimal(abr('leave__histories', 'leave_duration_days')) }} as leave_duration_days,
    {{ baku('angkasabiruretail', 'leave_status', abr('leave__histories', 'leave_status')) }} as leave_status,
    {{ kolom_teknis('angkasabiruretail') }}
from {{ source('raw_abr', 'leave__histories') }} r
where {{ abr('leave__histories', 'id_leave_history') }} is not null
