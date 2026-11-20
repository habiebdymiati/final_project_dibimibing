"""Layer silver Angkasa Biru Retail (dbt): raw_table_angkasabiruretail -> staging_angkasabiruretail -> silver_angkasabiruretail.<entitas>_angkasabiruretail,
sesuai draf mapping data/refrence/mapping api to angkasabiruretail.csv. Aturan umumnya sama dengan Angkasa Biru."""
import pytest

from .conftest import query, scalar

ENTITAS = {
    "company", "org_unit", "position_master", "position_variant", "band", "position_competency_requirement",
    "job_family", "job_function", "employee_profile", "employee_identification", "employee_address",
    "employee_family_member", "employee_contract", "employee_position_history", "employee_assignment_history",
    "employee_performance_history", "employee_leave_history", "employee_education_history",
    "employee_disciplinary",
    "learning_history", "learning_agility_assessment", "competency_assessment", "employee_secondary_assignment",
    "top_talent",   # bukan entitas katalog: penanda top talent dari master data
}
TABEL_BER_ID_PEGAWAI = ("employee_profile", "employee_identification", "employee_address", "employee_family_member",
                        "employee_contract", "employee_assignment_history", "employee_performance_history",
                        "employee_leave_history", "employee_education_history", "employee_disciplinary")
S = "silver_angkasabiruretail"


@pytest.fixture(scope="module", autouse=True)
def _silver_sudah_dibangun(dwh):
    if not scalar(dwh, "select count(*) from information_schema.tables where table_schema = %s", (S,)):
        pytest.skip("schema silver_angkasabiruretail belum dibangun (jalankan `make silver`)")


def test_schema_dan_objek_berakhiran_angkasabiruretail(dwh):
    tabel = {r[0] for r in query(dwh, "select table_name from information_schema.tables where table_schema = %s", (S,))}
    assert tabel == {f"{e}_angkasabiruretail" for e in ENTITAS}
    schema = {r[0] for r in query(dwh, "select nspname from pg_namespace where nspname ~ '^(staging|silver|seed|registry)_angkasabiruretail$'")}
    assert schema == {"staging_angkasabiruretail", "silver_angkasabiruretail", "seed_angkasabiruretail", "registry_angkasabiruretail"}
    liar = query(dwh, """select table_schema, table_name from information_schema.tables
                         where table_schema in ('staging_angkasabiruretail', 'silver_angkasabiruretail', 'seed_angkasabiruretail', 'registry_angkasabiruretail')
                           and right(table_name, 18) <> '_angkasabiruretail'""")
    assert liar == []


def test_id_employee_varchar_awalan_20_diikuti_6_digit_dan_tidak_bentrok(dwh):
    """Kunci pegawai Angkasa Biru Retail: VARCHAR = 20 + enam digit nomor urut; tidak pernah sama dengan ID Angkasa Biru."""
    for t in TABEL_BER_ID_PEGAWAI:
        assert scalar(dwh, """select data_type from information_schema.columns
                              where table_schema = %s and table_name = %s and column_name = 'id_employee'""", (S, f"{t}_angkasabiruretail")) == "character varying", t
        assert scalar(dwh, f"select count(*) from {S}.{t}_angkasabiruretail where id_employee is null or id_employee !~ '^20[0-9]{{6}}$'") == 0, t
    assert scalar(dwh, "select bool_and(id_employee = (20000000 + urutan)::varchar) from registry_angkasabiruretail.registry_id_employee_angkasabiruretail")
    if scalar(dwh, "select count(*) from information_schema.tables where table_schema = 'registry_angkasabiru'"):
        assert scalar(dwh, """select count(*) from registry_angkasabiruretail.registry_id_employee_angkasabiruretail s
                              join registry_angkasabiru.registry_id_employee_angkasabiru a on a.id_employee = s.id_employee""") == 0


def test_company_angkasabiruretail_memakai_kode_dwh(dwh):
    assert query(dwh, f"select id_company, company_name, company_type, dt_establishment::text from {S}.company_angkasabiruretail") == [
        ("AB-COMP-ABR", "PT Angkasa Biru Retail", "Member", "1962-08-17")]
    assert scalar(dwh, f"select count(*) from {S}.org_unit_angkasabiruretail where fk_id_company is distinct from 'AB-COMP-ABR'") == 0


def test_id_employee_berurut_menurut_tanggal_mulai_bekerja(dwh):
    # urutan TMT dijamin di dalam tiap batch penambahan (registry incremental, ID stabil)
    assert scalar(dwh, """select count(*) from (select dt_tmt, lag(dt_tmt) over (partition by dwh_assigned_at order by urutan) as sebelum
                                               from registry_angkasabiruretail.registry_id_employee_angkasabiruretail) t where dt_tmt < sebelum""") == 0
    assert scalar(dwh, "select count(*) = max(urutan) and min(urutan) = 1 from registry_angkasabiruretail.registry_id_employee_angkasabiruretail")


