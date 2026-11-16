{# Mapping ABD: seluruh field band = DWH Generate, dari seed ref_band_abdestination. #}
select
    id_band, band_code, band_name, band_sequence, band_category, job_class_min, job_class_max,
    cast('abdestination' as text) as dwh_source_system,
    cast(null as text)          as dwh_batch_id,
    cast(null as timestamptz)   as dwh_extracted_at
from {{ ref('ref_band_abdestination') }}
where source_system = 'abdestination'
