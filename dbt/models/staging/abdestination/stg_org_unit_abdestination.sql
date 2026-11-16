{# Mapping ABD: org_unit <- org_units; fk_id_company dari seed (sama dengan company_abdestination.id_company). #}
select
    {{ abd('org_units', 'id_org_unit') }}        as id_org_unit,
    {{ abd('org_units', 'org_unit_name') }}      as org_unit_name,
    {{ ke_int(abd('org_units', 'org_level')) }}  as org_level,
    {{ abd('org_units', 'id_parent_org_unit') }} as id_parent_org_unit,
    (select id_company from {{ ref('ref_company_abdestination') }}) as fk_id_company,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'org_units') }} r
where {{ abd('org_units', 'id_org_unit') }} is not null
