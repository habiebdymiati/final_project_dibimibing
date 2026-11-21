"""Ingestion: unit test tanpa database, lalu pemeriksaan hasil di raw layer dan MinIO."""
import json
import os
import time

import pytest
import yaml

from ingestion.config import PROJECT_ROOT, _expand, load_source
from ingestion.connectors import EndpointNotFound, ExtractError, RestApiConnector, _unwrap
from ingestion.run_ingest import row_hash
from ingestion.storage import table_name

from .conftest import query, scalar


# ------------------------------------------------------------------ unit (tanpa DB)
def test_expand_env_inline_and_default(monkeypatch):
    monkeypatch.setenv("FOO", "bar")
    assert _expand("x-${FOO}-y") == "x-bar-y"
    assert _expand("${MISSING_VAR:-fallback}") == "fallback"
    assert _expand({"a": ["${FOO}"]}) == {"a": ["bar"]}


@pytest.mark.parametrize(
    "payload, expected",
    [
        ([{"a": 1}], [{"a": 1}]),
        ({"data": [{"a": 1}, {"a": 2}]}, [{"a": 1}, {"a": 2}]),
        ({"data": {"a": 1}}, [{"a": 1}]),
        ({"data": None}, []),
        ({"a": 1}, [{"a": 1}]),
        ([1, 2], [{"value": 1}, {"value": 2}]),
    ],
)
def test_unwrap_payload_shapes(payload, expected):
    assert _unwrap(payload) == expected


def test_row_hash_is_stable_and_order_independent():
    assert row_hash({"a": 1, "b": 2}) == row_hash({"b": 2, "a": 1})
    assert row_hash({"a": 1}) != row_hash({"a": 2})


def test_table_name_has_no_collision_between_hyphen_and_underscore():
    assert table_name("employee-contracts") != table_name("employee_contracts")


def test_live_mode_requires_credentials_and_never_falls_back_to_sample():
    cfg = {"mode": "live", "api": {"base_url": "http://x", "api_key": ""}, "sample_dir": "data/sample/angkasabiruretail"}
    with pytest.raises(ExtractError):
        RestApiConnector(cfg).fetch({"name": "companies", "path": "/companies"})


def test_live_mode_reports_unreachable_api():
    cfg = {"mode": "live", "api": {"base_url": "http://127.0.0.1:9", "api_key": "k", "timeout_seconds": 2, "retries": 0}}
    with pytest.raises(ExtractError):
        RestApiConnector(cfg).fetch({"name": "companies", "path": "/companies"})


class _Resp:
    def __init__(self, status, payload=None):
        self.status_code, self._payload = status, payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(f"{self.status_code} Error", response=self)

    def json(self):
        return self._payload


def _live_connector(monkeypatch, responses):
    """Konektor live dengan requests.get dan sleep dipalsukan; responses = urutan hasil per percobaan."""
    import requests

    calls = {"n": 0, "sleeps": []}

    def fake_get(url, headers=None, params=None, timeout=None):
        calls.setdefault("params", []).append(params)
        item = responses[min(calls["n"], len(responses) - 1)]
        calls["n"] += 1
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr("ingestion.connectors.requests.get", fake_get)
    monkeypatch.setattr("ingestion.connectors.time.sleep", lambda s: calls["sleeps"].append(s))
    cfg = {"mode": "live", "api": {"base_url": "http://x", "api_key": "k", "retries": 2, "retry_backoff_seconds": 3}}
    return RestApiConnector(cfg), calls, requests


EP = {"name": "companies", "path": "/companies"}


def test_transient_522_is_retried_then_succeeds(monkeypatch):
    conn, calls, _ = _live_connector(monkeypatch, [_Resp(522), _Resp(522), _Resp(200, {"data": [{"a": 1}]})])
    assert conn.fetch(EP) == [{"a": 1}]
    assert calls["n"] == 3 and calls["sleeps"] == [3, 6]


