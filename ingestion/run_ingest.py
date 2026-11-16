"""
Ingestion dua fase: sumber -> MinIO (arsip raw) -> Postgres DWH (schema raw_<sumber>).

  extract : tarik tiap endpoint API dan simpan APA ADANYA sebagai satu file JSON per endpoint per batch
            di MinIO; dicatat 'extracted' di _ingestion_log. Fase ini tidak menyentuh tabel raw.
  load    : baca kembali file batch itu dari MinIO lalu muat ke raw_<sumber> (JSONB); statusnya menjadi
            'success'. Yang masuk Postgres selalu persis isi arsip, dan memuat ulang tidak menyentuh API.

  python -m ingestion.run_ingest --source angkasabiruretail                       # kedua fase berurutan
  python -m ingestion.run_ingest --source angkasabiruretail --phase extract
  python -m ingestion.run_ingest --source angkasabiruretail --phase load --run-key "<run_id>"

Exit code 1 bila ada endpoint yang gagal; endpoint lain tetap diproses, dan batch yang belum berstatus
success tidak dipakai tahap berikutnya (flatten membaca batch success terbaru per endpoint).
"""
import argparse
import hashlib
import json
import logging
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from .config import load_source
from .connectors import EndpointNotFound, get_connector
from .storage import MinioArchive, RawLoader

log = logging.getLogger("ingestion")

# Status yang menandakan arsip batch run ini sudah ada di MinIO (fase extract selesai).
SUDAH_DIARSIP = ("extracted", "load_failed", "success")


