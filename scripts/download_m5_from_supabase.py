"""Download the private M5 archive from Supabase Storage and extract source CSVs.

Required environment:
  SUPABASE_URL
  SUPABASE_SECRET_KEY (or legacy SUPABASE_SERVICE_ROLE_KEY)

Optional:
  SUPABASE_BUCKET (default: m5-raw-data)
  M5_ZIP_PATH (exact object path; otherwise exactly one ZIP is auto-detected)
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
REQUIRED = {"calendar.csv", "sell_prices.csv"}
SALES_OPTIONS = {"sales_train_validation.csv", "sales_train_evaluation.csv"}
BUCKET_DEFAULT = "m5-raw-data"
TIMEOUT = (20, 180)


def _credentials() -> tuple[str, str]:
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = (
        os.environ.get("SUPABASE_SECRET_KEY")
        or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or ""
    )
    if not url or not key:
        raise RuntimeError(
            "Missing SUPABASE_URL and/or SUPABASE_SECRET_KEY GitHub Actions secrets."
        )
    return url, key


def _headers(key: str) -> dict[str, str]:
    return {"apikey": key, "Authorization": f"Bearer {key}"}


def _list_objects(
    session: requests.Session, url: str, bucket: str, prefix: str
) -> list[dict]:
    endpoint = f"{url}/storage/v1/object/list/{quote(bucket, safe='')}"
    response = session.post(
        endpoint,
        json={
            "prefix": prefix,
            "limit": 1000,
            "offset": 0,
            "sortBy": {"column": "name", "order": "asc"},
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise RuntimeError(f"Unexpected Supabase Storage list response for {prefix!r}.")
    return payload


def _discover_zip(
    session: requests.Session, url: str, bucket: str, prefix: str = ""
) -> list[str]:
    found: list[str] = []
    pending = [prefix]
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
            is_folder = not item.get("id") and not item.get("metadata")
            if is_folder:
                pending.append(path)
            elif name.lower().endswith(".zip"):
                found.append(path)
    return sorted(set(found))


def _download(
    session: requests.Session, url: str, bucket: str, object_path: str, target: Path
) -> None:
    encoded_path = quote(object_path, safe="/")
    endpoint = (
        f"{url}/storage/v1/object/authenticated/"
        f"{quote(bucket, safe='')}/{encoded_path}"
    )
    with session.get(endpoint, stream=True, timeout=TIMEOUT) as response:
        response.raise_for_status()
        with target.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output.write(chunk)


def _extract_csvs(archive_path: Path, destination: Path) -> list[Path]:
    destination.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    seen: set[str] = set()
    with zipfile.ZipFile(archive_path) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise RuntimeError(f"ZIP integrity check failed at {bad_member!r}.")
        for member in archive.infolist():
            if member.is_dir() or not member.filename.lower().endswith(".csv"):
                continue
            basename = Path(member.filename).name
            if basename in seen:
                raise RuntimeError(
                    f"Duplicate CSV basename {basename!r} in archive; refusing ambiguous extraction."
                )
            seen.add(basename)
            target = destination / basename
            with archive.open(member) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
            extracted.append(target)
    return extracted


def main() -> None:
    url, key = _credentials()
    bucket = os.environ.get("SUPABASE_BUCKET", BUCKET_DEFAULT)
    explicit_path = os.environ.get("M5_ZIP_PATH", "").strip()

    with requests.Session() as session:
        session.headers.update(_headers(key))
        if explicit_path:
            object_path = explicit_path.lstrip("/")
        else:
            candidates = _discover_zip(session, url, bucket)
            if len(candidates) != 1:
                raise RuntimeError(
                    "Expected exactly one ZIP in Supabase bucket "
                    f"{bucket!r}, found {len(candidates)}: {candidates}. "
                    "Set the optional M5_ZIP_PATH GitHub secret to the exact object path."
                )
            object_path = candidates[0]

        work_dir = ROOT / ".m5_download"
        if work_dir.exists():
            shutil.rmtree(work_dir)
        work_dir.mkdir(parents=True)
        archive_path = work_dir / "m5_source.zip"
        print(f"Downloading private source archive from bucket {bucket!r}...")
        _download(session, url, bucket, object_path, archive_path)
        print(f"Downloaded {archive_path.stat().st_size:,} bytes.")

        extracted = _extract_csvs(archive_path, RAW_DIR)
        names = {path.name for path in extracted}
        missing = REQUIRED - names
        if not (SALES_OPTIONS & names):
            missing.add("sales_train_validation.csv or sales_train_evaluation.csv")
        if missing:
            raise RuntimeError(
                "Archive is missing required M5 CSV file(s): "
                + ", ".join(sorted(missing))
                + f". CSV files found: {sorted(names)}"
            )

        print("Extracted CSV files:")
        for path in sorted(extracted):
            print(f"  {path.name}: {path.stat().st_size:,} bytes")
        print("Raw source files are temporary workflow inputs and are not committed.")
        shutil.rmtree(work_dir)


if __name__ == "__main__":
    try:
        main()
    except (OSError, requests.RequestException, zipfile.BadZipFile, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
