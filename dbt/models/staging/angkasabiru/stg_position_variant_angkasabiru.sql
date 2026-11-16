{#
  Mapping AB: position_variant <- position_variants (id_position_variant, position_variant_name, job_class).
  job_class: hanya nilai angka yang menjadi TINYINT; teks seperti "BOD"/"KOMISARIS" -> NULL.
  Di luar mapping, kolom bernama sama ada di raw -> dibawa: fk_position_master_id, fk_org_unit_id,
  dt_active, dt_inactive. fk_band_id diturunkan dari rentang job_class (seed ref_band_angkasabiru, aturan katalog).
#}
with v as (
    select
        {{ ab('position_variants', 'id_position_variant') }}   as id_position_variant,
        {{ ab('position_variants', 'fk_position_master_id') }} as fk_position_master_id,
        {{ ab('position_variants', 'position_variant_name') }} as position_variant_name,
        {{ ab('position_variants', 'fk_org_unit_id') }}        as fk_org_unit_id,
        case when {{ ab('position_variants', 'job_class') }} ~ '^[0-9]{1,4}$'
             then cast({{ ab('position_variants', 'job_class') }} as smallint) end as job_class,
        {{ ke_tanggal(ab('position_variants', 'dt_active')) }}   as dt_active,
        {{ ke_tanggal(ab('position_variants', 'dt_inactive')) }} as dt_inactive,
        r._batch_id, r._extracted_at
    from {{ source('raw_ab', 'position_variants') }} r
)
select
    r.id_position_variant,
    r.fk_position_master_id,
    r.position_variant_name,
    r.fk_org_unit_id,
    r.job_class,
    b.id_band as fk_band_id,
    r.dt_active,
    r.dt_inactive,
    {{ kolom_teknis('angkasabiru') }}
from v r
left join {{ ref('ref_band_angkasabiru') }} b
       on b.source_system = 'angkasabiru' and r.job_class between b.job_class_min and b.job_class_max
where r.id_position_variant is not null