def row_hash(record: Dict[str, Any]) -> str:
    return hashlib.md5(json.dumps(record, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def run(source: str, ds: str = None, only: set = None, resume: bool = False, run_key: str = None,
        phase: str = "all") -> Dict[str, Any]:
    """
    phase: 'extract' (API -> MinIO), 'load' (MinIO -> raw_), atau 'all' (keduanya berurutan per endpoint).
    run_key mengikat percobaan ulang dan fase load ke satu run (Airflow memakai run_id; default CLI = mode:ds).
    resume=True melewati endpoint yang fasenya sudah selesai pada run_key yang sama, DILIHAT DARI STATUS
    TERAKHIRNYA (run lain pada hari yang sama tidak dianggap sama):
      'success'                  selesai seluruhnya -> dilewati;
      'extracted'/'load_failed'  arsipnya sudah ada -> langsung dimuat ulang dari MinIO tanpa menyentuh API;
      'failed'/belum tercatat    diekstrak ulang dari API.
    """
    if phase not in ("extract", "load", "all"):
        raise ValueError(f"phase tidak dikenal: {phase}")
    cfg = load_source(source)
    ds = ds or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # akhiran acak: dua run dalam detik yang sama tidak boleh berbagi batch_id (kunci log dan baris raw)
    batch_id = f"batch_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    extracted_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S+00")

    raw_cfg = cfg["raw"]
    connector = get_connector(cfg) if phase != "load" else None
    archive = MinioArchive(raw_cfg["minio_bucket"])
    archive.ensure_bucket()
    loader = RawLoader(raw_cfg["schema"])
    loader.ensure_log()

    run_key = run_key or f"{cfg.get('mode')}:{ds}"
    terakhir = loader.latest_log(source, run_key) if (resume or phase == "load") else {}
    stats = {"source": source, "batch_id": batch_id, "ds": ds, "mode": cfg.get("mode"), "run_key": run_key,
             "extracted": {}, "loaded": {}, "failed": {}, "skipped": []}
    log.info("Ingestion %s | fase=%s | mode=%s | batch=%s | ds=%s", source, phase, cfg.get("mode"), batch_id, ds)
    if terakhir:
        log.info("Status terakhir run %s: %d endpoint tercatat", run_key, len(terakhir))

    eps_by_name = {e["name"]: e for e in cfg["endpoints"]}
    iterate_sources = {e["iterate"]["source"] for e in cfg["endpoints"] if e.get("iterate")}
    fetched: Dict[str, Any] = {}        # cache record endpoint yang jadi roster fan-out
    for ep in cfg["endpoints"]:
        name = ep["name"]
        if only and name not in only:
            continue
        awal = terakhir.get(name) or {}
        muat = None                     # info batch yang siap dimuat pada fase load

        if phase in ("extract", "all"):
            if resume and awal.get("status") in SUDAH_DIARSIP:
                if awal["status"] == "success" or phase == "extract":
                    stats["skipped"].append(name)
                    continue
                muat = awal             # arsipnya sudah ada; tinggal dimuat dari MinIO, tanpa menyentuh API
            else:
                try:
                    it = ep.get("iterate")
                    catatan = None
                    if it and cfg.get("mode") != "sample":
                        # fan-out: satu panggilan per nilai roster (mis. per NIK dari employee_profile)
                        src_name = it["source"]
                        if src_name not in fetched:
                            fetched[src_name] = connector.fetch(eps_by_name[src_name])
                        vals = sorted({str(r[it["field"]]) for r in fetched[src_name]
                                       if r.get(it["field"]) not in (None, "")})
                        log.info("  %-34s fan-out %d nilai %s", name, len(vals), it["param"])
                        records = connector.fetch(ep, iterate_values=vals)
                    else:
                        records = connector.fetch(ep)
                    if name in iterate_sources:
                        fetched[name] = records
                except EndpointNotFound as exc:
                    if not ep.get("optional"):
                        loader.log(source, name, batch_id, ds, extracted_at, "failed", 0, error=str(exc), run_key=run_key)
                        stats["failed"][name] = str(exc)
                        log.error("  %-34s GAGAL: %s", name, exc)
                        continue
                    # endpoint opsional yang 404: diarsipkan kosong agar tabel raw-nya tetap terbentuk saat dimuat
                    records, catatan = [], f"{exc}; endpoint opsional, diarsipkan kosong"
                    log.warning("  %-34s 404, opsional -> diarsipkan kosong", name)
                except Exception as exc:  # satu endpoint gagal tidak menghentikan yang lain
                    msg = str(exc)[:500]
                    loader.log(source, name, batch_id, ds, extracted_at, "failed", 0, error=msg, run_key=run_key)
                    stats["failed"][name] = msg
                    log.error("  %-34s GAGAL: %s", name, msg)
                    continue
                archive_path = archive.put_json(f"raw/{source}/{name}/dt={ds}/{batch_id}.json", records)
                loader.log(source, name, batch_id, ds, extracted_at, "extracted", len(records),
                           error=catatan, archive_path=archive_path, run_key=run_key)
                stats["extracted"][name] = len(records)
                log.info("  %-34s %6d baris -> %s", name, len(records), archive_path)
                if phase == "extract":
                    continue
                muat = {"batch_id": batch_id, "ds": ds, "extracted_at": extracted_at,
                        "archive_path": archive_path, "error": catatan}
        else:                           # phase == 'load'
            st = awal.get("status")
            if st == "success":
                stats["skipped"].append(name)
                continue
            if st in ("extracted", "load_failed"):
                muat = awal
            else:
                if st:                  # ekstraksinya gagal: tidak ada arsip run ini yang bisa dimuat
                    log.warning("  %-34s dilewati: status terakhirnya '%s', belum ada arsip pada run ini", name, st)
                continue

        # ---- fase load: baca arsip MinIO, muat ke raw_<sumber>
        try:
            records = archive.get_json(muat["archive_path"])
            loader.load(name, muat["batch_id"], muat["ds"], muat["extracted_at"],
                        [(row_hash(r), r) for r in records])
            loader.log(source, name, muat["batch_id"], muat["ds"], muat["extracted_at"], "success",
                       len(records), error=muat.get("error"), archive_path=muat["archive_path"], run_key=run_key)
            loader.prune(name, raw_cfg.get("keep_batches", 7))
            stats["loaded"][name] = len(records)
            log.info("  %-34s %6d baris <- arsip MinIO", name, len(records))
        except Exception as exc:
            msg = str(exc)[:500]
            loader.log(source, name, muat["batch_id"], muat["ds"], muat["extracted_at"], "load_failed",
                       muat.get("row_count") or 0, error=msg, archive_path=muat["archive_path"], run_key=run_key)
            stats["failed"][name] = msg
            log.error("  %-34s GAGAL dimuat dari arsip: %s", name, msg)

    loader.close()
    stats["skipped"].sort()
    log.info("Selesai fase %s: %d endpoint diarsipkan, %d dimuat (%d baris), %d gagal, %d dilewati",
             phase, len(stats["extracted"]), len(stats["loaded"]),
             sum(stats["loaded"].values()), len(stats["failed"]), len(stats["skipped"]))
    return stats


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--ds")
    ap.add_argument("--endpoints", help="daftar nama endpoint dipisah koma (default: semua)")
    ap.add_argument("--phase", choices=["extract", "load", "all"], default="all",
                    help="extract: API -> MinIO; load: MinIO -> raw_ (tanpa API); all: keduanya")
    ap.add_argument("--resume", action="store_true",
                    help="lewati endpoint yang fasenya sudah selesai pada run yang sama; "
                         "yang sudah terarsip dimuat dari MinIO tanpa menyentuh API")
    ap.add_argument("--run-key", help="pengenal run untuk resume dan fase load (default: <mode>:<ds>)")
    args = ap.parse_args(argv)
    only = set(args.endpoints.split(",")) if args.endpoints else None
    stats = run(args.source, args.ds, only, resume=args.resume, run_key=args.run_key, phase=args.phase)
    return 1 if stats["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
