"""
Sambungkan Data Hub ke layer silver di DWH lewat postgres_fdw, sebagai sumber dbt layer gold.

Layer gold berada di Postgres Data Hub, sedangkan silver di Postgres DWH. Untuk tiap sumber yang sudah punya
transformasi (blok `dbt:` di sources/<sumber>.yaml) dibuat schema fdw_silver_<sumber> berisi foreign table cermin
silver_<sumber>. Foreign table tidak menyimpan data, jadi tidak ada salinan silver di Data Hub. Server dan schema dibuat
ulang tiap run supaya kolom baru di silver ikut terbaca. Dilakukan di Python, bukan di dbt, supaya kata sandi DWH
tidak tertulis di log dbt.

  python -m ingestion.fdw_silver
"""
import logging
import sys

import psycopg2
from psycopg2 import sql

from .config import list_sources, load_source, pg_params

log = logging.getLogger("ingestion")
SERVER = "dwh_srv"


def sumber_silver() -> list:
    return [s for s in list_sources() if (load_source(s).get("dbt") or {}).get("select")]


def run() -> list:
    dwh = pg_params("DWH")
    sumber = sumber_silver()
    # sumber sistem (mis. lms) tidak punya schema silver sendiri: modelnya menumpang di silver perusahaan,
    # jadi hanya schema silver_<sumber> yang benar-benar berisi tabel yang dicerminkan ke Data Hub
    with psycopg2.connect(**dwh) as koneksi_dwh, koneksi_dwh.cursor() as cur:
        cur.execute("select distinct table_schema from information_schema.tables where table_schema like 'silver\\_%'")
        ada = {r[0] for r in cur.fetchall()}
    lewat = [s for s in sumber if f"silver_{s}" not in ada]
    for s in lewat:
        log.info("  silver_%s tidak ada (sumber sistem tanpa silver sendiri) -> dilewati", s)
    sumber = [s for s in sumber if f"silver_{s}" in ada]
    conn = psycopg2.connect(**pg_params("DATAHUB"))
    try:
        with conn.cursor() as cur:
            cur.execute("create extension if not exists postgres_fdw")
            cur.execute(sql.SQL("drop server if exists {} cascade").format(sql.Identifier(SERVER)))
            cur.execute(
                sql.SQL("create server {} foreign data wrapper postgres_fdw "
                        "options (host %s, port %s, dbname %s, fetch_size '10000')").format(sql.Identifier(SERVER)),
                (dwh["host"], str(dwh["port"]), dwh["dbname"]))
            cur.execute(
                sql.SQL("create user mapping for current_user server {} options (user %s, password %s)").format(sql.Identifier(SERVER)),
                (dwh["user"], dwh["password"]))
            for s in sumber:
                asal, cermin = f"silver_{s}", f"fdw_silver_{s}"
                cur.execute(sql.SQL("drop schema if exists {} cascade").format(sql.Identifier(cermin)))
                cur.execute(sql.SQL("create schema {}").format(sql.Identifier(cermin)))
                cur.execute(sql.SQL("import foreign schema {} from server {} into {}").format(
                    sql.Identifier(asal), sql.Identifier(SERVER), sql.Identifier(cermin)))
                cur.execute("select count(*) from information_schema.foreign_tables where foreign_table_schema = %s", (cermin,))
                n = cur.fetchone()[0]
                if not n:
                    raise RuntimeError(f"{asal} kosong di DWH: jalankan transformasi silver dulu")
                log.info("  %-24s %d foreign table -> %s", asal, n, cermin)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return sumber


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
