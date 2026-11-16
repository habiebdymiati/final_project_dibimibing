{# Jenis hubungan kerja yang benar-benar dipakai pegawai; nilainya sudah seragam sejak silver. #}
select distinct
    contract_type_key,
    contract_type_key as contract_type,
    case contract_type_key
        when 'PKWTT' then 'Perjanjian Kerja Waktu Tidak Tertentu (Tetap)'
        when 'PKWT' then 'Perjanjian Kerja Waktu Tertentu (Kontrak)'
        when 'UNKNOWN' then 'Tidak diketahui'
        else contract_type_key end as contract_type_name
from (select contract_type_key from {{ ref('int_employee_metrics') }} union all select 'UNKNOWN') t
