#!/usr/bin/env python3
"""Smoke-test the project-local Windows Send First staging folder.

The staging folder is a human handoff surface, so it is easy for the README and
the zip payload to drift apart. This smoke asserts that the folder contains the
current highest-priority pending runtime trace package and no stale zip.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_runtime_request_package(path: Path) -> bool:
    try:
        with zipfile.ZipFile(path) as archive:
            manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
    except (OSError, KeyError, json.JSONDecodeError, zipfile.BadZipFile):
        return False
    return manifest.get("kind") == "olm_runtime_trace_request_package"


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    pending_path = repo / "refs" / "reports" / "pending_runtime_trace_packages.json"
    project_staging_dir = repo / "refs" / "share_staging" / "20260707_windows_send_first"
    share_staging_dir = Path("/Volumes/onmk/olm_pr/new")
    staging_dir = share_staging_dir if share_staging_dir.is_dir() else project_staging_dir
    readme_candidates = [staging_dir / "README.md", *sorted(staging_dir.glob("*README*.txt"))]
    readme_path = next((path for path in readme_candidates if path.is_file()), None)

    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    rows = [row for row in pending.get("requests", []) if isinstance(row, dict) and row.get("status") == "pending"]
    rows.sort(key=lambda row: (int(row.get("priority") or 999999), str(row.get("request_id") or "")))
    if not rows:
        staged_zips = [path for path in sorted(staging_dir.glob("*.zip")) if is_runtime_request_package(path)]
        if staged_zips:
            print(f"[FAIL] no pending runtime trace requests, but stale staged zips remain: {[path.name for path in staged_zips]}")
            return 1
        print("[OK] Windows Send First staging has no pending runtime trace zip")
        return 0

    send_first = rows[0]
    package_rel = Path(send_first["package"])
    package_path = repo / package_rel
    expected_name = package_path.name
    staged_zips = [path for path in sorted(staging_dir.glob("*.zip")) if is_runtime_request_package(path)]
    matching_zips = [path for path in staged_zips if path.name == expected_name or path.name.endswith(f"__{expected_name}")]
    if len(staged_zips) != 1 or len(matching_zips) != 1:
        print(f"[FAIL] staged zips mismatch: got {[path.name for path in staged_zips]}, expected one matching {expected_name}")
        return 1
    staged_zip = matching_zips[0]
    if sha256(staged_zip) != sha256(package_path):
        print(f"[FAIL] staged zip hash mismatch: {staged_zip}")
        return 1

    # The NAS exchange contract keeps new/ zip-only. Project-local staging keeps
    # the human-readable sidecar and therefore still validates its contents.
    if staging_dir == project_staging_dir:
        if readme_path is None:
            print("[FAIL] project-local staging README is missing")
            return 1
        readme = readme_path.read_text(encoding="utf-8")
        required_needles = [send_first["request_id"], expected_name, sha256(package_path)]
        for needle in required_needles:
            if needle not in readme:
                print(f"[FAIL] README missing current Send First detail: {needle}")
                return 1

    print(f"[OK] Windows Send First staging matches {send_first['request_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
