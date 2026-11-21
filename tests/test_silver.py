"""Layer silver (dbt): raw_table_angkasabiru -> staging_angkasabiru -> silver_angkasabiru.<entitas>_angkasabiru,
sesuai Mapping transformasi Angkasa Biru. Setiap schema dan setiap tabel/view berakhiran _angkasabiru."""
import pytest

from .conftest import query, scalar

ENTITAS = {
    "company", "org_unit", "position_master", "position_variant", "band", "position_competency_requirement",
    "job_family", "job_function", "employee_profile", "employee_identification", "employee_address",
    "employee_family_member", "employee_contract", "employee_position_history", "employee_assignment_history",
    "employee_performance_history", "employee_leave_history", "employee_education_history",
    "employee_disciplinary",
    "learning_history", "learning_agility_assessment", "competency_assessment", "employee_secondary_assignment",
    "career_aspiration",   # katalog 5.1: dari Angkasa Biru TMS (sistem talenta grup), bukan dari HRIS perusahaan
    "top_talent",   # bukan entitas katalog: penanda top talent dari master data
}
AP = "dwh_source_system = 'angkasabiru'"


@pytest.fixture(scope="module", autouse=True)
def _silver_sudah_dibangun(dwh):
    if not scalar(dwh, "select count(*) from information_schema.tables where table_schema = 'silver_angkasabiru'"):
        pytest.skip("schema silver_angkasabiru belum dibangun (jalankan `make silver`)")


def _kolom_raw(dwh, tabel):
    return {r[0] for r in query(dwh, """select column_name from information_schema.columns
                                        where table_schema = 'raw_table_angkasabiru' and table_name = %s""", (tabel,))}


def test_satu_tabel_silver_per_entitas_katalog(dwh):
    """Setiap tabel silver berakhiran _angkasabiru: nama tabel menyatakan pemilik datanya."""
    tabel = {r[0] for r in query(dwh, "select table_name from information_schema.tables where table_schema = 'silver_angkasabiru'")}
    assert tabel == {f"{e}_angkasabiru" for e in ENTITAS}


def test_setiap_schema_dan_objek_transformasi_berakhiran_angkasabiru(dwh):
    """Nama schema dan nama tabel/view menyatakan pemilik datanya; tidak ada schema transformasi tanpa akhiran."""
    from ingestion.config import list_sources

    schema = {r[0] for r in query(dwh, "select nspname from pg_namespace where nspname ~ '^(staging|silver|seed|registry)'")}
    assert {"staging_angkasabiru", "silver_angkasabiru", "seed_angkasabiru", "registry_angkasabiru"} <= schema
    # tidak boleh ada schema transformasi tanpa akhiran nama sumber (mis. "silver" saja)
    akhiran = tuple(f"_{s}" for s in list_sources())
    assert [x for x in schema if not x.endswith(akhiran)] == []
    liar = query(dwh, """select table_schema, table_name from information_schema.tables
                         where table_schema in ('staging_angkasabiru', 'silver_angkasabiru', 'seed_angkasabiru',
                                                'registry_angkasabiru', 'reference_angkasabiru')
                           and right(table_name, 12) <> '_angkasabiru'""")
    assert liar == []


def test_setiap_tabel_membawa_kolom_teknis_dwh(dwh):
    for t in ENTITAS:
        kol = {r[0] for r in query(dwh, """select column_name from information_schema.columns
                                           where table_schema = 'silver_angkasabiru' and table_name = %s""", (f"{t}_angkasabiru",))}
        assert {"dwh_source_system", "dwh_batch_id", "dwh_extracted_at", "dwh_loaded_at"} <= kol, t


def test_company_angkasabiru_sesuai_mapping(dwh):
    assert query(dwh, f"select id_company, company_name, company_type, dt_establishment::text from silver_angkasabiru.company_angkasabiru where {AP}") == [
        ("AB-COMP-AB", "PT Angkasa Biru", "Holding", "2024-09-09")]


