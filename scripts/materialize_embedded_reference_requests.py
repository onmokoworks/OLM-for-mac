#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_extract_zip(archive_path: Path, dest: Path) -> Path:
    root = dest / archive_path.stem
    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            normalized = info.filename.replace("\\", "/")
            parts = [part for part in normalized.split("/") if part]
            if not parts:
                continue
            if any(part == ".." for part in parts):
                raise ValueError(f"unsafe zip path: {info.filename}")
            target = root.joinpath(*parts)
            if info.is_dir() or normalized.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
    return root


def read_request_ids(path: Path) -> tuple[str | None, str]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    request_id = data.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        request_id = None
    canonical = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return request_id, canonical


def materialize(source: Path, dest: Path, replace: bool) -> list[Path]:
    request_dir = source / "reference_requests"
    if not request_dir.exists():
        raise FileNotFoundError(f"reference_requests directory not found in {source}")

    written: list[Path] = []
    for request_path in sorted(request_dir.glob("*.json")):
        request_id, canonical = read_request_ids(request_path)
        out_name = request_path.name if request_id is None else f"{request_id}.json"
        out_path = dest / out_name
        if out_path.exists():
            existing = out_path.read_text(encoding="utf-8-sig")
            if sha256_bytes(existing.encode("utf-8")) == sha256_bytes(canonical.encode("utf-8")):
                written.append(out_path)
                continue
            if not replace:
                raise FileExistsError(f"destination exists with different contents: {out_path}")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(canonical, encoding="utf-8")
        written.append(out_path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Returned Windows zip or extracted folder containing reference_requests/")
    parser.add_argument("--dest", type=Path, default=Path("refs/reference_requests"))
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    source = args.source.resolve()
    dest = args.dest.resolve()

    if source.is_file():
        with tempfile.TemporaryDirectory(prefix="olm_embedded_requests_") as tmp:
            extracted = safe_extract_zip(source, Path(tmp))
            written = materialize(extracted, dest, args.replace)
    else:
        written = materialize(source, dest, args.replace)

    print(f"materialized_requests={len(written)}")
    for path in written:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