def test_connection_error_is_retried_then_gives_up(monkeypatch):
    import requests

    conn, calls, _ = _live_connector(monkeypatch, [requests.ConnectionError("Network is unreachable")])
    with pytest.raises(ExtractError, match="3 percobaan"):
        conn.fetch(EP)
    assert calls["n"] == 3


def test_persistent_522_fails_after_all_attempts(monkeypatch):
    conn, calls, _ = _live_connector(monkeypatch, [_Resp(522)])
    with pytest.raises(ExtractError):
        conn.fetch(EP)
    assert calls["n"] == 3


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_client_errors_are_not_retried(monkeypatch, status):
    conn, calls, _ = _live_connector(monkeypatch, [_Resp(status)])
    with pytest.raises(ExtractError):
        conn.fetch(EP)
    assert calls["n"] == 1 and calls["sleeps"] == []


def test_404_is_reported_as_endpoint_not_found_without_retry(monkeypatch):
    conn, calls, _ = _live_connector(monkeypatch, [_Resp(404)])
    with pytest.raises(EndpointNotFound):
        conn.fetch(EP)
    assert calls["n"] == 1


def test_invalid_json_is_not_retried(monkeypatch):
    class Bad(_Resp):
        def json(self):
            raise ValueError("bukan json")

    conn, calls, _ = _live_connector(monkeypatch, [Bad(200)])
    with pytest.raises(ExtractError):
        conn.fetch(EP)
    assert calls["n"] == 1


def test_sample_mode_missing_fixture_fails_loudly():
    cfg = {"mode": "sample", "sample_dir": "data/sample/angkasabiruretail"}
    with pytest.raises(ExtractError):
        RestApiConnector(cfg).fetch({"name": "endpoint_tidak_ada", "path": "/x"})


def test_sample_dir_defaults_to_per_source_subfolder():
    """Tanpa sample_dir, fixture dibaca dari data/sample/<sumber>/ agar tiap perusahaan punya folder sendiri."""
    c = RestApiConnector({"mode": "sample", "source": "perusahaan_x"})
    assert c.sample_dir == PROJECT_ROOT / "data" / "sample" / "perusahaan_x"


def test_invalid_mode_rejected():
    with pytest.raises(ValueError):
        RestApiConnector({"mode": "ngawur"})


def test_source_definition_is_complete():
    cfg = load_source("angkasabiruretail")
    names = [e["name"] for e in cfg["endpoints"]]
    assert len(names) == 39
    assert len(set(names)) == 39
    assert len({table_name(n) for n in names}) == 39
    assert all(e["path"].startswith("/") for e in cfg["endpoints"])
    # duplikat bergaya underscore memang 404 di API asli; harus opsional agar tidak menggagalkan run
    optional = {e["name"] for e in cfg["endpoints"] if e.get("optional")}
    assert {"employee_contracts", "employee_addresses"} <= optional


# ---------------------------------------------------------- integrasi (DWH + MinIO)
@pytest.mark.integration
def test_every_endpoint_loaded_with_all_sample_rows(dwh):
    cfg = load_source("angkasabiruretail")
    if cfg["mode"] != "sample":
        pytest.skip("perbandingan jumlah baris hanya berlaku pada mode sample")
    sample_dir = PROJECT_ROOT / cfg["sample_dir"]
    for ep in cfg["endpoints"]:
        with open(sample_dir / f"{ep['name']}.json", encoding="utf-8") as fp:
            expected = len(_unwrap(json.load(fp)))
        got = scalar(
            dwh,
            f"""select count(*) from raw_angkasabiruretail.{table_name(ep['name'])} r
                join (select batch_id from raw_angkasabiruretail._ingestion_log
                      where endpoint = %s and status = 'success' order by extracted_at desc limit 1) l
                  on l.batch_id = r.batch_id""",
            (ep["name"],),
        )
        assert got == expected, ep["name"]


