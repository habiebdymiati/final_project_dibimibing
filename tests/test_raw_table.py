"""raw_table_<sumber>: pendataran payload JSONB menjadi tabel kolom-baris (kunci -> kolom),
diisi ulang dengan TRUNCATE + INSERT sehingga hanya batch sukses terakhir yang tersimpan."""
import psycopg2
import pytest

from ingestion.config import list_sources, load_source, pg_params
from ingestion.flatten import LINEAGE, flat_schema_name, flatten_endpoint
from ingestion.storage import table_name

from .conftest import query, scalar


def _success_endpoints(dwh, schema):
    return [r[0] for r in query(dwh, f"select distinct endpoint from {schema}._ingestion_log where status = 'success'")]


@pytest.mark.parametrize("source", list_sources())
def test_every_defined_endpoint_has_raw_and_flat_table_even_when_empty(dwh, source):
    """Aturan layer raw: endpoint diproses apa adanya dan lengkap sesuai jumlahnya. Endpoint yang kosong
    tetap punya tabel (kosong) di raw_ dan raw_table_; tidak ada endpoint yang dibuang, tidak ada tabel liar."""
    cfg = load_source(source)
    raw, flat = cfg["raw"]["schema"], flat_schema_name(cfg["raw"]["schema"])
    expected = {table_name(e["name"]) for e in cfg["endpoints"]}
    tables = lambda schema: {r[0] for r in query(dwh, "select tablename from pg_tables where schemaname = %s", (schema,))}
    assert tables(raw) - {"_ingestion_log"} == expected, f"{source}: tabel raw_ tidak sama dengan daftar endpoint"
    assert tables(flat) == expected, f"{source}: tabel raw_table_ tidak sama dengan daftar endpoint"
    assert len(tables(flat)) == len(cfg["endpoints"])


@pytest.mark.parametrize("source", list_sources())
def test_every_ingested_endpoint_has_flat_table_with_matching_rowcount(dwh, source):
    cfg = load_source(source)
    raw, flat = cfg["raw"]["schema"], flat_schema_name(cfg["raw"]["schema"])
    for ep in _success_endpoints(dwh, raw):
        tbl = table_name(ep)
        n_flat = scalar(dwh, f'select count(*) from {flat}."{tbl}"')
        n_raw = scalar(dwh, f"""select count(*) from {raw}."{tbl}" r
            join (select batch_id from {raw}._ingestion_log where endpoint = %s and status = 'success'
                  order by extracted_at desc limit 1) b using (batch_id)""", (ep,))
        assert n_flat == n_raw, f"{source}.{ep}: flat {n_flat} != raw batch terakhir {n_raw}"


@pytest.mark.parametrize("source", list_sources())
def test_flat_columns_cover_payload_keys_plus_lineage(dwh, source):
    """Semua kunci payload batch terakhir + kolom silsilah ada sebagai kolom. Kolom lebih hanya boleh berasal
    dari kunci yang tidak lagi dikirim sumber (dipertahankan oleh truncate-insert) dan isinya harus NULL."""
    cfg = load_source(source)
    raw, flat = cfg["raw"]["schema"], flat_schema_name(cfg["raw"]["schema"])
    for ep in _success_endpoints(dwh, raw):
        tbl = table_name(ep)
        cols = {r[0] for r in query(dwh, """select column_name from information_schema.columns
                                            where table_schema = %s and table_name = %s""", (flat, tbl))}
        keys = {r[0][:63] for r in query(dwh, f"""select distinct jsonb_object_keys(payload) from {raw}."{tbl}" r
            join (select batch_id from {raw}._ingestion_log where endpoint = %s and status = 'success'
                  order by extracted_at desc limit 1) b using (batch_id)""", (ep,))}
        assert keys | set(LINEAGE) <= cols, f"{source}.{ep}: kunci payload belum menjadi kolom: {sorted(keys - cols)}"
        for stale in cols - keys - set(LINEAGE):
            assert scalar(dwh, f'select count("{stale}") from {flat}."{tbl}"') == 0, \
                f"{source}.{ep}: kolom {stale} tidak ada di payload terbaru tetapi masih berisi nilai"


@pytest.mark.parametrize("source", list_sources())
def test_flat_table_holds_only_latest_success_batch(dwh, source):
    """Truncate-insert: tidak ada sisa batch lama di raw_table_."""
    cfg = load_source(source)
    raw, flat = cfg["raw"]["schema"], flat_schema_name(cfg["raw"]["schema"])
    for ep in _success_endpoints(dwh, raw):
        tbl = table_name(ep)
        latest = scalar(dwh, f"""select batch_id from {raw}._ingestion_log where endpoint = %s and status = 'success'
                                 order by extracted_at desc limit 1""", (ep,))
        batches = {r[0] for r in query(dwh, f'select distinct _batch_id from {flat}."{tbl}"')}
        assert batches <= {latest}, f"{source}.{ep}: raw_table menyimpan batch selain yang terbaru: {batches}"