def test_org_level_mengikuti_hirarki(dwh):
    """Puncak (id = induk) level 1; setiap anak tepat satu tingkat di bawah induknya."""
    assert scalar(dwh, f"select count(*) from silver_angkasabiru.org_unit_angkasabiru where {AP} and id_org_unit = id_parent_org_unit and org_level <> 1") == 0
    assert scalar(dwh, f"""select count(*) from silver_angkasabiru.org_unit_angkasabiru c join silver_angkasabiru.org_unit_angkasabiru p on p.id_org_unit = c.id_parent_org_unit
                           where c.{AP} and c.id_org_unit <> c.id_parent_org_unit
                             and c.org_level is distinct from p.org_level + 1""") == 0
    assert scalar(dwh, f"select count(*) from silver_angkasabiru.org_unit_angkasabiru where {AP} and org_level is not null") > 0


def test_band_mengikuti_rentang_job_class(dwh):
    assert query(dwh, f"select band_code, job_class_min, job_class_max from silver_angkasabiru.band_angkasabiru where {AP} order by band_sequence") == [
        ("BOD-1", 18, 23), ("BOD-2", 16, 17), ("BOD-3", 14, 15), ("BOD-4", 7, 13)]
    salah = scalar(dwh, f"""select count(*) from silver_angkasabiru.position_variant_angkasabiru v left join silver_angkasabiru.band_angkasabiru b on b.id_band = v.fk_band_id
                            where v.{AP} and (
                                  (b.id_band is not null and v.job_class not between b.job_class_min and b.job_class_max)
                               or (b.id_band is null and v.job_class between 7 and 23))""")
    assert salah == 0


TABEL_BER_ID_PEGAWAI = ("employee_profile", "employee_identification", "employee_address", "employee_family_member",
                        "employee_contract", "employee_assignment_history", "employee_performance_history",
                        "employee_leave_history", "employee_education_history", "employee_disciplinary")


def test_id_employee_varchar_8_digit_berawalan_10(dwh):
    """Kunci pegawai buatan DWH: VARCHAR berisi 8 digit = 10 + enam digit nomor urut."""
    for t in TABEL_BER_ID_PEGAWAI:
        assert scalar(dwh, """select data_type from information_schema.columns
                              where table_schema = 'silver_angkasabiru' and table_name = %s and column_name = 'id_employee'""", (f"{t}_angkasabiru",)) == "character varying", t
        assert scalar(dwh, f"""select count(*) from silver_angkasabiru.{t}_angkasabiru where {AP}
                               and (id_employee is null or id_employee !~ '^10[0-9]{{6}}$')""") == 0, t


def test_new_nip_varchar_apa_adanya(dwh):
    """new_nip disimpan sebagai VARCHAR, sama persis dengan yang dikirim API (tanpa konversi angka)."""
    for t in ("employee_profile", "employee_position_history"):
        assert scalar(dwh, """select data_type from information_schema.columns
                              where table_schema = 'silver_angkasabiru' and table_name = %s and column_name = 'new_nip'""", (f"{t}_angkasabiru",)) == "character varying", t
    assert scalar(dwh, f"""select count(*) from silver_angkasabiru.employee_profile_angkasabiru s
                           where s.{AP} and not exists (select 1 from raw_table_angkasabiru.employee_profile r
                                                        where nullif(btrim(r.new_nip), '') = s.new_nip)""") == 0
    assert scalar(dwh, f"""select count(*) from silver_angkasabiru.employee_position_history_angkasabiru s
                           join raw_table_angkasabiru.employee_position_history r on r.id_position_history = s.id_position_history
                           where s.{AP} and s.new_nip is distinct from nullif(btrim(r.new_nip), '')""") == 0


def test_dt_birth_dan_dt_appointed_dari_berkas_referensi(dwh):
    """Keduanya diambil dari reference_angkasabiru (tanggal_lahir, tmt_karyawan) per new_nip."""
    beda = scalar(dwh, f"""select count(*) from silver_angkasabiru.employee_identification_angkasabiru i
        join registry_angkasabiru.registry_id_employee_angkasabiru g on g.id_employee = i.id_employee
        join reference_angkasabiru.tmt_karyawan_angkasabiru f on f.new_nip = g.nip
        where i.{AP} and (i.dt_birth is distinct from public.try_date(f.tanggal_lahir)
                       or i.dt_appointed_employee is distinct from public.try_date(f.tmt_karyawan))""")
    assert beda == 0
    terisi = scalar(dwh, f"select count(dt_birth) from silver_angkasabiru.employee_identification_angkasabiru where {AP}")
    assert terisi == scalar(dwh, """select count(*) from raw_table_angkasabiru.employee_profile p
                                    join reference_angkasabiru.tmt_karyawan_angkasabiru f on f.new_nip = p.new_nip""")


