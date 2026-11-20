"""Layer silver Angkasa Biru Destinasi (dbt): raw_table_abdestination -> staging -> silver_abdestination.
API NATA RINJANI memakai field bergaya katalog, jadi pemetaannya tipis. Usia pensiun 56 tahun."""
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
S = "silver_abdestination"


@pytest.fixture(scope="module", autouse=True)
def _silver_sudah_dibangun(dwh):
    if not scalar(dwh, "select count(*) from information_schema.tables where table_schema = %s", (S,)):
        pytest.skip("schema silver_abdestination belum dibangun (jalankan `make silver`)")


def test_satu_tabel_silver_per_entitas(dwh):
    tabel = {r[0] for r in query(dwh, "select table_name from information_schema.tables where table_schema = %s", (S,))}
    assert tabel == {f"{e}_abdestination" for e in ENTITAS}


def test_id_employee_varchar_awalan_30_diikuti_6_digit(dwh):
    """Kunci pegawai ABD: VARCHAR = 30 + enam digit nomor urut menurut tahun/tanggal masuk."""
    assert scalar(dwh, f"select count(*) from {S}.employee_profile_abdestination "
                       "where id_employee is null or id_employee !~ '^30[0-9]{6}$'") == 0
    assert scalar(dwh, "select bool_and(id_employee = (30000000 + urutan)::varchar) from registry_abdestination.registry_id_employee_abdestination")
    # urutan TMT dijamin di dalam tiap batch penambahan (registry incremental, ID stabil)
    assert scalar(dwh, """select count(*) from (select dt_tmt, lag(dt_tmt) over (partition by dwh_assigned_at order by urutan) as sebelum
                                               from registry_abdestination.registry_id_employee_abdestination) t where dt_tmt < sebelum""") == 0


def test_company_memakai_kode_dwh(dwh):
    assert query(dwh, f"select id_company, company_name, company_type from {S}.company_abdestination") == [
        ("AB-COMP-ABD", "PT Angkasa Biru Destination", "Member")]
    assert scalar(dwh, f"select count(*) from {S}.org_unit_abdestination where fk_id_company is distinct from 'AB-COMP-ABD'") == 0


def test_band_mengikuti_tangga(dwh):
    assert query(dwh, f"select band_name, band_code, job_class_min, job_class_max from {S}.band_abdestination order by band_sequence") == [
        ("Band 1", "BOD-1", 17, 23), ("Band 2", "BOD-2", 14, 16), ("Band 3", "BOD-3", 12, 13), ("Band 4", "BOD-4", 7, 11)]


def test_usia_pensiun_56(dwh):
    """dt_retirement = ulang tahun ke-56; pegawai aktif belum melewati usia pensiun."""
    assert scalar(dwh, f"""select count(*) from {S}.employee_identification_abdestination
                           where dt_retirement is distinct from (dt_birth + interval '56 years')::date
                             and extract(day from dt_birth) <= 28""") == 0
    assert scalar(dwh, f"""select count(*) from {S}.employee_identification_abdestination i
                           join {S}.employee_profile_abdestination p on p.id_employee = i.id_employee
                           where p.employment_status = 'aktif' and i.dt_retirement <= current_date""") == 0


def test_referensi_posisi_dan_pegawai_utuh(dwh):
    """Aturan referential integrity: riwayat posisi -> varian sah; tabel anak -> profil."""
    assert scalar(dwh, f"""select count(*) from {S}.employee_position_history_abdestination h
                           where not exists (select 1 from {S}.position_variant_abdestination v
                                             where v.id_position_variant = h.fk_position_variant_id)""") == 0
    for t in ("employee_identification", "employee_contract", "employee_leave_history", "learning_history"):
        assert scalar(dwh, f"""select count(*) from {S}.{t}_abdestination x
                               where not exists (select 1 from {S}.employee_profile_abdestination p
                                                 where p.id_employee = x.id_employee)""") == 0, t


def test_kontrak_mengikuti_business_rules(dwh):
    assert scalar(dwh, f"select count(*) from {S}.employee_contract_abdestination where dt_contract_end <= dt_contract_start") == 0
    assert scalar(dwh, f"""select count(*) from raw_table_abdestination.employee_contracts
                           where public.try_date(dt_probation_end) > public.try_date(dt_contract_start) + interval '3 months'""") == 0
