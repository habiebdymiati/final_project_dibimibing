{# Mapping AB: seluruh field company = DWH Generate (seed ref_company_angkasabiru). dwh_source_system: kode sumber buatan DWH. #}
select
    id_company,
    company_name,
    company_type,
    dt_establishment,
    cast('angkasabiru' as text)   as dwh_source_system,
    cast(null as text)            as dwh_batch_id,
    cast(null as timestamptz)     as dwh_extracted_at
from {{ ref('ref_company_angkasabiru') }}
where source_system = 'angkasabiru'