def test_id_employee_berurut_menurut_tmt_karyawan(dwh):
    """Nomor urut mengikuti TMT pada berkas referensi: TMT lebih awal -> nomor lebih kecil; tanpa TMT di belakang.
    Registry incremental (ID stabil), jadi urutan TMT dijamin di dalam tiap batch penambahan (dwh_assigned_at)."""
    assert scalar(dwh, """select count(*) from (select dt_tmt, lag(dt_tmt) over (partition by dwh_assigned_at order by urutan) as sebelum
                                               from registry_angkasabiru.registry_id_employee_angkasabiru) t where dt_tmt < sebelum""") == 0
    assert scalar(dwh, """select count(*) from registry_angkasabiru.registry_id_employee_angkasabiru a join registry_angkasabiru.registry_id_employee_angkasabiru b
                          on a.dwh_assigned_at = b.dwh_assigned_at
                         and a.dt_tmt is null and b.dt_tmt is not null and a.urutan < b.urutan""") == 0
    assert scalar(dwh, "select count(*) = max(urutan) and min(urutan) = 1 from registry_angkasabiru.registry_id_employee_angkasabiru")
    assert scalar(dwh, "select bool_and(id_employee = (10000000 + urutan)::varchar) from registry_angkasabiru.registry_id_employee_angkasabiru")
    cocok = scalar(dwh, """select count(*) from registry_angkasabiru.registry_id_employee_angkasabiru g
                           join reference_angkasabiru.tmt_karyawan_angkasabiru t on t.new_nip = g.nip
                           where g.dt_tmt = public.try_date(t.tmt_karyawan)""")
    assert cocok == scalar(dwh, "select count(*) from reference_angkasabiru.tmt_karyawan_angkasabiru")


def test_kunci_pegawai_seragam_di_semua_tabel(dwh):
    """id_employee diambil dari registri yang sama, supaya relasi ke employee_profile utuh."""
    assert scalar(dwh, f"""select count(*) from silver_angkasabiru.employee_profile_angkasabiru p
                           join registry_angkasabiru.registry_id_employee_angkasabiru g on g.nip = p.new_nip
                           where p.{AP} and g.id_employee <> p.id_employee""") == 0
    assert scalar(dwh, f"select count(*) from silver_angkasabiru.employee_profile_angkasabiru where {AP}") == \
        scalar(dwh, "select count(distinct new_nip) from raw_table_angkasabiru.employee_profile")
    assert scalar(dwh, f"""select count(*) from silver_angkasabiru.employee_identification_angkasabiru i where i.{AP}
                           and not exists (select 1 from silver_angkasabiru.employee_profile_angkasabiru p where p.id_employee = i.id_employee)""") == 0


def test_mobile_phone_distandarkan_berawalan_08(dwh):
    assert scalar(dwh, f"select count(*) from silver_angkasabiru.employee_identification_angkasabiru where {AP} and mobile_phone !~ '^08[0-9]{{8,12}}$'") == 0
    assert scalar(dwh, f"select count(mobile_phone) from silver_angkasabiru.employee_identification_angkasabiru where {AP}") > 0


def test_entitas_tanpa_sumber_terbentuk_kosong(dwh):
    for t in ("employee_contract", "employee_disciplinary"):
        assert scalar(dwh, f"select count(*) from silver_angkasabiru.{t}_angkasabiru where {AP}") == 0


def test_kolom_mapping_yang_belum_dikirim_api_menjadi_null_bukan_tebakan(dwh):
    """Mapping merujuk employee_profile.photo_blob; selama kolom itu belum ada di raw dan tidak ada keputusan
    sumber pengganti, hasilnya NULL."""
    if "photo_blob" in _kolom_raw(dwh, "employee_profile"):
        pytest.skip("API sudah mengirim photo_blob")
    assert scalar(dwh, f"select count(photo_blob) from silver_angkasabiru.employee_profile_angkasabiru where {AP}") == 0


NAMA_JABATAN = "upper(regexp_replace(btrim(n.nama_jabatan), '\\s+', ' ', 'g'))"

