{# Mapping Angkasa Biru Retail: seluruh field band = DWH Generate, dari seed ref_band_angkasabiruretail (tangga band per rentang job_class). #}
select
    id_band,
    band_code,
    band_name,
    band_sequence,
    band_category,
    job_class_min,
    job_class_max,
    cast('angkasabiruretail' as text)       as dwh_source_system,
    cast(null as text)            as dwh_batch_id,
    cast(null as timestamptz)     as dwh_extracted_at
from {{ ref('ref_band_angkasabiruretail') }}
