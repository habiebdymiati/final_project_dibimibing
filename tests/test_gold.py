"""Layer gold (Data Hub): star schema gabungan semua perusahaan, sesuai katalog BRD bagian 6.2
(2 fact + 10 dimensi; EQS dan 9-Box dihidupkan lagi 15 November 2026 setelah sumber datanya
dilengkapi instance API tiruan)."""
import pytest

from .conftest import query, scalar

DIM = {"dim_employee", "dim_position_master", "dim_position_variant", "dim_band", "dim_org_unit", "dim_company",
       "dim_date", "dim_contract_type", "dim_period", "dim_nine_box"}
FACT = {"fact_employee_snapshot", "fact_talent_analytics"}
SUMBER = {"angkasabiru": "AB-COMP-AB", "angkasabiruretail": "AB-COMP-ABR", "abdestination": "AB-COMP-ABD"}


@pytest.fixture(scope="module", autouse=True)
def _gold_sudah_dibangun(datahub):
    if not scalar(datahub, "select count(*) from information_schema.tables where table_schema = 'gold'"):
        pytest.skip("schema gold belum dibangun (jalankan `make gold`)")


def _baris_silver(dwh, sumber, entitas, syarat="true"):
    return scalar(dwh, f"select count(*) from silver_{sumber}.{entitas}_{sumber} where {syarat}")


def test_star_schema_lengkap_sesuai_katalog(datahub):
    tabel = {r[0] for r in query(datahub, "select table_name from information_schema.tables where table_schema = 'gold'")}
    assert tabel == DIM | FACT


def test_dim_employee_memuat_semua_pegawai_semua_perusahaan(dwh, datahub):
    harap = sum(_baris_silver(dwh, s, "employee_profile") for s in SUMBER)
    assert scalar(datahub, "select count(*) from gold.dim_employee") == harap


@pytest.mark.parametrize("sumber,company", SUMBER.items())
def test_fact_hanya_memuat_pegawai_aktif_per_perusahaan(dwh, datahub, sumber, company):
    aktif = _baris_silver(dwh, sumber, "employee_profile", "employment_status = 'aktif'")
    tanggal = scalar(datahub, "select max(date_key) from gold.fact_employee_snapshot")
    assert scalar(datahub, "select count(*) from gold.fact_employee_snapshot where company_key = %s and date_key = %s", (company, tanggal)) == aktif


def test_top_talent_mengikuti_master_data(dwh, datahub):
    """is_top_talent di snapshot sama dengan kolom Top Talent master data untuk pegawai aktif, dan tidak pernah kosong."""
    ya = set()
    for s in SUMBER:
        ya |= {r[0] for r in query(dwh, f"select id_employee from silver_{s}.top_talent_{s} where is_top_talent")}
    tanggal = "date_key = (select max(date_key) from gold.fact_employee_snapshot)"
    aktif = {r[0] for r in query(datahub, f"select employee_key from gold.fact_employee_snapshot where {tanggal}")}
    ditandai = {r[0] for r in query(datahub, f"select employee_key from gold.fact_employee_snapshot where {tanggal} and is_top_talent")}
    assert ditandai and ditandai == ya & aktif
    assert scalar(datahub, "select count(*) from gold.fact_employee_snapshot where is_top_talent is null") == 0


def test_master_data_di_dwh_hanya_berisi_kolom_yang_dipakai(dwh):
    """Nama, tanggal lahir, dan kolom lain di master data tidak boleh ikut masuk DWH."""
    for s in SUMBER:
        kolom = {r[0] for r in query(dwh, """select column_name from information_schema.columns
                                             where table_schema = %s and table_name = %s""", (f"reference_{s}", f"master_data_{s}"))}
        assert kolom == {"_file", "_loaded_at", "nik", "top_talent"}, s


def test_kunci_gold_tidak_bentrok_antar_perusahaan(datahub):
    for tabel, kolom in (("dim_org_unit", "org_unit_key"), ("dim_position_master", "position_master_key"), ("dim_position_variant", "position_variant_key")):
        awalan = {r[0] for r in query(datahub, f"select distinct split_part({kolom}, '-', 1) from gold.{tabel}")}
        assert awalan == {"AB", "ABR", "ABD", "UNKNOWN"}, tabel


def test_varian_bawaan_hanya_untuk_master_tanpa_varian(dwh, datahub):
    for sumber, kode in (("angkasabiru", "AB"), ("angkasabiruretail", "ABR"), ("abdestination", "ABD")):
        harap = scalar(dwh, f"""select count(*) from silver_{sumber}.position_master_{sumber} m
            where not exists (select 1 from silver_{sumber}.position_variant_{sumber} v
                              where v.fk_position_master_id = m.id_position_master or v.id_position_variant = m.id_position_master)""")
        assert scalar(datahub, "select count(*) from gold.dim_position_variant where is_default_variant and position_variant_key like %s", (f"{kode}-%",)) == harap, sumber


def test_umur_wajar(datahub):
    """Tanggal lahir placeholder (1900 ke bawah) tidak boleh menghasilkan umur tidak masuk akal."""
    assert scalar(datahub, "select coalesce(max(age), 0) from gold.dim_employee") < 100


def test_talent_analytics_periode_berjalan_mencakup_pegawai_aktif(dwh, datahub):
    """fact_talent_analytics (katalog BRD 6.2): satu baris per pegawai aktif pada periode berjalan."""
    periode = scalar(datahub, "select max(period_key) from gold.fact_talent_analytics")
    aktif = sum(_baris_silver(dwh, s, "employee_profile", "employment_status = 'aktif'") for s in SUMBER)
    assert scalar(datahub, "select count(*) from gold.fact_talent_analytics where period_key = %s", (periode,)) == aktif
    assert scalar(datahub, "select count(*) from gold.fact_talent_analytics where period_key = %s and is_top_talent",
                  (periode,)) > 0


def test_eqs_komponen_dan_sumbu_dalam_rentang_0_100(datahub):
    for kolom in ("eqs_score", "performance_axis_score", "capacity_axis_score", "kinerja_component",
                  "kompetensi_component", "pengalaman_component", "pelatihan_component", "rekam_jejak_component"):
        assert scalar(datahub, f"select count(*) from gold.fact_talent_analytics where {kolom} < 0 or {kolom} > 100") == 0, kolom


def test_aspirasi_masih_null_menunggu_rinjani(datahub):
    """Komponen Aspirasi bersumber career_aspiration milik Rinjani (inbound) yang belum tersedia."""
    assert scalar(datahub, "select count(aspirasi_component) from gold.fact_talent_analytics") == 0


def test_nine_box_terisi_dan_valid(datahub):
    """nine_box_key selalu merujuk dim_nine_box; mayoritas pegawai terklasifikasi (bukan Unclassified)."""
    assert scalar(datahub, "select count(*) from gold.fact_talent_analytics t "
                           "where not exists (select 1 from gold.dim_nine_box n where n.nine_box_key = t.nine_box_key)") == 0
    periode = scalar(datahub, "select max(period_key) from gold.fact_talent_analytics")
    total = scalar(datahub, "select count(*) from gold.fact_talent_analytics where period_key = %s", (periode,))
    terkelas = scalar(datahub, "select count(*) from gold.fact_talent_analytics where period_key = %s and nine_box_key > 0", (periode,))
    assert terkelas >= total * 0.9