# Posisi terkini dihitung ulang di sini langsung dari raw, terpisah dari model dbt, sebagai pembanding.
POSISI_TERKINI = """
    with h as (select nullif(btrim(new_nip), '') nip, nullif(btrim(fk_position_variant_id), '') fk,
                      public.try_date(dt_position_start) dt,
                      case when id_position_history ~ '^[0-9]+$' then id_position_history::int end urut,
                      case when btrim(job_class) ~ '^[0-9]+$' then btrim(job_class) end jc,
                      upper(regexp_replace(btrim(position_name), '\\s+', ' ', 'g')) pn
               from raw_table_angkasabiru.employee_position_history),
         a as (select distinct on (nip) * from h where nip is not null order by nip, dt desc nulls last, urut desc nulls last),
         b as (select distinct on (h.nip) h.nip, h.fk, nullif(btrim(v.job_class), '') jc
               from h join raw_table_angkasabiru.position_variants v on nullif(btrim(v.id_position_variant), '') = h.fk
               where h.nip is not null order by h.nip, h.dt desc nulls last, h.urut desc nulls last),
         pos as (select nullif(btrim(code_position), '') id, nullif(btrim(code_directorate), '') cd, nullif(btrim(code_group), '') cg,
                        upper(regexp_replace(btrim(name_position), '\\s+', ' ', 'g')) pn from raw_table_angkasabiru.positions),
         nd as (select pn, min(cd) cd from pos where pn is not null and cd is not null group by pn having count(distinct cd) = 1),
         t as (select a.nip, a.dt, coalesce(b.jc, a.jc) jc, b.nip is not null as punya_varian,
                      coalesce(d1.name_directorat, case when b.nip is null then d2.name_directorat end) dir,
                      nullif(btrim(g.name_group), '') grp
               from a left join b using (nip)
               left join pos p on p.id = b.fk
               left join raw_table_angkasabiru.directorates d1 on btrim(d1.code_directorat) = p.cd
               left join nd on nd.pn = a.pn
               left join raw_table_angkasabiru.directorates d2 on btrim(d2.code_directorat) = nd.cd
               left join raw_table_angkasabiru.groups g on btrim(g.code_group) = p.cg)
"""


def test_job_class_varian_posisi_terakhir_dengan_cadangan_riwayat(dwh):
    """job_class = position_variants.job_class varian posisi terakhir per new_nip; pegawai tanpa varian posisi
    memakai job_class baris riwayat posisi terakhirnya."""
    salah = scalar(dwh, POSISI_TERKINI + f"""
        select count(*) from silver_angkasabiru.employee_identification_angkasabiru i
        join registry_angkasabiru.registry_id_employee_angkasabiru g on g.id_employee = i.id_employee
        left join t on t.nip = g.nip
        where i.{AP} and i.job_class is distinct from t.jc""")
    assert salah == 0
    # yang tersambung ke varian HARUS memakai nilai varian, bukan nilai riwayat
    assert scalar(dwh, POSISI_TERKINI + f"""
        select count(*) from silver_angkasabiru.employee_identification_angkasabiru i
        join registry_angkasabiru.registry_id_employee_angkasabiru g on g.id_employee = i.id_employee
        join b on b.nip = g.nip where i.{AP} and b.jc is not null and i.job_class <> b.jc""") == 0


def test_directorate_dan_group_dari_posisi_terkini(dwh):
    """Nilai dari API menang: directorate_name lewat kode posisi (cadangan nama posisi hanya untuk pegawai tanpa varian
    posisi), org_group_name lewat kode posisi. Nominatif hanya mengisi yang tetap kosong."""
    beda = scalar(dwh, POSISI_TERKINI + f"""
        select count(*) from silver_angkasabiru.employee_profile_angkasabiru p left join t on t.nip = p.new_nip
        where p.{AP} and ((t.dir is not null and lower(regexp_replace(p.directorate_name, '^Direktorat ', '')) is distinct from lower(t.dir))
                          or (t.grp is not null and p.org_group_name is distinct from t.grp))""")
    assert beda == 0
    # pegawai tanpa varian posisi hanya mendapat group dari nominatif, dan hanya bila nama jabatan API sama dengan nominatif
    assert scalar(dwh, POSISI_TERKINI + f"""
        select count(*) from silver_angkasabiru.employee_profile_angkasabiru p join t on t.nip = p.new_nip join a on a.nip = p.new_nip
        left join reference_angkasabiru.nominatif_angkasabiru n on n.nik_baru = p.new_nip
        where p.{AP} and not t.punya_varian and p.org_group_name is not null
          and {NAMA_JABATAN} is distinct from a.pn""") == 0
    assert scalar(dwh, f"select count(directorate_name) from silver_angkasabiru.employee_profile_angkasabiru where {AP}") > 0


