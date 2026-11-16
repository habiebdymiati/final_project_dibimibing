"""
Pendataran payload JSONB -> tabel kolom-baris (medallion: sub-layer bronze tabular).

Setiap endpoint pada schema raw_<sumber> dibuatkan tabel kembar di schema raw_table_<sumber>:
kunci payload menjadi kolom (teks, apa adanya tanpa cleansing), satu record menjadi satu baris,
plus kolom silsilah _batch_id/_ds/_extracted_at/_row_hash. Tabel diisi ulang dengan TRUNCATE + INSERT dari
batch sukses terakhir, sehingga hanya nilai terbaru yang tersimpan dan struktur tabelnya tetap.

Backfill / jalankan manual:
  python -m ingestion.flatten --source angkasabiruretail [--endpoints companies,areas]
"""
import argparse
import logging
import sys

import psycopg2
from psycopg2 import sql

from .config import load_source, pg_params
from .storage import table_name

log = logging.getLogger("ingestion")
LINEAGE = ["_batch_id", "_ds", "_extracted_at", "_row_hash"]


def flat_schema_name(raw_schema: str) -> str:
    """raw_angkasabiruretail -> raw_table_angkasabiruretail (sumber baru otomatis mengikuti pola yang sama)."""
    return raw_schema.replace("raw_", "raw_table_", 1) if raw_schema.startswith("raw_") else f"raw_table_{raw_schema}"


def _colname(key: str) -> str:
    """Nama kolom = kunci payload apa adanya (identifier Postgres dibatasi 63 byte)."""
    return key[:63]


def flatten_endpoint(conn, raw_schema: str, endpoint: str, batch_id: str = None) -> int:
    """Isi ulang raw_table_<sumber>.<endpoint> dari satu batch (default: batch sukses terakhir)
    dengan metode TRUNCATE + INSERT dalam satu transaksi. Mengembalikan jumlah baris.

    Tabel dibuat sekali lalu dipertahankan: strukturnya tidak di-drop tiap run, sehingga objek yang
    bergantung padanya (view / model transformasi) tetap utuh dan hanya nilai terbaru yang tersimpan.
      * kunci payload baru          -> kolom ditambahkan (ALTER TABLE ADD COLUMN);
      * kunci yang hilang dari sumber -> kolomnya dipertahankan dan terisi NULL (dicatat sebagai peringatan),
        bukan di-drop, supaya kontrak kolom bagi transformasi hilir tidak berubah diam-diam.
    """
    flat_schema = flat_schema_name(raw_schema)
    tbl = table_name(endpoint)
    raw_t = sql.Identifier(raw_schema, tbl)
    flat_t = sql.Identifier(flat_schema, tbl)
    try:
        with conn.cursor() as cur:
            if batch_id is None:
                cur.execute(
                    sql.SQL("""select batch_id from {}._ingestion_log
                               where endpoint = %s and status = 'success'
                               order by extracted_at desc limit 1""").format(sql.Identifier(raw_schema)),
                    (endpoint,))
                row = cur.fetchone()
                if not row:
                    conn.rollback()
                    return 0
                batch_id = row[0]

            # kunci payload pada batch itu -> daftar kolom (urut alfabet agar deterministik)
            cur.execute(
                sql.SQL("select distinct jsonb_object_keys(payload) from {} where batch_id = %s order by 1")
                .format(raw_t), (batch_id,))
            keys = [r[0] for r in cur.fetchall()]

            # tabel dibuat sekali; kolom silsilah bertipe sama dengan layer raw
            cur.execute(sql.SQL("create schema if not exists {}").format(sql.Identifier(flat_schema)))
            cur.execute(sql.SQL("""create table if not exists {} (
                                       _batch_id text, _ds date, _extracted_at timestamptz, _row_hash text)""")
                        .format(flat_t))
            cur.execute("""select column_name from information_schema.columns
                           where table_schema = %s and table_name = %s""", (flat_schema, tbl))
            existing = {r[0] for r in cur.fetchall()}
            for k in keys:
                if _colname(k) not in existing:
                    cur.execute(sql.SQL("alter table {} add column {} text").format(flat_t, sql.Identifier(_colname(k))))
            stale = sorted(existing - {_colname(k) for k in keys} - set(LINEAGE))
            if stale:
                log.warning("  %s.%s: kunci tidak lagi dikirim sumber, kolom dipertahankan (NULL): %s",
                            flat_schema, tbl, ", ".join(stale))

            # TRUNCATE + INSERT: hanya nilai batch terbaru yang tersimpan
            cur.execute(sql.SQL("truncate table {}").format(flat_t))
            target_cols = [sql.Identifier(c) for c in LINEAGE] + [sql.Identifier(_colname(k)) for k in keys]
            select_cols = ([sql.SQL("r.batch_id"), sql.SQL("r.ds"), sql.SQL("r.extracted_at"), sql.SQL("r.row_hash")]
                           + [sql.SQL("r.payload ->> {}").format(sql.Literal(k)) for k in keys])
            cur.execute(sql.SQL("insert into {} ({}) select {} from {} r where r.batch_id = %s").format(
                flat_t, sql.SQL(", ").join(target_cols), sql.SQL(", ").join(select_cols), raw_t), (batch_id,))
            n = cur.rowcount
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return n


def run(source: str, only: set = None) -> int:
    cfg = load_source(source)
    raw_schema = cfg["raw"]["schema"]
    conn = psycopg2.connect(**pg_params("DWH"))
    total = 0
    try:
        for ep in cfg["endpoints"]:
            name = ep["name"]
            if only and name not in only:
                continue
            n = flatten_endpoint(conn, raw_schema, name)
            total += n
            log.info("  %-34s %6d baris -> %s.%s", name, n, flat_schema_name(raw_schema), table_name(name))
    finally:
        conn.close()
    return total


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--endpoints", help="daftar endpoint dipisah koma (default: semua)")
    args = ap.parse_args()
    only = set(args.endpoints.split(",")) if args.endpoints else None
    total = run(args.source, only)
    log.info("Pendataran selesai: %d baris", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