def test_pegawai_terhubung_lewat_old_nip(dwh):
    """old_nip adalah penghubung dua nomor pegawai Angkasa Biru Retail; setiap profil mendapat tepat satu id_employee."""
    assert scalar(dwh, f"select count(*) = count(distinct id_employee) and count(*) = count(distinct old_nip) from {S}.employee_profile_angkasabiruretail")
    # semua orang di employee-profile dan di employees ikut dimuat
    assert scalar(dwh, f"select count(*) from {S}.employee_profile_angkasabiruretail") == \
        scalar(dwh, """select count(*) from (select old_nip from raw_table_angkasabiruretail.employee__profile
                                             union select code_member from raw_table_angkasabiruretail.employees) t""")
    assert scalar(dwh, f"""select count(*) from {S}.employee_profile_angkasabiruretail p
                           join registry_angkasabiruretail.registry_id_employee_angkasabiruretail g on g.nip = p.old_nip
                           where g.id_employee <> p.id_employee""") == 0
    for t in ("employee_identification", "employee_address", "employee_contract", "employee_family_member",
              "employee_performance_history", "employee_disciplinary"):
        yatim = scalar(dwh, f"""select count(*) from {S}.{t}_angkasabiruretail x
                                where not exists (select 1 from {S}.employee_profile_angkasabiruretail p where p.id_employee = x.id_employee)""")
        assert yatim == 0, t


def test_new_nip_sama_dengan_old_nip(dwh):
    assert scalar(dwh, f"select count(*) from {S}.employee_profile_angkasabiruretail where new_nip is distinct from old_nip") == 0


# Selaras dengan Angkasa Biru (keputusan 09 November 2026): 17 ke atas Band 1, 14-16 Band 2, 12-13 Band 3, 7-11 Band 4.
TANGGA_BAND = [("Band 1", "BOD-1", 17, 23), ("Band 2", "BOD-2", 14, 16),
               ("Band 3", "BOD-3", 12, 13), ("Band 4", "BOD-4", 7, 11)]


def test_band_mengikuti_tangga_angkasabiruretail(dwh):
    assert query(dwh, f"select band_name, band_code, job_class_min, job_class_max from {S}.band_angkasabiruretail order by band_sequence") == TANGGA_BAND
    assert scalar(dwh, f"select count(*) = count(distinct id_band) from {S}.band_angkasabiruretail")


def _band_seharusnya(jc):
    return next((nama for nama, _, a, b in TANGGA_BAND if a <= jc <= b), None)


def test_fk_band_dan_band_name_mengikuti_job_class(dwh):
    """position_variant.fk_band_id dan employee_profile.band_name mengikuti rentang job_class; di luar rentang tidak punya band."""
    for jc, nama in query(dwh, f"""select v.job_class, b.band_name from {S}.position_variant_angkasabiruretail v
                                   left join {S}.band_angkasabiruretail b on b.id_band = v.fk_band_id where v.job_class is not null"""):
        assert nama == _band_seharusnya(jc), jc
    for jc, nama in query(dwh, f"""select i.job_class, p.band_name from {S}.employee_profile_angkasabiruretail p
                                   join {S}.employee_identification_angkasabiruretail i on i.id_employee = p.id_employee"""):
        harap = _band_seharusnya(int(jc)) if jc and jc.isdigit() else None
        assert nama == harap, jc


def test_area_name_dari_master_area(dwh):
    assert scalar(dwh, f"""select count(*) from {S}.employee_profile_angkasabiruretail p
                           where p.area_name is not null
                             and not exists (select 1 from raw_table_angkasabiruretail.areas a where btrim(a.name_area) = p.area_name)""") == 0
    assert scalar(dwh, f"select count(area_name) from {S}.employee_profile_angkasabiruretail") > 0


def test_mobile_phone_distandarkan_berawalan_08(dwh):
    assert scalar(dwh, f"select count(*) from {S}.employee_identification_angkasabiruretail where mobile_phone !~ '^08[0-9]{{8,12}}$'") == 0
    assert scalar(dwh, f"select count(mobile_phone) from {S}.employee_identification_angkasabiruretail") > 0


def test_keluarga_gabungan_pasangan_dan_anak(dwh):
    assert {r[0] for r in query(dwh, f"select distinct relationship_type from {S}.employee_family_member_angkasabiruretail")} <= {"Pasangan", "Anak"}
    assert scalar(dwh, f"select count(*) from {S}.employee_family_member_angkasabiruretail") == \
        scalar(dwh, "select (select count(*) from raw_table_angkasabiruretail.spouses) + (select count(*) from raw_table_angkasabiruretail.childrens)")


def test_position_variant_merujuk_position_master_tanpa_awalan(dwh):
    assert scalar(dwh, f"select count(*) from {S}.position_variant_angkasabiruretail where fk_position_master_id like 'PM\\_%'") == 0
    assert scalar(dwh, f"""select count(*) from {S}.position_variant_angkasabiruretail v
                           where not exists (select 1 from {S}.position_master_angkasabiruretail m where m.id_position_master = v.fk_position_master_id)""") == 0
