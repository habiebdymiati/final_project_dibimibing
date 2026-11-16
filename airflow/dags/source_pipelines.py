"""
DAG per sumber, dibangkitkan otomatis dari sources/*.yaml.
Menambah sumber baru = menambah file YAML; DAG-nya ikut terbentuk.

  check_connections -> extract_api -> load_raw -> flatten_raw_tables [-> transform_silver -> build_gold]

  check_connections   : MinIO, Postgres DWH, dan Postgres Data Hub terjangkau
  extract_api         : endpoint API -> arsip JSON di MinIO (satu file per endpoint per batch); belum menyentuh Postgres
  load_raw            : arsip batch run ini di MinIO -> payload JSONB di raw_<sumber>. Yang masuk Postgres selalu
                        persis isi arsip, dan percobaan ulangnya membaca MinIO saja, tidak menyentuh API
  flatten_raw_tables  : payload JSONB -> tabel kolom-baris di raw_table_<sumber> (truncate + insert)
  transform_silver    : muat berkas referensi sumber, lalu dbt: raw_table_<sumber> -> staging -> silver. Hanya ada untuk sumber yang pemetaan
                        transformasinya sudah disusun (blok `dbt:` di sources/<sumber>.yaml).
  build_gold          : silver semua sumber -> star schema gold di Data Hub. Gold memuat semua perusahaan, jadi dua pipeline
                        yang selesai bersamaan dijalankan bergantian (flock).
"""
import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

PROJECT_ROOT = os.environ.get("PROJECT_ROOT", "/opt/airflow/project")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ingestion.config import list_sources, load_source, pg_params  # noqa: E402


def task_check_connections(source: str, **_):
    """Cek koneksi infrastruktur sebelum pipeline berjalan. Gagal = task gagal (bisa diulang)."""
    import psycopg2

    from ingestion.storage import MinioArchive

    cfg = load_source(source)
    hasil = {}

    # MinIO: terjangkau dan bucket arsip sumber ini siap (dibuat bila belum ada)
    bucket = cfg["raw"]["minio_bucket"]
    MinioArchive(bucket).ensure_bucket()
    hasil["minio"] = f"bucket {bucket} siap"

    # Postgres DWH dan Data Hub: cukup terjangkau dan bisa menjalankan query
    for nama, prefix in (("dwh", "DWH"), ("datahub", "DATAHUB")):
        with psycopg2.connect(**pg_params(prefix)) as conn, conn.cursor() as cur:
            cur.execute("select current_database(), version()")
            db, versi = cur.fetchone()
            hasil[nama] = f"{db} terjangkau ({versi.split(',')[0]})"
    return hasil


def task_extract(source: str, ds: str, run_id: str = None, ti=None, **_):
    """
    Fase extract: endpoint API -> arsip JSON di MinIO. Percobaan pertama menarik semua endpoint;
    percobaan ulang hanya endpoint yang belum terarsip pada run Airflow yang sama. Kegagalan parsial
    memakai AirflowException (bisa diulang), bukan AirflowFailException (yang melewati retry).
    """
    from ingestion.run_ingest import run

    stats = run(source, ds, resume=bool(ti and ti.try_number > 1), run_key=run_id, phase="extract")
    if stats["failed"]:
        raise AirflowException(f"Endpoint gagal diekstrak: {sorted(stats['failed'])}")
    return {"extracted": len(stats["extracted"]), "rows": sum(stats["extracted"].values())}


def task_load(source: str, ds: str, run_id: str = None, **_):
    """
    Fase load: arsip batch run ini di MinIO -> raw_<sumber> (JSONB). Tidak menyentuh API sama sekali;
    endpoint yang sudah berstatus success dilewati, jadi percobaan ulang hanya memuat yang tersisa.
    """
    from ingestion.run_ingest import run

    stats = run(source, ds, run_key=run_id, phase="load")
    if stats["failed"]:
        raise AirflowException(f"Arsip gagal dimuat ke raw: {sorted(stats['failed'])}")
    return {"loaded": len(stats["loaded"]), "rows": sum(stats["loaded"].values())}


def task_flatten(source: str, **_):
    """Isi ulang raw_table_<sumber> (payload JSONB didatarkan: kunci -> kolom) dengan TRUNCATE + INSERT
    dari batch sukses terakhir, sehingga hanya nilai terbaru yang tersimpan."""
    from ingestion.flatten import run

    return {"rows_flattened": run(source)}


def build_dag(source: str) -> DAG:
    cfg = load_source(source)

    with DAG(
        dag_id=f"pipeline_{source}",
        description=f"{source}: API -> MinIO -> raw_{source} (JSONB) -> raw_table_{source}" + (" -> silver -> gold" if cfg.get("dbt") else ""),
        schedule=cfg.get("schedule", "@daily"),
        start_date=datetime(2026, 1, 1),
        catchup=False,
        max_active_runs=1,
        default_args={"retries": 3, "retry_delay": timedelta(minutes=5)},
        tags=["ingestion", source] + (["silver"] if cfg.get("dbt") else []),
    ) as dag:
        check = PythonOperator(
            task_id="check_connections",
            python_callable=task_check_connections,
            op_kwargs={"source": source},
        )
        extract = PythonOperator(
            task_id="extract_api",
            python_callable=task_extract,
            op_kwargs={"source": source, "ds": "{{ ds }}"},
        )
        load = PythonOperator(
            task_id="load_raw",
            python_callable=task_load,
            op_kwargs={"source": source, "ds": "{{ ds }}"},
        )
        flatten = PythonOperator(
            task_id="flatten_raw_tables",
            python_callable=task_flatten,
            op_kwargs={"source": source},
        )

        check >> extract >> load >> flatten

        # Transformasi silver hanya untuk sumber yang pemetaannya sudah ada (blok `dbt:` di YAML sumber).
        dbt_select = (cfg.get("dbt") or {}).get("select")
        if dbt_select:
            transform = BashOperator(
                task_id="transform_silver",
                # berkas referensi (mis. TMT karyawan untuk id_employee) dimuat dulu, lalu dbt
                bash_command=(f"cd {PROJECT_ROOT} && python -m ingestion.load_reference --source {source} "
                              f"&& dbt build --target dwh --select '{dbt_select}'"),
            )
            gold = BashOperator(
                task_id="build_gold",
                bash_command=(f"cd {PROJECT_ROOT} && flock -w 1800 /tmp/angkasabiru_gold.lock sh -c "
                              "'python -m ingestion.fdw_silver && dbt build --target datahub'"),
            )
            flatten >> transform >> gold
    return dag


for _source in list_sources():
    globals()[f"pipeline_{_source}"] = build_dag(_source)