AREA_PEGAWAI = POSISI_TERKINI + """,
         posa as (select nullif(btrim(code_position), '') id, nullif(btrim(area), '') area,
                         upper(regexp_replace(btrim(name_position), '\\s+', ' ', 'g')) pn from raw_table_angkasabiru.positions),
         -- area lewat rantai varian -> master -> posisi
         area_varian as (select b.nip, ps.area from b
                         join raw_table_angkasabiru.position_variants pv on nullif(btrim(pv.id_position_variant), '') = b.fk
                         join raw_table_angkasabiru.position_master pm on btrim(pm.id_position_master) = btrim(pv.fk_position_master_id)
                         join posa ps on ps.id = btrim(pm.id_position_master)),
         nama_area as (select pn, min(area) area from posa where pn is not null and area is not null group by pn having count(distinct area) = 1),
         suara as (select c.nip, count(distinct av.area) n_area, min(av.area) area
                   from (select nullif(btrim(id_employee), '') nip, nullif(btrim(split_part(approve_by, ',', 1)), '') atasan,
                                public.try_date(dt_leave_start) dt from raw_table_angkasabiru.employee_leave_history) c
                   join area_varian av on av.nip = c.atasan
                   where c.atasan <> c.nip and c.dt >= current_date - interval '6 months' and av.area is not null group by c.nip),
         area as (select a.nip, av.nip is not null as punya_varian, sa.nip is not null as ada_suara, sa.n_area, sa.area area_atasan, na.area area_nama,
                         coalesce(av.area, case when av.nip is null and b2.nip is null and na.area is not null
                                                     and (sa.nip is null or (sa.n_area = 1 and sa.area = na.area)) then na.area end) kode
                  from a left join area_varian av using (nip) left join b b2 using (nip)
                  left join nama_area na on na.pn = a.pn left join suara sa using (nip))
"""


AREA_NOMINATIF = """left join reference_angkasabiru.nominatif_angkasabiru n on n.nik_baru = p.new_nip
        left join raw_table_angkasabiru.branches bn on btrim(bn."NAME_ALIAS") = btrim(n.area)"""


def test_area_name_berisi_nama_area_dari_branches(dwh):
    """area_name = branches.NAME_AREA. Kode areanya: rantai varian posisi terakhir -> position_master -> positions;
    pegawai tanpa varian posisi memakai nama posisi yang hanya ada di satu area, kecuali bila atasan membantahnya.
    Bila semua itu kosong, nominatif yang mengisi. Kolom ini tidak pernah berisi kode."""
    beda = scalar(dwh, AREA_PEGAWAI + f"""
        select count(*) from silver_angkasabiru.employee_profile_angkasabiru p
        left join area ar on ar.nip = p.new_nip
        left join raw_table_angkasabiru.branches br on btrim(br."CODE_AREA") = ar.kode
        {AREA_NOMINATIF}
        where p.{AP} and p.area_name is distinct from coalesce(nullif(btrim(br."NAME_AREA"), ''), nullif(btrim(bn."NAME_AREA"), ''))""")
    assert beda == 0
    assert scalar(dwh, f"""select count(*) from silver_angkasabiru.employee_profile_angkasabiru p
                           where p.{AP} and p.area_name is not null
                             and not exists (select 1 from raw_table_angkasabiru.branches br where btrim(br."NAME_AREA") = p.area_name)""") == 0


def test_area_dari_nama_posisi_tidak_dipakai_bila_atasan_membantah(dwh):
    """Bila atasan penyetuju cuti berada di area lain (atau di beberapa area), tebakan dari nama posisi tidak dipakai:
    pada kasus itu ia terbukti lebih sering salah daripada benar. Nilainya hanya boleh datang dari nominatif."""
    terisi = scalar(dwh, AREA_PEGAWAI + f"""
        select count(*) from silver_angkasabiru.employee_profile_angkasabiru p join area ar on ar.nip = p.new_nip
        {AREA_NOMINATIF}
        where p.{AP} and not ar.punya_varian and ar.ada_suara
          and not (ar.n_area = 1 and ar.area_atasan = ar.area_nama)
          and p.area_name is distinct from nullif(btrim(bn."NAME_AREA"), '')""")
    assert terisi == 0


