{#
  Mapping AB: employee_address <- employee_address. API saat ini hanya mengirim dua kolom:
    id_employee    : kolom di raw bernama "nik_new"
    street_address : kolom di raw bernama "Alamat"
  address_type, district, city, province, postal_code belum dikirim API -> NULL sampai kolomnya ada.
#}
select
    {{ id_employee('angkasabiru', ab('employee_address', ['id_employee', 'nik_new'])) }} as id_employee,
    {{ ab('employee_address', 'address_type') }}               as address_type,
    upper({{ ab('employee_address', ['street_address', 'Alamat']) }}) as street_address,
    {{ ab('employee_address', 'district') }}                   as district,
    {{ ab('employee_address', 'city') }}                       as city,
    {{ ab('employee_address', 'province') }}                   as province,
    {{ ab('employee_address', 'postal_code') }}                as postal_code,
    {{ kolom_teknis('angkasabiru') }}
from {{ source('raw_ab', 'employee_address') }} r
where {{ ab('employee_address', ['id_employee', 'nik_new']) }} is not null