@pytest.fixture
def scratch(dwh):
    """Schema raw_/raw_table_ sementara untuk menguji perilaku truncate-insert; selalu dibersihkan."""
    raw, flat = "raw_test_flatten", "raw_table_test_flatten"

    def cleanup():
        with dwh.cursor() as cur:
            cur.execute(f"drop schema if exists {raw} cascade")
            cur.execute(f"drop schema if exists {flat} cascade")

    cleanup()
    with dwh.cursor() as cur:
        cur.execute(f"create schema {raw}")
        cur.execute(f"""create table {raw}._ingestion_log (batch_id text, source text, endpoint text, ds date,
                            extracted_at timestamptz, status text, row_count int)""")
        cur.execute(f"""create table {raw}.pegawai (batch_id text, ds date, extracted_at timestamptz,
                            source_endpoint text, row_hash text, payload jsonb)""")
    conn = psycopg2.connect(**pg_params("DWH"))   # transaksional (bukan autocommit) seperti ingestion.flatten.run
    try:
        yield conn, raw, flat
    finally:
        conn.close()
        cleanup()


def _load_batch(dwh, raw, batch_id, ts, rows):
    with dwh.cursor() as cur:
        for i, payload in enumerate(rows):
            cur.execute(f"insert into {raw}.pegawai values (%s, %s::timestamptz::date, %s, 'pegawai', %s, %s::jsonb)",
                        (batch_id, ts, ts, f"h{i}", payload))
        cur.execute(f"insert into {raw}._ingestion_log values (%s, 'test', 'pegawai', %s::timestamptz::date, %s, 'success', %s)",
                    (batch_id, ts, ts, len(rows)))


def test_truncate_insert_keeps_table_and_stores_only_latest_values(dwh, scratch):
    conn, raw, flat = scratch
    oid = lambda: scalar(dwh, "select %s::regclass::oid", (f"{flat}.pegawai",))

    _load_batch(dwh, raw, "b1", "2026-01-01 08:00+07",
                ['{"nik": "1", "nama": "A", "lama": "x"}', '{"nik": "2", "nama": "B", "lama": "y"}',
                 '{"nik": "3", "nama": "C", "lama": "z"}'])
    assert flatten_endpoint(conn, raw, "pegawai") == 3
    oid_awal = oid()
    dwh.cursor().execute(f"create view {flat}.v_pegawai as select nik, nama from {flat}.pegawai")

    # batch baru: nilai berubah, satu pegawai hilang, kunci "lama" hilang, kunci "unit" baru
    _load_batch(dwh, raw, "b2", "2026-01-02 08:00+07",
                ['{"nik": "1", "nama": "A2", "unit": "HC"}', '{"nik": "2", "nama": "B", "unit": "IT"}'])
    assert flatten_endpoint(conn, raw, "pegawai") == 2

    assert oid() == oid_awal, "tabel tidak boleh di-drop/dibuat ulang"
    assert query(dwh, f"select nik, nama, unit, lama, _batch_id from {flat}.pegawai order by nik") == [
        ("1", "A2", "HC", None, "b2"), ("2", "B", "IT", None, "b2")]
    assert query(dwh, f"select nik, nama from {flat}.v_pegawai order by nik") == [("1", "A2"), ("2", "B")]

    # dijalankan ulang tanpa batch baru: hasil sama (idempoten), tidak menggandakan baris
    assert flatten_endpoint(conn, raw, "pegawai") == 2
    assert scalar(dwh, f"select count(*) from {flat}.pegawai") == 2


def test_failed_reload_leaves_previous_values_intact(dwh, scratch):
    """TRUNCATE dan INSERT satu transaksi: bila pengisian gagal, isi lama tidak hilang."""
    conn, raw, flat = scratch
    _load_batch(dwh, raw, "b1", "2026-01-01 08:00+07", ['{"nik": "1"}', '{"nik": "2"}'])
    assert flatten_endpoint(conn, raw, "pegawai") == 2
    dwh.cursor().execute(f"alter table {flat}.pegawai add constraint nik_bukan_9 check (nik <> '9')")
    _load_batch(dwh, raw, "b2", "2026-01-02 08:00+07", ['{"nik": "9"}'])
    with pytest.raises(psycopg2.Error):
        flatten_endpoint(conn, raw, "pegawai")
    assert query(dwh, f"select nik, _batch_id from {flat}.pegawai order by nik") == [("1", "b1"), ("2", "b1")]


def test_flat_schema_name_follows_pattern():
    assert flat_schema_name("raw_angkasabiruretail") == "raw_table_angkasabiruretail"
    assert flat_schema_name("raw_angkasabiru") == "raw_table_angkasabiru"
