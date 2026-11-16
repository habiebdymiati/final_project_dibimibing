{# Mapping ABD: employee_address <- employee_addresses. #}
select
    {{ id_employee('abdestination', abd('employee_addresses', 'id_employee')) }} as id_employee,
    {{ abd('employee_addresses', 'address_type') }}   as address_type,
    upper({{ abd('employee_addresses', 'street_address') }}) as street_address,
    {{ abd('employee_addresses', 'district') }}       as district,
    {{ abd('employee_addresses', 'city') }}           as city,
    {{ abd('employee_addresses', 'province') }}       as province,
    {{ abd('employee_addresses', 'postal_code') }}    as postal_code,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'employee_addresses') }} r
where {{ abd('employee_addresses', 'id_employee') }} is not null
