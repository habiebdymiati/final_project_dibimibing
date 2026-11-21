"""Layer gold (Data Hub): star schema gabungan semua perusahaan, sesuai katalog BRD bagian 6.2
(3 fact + 10 dimensi; EQS dan 9-Box dihidupkan lagi 15 November 2026 setelah sumber datanya
dilengkapi instance API tiruan; fact_talent_mobility ditambah 20 November 2026; komponen Aspirasi
EQS terisi dari Angkasa Biru TMS sejak 21 November 2026)."""
import pytest

from .conftest import query, scalar

DIM = {"dim_employee", "dim_position_master", "dim_position_variant", "dim_band", "dim_org_unit", "dim_company",
       "dim_date", "dim_contract_type", "dim_period", "dim_nine_box"}
FACT = {"fact_employee_snapshot", "fact_talent_analytics", "fact_talent_mobility"}
SUMBER = {"angkasabiru": "AB-COMP-AB", "angkasabiruretail": "AB-COMP-ABR", "abdestination": "AB-COMP-ABD"}
KODE = {"angkasabiru": "AB", "angkasabiruretail": "ABR", "abdestination": "ABD"}
# Bobot komponen EQS (lampiran katalog 7.1). Jumlahnya 105, bukan 100: eqs_score adalah RATA-RATA tertimbang.
BOBOT_EQS = {"kinerja": 25, "kompetensi": 20, "pengalaman": 15, "aspirasi": 30, "pelatihan": 10, "rekam_jejak": 5}
# Bobot empat sumber aspirasi (katalog 5.1) dan semua jumlah bobot yang mungkin dari gabungan sumbernya.
BOBOT_ASPIRASI = {"individual": 20, "supervisor": 20, "job_holder": 30, "unit": 30}
NILAI_ASPIRASI = {0, 20, 30, 40, 50, 60, 70, 80, 100}


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
    for kolom in ("eqs_score", "performance_axis_score", "capacity_axis_score", *(f"{k}_component" for k in BOBOT_EQS)):
        assert scalar(datahub, f"select count(*) from gold.fact_talent_analytics where {kolom} < 0 or {kolom} > 100") == 0, kolom


def test_aspirasi_terisi_untuk_semua_pegawai_periode_berjalan(datahub):
    """Komponen Aspirasi (career_aspiration dari Angkasa Biru TMS, katalog 5.1) terisi untuk setiap pegawai aktif:
    0 bila pegawai tidak punya aspirasi, selain itu jumlah bobot sumber aspirasi pada target terbaiknya."""
    periode = scalar(datahub, "select max(period_key) from gold.fact_talent_analytics")
    assert scalar(datahub, "select count(*) from gold.fact_talent_analytics where period_key = %s and aspirasi_component is null",
                  (periode,)) == 0
    nilai = {float(r[0]) for r in query(datahub, """select distinct aspirasi_component from gold.fact_talent_analytics
                                                    where period_key = %s""", (periode,))}
    assert nilai <= NILAI_ASPIRASI, sorted(nilai - NILAI_ASPIRASI)
    assert nilai - {0}, "tidak ada satu pun pegawai yang punya nilai aspirasi"


@pytest.mark.parametrize("sumber", SUMBER)
def test_aspirasi_sama_dengan_komposit_career_aspiration_silver(dwh, datahub, sumber):
    """Nilai aspirasi dihitung ulang di sini langsung dari silver, terpisah dari model dbt: per (pegawai, target) bobot
    sumber aspirasi yang berbeda dijumlahkan, lalu diambil target bernilai tertinggi. Aspirasi yang hanya menyebut
    job family dihitung sebagai target tersendiri; aspirasi bertanggal sesudah tanggal acuan belum dihitung."""
    tanggal = scalar(datahub, "select max(date_key) from gold.fact_employee_snapshot")
    periode = scalar(datahub, "select max(period_key) from gold.fact_talent_analytics")
    per_target = {}
    for pegawai, asal, target in query(dwh, f"""
            select id_employee, aspiration_source, coalesce(id_target_position, 'JF:' || coalesce(id_target_job_family, '-'))
            from silver_{sumber}.career_aspiration_{sumber}
            where dt_aspiration is null or dt_aspiration <= %s""", (tanggal,)):
        per_target.setdefault((pegawai, target), set()).add(asal)
    nilai = {}
    for (pegawai, _), asal in per_target.items():
        nilai[pegawai] = max(nilai.get(pegawai, 0), sum(BOBOT_ASPIRASI.get(a, 0) for a in asal))
    aktif = [r[0] for r in query(dwh, f"""select id_employee from silver_{sumber}.employee_profile_{sumber}
                                         where employment_status = 'aktif'""")]
    # pegawai tanpa aspirasi = 0; perusahaan tanpa data aspirasi sama sekali = NULL (bobot EQS-nya dinormalkan ulang)
    harap = {p: (nilai.get(p, 0) if per_target else None) for p in aktif}
    gold = dict(query(datahub, "select employee_key, aspirasi_component from gold.fact_talent_analytics where period_key = %s",
                      (periode,)))
    beda = {p: (gold.get(p), v) for p, v in harap.items() if gold.get(p) != v}
    assert harap and not beda, f"{sumber}: {len(beda)} pegawai berbeda (gold, silver), contoh {sorted(beda.items())[:5]}"