@pytest.mark.integration
def test_ingestion_log_has_no_failed_latest_batch(dwh):
    rows = query(
        dwh,
        """select endpoint, status from (
             select distinct on (endpoint) endpoint, status from raw_angkasabiruretail._ingestion_log
             order by endpoint, extracted_at desc) x where status <> 'success'""",
    )
    assert rows == []


@pytest.mark.integration
def test_raw_archive_exists_in_minio():
    from ingestion.storage import MinioArchive

    cfg = load_source("angkasabiruretail")
    archive = MinioArchive(cfg["raw"]["minio_bucket"])
    names = [o.object_name for o in archive.client.list_objects(archive.bucket, prefix="raw/angkasabiruretail/employees/", recursive=True)]
    assert names, "arsip raw endpoint employees tidak ada di MinIO"
    body = archive.client.get_object(archive.bucket, names[-1]).read()
    assert len(json.loads(body)) > 0


# ------------------------------------------- run(): optional, resume, isolasi kegagalan
class _StubConnector:
    """fetch() per endpoint: nilai list = sukses, Exception = gagal. `calls` mencatat endpoint yang diminta."""

    def __init__(self, behaviour):
        self.behaviour, self.calls = behaviour, []

    def fetch(self, ep):
        self.calls.append(ep["name"])
        result = self.behaviour[ep["name"]]
        if isinstance(result, Exception):
            raise result
        return result


@pytest.fixture
def isolated_run(monkeypatch, dwh):
    """Jalankan run() dengan sumber kecil di schema dan bucket uji, lalu bersihkan."""
    from ingestion import run_ingest
    from ingestion.storage import MinioArchive

    cfg = {
        "type": "rest_api", "mode": "sample",
        "raw": {"schema": "raw_test_ingest", "minio_bucket": "test-ingest", "keep_batches": 3},
        "endpoints": [
            {"name": "ok-endpoint", "path": "/ok"},
            {"name": "dead-optional", "path": "/dead", "optional": True},
            {"name": "dead-required", "path": "/gone"},
            {"name": "flaky", "path": "/flaky"},
        ],
    }
    monkeypatch.setattr(run_ingest, "load_source", lambda name: cfg)
    stub_holder = {}

    def use(behaviour):
        stub_holder["c"] = _StubConnector(behaviour)
        monkeypatch.setattr(run_ingest, "get_connector", lambda c: stub_holder["c"])
        return stub_holder["c"]

    yield run_ingest, use
    with dwh.cursor() as cur:
        cur.execute("drop schema if exists raw_test_ingest cascade")
        cur.execute("drop schema if exists raw_table_test_ingest cascade")  # jejak flatten, bila ada
    archive = MinioArchive("test-ingest")
    if archive.client.bucket_exists("test-ingest"):
        for o in archive.client.list_objects("test-ingest", recursive=True):
            archive.client.remove_object("test-ingest", o.object_name)
        archive.client.remove_bucket("test-ingest")


@pytest.mark.integration
def test_run_handles_optional_404_failures_and_resume(isolated_run, dwh):
    run_ingest, use = isolated_run
    boom = ExtractError("GET /flaky gagal: 522")
    stub = use({"ok-endpoint": [{"a": 1}, {"a": 2}], "dead-optional": EndpointNotFound("404"),
                "dead-required": EndpointNotFound("404"), "flaky": boom})

    first = run_ingest.run("t", "2026-01-01")
    # satu endpoint gagal tidak menghentikan yang lain; 404 opsional bukan kegagalan
    assert first["loaded"] == {"ok-endpoint": 2, "dead-optional": 0}
    assert set(first["failed"]) == {"dead-required", "flaky"}
    assert scalar(dwh, "select count(*) from raw_test_ingest.ok__endpoint") == 2
    assert scalar(dwh, "select count(*) from raw_test_ingest.dead__optional") == 0   # tabel ada, kosong
    assert scalar(dwh, "select status from raw_test_ingest._ingestion_log where endpoint = 'dead-optional'") == "success"
    assert scalar(dwh, "select status from raw_test_ingest._ingestion_log where endpoint = 'flaky'") == "failed"

    # percobaan ulang (resume): hanya endpoint yang belum sukses yang diminta ulang
    stub.behaviour["flaky"] = [{"b": 1}]
    stub.calls.clear()
    second = run_ingest.run("t", "2026-01-01", resume=True)  # run_key bawaan sama: mode:ds
    assert sorted(stub.calls) == ["dead-required", "flaky"]
    assert second["loaded"] == {"flaky": 1} and set(second["failed"]) == {"dead-required"}
    assert sorted(second["skipped"]) == ["dead-optional", "ok-endpoint"]

    # tanpa resume, semua diminta lagi
    stub.calls.clear()
    run_ingest.run("t", "2026-01-01")
    assert len(stub.calls) == 4


