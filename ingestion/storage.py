"""Penyimpanan: arsip raw di MinIO dan tabel raw di Postgres DWH."""
import io
import json
import os
import time
from typing import Any, Dict, List

import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json, execute_values

from .config import pg_params


# --------------------------------------------------------------------------- MinIO
class MinioArchive:
    def __init__(self, bucket: str):
        from minio import Minio

        self.bucket = bucket
        self.client = Minio(
            os.environ["MINIO_ENDPOINT"],
            access_key=os.environ["MINIO_ACCESS_KEY"],
            secret_key=os.environ["MINIO_SECRET_KEY"],
            secure=False,
        )

    def ensure_bucket(self, retries: int = 30, delay: float = 2.0):
        last = None
        for _ in range(retries):
            try:
                if not self.client.bucket_exists(self.bucket):
                    self.client.make_bucket(self.bucket)
                return
            except Exception as exc:  # MinIO bisa belum siap saat container baru naik
                last = exc
                time.sleep(delay)
        raise RuntimeError(f"MinIO tidak dapat dijangkau: {last}")

    def put_json(self, object_name: str, records: List[Dict[str, Any]]) -> str:
        body = json.dumps(records, ensure_ascii=False).encode("utf-8")
        self.client.put_object(self.bucket, object_name, io.BytesIO(body), len(body), content_type="application/json")
        return f"s3://{self.bucket}/{object_name}"

    def get_json(self, object_name: str) -> List[Dict[str, Any]]:
        """Baca kembali satu arsip batch; sumber data fase load. Menerima jalur objek
        maupun bentuk s3://<bucket>/<objek> seperti yang tercatat di _ingestion_log."""
        prefix = f"s3://{self.bucket}/"
        if object_name.startswith(prefix):
            object_name = object_name[len(prefix):]
        resp = self.client.get_object(self.bucket, object_name)
        try:
            return json.loads(resp.read().decode("utf-8"))
        finally:
            resp.close()
            resp.release_conn()


# ---------------------------------------------------------------------- Postgres raw
def table_name(endpoint: str) -> str:
    return endpoint.replace("-", "__")


class RawLoader:
    def __init__(self, schema: str):
        self.schema = schema
        self.conn = psycopg2.connect(**pg_params("DWH"))
        self.conn.autocommit = False

    def close(self):
        self.conn.close()

    def ensure_log(self):
        with self.conn, self.conn.cursor() as cur:
            cur.execute(sql.SQL("create schema if not exists {}").format(sql.Identifier(self.schema)))
            cur.execute(
                sql.SQL(
                    """create table if not exists {}._ingestion_log (
                        batch_id text not null, source text not null, endpoint text not null,
                        ds date not null, extracted_at timestamptz not null, status text not null,
                        row_count integer, error text, archive_path text,
                        primary key (batch_id, endpoint))"""
                ).format(sql.Identifier(self.schema))
            )
            # run_key mengikat percobaan ulang ke satu run (Airflow run_id, atau mode:ds untuk CLI)
            cur.execute(sql.SQL("alter table {}._ingestion_log add column if not exists run_key text").format(sql.Identifier(self.schema)))

    def load(self, endpoint: str, batch_id: str, ds: str, extracted_at: str, rows: List[Dict[str, Any]]):
        """rows: [(row_hash, payload)]. Satu transaksi per endpoint. Baris batch yang sama dihapus dulu,
        supaya muat ulang dari arsip (mis. setelah load_failed di tengah) tidak menggandakan baris."""
        tbl = sql.Identifier(self.schema, table_name(endpoint))
        with self.conn, self.conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    """create table if not exists {} (
                        batch_id text not null, ds date not null, extracted_at timestamptz not null,
                        source_endpoint text not null, row_hash text not null, payload jsonb not null)"""
                ).format(tbl)
            )
            cur.execute(
                sql.SQL("create index if not exists {} on {} (batch_id)").format(
                    sql.Identifier(f"ix_{table_name(endpoint)}_batch"), tbl
                )
            )
            cur.execute(sql.SQL("delete from {} where batch_id = %s").format(tbl), (batch_id,))
            if rows:
                execute_values(
                    cur,
                    sql.SQL("insert into {} (batch_id, ds, extracted_at, source_endpoint, row_hash, payload) values %s")
                    .format(tbl)
                    .as_string(cur),
                    [(batch_id, ds, extracted_at, endpoint, h, Json(p)) for h, p in rows],
                    page_size=1000,
                )

    def log(self, source: str, endpoint: str, batch_id: str, ds: str, extracted_at: str,
            status: str, row_count: int = 0, error: str = None, archive_path: str = None, run_key: str = None):
        with self.conn, self.conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    """insert into {}._ingestion_log
                       (batch_id, source, endpoint, ds, extracted_at, status, row_count, error, archive_path, run_key)
                       values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       on conflict (batch_id, endpoint) do update set status = excluded.status,
                       row_count = excluded.row_count, error = excluded.error, archive_path = excluded.archive_path,
                       run_key = excluded.run_key"""
                ).format(sql.Identifier(self.schema)),
                (batch_id, source, endpoint, ds, extracted_at, status, row_count, error, archive_path, run_key),
            )

    def latest_log(self, source: str, run_key: str) -> dict:
        """Baris log TERAKHIR tiap endpoint pada satu run: {endpoint: {status, batch_id, ds, extracted_at,
        row_count, error, archive_path}}. Dipakai mode resume dan fase load. Run yang diulang bisa punya
        sukses lama lalu gagal baru; yang menentukan selalu baris terakhirnya. extracted_at beresolusi
        detik: bila waktunya sama, status bukan-success yang dipilih supaya tidak ada yang terlewat."""
        with self.conn, self.conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    """select distinct on (endpoint)
                           endpoint, status, batch_id, ds, extracted_at, row_count, error, archive_path
                       from {}._ingestion_log
                       where source = %s and run_key = %s
                       order by endpoint, extracted_at desc, (status = 'success')"""
                ).format(sql.Identifier(self.schema)),
                (source, run_key),
            )
            kolom = ("status", "batch_id", "ds", "extracted_at", "row_count", "error", "archive_path")
            return {r[0]: dict(zip(kolom, r[1:])) for r in cur.fetchall()}

    def prune(self, endpoint: str, keep: int):
        """Simpan hanya `keep` batch sukses terbaru per endpoint (arsip lengkap tetap di MinIO)."""
        tbl = sql.Identifier(self.schema, table_name(endpoint))
        with self.conn, self.conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    """select batch_id from {}._ingestion_log
                       where endpoint = %s and status = 'success'
                       order by extracted_at desc offset %s"""
                ).format(sql.Identifier(self.schema)),
                (endpoint, keep),
            )
            old = [r[0] for r in cur.fetchall()]
            if old:
                cur.execute(sql.SQL("delete from {} where batch_id = any(%s)").format(tbl), (old,))
