{#
  Mapping Angkasa Biru Retail: org_unit <- org-units (id_org_unit, org_unit_name, org_level, id_parent_org_unit apa adanya dari API).
  fk_id_company: API mengirim 0 untuk semua unit (bukan id perusahaan), sehingga diisi id_company Angkasa Biru Retail (DWH Generate,
  seed ref_company_angkasabiruretail), sama dengan company_angkasabiruretail.id_company.
#}
select
    {{ abr('org__units', 'id_org_unit') }}        as id_org_unit,
    {{ abr('org__units', 'org_unit_name') }}      as org_unit_name,
    {{ ke_int(abr('org__units', 'org_level')) }} as org_level,
    {{ abr('org__units', 'id_parent_org_unit') }} as id_parent_org_unit,
    (select id_company from {{ ref('ref_company_angkasabiruretail') }}) as fk_id_company,
    {{ kolom_teknis('angkasabiruretail') }}
from {{ source('raw_abr', 'org__units') }} r
where {{ abr('org__units', 'id_org_unit') }} is not null
