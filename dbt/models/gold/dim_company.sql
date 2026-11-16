{# Satu baris per perusahaan; company_key sama dengan id_company di silver. #}
select id_company as company_key, kode_sumber as company_code, company_name, company_type
from ({{ dari_silver('company', 'id_company, company_name, company_type') }}) c
union all
select 'UNKNOWN', 'UNKNOWN', 'Tidak diketahui', null
