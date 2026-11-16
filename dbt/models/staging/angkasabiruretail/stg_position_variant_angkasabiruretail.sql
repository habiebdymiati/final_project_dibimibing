{#
  Mapping Angkasa Biru Retail: position_variant <- position-variants (nama kolom sama dengan target).
  fk_position_master_id: API mengirim 'PM_<kode>'; awalan PM_ dibuang supaya sama dengan positions.code_position
                         (id_position_master), kalau tidak relasinya tidak pernah cocok.
  job_class: hanya angka -> TINYINT. fk_band_id diturunkan dari job_class lewat tangga band (seed ref_band_angkasabiruretail).
  dt_active/dt_inactive: stempel waktu ISO UTC -> tanggal WIB.
#}
with v as (
    select
        {{ abr('position__variants', 'id_position_variant') }}   as id_position_variant,
        regexp_replace({{ abr('position__variants', 'fk_position_master_id') }}, '^PM_', '') as fk_position_master_id,
        {{ abr('position__variants', 'position_variant_name') }} as position_variant_name,
        {{ abr('position__variants', 'fk_org_unit_id') }}        as fk_org_unit_id,
        case when {{ abr('position__variants', 'job_class') }} ~ '^[0-9]{1,4}$'
             then cast({{ abr('position__variants', 'job_class') }} as smallint) end as job_class,
        {{ ke_tanggal(abr('position__variants', 'dt_active')) }}   as dt_active,
        {{ ke_tanggal(abr('position__variants', 'dt_inactive')) }} as dt_inactive,
        r._batch_id, r._extracted_at
    from {{ source('raw_abr', 'position__variants') }} r
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
    {{ kolom_teknis('angkasabiruretail') }}
from v r
left join {{ ref('ref_band_angkasabiruretail') }} b
       on r.job_class between b.job_class_min and b.job_class_max
where r.id_position_variant is not null
