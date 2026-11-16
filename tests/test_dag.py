"""Struktur DAG Airflow (tanpa menjalankannya)."""
import os

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def dagbag():
    airflow = pytest.importorskip("airflow")
    from airflow.models import DagBag

    folder = os.path.join(os.environ.get("PROJECT_ROOT", "."), "airflow", "dags")
    return DagBag(dag_folder=folder, include_examples=False)


def test_dags_import_without_errors(dagbag):
    assert dagbag.import_errors == {}


def test_one_dag_per_source_with_expected_chain(dagbag):
    from ingestion.config import list_sources, load_source

    for source in list_sources():
        dag = dagbag.dags.get(f"pipeline_{source}")
        assert dag is not None
        # transform_silver dan build_gold hanya ada untuk sumber yang pemetaan transformasinya sudah disusun (blok dbt di YAML)
        expected = ["check_connections", "extract_api", "load_raw", "flatten_raw_tables"]
        if (load_source(source).get("dbt") or {}).get("select"):
            expected += ["transform_silver", "build_gold"]
        assert [t.task_id for t in dag.topological_sort()] == expected
        assert dag.catchup is False
        assert dag.max_active_runs == 1


def test_extract_task_retries_enough_for_flaky_api(dagbag):
    dag = dagbag.dags["pipeline_angkasabiruretail"]
    assert dag.default_args["retries"] >= 3


def _load_dag_module():
    import importlib.util

    path = os.path.join(os.environ.get("PROJECT_ROOT", "."), "airflow", "dags", "source_pipelines.py")
    spec = importlib.util.spec_from_file_location("source_pipelines_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _TI:
    def __init__(self, try_number):
        self.try_number = try_number


def test_extract_partial_failure_is_retryable_not_fail_fast(monkeypatch):
    """AirflowFailException melewati retry; kegagalan parsial harus AirflowException biasa."""
    from airflow.exceptions import AirflowException, AirflowFailException

    module = _load_dag_module()
    monkeypatch.setattr("ingestion.run_ingest.run",
                        lambda *a, **k: {"extracted": {"a": 1}, "loaded": {}, "failed": {"b": "522"}})
    with pytest.raises(AirflowException) as err:
        module.task_extract("angkasabiruretail", "2026-11-03", run_id="r1", ti=_TI(1))
    assert not isinstance(err.value, AirflowFailException)


def test_extract_resumes_only_on_retry_and_passes_run_id(monkeypatch):
    module = _load_dag_module()
    seen = []

    def fake_run(source, ds, resume=False, run_key=None, phase="all", **_):
        seen.append((resume, run_key, phase))
        return {"extracted": {"a": 1}, "loaded": {}, "failed": {}}

    monkeypatch.setattr("ingestion.run_ingest.run", fake_run)
    module.task_extract("angkasabiruretail", "2026-11-03", run_id="run-X", ti=_TI(1))
    module.task_extract("angkasabiruretail", "2026-11-03", run_id="run-X", ti=_TI(2))
    assert seen == [(False, "run-X", "extract"), (True, "run-X", "extract")]


def test_load_raw_memakai_fase_load_dan_run_id(monkeypatch):
    """load_raw hanya memuat arsip run yang sama dari MinIO; tidak ada jalur yang menyentuh API."""
    module = _load_dag_module()
    seen = []

    def fake_run(source, ds=None, only=None, resume=False, run_key=None, phase="all"):
        seen.append((phase, run_key))
        return {"extracted": {}, "loaded": {"a": 1}, "failed": {}}

    monkeypatch.setattr("ingestion.run_ingest.run", fake_run)
    module.task_load("angkasabiruretail", "2026-11-03", run_id="run-X")
    assert seen == [("load", "run-X")]


def test_dag_terbentuk_tepat_dari_sumber_aktif(dagbag):
    """Satu DAG per sources/*.yaml. ITDC ditangguhkan, jadi pipeline_itdc tidak boleh muncul."""
    from ingestion.config import list_sources

    assert set(dagbag.dags) == {f"pipeline_{s}" for s in list_sources()}
    assert "pipeline_itdc" not in dagbag.dags