@pytest.mark.integration
def test_resume_is_bound_to_the_run_not_just_the_date(isolated_run):
    run_ingest, use = isolated_run
    stub = use({"ok-endpoint": [{"a": 1}], "dead-optional": EndpointNotFound("404"),
                "dead-required": [{"x": 1}], "flaky": [{"y": 1}]})
    run_ingest.run("t", "2026-01-01", run_key="airflow-run-A")
    stub.calls.clear()
    # run lain pada tanggal yang sama (mis. mode atau run_id berbeda) tidak boleh dianggap sudah selesai
    run_ingest.run("t", "2026-01-01", resume=True, run_key="airflow-run-B")
    assert len(stub.calls) == 4
    stub.calls.clear()
    run_ingest.run("t", "2026-01-02", resume=True, run_key="airflow-run-A")
    assert len(stub.calls) == 0, "run_key yang sama = percobaan ulang dari run itu"


@pytest.mark.integration
def test_resume_menarik_ulang_endpoint_yang_status_terakhirnya_gagal(isolated_run):
    """Run yang diulang: endpoint yang pernah sukses lalu gagal pada percobaan terbaru belum selesai.
    Dulu ia dilewati karena sukses lamanya, sehingga task dilaporkan sukses padahal datanya tidak tertarik."""
    run_ingest, use = isolated_run
    stub = use({"ok-endpoint": [{"a": 1}], "dead-optional": EndpointNotFound("404"),
                "dead-required": [{"x": 1}], "flaky": [{"y": 1}]})
    run_ingest.run("t", "2026-01-01", run_key="run-A")
    stub.behaviour["flaky"] = ExtractError("GET /flaky gagal: 522")
    assert set(run_ingest.run("t", "2026-01-01", run_key="run-A")["failed"]) == {"flaky"}

    time.sleep(1.1)  # extracted_at beresolusi detik; percobaan sungguhan berselang beberapa menit
    stub.behaviour["flaky"] = [{"y": 2}]
    stub.calls.clear()
    ulang = run_ingest.run("t", "2026-01-01", resume=True, run_key="run-A")
    assert stub.calls == ["flaky"]
    assert ulang["loaded"] == {"flaky": 1} and not ulang["failed"]

    stub.calls.clear()
    run_ingest.run("t", "2026-01-01", resume=True, run_key="run-A")
    assert stub.calls == [], "setelah sukses lagi, endpoint itu selesai"


