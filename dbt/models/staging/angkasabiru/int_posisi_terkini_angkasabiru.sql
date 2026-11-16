{#
  POSISI TERKINI tiap pegawai Angkasa Biru: satu baris per new_nip yang punya riwayat posisi.

  Dua "baris terkini" dipakai:
    (a) baris riwayat TERAKHIR (dt_position_start terbesar)                       -> tanggal mulai posisi, job_class riwayat, nama posisi
    (b) baris riwayat terakhir yang fk_position_variant_id-nya ADA di position_variants  -> varian posisi terakhir pegawai
  Sekitar separuh pegawai tidak punya (b): baris terakhir mereka (2 Juli 2025) tidak menyebut varian posisi dan
  baris lamanya memakai kode format lama yang tidak ada di master. Untuk mereka dipakai aturan cadangan di bawah.

  Dari varian posisi (b), atribut posisi dicapai lewat rantai master:
    position_variants.fk_position_master_id -> position_master.id_position_master -> positions.code_position
    -> branches (area), directorates (direktorat), groups (group).
  Rantai master ini lengkap (10.695 varian -> 10.695 master -> 10.695 posisi); yang membatasi cakupan adalah
  langkah pegawai -> varian posisi, bukan rantainya.

  Kolom dan aturannya (keputusan 06 November 2026):
    job_class        = position_variants.job_class dari (b); bila pegawai tidak punya (b) -> job_class baris (a).
                       Pada pegawai yang punya keduanya, nilainya sama pada 95,8% (selisih hampir selalu satu tingkat).
    area             = kode area: positions.area dari (b) lewat rantai master.
                       Bila pegawai tidak punya (b): dicocokkan lewat NAMA posisi baris (a), hanya bila semua posisi
                       bernama sama berada di SATU area, dan hanya bila petunjuk dari atasan tidak membantahnya:
                         - 'nama posisi + atasan sepakat': semua atasan penyetuju cuti 6 bulan terakhir berada di area
                           yang sama dengan area dari nama posisi (uji: 362 dari 362 benar);
                         - 'nama posisi': pegawai tidak punya petunjuk atasan sama sekali (uji: 94 dari 119 benar = 79%).
                       TIDAK diisi bila atasan berada di area lain atau di beberapa area: pada kasus itu tebakan dari
                       nama posisi terbukti lebih sering salah (uji: 11 dari 58 dan 6 dari 17 benar).
    area_name        = nama area: kode area dicari di branches (CODE_AREA -> NAME_AREA). Kode yang tidak ada di
                       branches menghasilkan NULL (bukan kode), supaya kolom nama tidak bercampur kode.
    directorate_name = (b) -> positions.code_directorate -> directorates.name_directorat.
                       Bila pegawai tidak punya (b): dicocokkan lewat NAMA posisi baris (a) ke positions.name_position,
                       dan hanya dipakai bila semua posisi bernama sama berada di SATU direktorat
                       (uji pada pegawai yang punya (b): 2.191 dari 2.194 benar = 99,86%).
    org_group_name   = (b) -> positions.code_group -> groups.name_group. TANPA cadangan nama posisi, karena nama posisi
                       tidak menentukan group (uji yang sama: hanya 29,6% benar).
    dt_position_start = tanggal mulai baris (a); dipakai sebagai cadangan dt_grade_start.
  sumber_job_class / sumber_directorate / sumber_org_group mencatat aturan mana yang mengisi tiap baris (untuk audit).

  Nominatif (int_nominatif_angkasabiru, keputusan 07 November 2026): cadangan TERAKHIR, karena bersifat history dan data API lebih baru.
    area, directorate_name : diisi nominatif bila semua aturan di atas tidak menghasilkan nilai.
    org_group_name         : group dari posisi hasil pencocokan nominatif, hanya untuk pegawai tanpa (b) dan nama sama.
    fk_position_variant_id_nominatif, org_unit_name_nominatif : dipakai stg_employee_position_history_angkasabiru untuk mengisi
                             baris riwayat terakhir yang kosong.
    "Nama sama" = nama posisi baris (a) sama dengan Nama jabatan di nominatif. Bila berbeda, pegawai sudah pindah setelah berkas
    itu dibuat, sehingga posisi dan unit di nominatif tidak lagi berlaku. Kode lama di API (PS-...) tidak ditimpa.
    job_class tidak diisi dari nominatif: nilai dari riwayat API sudah tersedia.
#}
with riwayat as (
    select
        {{ ab('employee_position_history', 'new_nip') }}                as new_nip,
        {{ ab('employee_position_history', 'id_position_history') }}    as id_position_history,
        {{ ab('employee_position_history', 'fk_position_variant_id') }} as fk_position_variant_id,
        {{ ke_tanggal(ab('employee_position_history', 'dt_position_start')) }} as dt_position_start,
        {{ ke_int(ab('employee_position_history', 'id_position_history')) }}   as urut,
        case when {{ ab('employee_position_history', 'job_class') }} ~ '^[0-9]+$'
             then {{ ab('employee_position_history', 'job_class') }} end       as job_class_riwayat,
        upper(regexp_replace({{ ab('employee_position_history', 'position_name') }}, '\s+', ' ', 'g')) as nama_posisi
    from {{ source('raw_ab', 'employee_position_history') }} r
),
varian as (
    select
        {{ ab('position_variants', 'id_position_variant', 'v') }}   as id_position_variant,
        {{ ab('position_variants', 'fk_position_master_id', 'v') }} as fk_position_master_id,
        {{ ab('position_variants', 'job_class', 'v') }}             as job_class
    from {{ source('raw_ab', 'position_variants') }} v
),
induk as (
    select {{ ab('position_master', 'id_position_master', 'm') }} as id_position_master
    from {{ source('raw_ab', 'position_master') }} m
),
posisi as (
    select
        {{ ab('positions', 'code_position', 'p') }}    as code_position,
        {{ ab('positions', 'area', 'p') }}             as area,
        {{ ab('positions', 'code_directorate', 'p') }} as code_directorate,
        {{ ab('positions', 'code_group', 'p') }}       as code_group,
        upper(regexp_replace({{ ab('positions', 'name_position', 'p') }}, '\s+', ' ', 'g')) as nama_posisi
    from {{ source('raw_ab', 'positions') }} p
),
direktorat as (
    select {{ ab('directorates', 'code_directorat', 'd') }} as code_directorate,
           {{ ab('directorates', 'name_directorat', 'd') }} as directorate_name
    from {{ source('raw_ab', 'directorates') }} d
),
cabang as (
    select {{ ab('branches', 'CODE_AREA', 'b') }} as area,
           {{ ab('branches', 'NAME_AREA', 'b') }} as area_name
    from {{ source('raw_ab', 'branches') }} b
),
grup as (
    select {{ ab('groups', 'code_group', 'g') }} as code_group,
           {{ ab('groups', 'name_group', 'g') }} as org_group_name
    from {{ source('raw_ab', 'groups') }} g
),
-- (a) baris riwayat terakhir
terkini as (
    select distinct on (new_nip) new_nip, id_position_history, fk_position_variant_id as fk_baris_terakhir,
           dt_position_start, job_class_riwayat, nama_posisi
    from riwayat
    where new_nip is not null
    order by new_nip, dt_position_start desc nulls last, urut desc nulls last
),
-- (b) baris riwayat terakhir yang tersambung ke varian posisi
terkini_varian as (
    select distinct on (h.new_nip) h.new_nip, h.fk_position_variant_id, v.fk_position_master_id, v.job_class
    from riwayat h
    join varian v on v.id_position_variant = h.fk_position_variant_id
    where h.new_nip is not null
    order by h.new_nip, h.dt_position_start desc nulls last, h.urut desc nulls last
),
-- nama posisi yang SEMUA posisinya berada di satu direktorat
nama_ke_direktorat as (
    select nama_posisi, min(code_directorate) as code_directorate
    from posisi
    where nama_posisi is not null and code_directorate is not null
    group by nama_posisi
    having count(distinct code_directorate) = 1
),
-- nama posisi yang SEMUA posisinya berada di satu area
nama_ke_area as (
    select nama_posisi, min(area) as area
    from posisi
    where nama_posisi is not null and area is not null
    group by nama_posisi
    having count(distinct area) = 1
),
-- area tiap NIP yang punya varian posisi (dipakai untuk mengetahui area ATASAN)
area_varian as (
    select tv.new_nip, p.area
    from terkini_varian tv
    join induk m on m.id_position_master = tv.fk_position_master_id
    join posisi p on p.code_position = m.id_position_master
    where p.area is not null
),
-- atasan penyetuju cuti: approve_by berisi "NIP atasan-1, NIP atasan-2"; dipakai atasan-1 (atasan langsung)
cuti as (
    select
        {{ ab('employee_leave_history', 'id_employee', 'c') }} as nip,
        nullif(btrim(split_part({{ ab('employee_leave_history', 'approve_by', 'c') }}, ',', 1)), '') as atasan,
        {{ ke_tanggal(ab('employee_leave_history', 'dt_leave_start', 'c')) }} as dt_leave_start
    from {{ source('raw_ab', 'employee_leave_history') }} c
),
suara_atasan as (
    select c.nip, count(distinct a.area) as n_area, min(a.area) as area
    from cuti c
    join area_varian a on a.new_nip = c.atasan
    where c.atasan <> c.nip and c.dt_leave_start >= current_date - interval '6 months'
    group by c.nip
),
gabung as (
    select
        t.new_nip,
        t.id_position_history as id_riwayat_terakhir,
        tv.fk_position_variant_id,
        t.dt_position_start,
        coalesce(p.area,
                 case when tv.new_nip is null and na.area is not null
                           and (sa.nip is null or (sa.n_area = 1 and sa.area = na.area)) then na.area end,
                 n.area) as area,
        case when p.area is not null then 'varian posisi'
             when tv.new_nip is null and na.area is not null and sa.n_area = 1 and sa.area = na.area then 'nama posisi + atasan sepakat'
             when tv.new_nip is null and na.area is not null and sa.nip is null then 'nama posisi'
             when n.area is not null then 'nominatif' end as sumber_area,
        coalesce(tv.job_class, t.job_class_riwayat) as job_class,
        case when tv.job_class is not null then 'position_variants'
             when t.job_class_riwayat is not null then 'employee_position_history' end as sumber_job_class,
        coalesce(d1.directorate_name, case when tv.new_nip is null then d2.directorate_name end, n.directorate_name) as directorate_name,
        case when d1.directorate_name is not null then 'kode posisi'
             when tv.new_nip is null and d2.directorate_name is not null then 'nama posisi'
             when n.directorate_name is not null then 'nominatif' end as sumber_directorate,
        coalesce(g.org_group_name, case when tv.new_nip is null and n.nama_jabatan = t.nama_posisi then n.org_group_name end) as org_group_name,
        case when g.org_group_name is not null then 'kode posisi'
             when tv.new_nip is null and n.nama_jabatan = t.nama_posisi and n.org_group_name is not null then 'nominatif' end as sumber_org_group,
        case when tv.new_nip is null and t.fk_baris_terakhir is null and n.nama_jabatan = t.nama_posisi
             then n.fk_position_variant_id end as fk_position_variant_id_nominatif,
        case when n.nama_jabatan = t.nama_posisi then n.unit end as org_unit_name_nominatif
    from terkini t
    left join terkini_varian tv on tv.new_nip = t.new_nip
    left join induk m on m.id_position_master = tv.fk_position_master_id
    left join posisi p on p.code_position = m.id_position_master
    left join direktorat d1 on d1.code_directorate = p.code_directorate
    left join nama_ke_direktorat nd on nd.nama_posisi = t.nama_posisi
    left join direktorat d2 on d2.code_directorate = nd.code_directorate
    left join grup g on g.code_group = p.code_group
    left join nama_ke_area na on na.nama_posisi = t.nama_posisi
    left join suara_atasan sa on sa.nip = t.new_nip
    left join {{ ref('int_nominatif_angkasabiru') }} n on n.new_nip = t.new_nip
)
select
    x.new_nip,
    x.id_riwayat_terakhir,
    x.fk_position_variant_id,
    x.fk_position_variant_id_nominatif,
    x.org_unit_name_nominatif,
    x.dt_position_start,
    x.area,
    c.area_name,
    x.sumber_area,
    x.job_class,
    x.sumber_job_class,
    x.directorate_name,
    x.sumber_directorate,
    x.org_group_name,
    x.sumber_org_group
from gabung x
left join cabang c on c.area = x.area
