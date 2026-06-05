#!/usr/bin/env python3
"""Import a Windows reference package or PNG folder into refs/win."""

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_png(source_root, frame):
    candidates = [
        source_root / frame,
        source_root / "png" / frame,
        source_root / "win" / frame,
        source_root / "reference" / frame,
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def load_package_metadata(source_root):
    path = source_root / "reference_package.json"
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def import_from_root(source_root, local_manifest_path, dest_dir):
    with local_manifest_path.open(encoding="utf-8") as handle:
        local_manifest = json.load(handle)

    package = load_package_metadata(source_root)
    package_cases = {}
    if package:
        package_cases = {case["frame"]: case for case in package.get("cases", [])}

    imported = []
    missing = []
    mismatched = []
    dest_dir.mkdir(parents=True, exist_ok=True)

    for case in local_manifest["cases"]:
        frame = case["frame"]
        source_png = find_png(source_root, frame)
        if source_png is None:
            missing.append(frame)
            continue

        actual_hash = sha256(source_png)
        package_case = package_cases.get(frame)
        if package_case and package_case.get("sha256") != actual_hash:
            mismatched.append(frame)
            continue

        shutil.copy2(source_png, dest_dir / frame)
        imported.append(
            {
                "id": case["id"],
                "frame": frame,
                "params": case.get("params", {}),
                "sha256": actual_hash,
                "bytes": source_png.stat().st_size,
            }
        )

    if missing or mismatched:
        if missing:
            print("missing frames:", ", ".join(missing), file=sys.stderr)
        if mismatched:
            print("hash mismatches:", ", ".join(mismatched), file=sys.stderr)
        return 1

    receipt = {
        "schema": 1,
        "kind": "olm_imported_win_reference",
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source_root),
        "package": package,
        "local_manifest": str(local_manifest_path),
        "dest_dir": str(dest_dir),
        "cases": imported,
    }
    receipt_path = dest_dir / "reference_import.json"
    with receipt_path.open("w", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)

    print(f"imported {len(imported)} frames into {dest_dir}")
    print(f"receipt={receipt_path}")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Windows reference zip or folder")
    parser.add_argument(
        "--manifest",
        default="refs/cases/olmsmoother_v1_minimal.json",
        help="local case manifest JSON",
    )
    parser.add_argument("--dest", default="refs/win", help="destination reference directory")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    manifest_path = Path(args.manifest).resolve()
    dest_dir = Path(args.dest).resolve()

    if not manifest_path.exists():
        print(f"manifest not found: {manifest_path}", file=sys.stderr)
        return 2
    if not source.exists():
        print(f"source not found: {source}", file=sys.stderr)
        return 2

    if source.is_dir():
        return import_from_root(source, manifest_path, dest_dir)

    if zipfile.is_zipfile(source):
        with tempfile.TemporaryDirectory(prefix="olm_win_ref_") as tmp:
            with zipfile.ZipFile(source) as archive:
                archive.extractall(tmp)
            return import_from_root(Path(tmp), manifest_path, dest_dir)

    print(f"source is neither a directory nor a zip file: {source}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