@pytest.mark.integration
def test_fase_extract_dan_load_terpisah_lewat_minio(isolated_run, dwh):
    """raw_ dimuat dari arsip MinIO, bukan dari API: fase extract hanya menulis arsip,
    dan fase load tidak boleh memanggil API sama sekali."""
    run_ingest, use = isolated_run
    use({"ok-endpoint": [{"a": 1}, {"a": 2}], "dead-optional": EndpointNotFound("404"),
         "dead-required": [{"x": 1}], "flaky": [{"y": 1}]})

    hasil = run_ingest.run("t", "2026-01-01", run_key="run-F", phase="extract")
    assert set(hasil["extracted"]) == {"ok-endpoint", "dead-optional", "dead-required", "flaky"}
    assert not hasil["loaded"] and not hasil["failed"]
    # belum ada yang menyentuh tabel raw; statusnya 'extracted'
    assert scalar(dwh, """select count(*) from information_schema.tables
                          where table_schema = 'raw_test_ingest' and table_name = 'ok__endpoint'""") == 0
    assert scalar(dwh, "select status from raw_test_ingest._ingestion_log where endpoint = 'ok-endpoint'") == "extracted"

    # fase load: konektor yang meledak membuktikan API tidak pernah disentuh
    stub = use({n: ExtractError("fase load tidak boleh menyentuh API") for n in
                ("ok-endpoint", "dead-optional", "dead-required", "flaky")})
    hasil = run_ingest.run("t", "2026-01-01", run_key="run-F", phase="load")
    assert stub.calls == []
    assert hasil["loaded"] == {"ok-endpoint": 2, "dead-optional": 0, "dead-required": 1, "flaky": 1}
    assert not hasil["failed"]
    assert scalar(dwh, "select count(*) from raw_test_ingest.ok__endpoint") == 2
    assert scalar(dwh, """select count(*) from raw_test_ingest._ingestion_log
                          where run_key = 'run-F' and status <> 'success'""") == 0
    # catatan endpoint opsional (404 -> diarsipkan kosong) ikut terbawa sampai status success
    assert "opsional" in scalar(dwh, "select error from raw_test_ingest._ingestion_log where endpoint = 'dead-optional'")
    # fase load yang diulang tidak memuat ulang yang sudah success
    hasil = run_ingest.run("t", "2026-01-01", run_key="run-F", phase="load")
    assert not hasil["loaded"] and sorted(hasil["skipped"]) == ["dead-optional", "dead-required", "flaky", "ok-endpoint"]
    assert scalar(dwh, "select count(*) from raw_test_ingest.ok__endpoint") == 2


@pytest.mark.integration
def test_berkas_referensi_bisa_disaring_baris_dan_kolom(dwh, tmp_path):
    """Master data berisi banyak perusahaan dan data pribadi: hanya baris dan kolom yang diminta yang boleh masuk."""
    import psycopg2

    from ingestion.config import pg_params
    from ingestion.load_reference import load_file

    berkas = tmp_path / "master.csv"
    berkas.write_text("Kode Perusahaan,NIK,Nama,Top Talent\nAB,1,SATU,Ya\nABR,2,DUA,Tidak\nAB,3,TIGA,\n", encoding="utf-8")
    conn = psycopg2.connect(**pg_params("DWH"))
    try:
        n = load_file(conn, "uji_saring", "m", berkas, saring={"Kode Perusahaan": "AB"}, kolom=["NIK", "Top Talent"])
        assert n == 2
        assert query(dwh, "select nik, top_talent from reference_uji_saring.m order by nik") == [("1", "Ya"), ("3", None)]
        kolom = {r[0] for r in query(dwh, "select column_name from information_schema.columns where table_schema = 'reference_uji_saring'")}
        assert "nama" not in kolom and "kode_perusahaan" not in kolom
        # saringan tanpa hasil harus berhenti, bukan mengosongkan tabel
        with pytest.raises(ValueError):
            load_file(conn, "uji_saring", "m", berkas, saring={"Kode Perusahaan": "TIDAK-ADA"})
        with pytest.raises(ValueError):
            load_file(conn, "uji_saring", "m", berkas, kolom=["Kolom Hilang"])
        assert scalar(dwh, "select count(*) from reference_uji_saring.m") == 2
    finally:
        conn.close()
        with dwh.cursor() as cur:
            cur.execute("drop schema if exists reference_uji_saring cascade")