def test_dt_grade_start_nilai_api_dengan_cadangan_tanggal_mulai_posisi(dwh):
    salah = scalar(dwh, POSISI_TERKINI + f""",
        api as (select distinct on (id_employee) nullif(btrim(id_employee), '') nip, public.try_date(dt_grade_start) dgs
                from raw_table_angkasabiru.employee_identification order by id_employee, _row_hash)
        select count(*) from silver_angkasabiru.employee_identification_angkasabiru i
        join registry_angkasabiru.registry_id_employee_angkasabiru g on g.id_employee = i.id_employee
        join api on api.nip = g.nip left join t on t.nip = g.nip
        where i.{AP} and i.dt_grade_start is distinct from coalesce(api.dgs, t.dt)""")
    assert salah == 0


def test_konversi_rating_kinerja(dwh):
    assert query(dwh, """select performance_rating, performance_score::int from seed_angkasabiru.ref_performance_rating_angkasabiru
                         where source_system = 'angkasabiru' order by performance_score""") == [
        ("Partially Successful", 75), ("Successful", 100), ("Excellence", 110), ("Outstanding", 120)]


def test_tanggal_iso_utc_dikonversi_ke_tanggal_wib(dwh):
    """'2020-01-31T17:00:00.000Z' adalah 1 Februari 2020 WIB, bukan 31 Januari."""
    assert scalar(dwh, "select public.try_date('2020-01-31T17:00:00.000Z')::text") == "2020-02-01"
    assert scalar(dwh, "select public.try_date('15/03/2024')::text") == "2024-03-15"
    assert scalar(dwh, "select public.try_date('-')") is None
    assert scalar(dwh, "select public.try_date('2024-02-30')") is None


# ---------------------------------------------------------------- Nominatif 8 September 2026: cadangan saat API kosong
def test_nilai_api_tidak_pernah_ditimpa_nominatif(dwh):
    """fk_position_variant_id yang ada di API, termasuk kode lama yang tidak dikenal, tetap apa adanya."""
    assert scalar(dwh, """
        select count(*) from raw_table_angkasabiru.employee_position_history r
        join silver_angkasabiru.employee_position_history_angkasabiru s on s.id_position_history = btrim(r.id_position_history)
        where nullif(btrim(r.fk_position_variant_id), '') is not null
          and s.fk_position_variant_id is distinct from btrim(r.fk_position_variant_id)""") == 0


def test_nominatif_hanya_mengisi_baris_terakhir_bila_nama_jabatan_sama(dwh):
    """Nama berbeda berarti pegawai sudah pindah setelah berkas dibuat, jadi posisi dan unit di nominatif tidak berlaku lagi."""
    dasar = POSISI_TERKINI + """
        select count(*) from silver_angkasabiru.employee_position_history_angkasabiru s
        join raw_table_angkasabiru.employee_position_history r on btrim(r.id_position_history) = s.id_position_history
        join a on a.nip = s.new_nip
        left join reference_angkasabiru.nominatif_angkasabiru n on n.nik_baru = s.new_nip
        where {syarat}"""
    terisi = "(nullif(btrim(r.fk_position_variant_id), '') is null and s.fk_position_variant_id is not null or s.org_unit_name is not null)"
    assert scalar(dwh, dasar.format(syarat=terisi)) > 0
    assert scalar(dwh, dasar.format(syarat=f"{terisi} and a.urut::text <> s.id_position_history")) == 0
    assert scalar(dwh, dasar.format(syarat=f"{terisi} and {NAMA_JABATAN} is distinct from a.pn")) == 0


def test_pencocokan_nominatif_akurat_terhadap_fk_api(dwh):
    """Uji balik: pada pegawai yang punya fk dari API dan nama jabatannya sama, hasil pencocokan harus menemukan fk yang sama."""
    benar, total = query(dwh, POSISI_TERKINI + f"""
        select count(*) filter (where k.fk_position_variant_id = b.fk), count(*)
        from staging_angkasabiru.int_nominatif_angkasabiru k
        join b on b.nip = k.new_nip join a on a.nip = k.new_nip
        where k.fk_position_variant_id is not null and k.nama_jabatan = a.pn""")[0]
    assert total > 1000
    assert benar / total >= 0.97, f"{benar}/{total}"


