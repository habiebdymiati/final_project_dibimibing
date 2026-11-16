{#
  Nominatif pegawai Angkasa Biru: berkas "Data Pegawai 08092026 - Nominatif.csv" (keadaan 8 September 2026), satu baris per NIP.
  Bersifat history. HANYA mengisi yang kosong dari API, karena data API lebih baru (keputusan 07 November 2026).
  Prioritasnya diterapkan di int_posisi_terkini_angkasabiru, bukan di sini.

    area, area_name   : Area berisi kode bandara (CGK, HO, REG1) -> branches.NAME_ALIAS -> CODE_AREA, NAME_AREA.
                        Kode tanpa padanan di branches (RLK) -> NULL.
    directorate_name  : Direktorat (DO, DT) -> directorates.code_directorat -> name_directorat.
    unit              : Unit apa adanya. Tingkatnya unit, BUKAN group: dibanding org_group_name dari API hanya 129 dari
                        3.563 yang sama, jadi kolom ini tidak boleh mengisi org_group_name.
    nama_jabatan      : Nama jabatan yang dibakukan, pembanding dengan nama posisi terakhir di API.
    fk_position_variant_id, org_group_name : hasil mencocokkan nomenklatur ke master posisi. Nama jabatan + area + Unit dicari
                        di varian posisi; bila Unit tidak menemukan apa pun, dipakai nama jabatan + area. Hanya diisi bila
                        kandidatnya tepat satu, supaya tidak menebak di antara posisi yang bernama sama.
                        Uji terhadap pegawai yang punya fk dari API, saat nama jabatan API sama dengan CSV: 99,4% benar.
                        Saat namanya berbeda hanya 0,3% benar (pegawai sudah pindah setelah CSV dibuat), maka
                        int_posisi_terkini_angkasabiru hanya memakainya bila kedua nama sama.
#}
with nominatif as (
    select
        nullif(btrim(n.nik_baru), '')                                  as new_nip,
        upper(regexp_replace(btrim(n.nama_jabatan), '\s+', ' ', 'g')) as nama_jabatan,
        public.bersih_teks(n.unit)                                     as unit,
        upper(regexp_replace(btrim(n.unit), '\s+', ' ', 'g'))         as unit_cari,
        nullif(btrim(n.area), '')                                      as kode_bandara,
        nullif(btrim(n.direktorat), '')                                as kode_direktorat
    from {{ source('ref_ab', 'nominatif_angkasabiru') }} n
),
cabang as (
    select {{ ab('branches', 'NAME_ALIAS', 'b') }} as kode_bandara,
           {{ ab('branches', 'CODE_AREA', 'b') }}  as area,
           {{ ab('branches', 'NAME_AREA', 'b') }}  as area_name
    from {{ source('raw_ab', 'branches') }} b
),
direktorat as (
    select {{ ab('directorates', 'code_directorat', 'd') }} as kode_direktorat,
           {{ ab('directorates', 'name_directorat', 'd') }} as directorate_name
    from {{ source('raw_ab', 'directorates') }} d
),
grup as (
    select {{ ab('groups', 'code_group', 'g') }} as code_group,
           {{ ab('groups', 'name_group', 'g') }} as org_group_name
    from {{ source('raw_ab', 'groups') }} g
),
varian as (
    select distinct
        {{ ab('position_variants', 'id_position_variant', 'v') }} as id_position_variant,
        upper(regexp_replace({{ ab('position_variants', 'position_variant_name', 'v') }}, '\s+', ' ', 'g')) as nama,
        {{ ab('positions', 'area', 'p') }}       as area,
        {{ ab('positions', 'code_group', 'p') }} as code_group,
        upper(regexp_replace({{ ab('units', 'org_unit_name', 'u') }}, '\s+', ' ', 'g')) as unit
    from {{ source('raw_ab', 'position_variants') }} v
    join {{ source('raw_ab', 'position_master') }} m
      on {{ ab('position_master', 'id_position_master', 'm') }} = {{ ab('position_variants', 'fk_position_master_id', 'v') }}
    join {{ source('raw_ab', 'positions') }} p
      on {{ ab('positions', 'code_position', 'p') }} = {{ ab('position_master', 'id_position_master', 'm') }}
    left join {{ source('raw_ab', 'units') }} u
      on {{ ab('units', 'id_org_unit', 'u') }} = {{ ab('position_variants', 'fk_org_unit_id', 'v') }}
),
calon as (
    select
        n.new_nip,
        count(distinct x.id_position_variant) filter (where x.unit = n.unit_cari) as n_varian_unit,
        min(x.id_position_variant) filter (where x.unit = n.unit_cari)            as varian_unit,
        count(distinct x.id_position_variant)                                     as n_varian,
        min(x.id_position_variant)                                                as varian_area,
        count(distinct x.code_group) filter (where x.unit = n.unit_cari)          as n_group_unit,
        min(x.code_group) filter (where x.unit = n.unit_cari)                     as group_unit,
        count(distinct x.code_group)                                              as n_group,
        min(x.code_group)                                                         as group_area
    from nominatif n
    join cabang c on c.kode_bandara = n.kode_bandara
    join varian x on x.nama = n.nama_jabatan and x.area = c.area
    group by n.new_nip
)
select
    n.new_nip,
    n.nama_jabatan,
    n.unit,
    c.area,
    c.area_name,
    d.directorate_name,
    case when k.n_varian_unit = 1 then k.varian_unit
         when k.n_varian_unit = 0 and k.n_varian = 1 then k.varian_area end as fk_position_variant_id,
    g.org_group_name
from nominatif n
left join cabang c on c.kode_bandara = n.kode_bandara
left join direktorat d on d.kode_direktorat = n.kode_direktorat
left join calon k on k.new_nip = n.new_nip
left join grup g on g.code_group = case when k.n_group_unit = 1 then k.group_unit
                                        when k.n_varian_unit = 0 and k.n_group = 1 then k.group_area end
where n.new_nip is not null