# ---------------------------------------------------------------- Angkasa Biru: bearer login + paginasi
def test_unwrap_handles_double_nested_and_empty_dict():
    nested = {"data": {"data": [{"a": 1}], "pagination": {"page": 1}}, "status": "success"}
    assert _unwrap(nested) == [{"a": 1}]
    assert _unwrap({}) == []          # getDivision membalas {} = tidak ada data, bukan satu baris kosong


def _bearer_connector(monkeypatch, get_responses, login_responses=None, retries=1):
    calls = {"gets": [], "logins": 0}

    def fake_get(url, headers=None, params=None, timeout=None):
        item = get_responses[min(len(calls["gets"]), len(get_responses) - 1)]
        calls["gets"].append((url, dict(params or {}), dict(headers or {})))
        if isinstance(item, Exception):
            raise item
        return item

    def fake_post(url, json=None, timeout=None):
        calls["logins"] += 1
        seq = login_responses or [_Resp(200, {"data": {"token": f"tok{calls['logins']}"}, "status": "success"})]
        return seq[min(calls["logins"] - 1, len(seq) - 1)]

    monkeypatch.setattr("ingestion.connectors.requests.get", fake_get)
    monkeypatch.setattr("ingestion.connectors.requests.post", fake_post)
    monkeypatch.setattr("ingestion.connectors.time.sleep", lambda s: None)
    cfg = {"mode": "live", "api": {
        "base_url": "http://x", "retries": retries, "retry_backoff_seconds": 0,
        "auth": {"type": "bearer_login", "login_path": "/login", "username": "u", "password": "p"},
        "pagination": {"page_param": "page", "limit_param": "limit", "limit": 2},
    }}
    return RestApiConnector(cfg), calls


def test_bearer_login_once_and_pagination_stops_on_short_page(monkeypatch):
    conn, calls = _bearer_connector(monkeypatch, [
        _Resp(200, {"data": [{"a": 1}, {"a": 2}]}),   # page 1 penuh (limit 2)
        _Resp(200, {"data": [{"a": 3}]}),             # page 2 pendek -> berhenti
    ])
    rows = conn.fetch(EP)
    assert rows == [{"a": 1}, {"a": 2}, {"a": 3}]
    assert calls["logins"] == 1                        # token di-cache, tidak login per halaman
    assert [c[1]["page"] for c in calls["gets"]] == [1, 2]
    assert all(c[2]["Authorization"] == "Bearer tok1" for c in calls["gets"])


def test_bearer_401_triggers_relogin_then_succeeds(monkeypatch):
    conn, calls = _bearer_connector(monkeypatch, [
        _Resp(401, {"message": "Unauthorized"}),       # token kedaluwarsa
        _Resp(200, {"data": [{"a": 1}]}),
    ])
    assert conn.fetch(EP) == [{"a": 1}]
    assert calls["logins"] == 2                        # login ulang setelah 401
    assert calls["gets"][-1][2]["Authorization"] == "Bearer tok2"


def test_bearer_login_failure_is_extract_error(monkeypatch):
    conn, _ = _bearer_connector(monkeypatch, [], login_responses=[_Resp(500, {})])
    with pytest.raises(ExtractError):
        conn.fetch(EP)


def test_bearer_empty_credentials_fail_loudly():
    cfg = {"mode": "live", "api": {"base_url": "http://x",
           "auth": {"type": "bearer_login", "username": "", "password": ""}}}
    with pytest.raises(ExtractError):
        RestApiConnector(cfg).fetch(EP)