def test_unit_nominatif_tidak_mengisi_org_group(dwh):
    """Unit di nominatif tingkatnya berbeda dengan group, jadi org_group_name harus selalu nama dari tabel groups."""
    assert scalar(dwh, f"""select count(*) from silver_angkasabiru.employee_profile_angkasabiru p where p.{AP} and p.org_group_name is not null
        and not exists (select 1 from raw_table_angkasabiru.groups g where btrim(g.name_group) = p.org_group_name)""") == 0


def test_cakupan_setelah_nominatif(dwh):
    total, area, direktorat, grup = query(dwh, f"""select count(*), count(area_name), count(directorate_name), count(org_group_name)
        from silver_angkasabiru.employee_profile_angkasabiru where {AP}""")[0]
    assert area / total >= 0.99 and direktorat / total >= 0.97 and grup / total >= 0.90


def test_career_aspiration_merujuk_pegawai_posisi_dan_job_family(dwh):
    """career_aspiration berasal dari Angkasa Biru TMS (baris ber-company_code 'AB'): setiap baris TMS masuk, dan
    pegawai, posisi target, serta job family target-nya dikenal di silver perusahaan ini."""
    total, posisi, job_family = query(dwh, """select count(*), count(id_target_position), count(id_target_job_family)
                                              from silver_angkasabiru.career_aspiration_angkasabiru""")[0]
    assert total > 0 and posisi > 0 and job_family > 0
    assert total == scalar(dwh, "select count(*) from raw_table_tms.career_aspirations where company_code = 'AB'")
    assert scalar(dwh, """select count(*) from silver_angkasabiru.career_aspiration_angkasabiru a
                          where not exists (select 1 from silver_angkasabiru.employee_profile_angkasabiru p
                                            where p.id_employee = a.id_employee)""") == 0
    assert scalar(dwh, """select count(*) from silver_angkasabiru.career_aspiration_angkasabiru a
                          where a.id_target_position is not null
                            and not exists (select 1 from silver_angkasabiru.position_master_angkasabiru m
                                            where m.id_position_master = a.id_target_position)""") == 0
    assert scalar(dwh, """select count(*) from silver_angkasabiru.career_aspiration_angkasabiru a
                          where a.id_target_job_family is not null
                            and not exists (select 1 from silver_angkasabiru.job_family_angkasabiru f
                                            where f.id_job_family = a.id_target_job_family)""") == 0


def test_career_aspiration_satu_baris_per_pegawai_per_sumber_aspirasi(dwh):
    """Sumber aspirasi hanya empat nilai baku, paling banyak satu baris per pegawai per sumber aspirasi, dan tanggal
    aspirasi tidak di masa depan."""
    assert {r[0] for r in query(dwh, "select distinct aspiration_source from silver_angkasabiru.career_aspiration_angkasabiru")} == {
        "individual", "supervisor", "job_holder", "unit"}
    assert scalar(dwh, """select count(*) from (select 1 from silver_angkasabiru.career_aspiration_angkasabiru
                                                group by id_employee, aspiration_source having count(*) > 1) d""") == 0
    assert scalar(dwh, "select count(*) from silver_angkasabiru.career_aspiration_angkasabiru where dt_aspiration > current_date") == 0
    assert scalar(dwh, "select count(dt_aspiration) from silver_angkasabiru.career_aspiration_angkasabiru") > 0


def test_employment_type_mentah_hanya_pkwtt_dan_pkwt(dwh):
    """API Angkasa Biru hanya mengirim PKWTT dan PKWT; pegawai Talent Mobility pun berstatus PKWTT
    (mobilitas dikenali di gold lewat identitas yang sama di dua perusahaan, bukan dari employment_type)."""
    assert {r[0] for r in query(dwh, "select distinct employment_type from raw_table_angkasabiru.employee_identification")} == {"PKWTT", "PKWT"}
    assert {r[0] for r in query(dwh, "select distinct employment_type from silver_angkasabiru.employee_identification_angkasabiru")} == {"PKWTT", "PKWT"}
