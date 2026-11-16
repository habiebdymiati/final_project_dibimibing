{#
  Mapping Angkasa Biru Retail: employee_contract <- employee-contracts (nama kolom sama dengan target).
  id_employee: kunci pegawai DWH dari registri, dicari lewat old_nip. dt_contract_start: stempel waktu ISO UTC -> tanggal WIB.
  contract_number dan dt_contract_end dikirim API tetapi kosong -> NULL.
#}
select
    {{ abr('employee__contracts', 'id_contract') }}     as id_contract,
    {{ id_employee('angkasabiruretail', abr('employee__contracts', 'old_nip')) }} as id_employee,
    {{ abr('employee__contracts', 'contract_number') }} as contract_number,
    {{ baku('angkasabiruretail', 'contract_type', abr('employee__contracts', 'contract_type')) }} as contract_type,
    {{ ke_tanggal(abr('employee__contracts', 'dt_contract_start')) }} as dt_contract_start,
    {{ ke_tanggal(abr('employee__contracts', 'dt_contract_end')) }}   as dt_contract_end,
    {{ baku('angkasabiruretail', 'contract_status', abr('employee__contracts', 'contract_status')) }} as contract_status,
    {{ kolom_teknis('angkasabiruretail') }}
from {{ source('raw_abr', 'employee__contracts') }} r
where {{ abr('employee__contracts', 'id_contract') }} is not null