def test_angkasabiru_source_definition_is_consistent():
    from ingestion.config import load_source
    cfg = load_source("angkasabiru")
    assert cfg["raw"]["schema"] == "raw_angkasabiru"
    assert cfg["raw"]["minio_bucket"].endswith("angkasabiru-raw")
    assert cfg["api"]["auth"]["type"] == "bearer_login"
    assert cfg["api"]["pagination"]["limit"] > 0
    names = [e["name"] for e in cfg["endpoints"]]
    assert len(names) == len(set(names)) == 29

    cfg = load_source("abdestination")
    assert cfg["raw"]["schema"] == "raw_abdestination"
    assert cfg["api"]["auth"]["type"] == "bearer_token"
    assert cfg["api"]["pagination"]["limit_param"] == "per_page"
    names = [e["name"] for e in cfg["endpoints"]]
    assert len(names) == len(set(names)) == 29

    cfg = load_source("lms")
    assert cfg["raw"]["schema"] == "raw_lms"
    assert cfg["api"]["default_auth_header"] == "x-api-key"
    assert [e["name"] for e in cfg["endpoints"]] == ["learning_agility_assessments"]

    cfg = load_source("tms")
    assert cfg["raw"]["schema"] == "raw_tms"
    assert cfg["api"]["default_auth_header"] == "x-api-key"
    assert [(e["name"], e["path"]) for e in cfg["endpoints"]] == [("career_aspirations", "/aspirations")]


# ===================== Kemampuan konektor untuk API bergaya SF6 =====================
# API seperti ini membedakan endpoint lewat query parameter ?sfid=..., bukan lewat path, dan setiap
# endpoint memakai api_key sendiri. Kemampuan itu generik, jadi tetap diuji tanpa sumber yang aktif.

def test_static_query_params_are_sent(monkeypatch):
    """endpoint['query'] harus ikut terkirim; tanpa ini seluruh endpoint menunjuk sfid yang sama."""
    seen = {}

    def fake_get(url, headers=None, params=None, timeout=None):
        seen["url"], seen["params"], seen["headers"] = url, params, headers
        return _Resp(200, [{"id": 1}])

    monkeypatch.setattr("ingestion.connectors.requests.get", fake_get)
    cfg = {"mode": "live", "api": {"base_url": "https://hris.example/sf6", "api_key": "sumber"}}
    rows = RestApiConnector(cfg).fetch(
        {"name": "company", "path": "/index.cfm", "query": {"sfid": "sys.sec.api.tCompany"}}
    )
    assert rows == [{"id": 1}]
    assert seen["url"] == "https://hris.example/sf6/index.cfm"
    assert seen["params"] == {"sfid": "sys.sec.api.tCompany"}


def test_per_endpoint_api_key_overrides_source_level_key(monkeypatch):
    seen = {}

    def fake_get(url, headers=None, params=None, timeout=None):
        seen["headers"] = headers
        return _Resp(200, [])

    monkeypatch.setattr("ingestion.connectors.requests.get", fake_get)
    cfg = {"mode": "live", "api": {"base_url": "http://x", "api_key": "kunci-sumber"}}
    conn = RestApiConnector(cfg)

    conn.fetch({"name": "a", "path": "/p", "api_key": "kunci-endpoint"})
    assert seen["headers"]["api_key"] == "kunci-endpoint"

    conn.fetch({"name": "b", "path": "/p"})
    assert seen["headers"]["api_key"] == "kunci-sumber"


def test_result_envelope_is_unwrapped():
    """API SF6 membungkus baris di kunci 'result' bersama metadata paginasi.
    Tanpa dukungan ini seluruh amplop terbaca sebagai SATU baris."""
    from ingestion.connectors import _unwrap

    body = {"page": 1.0, "result": [{"id": 1}, {"id": 2}, {"id": 3}],
            "start_row": 1, "end_row": "1000", "total_data": 3, "error_code": "000"}
    assert _unwrap(body) == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert _unwrap({"result": [], "status": "Success", "total_data": 0}) == []
    # amplop 'data' milik Angkasa Biru Retail / Angkasa Biru tetap jalan
    assert _unwrap({"data": {"data": [{"id": 1}], "pagination": {}}}) == [{"id": 1}]
    # objek tunggal tanpa amplop tetap satu baris
    assert _unwrap({"id": 1}) == [{"id": 1}]


