"""Pemuat konfigurasi sumber (sources/*.yaml) dan koneksi database dari environment."""
import os
import re
from pathlib import Path
from typing import Any, Dict

import yaml

PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parent.parent))

# ${VAR} atau ${VAR:-default}, boleh disisipkan di tengah string
_ENV = re.compile(r"\$\{([^}:]+)(?::-([^}]*))?\}")


def _expand(obj: Any) -> Any:
    if isinstance(obj, str):
        return _ENV.sub(lambda m: os.environ.get(m.group(1), m.group(2) or ""), obj)
    if isinstance(obj, dict):
        return {k: _expand(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand(v) for v in obj]
    return obj


def load_source(name: str) -> Dict[str, Any]:
    path = PROJECT_ROOT / "sources" / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Definisi sumber tidak ditemukan: {path}")
    with open(path, "r", encoding="utf-8") as fp:
        return _expand(yaml.safe_load(fp))


def list_sources() -> list:
    return sorted(p.stem for p in (PROJECT_ROOT / "sources").glob("*.yaml"))


def pg_params(prefix: str) -> Dict[str, Any]:
    """prefix: DWH atau DATAHUB. Host default localhost agar bisa dijalankan dari luar container."""
    default_port = {"DWH": "5433", "DATAHUB": "5434"}[prefix]
    return {
        "host": os.environ.get(f"{prefix}_HOST", "localhost"),
        "port": int(os.environ.get(f"{prefix}_PORT", default_port)),
        "dbname": os.environ[f"{prefix}_DB"],
        "user": os.environ[f"{prefix}_USER"],
        "password": os.environ[f"{prefix}_PASSWORD"],
    }
