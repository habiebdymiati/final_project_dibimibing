{# Mapping ABD: company <- companies; id_company dan company_type dari seed ref_company_abdestination (AB-COMP-ABD). #}
select
    (select id_company from {{ ref('ref_company_abdestination') }}) as id_company,
    {{ abd('companies', 'company_name') }}                  as company_name,
    (select company_type from {{ ref('ref_company_abdestination') }}) as company_type,
    {{ ke_tanggal(abd('companies', 'dt_establishment')) }}  as dt_establishment,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'companies') }} r