def test_pagination_can_be_sent_as_header(monkeypatch):
    """SF6 mengabaikan ?page= dan hanya menerima header 'page'; tanpa ini hanya halaman 1 tertarik."""
    seen = []

    def fake_get(url, headers=None, params=None, timeout=None):
        seen.append({"page_header": headers.get("page"), "params": dict(params or {})})
        page = int(headers["page"])
        rows = [{"i": page * 10 + n} for n in range(2 if page < 3 else 1)]
        return _Resp(200, {"result": rows, "total_data": 5})

    monkeypatch.setattr("ingestion.connectors.requests.get", fake_get)
    cfg = {"mode": "live", "api": {
        "base_url": "https://hris.example/sf6", "api_key": "k",
        "pagination": {"in": "header", "page_param": "page", "limit_param": None, "limit": 2, "max_pages": 10},
    }}
    rows = RestApiConnector(cfg).fetch(
        {"name": "x", "path": "/index.cfm", "query": {"sfid": "sys.sec.api.tEmpohis"}}
    )
    assert len(rows) == 5                                   # 2 + 2 + 1, berhenti di halaman pendek
    assert [c["page_header"] for c in seen] == ["1", "2", "3"]
    # nomor halaman TIDAK boleh ikut sebagai query param, dan sfid tetap terkirim
    assert all(c["params"] == {"sfid": "sys.sec.api.tEmpohis"} for c in seen)


def test_pagination_in_query_is_still_the_default(monkeypatch):
    seen = []

    def fake_get(url, headers=None, params=None, timeout=None):
        seen.append(dict(params or {}))
        return _Resp(200, {"data": []})

    monkeypatch.setattr("ingestion.connectors.requests.get", fake_get)
    cfg = {"mode": "live", "api": {"base_url": "http://x", "api_key": "k",
                                   "pagination": {"limit": 50, "max_pages": 3}}}
    RestApiConnector(cfg).fetch({"name": "x", "path": "/p"})
    assert seen[0] == {"page": 1, "limit": 50}


def test_invalid_pagination_location_is_rejected(monkeypatch):
    cfg = {"mode": "live", "api": {"base_url": "http://x", "api_key": "k",
                                   "pagination": {"in": "body", "limit": 10}}}
    with pytest.raises(ValueError):
        RestApiConnector(cfg).fetch({"name": "x", "path": "/p"})


def test_endpoint_without_any_api_key_fails_in_live_mode():
    cfg = {"mode": "live", "api": {"base_url": "http://x"}}
    with pytest.raises(ExtractError) as exc:
        RestApiConnector(cfg).fetch({"name": "company", "path": "/index.cfm", "api_key": ""})
    assert "company" in str(exc.value)


# ============ Sumber berkas CSV (konektor generik) ============

def test_csv_file_connector_reads_rows(tmp_path):
    from ingestion.connectors import CsvFileConnector

    f = tmp_path / "nominatif.csv"
    f.write_text("NIK baru,Employee Name,Person Grade\n"
                 "20240001, BUDI ,14\n"
                 "20240002,SITI,16\n"
                 ",,\n", encoding="utf-8")
    rows = CsvFileConnector({"base_dir": str(tmp_path)}).fetch({"name": "nominatif", "path": "nominatif.csv"})
    assert len(rows) == 2, "baris kosong tidak ikut dimuat"
    assert rows[0] == {"NIK baru": "20240001", "Employee Name": "BUDI", "Person Grade": "14"}


def test_csv_file_connector_fails_loudly_when_file_missing(tmp_path):
    from ingestion.connectors import CsvFileConnector

    conn = CsvFileConnector({"base_dir": str(tmp_path)})
    with pytest.raises(ExtractError):
        conn.fetch({"name": "x", "path": "tidak-ada.csv"})
    # endpoint opsional tetap dimuat kosong, bukan gagal
    assert conn.fetch({"name": "x", "path": "tidak-ada.csv", "optional": True}) == []


def test_unknown_source_type_is_rejected():
    from ingestion.connectors import get_connector

    with pytest.raises(ValueError):
        get_connector({"type": "sftp"})
