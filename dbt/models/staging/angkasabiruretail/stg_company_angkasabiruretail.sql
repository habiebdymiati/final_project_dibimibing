{#
  Mapping Angkasa Biru Retail: company.
    id_company, company_type = DWH Generate (seed ref_company_angkasabiruretail): AB-COMP-ABR, Member (keputusan 07 Nov 2026).
    company_name, dt_establishment <- companies (API mengirim satu baris perusahaan).
  dwh_source_system: kode sumber buatan DWH.
#}
select
    s.id_company                                as id_company,
    {{ abr('companies', 'company_name') }}      as company_name,
    s.company_type                              as company_type,
    {{ ke_tanggal(abr('companies', 'dt_establishment')) }} as dt_establishment,
    {{ kolom_teknis('angkasabiruretail') }}
from {{ source('raw_abr', 'companies') }} r
cross join {{ ref('ref_company_angkasabiruretail') }} s
where {{ abr('companies', 'id_company') }} is not null
