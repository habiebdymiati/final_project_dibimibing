{#
  Varian posisi yang dijabat pegawai. Dua asal:
    - varian asli dari silver position_variant;
    - varian bawaan (is_default_variant): master posisi yang belum punya varian di sumber dibuatkan satu varian dengan kode yang
      sama. Angkasa Biru Retail baru mengirim 100 varian dari 883 master, sedangkan riwayat posisinya merujuk kode master; tanpa ini sebagian
      besar pegawai Angkasa Biru Retail tidak tersambung ke posisinya. Kelas jabatannya dari id_grade master, band dari tangga perusahaan.
  org_unit_key UNKNOWN bila unitnya tidak ada di org_unit (kolom fk_org_unit_id Angkasa Biru Retail berisi kode posisi, bukan id unit).
#}
with master as (
    {{ dari_silver('position_master', 'id_position_master, position_master_name, id_grade') }}
),
varian as (
    {{ dari_silver('position_variant', 'id_position_variant, fk_position_master_id, position_variant_name, fk_org_unit_id, job_class, fk_band_id') }}
),
unit as (
    {{ dari_silver('org_unit', 'id_org_unit') }}
),
band as (
    {{ dari_silver('band', 'id_band, band_name, job_class_min, job_class_max') }}
),
asli as (
    select
        v.kode_sumber || '-' || v.id_position_variant as position_variant_key,
        v.id_position_variant as position_variant_id,
        v.position_variant_name,
        v.kode_sumber || '-' || v.fk_position_master_id as position_master_key,
        case when u.id_org_unit is not null then v.kode_sumber || '-' || v.fk_org_unit_id else 'UNKNOWN' end as org_unit_key,
        m.id_grade as grade_name,
        cast(v.job_class as int) as job_class,
        v.fk_band_id as band_key,
        b.band_name,
        false as is_default_variant
    from varian v
    left join master m on m.source_system_code = v.source_system_code and m.id_position_master = v.fk_position_master_id
    left join unit u on u.source_system_code = v.source_system_code and u.id_org_unit = v.fk_org_unit_id
    left join band b on b.source_system_code = v.source_system_code and b.id_band = v.fk_band_id
),
bawaan as (
    select
        m.kode_sumber || '-' || m.id_position_master as position_variant_key,
        m.id_position_master as position_variant_id,
        m.position_master_name as position_variant_name,
        m.kode_sumber || '-' || m.id_position_master as position_master_key,
        'UNKNOWN' as org_unit_key,
        m.id_grade as grade_name,
        {{ ke_int('m.id_grade') }} as job_class,
        b.id_band as band_key,
        b.band_name,
        true as is_default_variant
    from master m
    left join band b on b.source_system_code = m.source_system_code
                    and {{ ke_int('m.id_grade') }} between b.job_class_min and b.job_class_max
    where not exists (select 1 from varian v where v.source_system_code = m.source_system_code
                        and (v.fk_position_master_id = m.id_position_master or v.id_position_variant = m.id_position_master))
)
select * from asli
union all
select * from bawaan
union all
select 'UNKNOWN', 'UNKNOWN', 'Tidak diketahui', 'UNKNOWN', 'UNKNOWN', null, null, null, null, false
