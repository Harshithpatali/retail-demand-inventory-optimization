"""Download only the M5 source tables needed for the selected forecasting run.

The ZIP stays intact. Only one sales matrix, calendar.csv and sell_prices.csv
are streamed out to the runner's temporary ignored data/raw directory.
"""
from __future__ import annotations

import os
import shutil
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
SALES_PREFERRED = "sales_train_evaluation.csv"
SALES_FALLBACK = "sales_train_validation.csv"
REQUIRED_TABLES = {"calendar.csv", "sell_prices.csv"}
BUCKET_DEFAULT = "m5-raw-data"
TIMEOUT = (20, 180)


def _credentials() -> tuple[str, str]:
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SECRET_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or ""
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL and/or SUPABASE_SECRET_KEY GitHub Actions secrets.")
    return url, key


def _headers(key: str) -> dict[str, str]:
    return {"apikey": key, "Authorization": f"Bearer {key}"}


def _list_objects(session: requests.Session, url: str, bucket: str, prefix: str) -> list[dict]:
    endpoint = f"{url}/storage/v1/object/list/{quote(bucket, safe='')}"
    response = session.post(endpoint, json={
        "prefix": prefix, "limit": 1000, "offset": 0,
        "sortBy": {"column": "name", "order": "asc"},
    }, timeout=TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise RuntimeError(f"Unexpected Supabase Storage list response for {prefix!r}.")
    return payload


def _discover_zip(session: requests.Session, url: str, bucket: str) -> list[str]:
    found: list[str] = []
    pending = [""]
    visited: set[str] = set()
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        for item in _list_objects(session, url, bucket, current):
            name = str(item.get("name", ""))
            if not name or name in {".", ".."}:
                continue
            path = f"{current}/{name}".strip("/")
            if not item.get("id") and not item.get("metadata"):
                pending.append(path)
            elif name.lower().endswith(".zip"):
                found.append(path)
    return sorted(set(found))


def _download(session: requests.Session, url: str, bucket: str, object_path: str, target: Path) -> None:
    endpoint = (
        f"{url}/storage/v1/object/authenticated/"
        f"{quote(bucket, safe='')}/{quote(object_path, safe='/')}"
    )
    with session.get(endpoint, stream=True, timeout=TIMEOUT) as response:
        response.raise_for_status()
        with target.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output.write(chunk)


def _extract_required_tables(archive_path: Path, destination: Path) -> list[Path]:
    """Extract only the preferred sales table (or fallback), calendar and prices."""
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise RuntimeError(f"ZIP integrity check failed at {bad_member!r}.")

        members_by_name: dict[str, zipfile.ZipInfo] = {}
        for member in archive.infolist():
            if member.is_dir() or not member.filename.lower().endswith(".csv"):
                continue
            basename = Path(member.filename).name
            if basename in members_by_name:
                raise RuntimeError(f"Duplicate CSV basename {basename!r} in archive.")
            members_by_name[basename] = member

        sales_name = SALES_PREFERRED if SALES_PREFERRED in members_by_name else SALES_FALLBACK
        required = REQUIRED_TABLES | {sales_name}
        missing = required - set(members_by_name)
        if missing:
            raise RuntimeError(f"Archive is missing required processing table(s): {sorted(missing)}")

        extracted: list[Path] = []
        for name in sorted(required):
            target = destination / name
            with archive.open(members_by_name[name]) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
            extracted.append(target)
            print(f"Prepared required input {name}: {target.stat().st_size:,} bytes")
        print(f"Using {sales_name}; skipped all other archive members.")
        return extracted


def main() -> None:
    url, key = _credentials()
    bucket = os.environ.get("SUPABASE_BUCKET", BUCKET_DEFAULT)
    explicit_path = os.environ.get("M5_ZIP_PATH", "").strip()
    work_dir = ROOT / ".m5_download"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)
    archive_path = work_dir / "m5_source.zip"

    try:
        with requests.Session() as session:
            session.headers.update(_headers(key))
            if explicit_path:
                object_path = explicit_path.lstrip("/")
            else:
                candidates = _discover_zip(session, url, bucket)
                if len(candidates) != 1:
                    raise RuntimeError(
                        f"Expected exactly one ZIP in Supabase bucket {bucket!r}, found {len(candidates)}: {candidates}. "
                        "Set M5_ZIP_PATH to the exact object path."
                    )
                object_path = candidates[0]

            print(f"Downloading private source archive from bucket {bucket!r}...")
            _download(session, url, bucket, object_path, archive_path)
            print(f"Downloaded compressed archive: {archive_path.stat().st_size:,} bytes.")
            _extract_required_tables(archive_path, RAW_DIR)
            print("Only the selected sales matrix, calendar and price table were extracted.")
    finally:
        if work_dir.exists():
            shutil.rmtree(work_dir)


if __name__ == "__main__":
    try:
        main()
    except (OSError, requests.RequestException, zipfile.BadZipFile, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
