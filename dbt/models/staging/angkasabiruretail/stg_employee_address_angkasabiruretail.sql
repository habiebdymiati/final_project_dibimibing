{#
  Mapping Angkasa Biru Retail: employee_address <- employee-address (nama kolom sama dengan target).
  id_employee: kunci pegawai DWH dari registri, dicari lewat kolom old_nip endpoint ini.
  district, city, province, postal_code dikirim API tetapi kosong -> NULL.
#}
select
    {{ id_employee('angkasabiruretail', abr('employee__address', 'old_nip')) }} as id_employee,
    {{ baku('angkasabiruretail', 'address_type', abr('employee__address', 'address_type')) }} as address_type,
    upper({{ abr('employee__address', 'street_address') }}) as street_address,
    {{ abr('employee__address', 'district') }}       as district,
    {{ abr('employee__address', 'city') }}           as city,
    {{ abr('employee__address', 'province') }}       as province,
    {{ abr('employee__address', 'postal_code') }}    as postal_code,
    {{ kolom_teknis('angkasabiruretail') }}
from {{ source('raw_abr', 'employee__address') }} r
where {{ abr('employee__address', 'old_nip') }} is not null
