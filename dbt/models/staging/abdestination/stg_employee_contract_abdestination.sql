{# Mapping ABD: employee_contract <- employee_contracts (transaction/contracts; nilai sudah baku). #}
select
    {{ abd('employee_contracts', 'id_contract') }}       as id_contract,
    {{ id_employee('abdestination', abd('employee_contracts', 'id_employee')) }} as id_employee,
    {{ abd('employee_contracts', 'contract_number') }}   as contract_number,
    {{ abd('employee_contracts', 'contract_type') }}     as contract_type,
    {{ ke_tanggal(abd('employee_contracts', 'dt_contract_start')) }} as dt_contract_start,
    {{ ke_tanggal(abd('employee_contracts', 'dt_contract_end')) }}   as dt_contract_end,
    {{ abd('employee_contracts', 'contract_status') }}   as contract_status,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'employee_contracts') }} r
where {{ abd('employee_contracts', 'id_contract') }} is not null
