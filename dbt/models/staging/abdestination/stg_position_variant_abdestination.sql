{# Mapping ABD: position_variant <- position_variants; fk_band_id diturunkan dari job_class lewat tangga band. #}
with v as (
    select
        {{ abd('position_variants', 'id_position_variant') }}   as id_position_variant,
        {{ abd('position_variants', 'fk_position_master_id') }} as fk_position_master_id,
        {{ abd('position_variants', 'position_variant_name') }} as position_variant_name,
        {{ abd('position_variants', 'fk_org_unit_id') }}        as fk_org_unit_id,
        case when {{ abd('position_variants', 'job_class') }} ~ '^[0-9]{1,4}$'
             then cast({{ abd('position_variants', 'job_class') }} as smallint) end as job_class,
        {{ ke_tanggal(abd('position_variants', 'dt_active')) }}   as dt_active,
        {{ ke_tanggal(abd('position_variants', 'dt_inactive')) }} as dt_inactive,
        r._batch_id, r._extracted_at
    from {{ source('raw_abd', 'position_variants') }} r
)
select
    r.id_position_variant, r.fk_position_master_id, r.position_variant_name, r.fk_org_unit_id,
    r.job_class, b.id_band as fk_band_id, r.dt_active, r.dt_inactive,
    cast('abdestination' as text) as dwh_source_system, r._batch_id as dwh_batch_id, r._extracted_at as dwh_extracted_at
from v r
left join {{ ref('ref_band_abdestination') }} b on r.job_class between b.job_class_min and b.job_class_max
where r.id_position_variant is not null
