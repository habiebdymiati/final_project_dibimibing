"""Konektor sumber: REST API dan berkas CSV lokal. Sumber baru = konektor baru dengan method fetch()."""
import csv
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from .config import PROJECT_ROOT

log = logging.getLogger("ingestion")

# Status HTTP yang bersifat sementara (termasuk 520-524 dari Cloudflare) layak diulang
RETRY_STATUS = {429, 500, 502, 503, 504, 520, 521, 522, 523, 524}


class ExtractError(RuntimeError):
    pass


class EndpointNotFound(ExtractError):
    """HTTP 404: endpoint tidak ada. Permanen, tidak diulang."""


# Kunci pembungkus daftar baris pada respons API. 'data' dipakai Angkasa Biru Retail dan Angkasa Biru
# (AP membungkus ganda: {"data": {"data": [...], "pagination": ...}}); 'result' dipakai API bergaya SF6
# (SF6), yang membungkus baris bersama metadata paginasi: {"result": [...], "total_data": N}.
ENVELOPE_KEYS = ("data", "result")


def _unwrap(payload: Any) -> List[Dict[str, Any]]:
    """Payload API bisa berupa list, atau objek dengan kunci pembungkus (list / objek tunggal)."""
    while isinstance(payload, dict):
        key = next((k for k in ENVELOPE_KEYS if k in payload), None)
        if key is None:
            break
        payload = payload[key]
    if payload is None:
        return []
    if isinstance(payload, dict):
        # dict tanpa kunci pembungkus = objek tunggal; dict kosong = tidak ada data
        return [payload] if payload else []
    if isinstance(payload, list):
        return [r if isinstance(r, dict) else {"value": r} for r in payload]
    raise ExtractError(f"Bentuk payload tidak dikenali: {type(payload).__name__}")


