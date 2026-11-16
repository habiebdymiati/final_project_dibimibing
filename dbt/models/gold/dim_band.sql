{# Satu baris per jenjang band per perusahaan; tangganya berbeda antar perusahaan, band_code (BOD-n) yang seragam. #}
select
    id_band as band_key,
    band_code,
    band_name,
    band_sequence as band_order,
    band_category,
    job_class_min,
    job_class_max,
    source_system_code
from ({{ dari_silver('band', 'id_band, band_code, band_name, band_sequence, band_category, job_class_min, job_class_max') }}) b
