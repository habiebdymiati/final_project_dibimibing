"""
Muat berkas referensi (CSV) sebuah sumber ke Postgres DWH, schema reference_<sumber>.

Berkas referensi BUKAN endpoint API: ia melengkapi aturan transformasi (mis. TMT karyawan sebagai dasar
urutan id_employee). Karena itu ia tidak masuk raw_/raw_table_ dan tidak punya DAG sendiri; daftar berkasnya
ada di blok `reference_files` pada sources/<sumber>.yaml.

Aturan muat sama dengan raw_table_: seluruh kolom teks apa adanya, TRUNCATE + INSERT dalam satu transaksi.
Berkas berisi banyak perusahaan atau data pribadi yang tidak dibutuhkan bisa dibatasi lewat `saring` (baris) dan `kolom`.
Nama kolom dibakukan ke snake_case ("Tmt karyawan" -> tmt_karyawan). Berkas yang tidak ditemukan
menggagalkan proses dengan pesan jelas: lebih baik berhenti daripada membentuk ID dengan urutan yang salah.

  python -m ingestion.load_reference --source angkasabiru
"""
import argparse
import csv
import logging
import re
import sys

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values

from .config import PROJECT_ROOT, load_source, pg_params

log = logging.getLogger("ingestion")


def schema_name(source: str) -> str:
    return f"reference_{source}"


def _kolom(nama: str) -> str:
    return (re.sub(r"[^a-z0-9]+", "_", nama.strip().lower()).strip("_") or "kolom")[:63]


def load_file(conn, source: str, name: str, path, saring: dict = None, kolom: list = None) -> int:
    if not path.exists():
        raise FileNotFoundError(f"Berkas referensi '{name}' tidak ditemukan: {path}")
    with open(path, encoding="utf-8-sig", newline="") as fp:
        rows = list(csv.reader(fp))
    if not rows:
        raise ValueError(f"Berkas referensi kosong: {path}")
    kepala, badan = [c.strip() for c in rows[0]], rows[1:]
    hilang = [k for k in [*(saring or {}), *(kolom or [])] if k not in kepala]
    if hilang:
        raise ValueError(f"Kolom {hilang} tidak ada pada {path}")
    for k, nilai in (saring or {}).items():
        i = kepala.index(k)
        badan = [r for r in badan if i < len(r) and r[i].strip() == nilai]
    if kolom:
        pilih = [kepala.index(k) for k in kolom]
        kepala, badan = list(kolom), [[r[i] if i < len(r) else "" for i in pilih] for r in badan]
    cols = [_kolom(c) for c in kepala]
    if len(set(cols)) != len(cols):
        raise ValueError(f"Nama kolom kembar setelah dibakukan pada {path}: {cols}")
    data = [[(v.strip() or None) for v in (r + [""] * len(cols))[:len(cols)]] for r in badan if any(v.strip() for v in r)]
    if saring and not data:
        raise ValueError(f"Berkas referensi '{name}' kosong setelah disaring {saring}: {path}")

    schema, tbl = schema_name(source), sql.Identifier(schema_name(source), name)
    try:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("create schema if not exists {}").format(sql.Identifier(schema)))
            cur.execute(sql.SQL("create table if not exists {} (_file text, _loaded_at timestamptz default now())").format(tbl))
            cur.execute("select column_name from information_schema.columns where table_schema = %s and table_name = %s",
                        (schema, name))
            ada = {r[0] for r in cur.fetchall()}
            for c in cols:
                if c not in ada:
                    cur.execute(sql.SQL("alter table {} add column {} text").format(tbl, sql.Identifier(c)))
            cur.execute(sql.SQL("truncate table {}").format(tbl))
            execute_values(cur, sql.SQL("insert into {} (_file, {}) values %s").format(
                tbl, sql.SQL(", ").join(sql.Identifier(c) for c in cols)).as_string(conn),
                [[path.name] + r for r in data], page_size=2000)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return len(data)


def run(source: str) -> int:
    cfg = load_source(source)
    files = cfg.get("reference_files") or []
    if not files:
        log.info("Sumber %s tidak punya berkas referensi", source)
        return 0
    total = 0
    conn = psycopg2.connect(**pg_params("DWH"))
    try:
        for f in files:
            n = load_file(conn, source, f["name"], PROJECT_ROOT / f["path"], saring=f.get("saring"), kolom=f.get("kolom"))
            total += n
            log.info("  %-28s %6d baris -> %s.%s", f["name"], n, schema_name(source), f["name"])
    finally:
        conn.close()
    return total


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    run(ap.parse_args().source)
    return 0


if __name__ == "__main__":
    sys.exit(main())