class RestApiConnector:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.mode = cfg.get("mode", "live")
        if self.mode not in ("live", "sample"):
            raise ValueError(f"mode harus 'live' atau 'sample', bukan '{self.mode}'")
        self.api = cfg.get("api", {})
        self._bearer_token = None
        # satu subfolder per sumber: data/sample/<sumber>/<endpoint>.json
        self.sample_dir = Path(cfg.get("sample_dir") or f"data/sample/{cfg.get('source', 'default')}")
        if not self.sample_dir.is_absolute():
            self.sample_dir = PROJECT_ROOT / self.sample_dir

    def fetch(self, endpoint: Dict[str, Any], iterate_values: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if self.mode == "sample":
            return self._fetch_sample(endpoint)
        it = endpoint.get("iterate")
        if not it:
            return self._fetch_live(endpoint)
        # fan-out: panggil endpoint sekali per nilai (mis. per NIK dari roster)
        if iterate_values is None:
            raise ExtractError(f"{endpoint['name']}: butuh nilai iterate dari endpoint '{it['source']}' "
                               "yang harus tercantum lebih dulu pada daftar endpoints")
        out: List[Dict[str, Any]] = []
        for v in iterate_values:
            out.extend(self._fetch_live(endpoint, extra_params={it["param"]: v}))
        return out

    # ---------------------------------------------------------------- autentikasi
    def _bearer_login(self) -> str:
        """POST ke login_path dengan kredensial; token di-cache untuk satu run."""
        if self._bearer_token:
            return self._bearer_token
        auth = self.api.get("auth", {})
        url = f"{self.api['base_url'].rstrip('/')}{auth.get('login_path', '/login')}"
        try:
            resp = requests.post(url, json={"username": auth.get("username", ""),
                                            "password": auth.get("password", "")},
                                 timeout=self.api.get("timeout_seconds", 30))
            resp.raise_for_status()
            body = resp.json()
        except (requests.RequestException, ValueError) as exc:
            raise ExtractError(f"Login bearer ke {url} gagal: {exc}") from exc
        token = (body.get("token") or body.get("access_token") or body.get("accessToken")
                 or (body.get("data") or {}).get("token") if isinstance(body, dict) else None)
        if not token:
            raise ExtractError(f"Login bearer ke {url}: token tidak ditemukan pada respons")
        self._bearer_token = token
        return token

    def _auth_headers(self, endpoint: Dict[str, Any]) -> Dict[str, str]:
        auth = self.api.get("auth")
        if auth and auth.get("type") == "bearer_token":
            # token statis (bukan hasil login), gaya API HRIS Angkasa Biru Destination: Authorization: Bearer <token>
            if not auth.get("token"):
                raise ExtractError("Token bearer kosong; isi token sumber di .env")
            return {"Authorization": f"Bearer {auth['token']}"}
        if auth and auth.get("type") == "bearer_login":
            if not auth.get("username") or not auth.get("password"):
                raise ExtractError("Kredensial bearer kosong; isi username/password sumber di .env")
            return {"Authorization": f"Bearer {self._bearer_login()}"}
        # api_key boleh ditetapkan per endpoint (API bergaya SF6: satu kunci berbeda untuk tiap sfid),
        # bila kosong jatuh ke api_key tingkat sumber.
        key = endpoint.get("api_key") or self.api.get("api_key")
        if not key:
            raise ExtractError(
                f"API key kosong untuk endpoint '{endpoint.get('name', '?')}'; "
                "mode live membutuhkan kredensial (isi di .env)")
        header = endpoint.get("auth_header", self.api.get("default_auth_header", "api_key"))
        headers = {header: key}
        if self.api.get("cookie"):
            headers["Cookie"] = self.api["cookie"]
        return headers

    def _fetch_sample(self, endpoint: Dict[str, Any]) -> List[Dict[str, Any]]:
        path = self.sample_dir / f"{endpoint['name']}.json"
        if not path.exists():
            raise ExtractError(f"Fixture sample tidak ada: {path}")
        with open(path, "r", encoding="utf-8") as fp:
            return _unwrap(json.load(fp))

    def _fetch_live(self, endpoint: Dict[str, Any], extra_params: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        headers = {"Accept": "application/json", **self._auth_headers(endpoint)}
        pag = self.api.get("pagination")
        if pag:
            return self._fetch_paginated(endpoint, headers, pag, extra_params or {})
        url = f"{self.api['base_url'].rstrip('/')}{endpoint.get('path', '')}"
        # query: parameter tetap milik endpoint (API bergaya SF6 membedakan endpoint lewat ?sfid=, bukan path)
        params = {**(endpoint.get("query") or {}), **(extra_params or {})} or None
        timeout = self.api.get("timeout_seconds", 30)
        attempts = 1 + int(self.api.get("retries", 2))
        backoff = float(self.api.get("retry_backoff_seconds", 3))
        last = "tidak ada percobaan"
        for attempt in range(1, attempts + 1):
            try:
                resp = requests.get(url, headers=headers, params=params, timeout=timeout)
                if resp.status_code in RETRY_STATUS and attempt < attempts:
                    last = f"HTTP {resp.status_code}"
                else:
                    resp.raise_for_status()
                    return _unwrap(resp.json())
            except (requests.ConnectionError, requests.Timeout) as exc:
                last = type(exc).__name__
                if attempt == attempts:
                    raise ExtractError(f"GET {url} gagal setelah {attempts} percobaan: {exc}") from exc
            except (requests.RequestException, ValueError) as exc:
                status = getattr(getattr(exc, "response", None), "status_code", None)
                if status == 404:
                    raise EndpointNotFound(f"GET {url} -> 404 Not Found") from exc
                raise ExtractError(f"GET {url} gagal: {exc}") from exc
            log.warning("  %s: %s (percobaan %d/%d), ulangi dalam %.0fs", endpoint["name"], last, attempt, attempts, backoff * attempt)
            time.sleep(backoff * attempt)
        raise ExtractError(f"GET {url} gagal setelah {attempts} percobaan ({last})")  # tidak tercapai


    def _fetch_paginated(self, endpoint, headers, pag, extra_params) -> List[Dict[str, Any]]:
        """
        Loop halaman sampai halaman kosong atau berisi kurang dari limit.

        pag['in'] menentukan di mana nomor halaman dikirim:
          'query'  (default) - sebagai query parameter (Angkasa Biru)
          'header'           - sebagai HTTP header (API SF6 hanya menerima header 'page')
        limit_param boleh dikosongkan bila server menetapkan ukuran halaman sendiri; 'limit'
        lalu dipakai hanya sebagai ambang berhenti.
        """
        base = f"{self.api['base_url'].rstrip('/')}{endpoint.get('path', '')}"
        static = endpoint.get("query") or {}
        # page_limit per endpoint mengalahkan limit global (untuk endpoint yang 500/timeout pada halaman besar)
        limit = int(endpoint.get("page_limit") or pag.get("limit", 200))
        max_pages = int(pag.get("max_pages", 500))
        where = pag.get("in", "query")
        if where not in ("query", "header"):
            raise ValueError(f"pagination.in harus 'query' atau 'header', bukan '{where}'")
        limit_param = pag.get("limit_param", "limit")
        out: List[Dict[str, Any]] = []
        for page in range(1, max_pages + 1):
            page_args = {pag.get("page_param", "page"): page}
            if limit_param:
                page_args[limit_param] = limit
            if where == "header":
                params = {**static, **extra_params}
                page_headers = {**headers, **{k: str(v) for k, v in page_args.items()}}
            else:
                params = {**static, **page_args, **extra_params}
                page_headers = headers
            attempts = 1 + int(self.api.get("retries", 2))
            backoff = float(self.api.get("retry_backoff_seconds", 3))
            batch = None
            for attempt in range(1, attempts + 1):
                try:
                    resp = requests.get(base, headers=page_headers, params=params,
                                        timeout=self.api.get("timeout_seconds", 30))
                    if resp.status_code in RETRY_STATUS and attempt < attempts:
                        pass
                    elif resp.status_code == 401 and self.api.get("auth", {}).get("type") == "bearer_login" and attempt < attempts:
                        self._bearer_token = None            # token kedaluwarsa: login ulang
                        headers = {"Accept": "application/json", **self._auth_headers(endpoint)}
                        page_headers = {**headers, **{k: str(v) for k, v in page_args.items()}} \
                            if where == "header" else headers
                    else:
                        if resp.status_code == 404:
                            raise EndpointNotFound(f"GET {base} -> 404 Not Found")
                        resp.raise_for_status()
                        batch = _unwrap(resp.json())
                        break
                except EndpointNotFound:
                    raise
                except (requests.ConnectionError, requests.Timeout) as exc:
                    if attempt == attempts:
                        raise ExtractError(f"GET {base} (page {page}) gagal setelah {attempts} percobaan: {exc}") from exc
                except (requests.RequestException, ValueError) as exc:
                    raise ExtractError(f"GET {base} (page {page}) gagal: {exc}") from exc
                time.sleep(backoff * attempt)
            if batch is None:
                raise ExtractError(f"GET {base} (page {page}) gagal setelah {attempts} percobaan")
            out.extend(batch)
            if len(batch) < limit:
                break
        return out


class CsvFileConnector:
    """
    Sumber berkas CSV lokal (mis. nominatif master data yang dikirim manual, bukan lewat API).
    Satu endpoint = satu berkas. Header dipakai apa adanya sebagai nama field payload, sehingga
    layer raw tetap menyimpan bentuk asli sumber persis seperti konektor REST.
    """

    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        base = cfg.get("base_dir") or "."
        self.base = Path(base) if Path(base).is_absolute() else PROJECT_ROOT / base

    def fetch(self, endpoint: Dict[str, Any], iterate_values: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        path = self.base / endpoint["path"]
        if not path.exists():
            if endpoint.get("optional"):
                log.warning("  %s: berkas %s tidak ada, dimuat kosong (optional)", endpoint["name"], path)
                return []
            raise ExtractError(f"Berkas sumber tidak ditemukan: {path}")
        enc = endpoint.get("encoding", self.cfg.get("encoding", "utf-8-sig"))
        delim = endpoint.get("delimiter", self.cfg.get("delimiter", ","))
        try:
            with open(path, newline="", encoding=enc) as fp:
                rows = list(csv.DictReader(fp, delimiter=delim))
        except (OSError, UnicodeDecodeError, csv.Error) as exc:
            raise ExtractError(f"Gagal membaca {path}: {exc}") from exc
        out: List[Dict[str, Any]] = []
        for r in rows:
            # kolom tanpa header (None) dibuang; nilai dirapikan seperlunya saja
            rec = {k.strip(): (v.strip() if isinstance(v, str) else v)
                   for k, v in r.items() if k is not None and k.strip()}
            if any(v not in (None, "") for v in rec.values()):
                out.append(rec)
        return out


def get_connector(cfg: Dict[str, Any]):
    kind = cfg.get("type")
    if kind == "rest_api":
        return RestApiConnector(cfg)
    if kind == "csv_file":
        return CsvFileConnector(cfg)
    raise ValueError(f"Tipe sumber belum didukung: {kind}")