def test_eqs_rata_rata_tertimbang_enam_komponen(datahub):
    """eqs_score = rata-rata tertimbang komponen dengan bobot lampiran 7.1 (25/20/15/30/10/5). Jumlah bobot itu 105,
    jadi pembaginya jumlah bobot komponen yang terisi: 105 bila keenamnya terisi, lebih kecil bila ada yang kosong.
    Toleransi 0,1: komponen di gold sudah dibulatkan satu desimal (rata-rata tertimbangnya bergeser paling banyak
    0,05) dan eqs_score sendiri dibulatkan satu desimal (0,05 lagi)."""
    terbobot = " + ".join(f"coalesce({k}_component, 0) * {b}" for k, b in BOBOT_EQS.items())
    pembagi = " + ".join(f"case when {k}_component is not null then {b} else 0 end" for k, b in BOBOT_EQS.items())
    lengkap = " and ".join(f"{k}_component is not null" for k in BOBOT_EQS)
    periode = scalar(datahub, "select max(period_key) from gold.fact_talent_analytics")
    total, enam = query(datahub, f"""select count(*), count(*) filter (where {lengkap})
                                     from gold.fact_talent_analytics where period_key = %s""", (periode,))[0]
    assert enam >= total * 0.9, f"keenam komponen hanya terisi pada {enam} dari {total} pegawai"
    assert scalar(datahub, f"""select count(*) from gold.fact_talent_analytics
                               where (eqs_score is null and ({pembagi}) > 0)
                                  or abs(eqs_score - ({terbobot}) / nullif({pembagi}, 0)::numeric) > 0.1""") == 0


def test_nine_box_terisi_dan_valid(datahub):
    """nine_box_key selalu merujuk dim_nine_box; mayoritas pegawai terklasifikasi (bukan Unclassified)."""
    assert scalar(datahub, "select count(*) from gold.fact_talent_analytics t "
                           "where not exists (select 1 from gold.dim_nine_box n where n.nine_box_key = t.nine_box_key)") == 0
    periode = scalar(datahub, "select max(period_key) from gold.fact_talent_analytics")
    total = scalar(datahub, "select count(*) from gold.fact_talent_analytics where period_key = %s", (periode,))
    terkelas = scalar(datahub, "select count(*) from gold.fact_talent_analytics where period_key = %s and nine_box_key > 0", (periode,))
    assert terkelas >= total * 0.9


def _orang_silver(dwh):
    """id_employee -> (kode perusahaan, id_nik, employment_status, employment_type) dari silver semua perusahaan."""
    orang = {}
    for sumber, kode in KODE.items():
        for pegawai, *rinci in query(dwh, f"""select p.id_employee, i.id_nik, p.employment_status, i.employment_type
                                             from silver_{sumber}.employee_profile_{sumber} p
                                             left join silver_{sumber}.employee_identification_{sumber} i using (id_employee)"""):
            orang[pegawai] = (kode, *rinci)
    return orang


def test_talent_mobility_dikenali_dari_identitas(dwh, datahub):
    """fact_talent_mobility berbasis identitas: orang yang sama (id_nik sama) tercatat di dua perusahaan, tidak aktif
    di perusahaan asal dan aktif di perusahaan sekarang. employment_type bukan penandanya: di Angkasa Biru pegawai
    Talent Mobility berstatus PKWTT, baik sebagai perusahaan asal maupun tujuan."""
    orang = _orang_silver(dwh)
    baris = query(datahub, """select id_employee, company_current_code, id_employee_origin, company_origin_code
                              from gold.fact_talent_mobility""")
    for kini, kode_kini, asal, kode_asal in baris:
        (k_kode, k_nik, k_status, k_jenis), (a_kode, a_nik, a_status, a_jenis) = orang[kini], orang[asal]
        assert (k_kode, k_status) == (kode_kini, "aktif"), kini
        assert a_kode == kode_asal and a_kode != k_kode and a_status not in (None, "aktif"), asal
        assert k_nik and k_nik == a_nik, f"{kini} dan {asal} bukan orang yang sama"
        for kode, jenis in ((k_kode, k_jenis), (a_kode, a_jenis)):
            assert kode != "AB" or jenis == "PKWTT", (kini, asal, jenis)
    # setiap orang ber-id_nik sama di dua perusahaan (satu aktif, satu tidak aktif) masuk, tepat satu baris per orang
    per_nik = {}
    for pegawai, (kode, nik, status, _) in orang.items():
        if nik:
            per_nik.setdefault(nik, []).append((kode, status, pegawai))
    harap = sorted((t[2], a[2]) for daftar in per_nik.values() for t in daftar for a in daftar
                   if t[0] != a[0] and t[1] == "aktif" and a[1] not in (None, "aktif"))
    assert sorted((b[0], b[2]) for b in baris) == harap
    assert len(baris) == 12 and len({(b[3], b[1]) for b in baris}) == 6   # data mock: 12 orang pada 6 rute
