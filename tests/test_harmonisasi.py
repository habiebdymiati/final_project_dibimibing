"""Harmonisasi silver antar perusahaan: field yang sama punya tipe, format, dan daftar nilai yang sama.
Sumber baru otomatis ikut diperiksa begitu punya schema silver_<sumber>."""
import pytest

from .conftest import query, scalar

DOMAIN = {'employee_profile': {'employment_status': ['aktif', 'tidak aktif']}, 'employee_identification': {'gender': ['L', 'P'], 'employment_type': ['PKWTT', 'PKWT', 'Non Pegawai', 'Talent Mobility']}, 'employee_family_member': {'gender': ['L', 'P'], 'relationship_type': ['Anak', 'Anak Angkat', 'Anak Tiri', 'Pasangan', 'Ayah', 'Ibu', 'Saudara', 'Paman', 'Lainnya']}, 'employee_contract': {'contract_type': ['PKWTT', 'PKWT'], 'contract_status': ['aktif', 'berakhir']}, 'employee_leave_history': {'leave_type': ['Cuti', 'Izin'], 'leave_status': ['Disetujui', 'Disetujui Atasan', 'Diajukan']}, 'employee_performance_history': {'performance_rating': ['Partially Successful', 'Successful', 'Excellence', 'Outstanding', 'Unsuccessful']}, 'employee_education_history': {'education_degree_type': ['TK', 'SD', 'SLTP', 'SLTA', 'SMK', 'D1', 'D2', 'D3', 'D4', 'S1', 'S2', 'S3', 'Profesi', 'Non Formal']}, 'employee_disciplinary': {'disciplinary_type': ['RINGAN', 'SEDANG', 'BERAT']}, 'employee_assignment_history': {'assignment_name': ['Pelaksana Tugas (PLT)', 'Pejabat Pengganti Sementara (PGS)', 'Pelaksana Harian (PLH)']}, 'employee_address': {'address_type': ['Alamat Tetap']}}


def _sumber(dwh):
    return [r[0].replace("silver_", "", 1) for r in query(dwh, "select nspname from pg_namespace where nspname like 'silver\\_%' order by 1")]


@pytest.fixture(scope="module")
def sumber(dwh):
    s = _sumber(dwh)
    if len(s) < 2:
        pytest.skip("butuh minimal dua sumber di silver")
    return s


def test_struktur_kolom_dan_tipe_sama_antar_sumber(dwh, sumber):
    """Setiap entitas punya kolom dan tipe data yang sama di semua perusahaan."""
    per = {}
    for s in sumber:
        per[s] = {(t[:-len(s) - 1], c, d) for t, c, d in query(dwh, """select table_name, column_name, data_type from information_schema.columns
                                                                         where table_schema = %s""", (f"silver_{s}",))}
    acuan = per[sumber[0]]
    for s in sumber[1:]:
        assert per[s] == acuan, f"{s}: {sorted(per[s] ^ acuan)[:10]}"


@pytest.mark.parametrize("entitas,kolom,nilai", [(e, k, v) for e, ks in DOMAIN.items() for k, v in ks.items()])
def test_nilai_mengikuti_daftar_baku(dwh, sumber, entitas, kolom, nilai):
    for s in sumber:
        ada = {r[0] for r in query(dwh, f'select distinct "{kolom}" from silver_{s}."{entitas}_{s}" where "{kolom}" is not null')}
        assert ada <= set(nilai), f"{s}.{entitas}.{kolom} di luar daftar baku: {sorted(ada - set(nilai))}"


@pytest.mark.parametrize("entitas,kolom", [("employee_profile", "full_name"), ("employee_family_member", "full_name"),
                                           ("employee_identification", "birth_place"), ("employee_family_member", "birth_place"),
                                           ("employee_address", "street_address"), ("employee_education_history", "institution_name"),
                                           ("employee_education_history", "major"), ("job_family", "job_family_name"),
                                           ("job_function", "job_function_name")])
def test_teks_bebas_huruf_besar(dwh, sumber, entitas, kolom):
    for s in sumber:
        assert scalar(dwh, f'select count(*) from silver_{s}."{entitas}_{s}" where "{kolom}" <> upper("{kolom}")') == 0, s


@pytest.mark.parametrize("entitas", ["employee_profile", "employee_identification"])
def test_email_huruf_kecil(dwh, sumber, entitas):
    for s in sumber:
        assert scalar(dwh, f"select count(*) from silver_{s}.{entitas}_{s} where corporate_email <> lower(corporate_email)") == 0, s


def test_npwp_hanya_digit(dwh, sumber):
    for s in sumber:
        assert scalar(dwh, f"select count(*) from silver_{s}.employee_identification_{s} where id_npwp !~ '^[0-9]+$'") == 0, s


def test_penanda_kosong_menjadi_null(dwh, sumber):
    for s in sumber:
        assert scalar(dwh, f"select count(*) from silver_{s}.employee_position_history_{s} where position_name = '-' or org_unit_name = '-'") == 0, s
    assert scalar(dwh, "select public.bersih_teks(' -  ')") is None
    assert scalar(dwh, "select public.bersih_teks('N/A')") is None
    assert scalar(dwh, "select public.bersih_teks('  a   b ')") == "a b"


def test_kompetensi_inti_bernama_dan_berkategori_sama(dwh, sumber):
    """Kompetensi Core, Leadership, dan Functional yang sama punya nama dan kategori yang sama di kedua perusahaan."""
    if not {"angkasabiru", "angkasabiruretail"} <= set(sumber):
        pytest.skip("butuh Angkasa Biru dan Angkasa Biru Retail")
    assert scalar(dwh, """select count(*) from (select distinct competency_name, competency_category
                                                from silver_angkasabiru.position_competency_requirement_angkasabiru) a
                          where not exists (select 1 from silver_angkasabiruretail.position_competency_requirement_angkasabiruretail s
                                            where s.competency_name = a.competency_name and s.competency_category = a.competency_category)""") == 0


def test_id_employee_8_digit_dan_tidak_bentrok_antar_sumber(dwh, sumber):
    """Kunci pegawai: VARCHAR 8 digit di semua perusahaan; awalan berbeda per perusahaan sehingga tidak pernah bentrok."""
    awalan = set()
    for s in sumber:
        assert scalar(dwh, f"select count(*) from silver_{s}.employee_profile_{s} where id_employee !~ '^[0-9]{{8}}$'") == 0, s
        awalan |= {(s, r[0]) for r in query(dwh, f"select distinct left(id_employee, 2) from silver_{s}.employee_profile_{s}")}
    assert len({a for _, a in awalan}) == len(sumber), awalan

