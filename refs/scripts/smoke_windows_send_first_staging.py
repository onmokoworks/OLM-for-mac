#!/usr/bin/env python3
"""Smoke-test the project-local Windows Send First staging folder.

The staging folder is a human handoff surface, so it is easy for the README and
the zip payload to drift apart. Every staged runtime request must map to a
pending row. Project-local staging must contain the highest-priority request;
the NAS may retain an already-active lower-priority exchange until it returns.
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
            basenames = {
                name.replace("\\", "/").split("/")[-1]
                for name in archive.namelist()
            }
            if basenames.intersection({
                "RETURN_RUNTIME_TRACE_RESULT.json",
                "RETURN_RUNTIME_TRACE.json",
                "AE_RUNTIME_TRACE_RESULT.json",
            }):
                return False
            candidates = [
                name for name in archive.namelist()
                if name == "runtime_trace_package_manifest.json"
                or name.endswith("/runtime_trace_package_manifest.json")
            ]
            if len(candidates) != 1:
                return False
            manifest = json.loads(archive.read(candidates[0]))
    except (OSError, KeyError, json.JSONDecodeError, zipfile.BadZipFile):
        return False
    return manifest.get("kind") == "olm_runtime_trace_request_package"


def runtime_request_ids(path: Path) -> set[str]:
    try:
        with zipfile.ZipFile(path) as archive:
            candidates = [
                name for name in archive.namelist()
                if name.replace("\\", "/").split("/")[-1] == "runtime_trace_package_manifest.json"
            ]
            if len(candidates) != 1:
                return set()
            manifest = json.loads(archive.read(candidates[0]).decode("utf-8-sig"))
    except (OSError, KeyError, json.JSONDecodeError, zipfile.BadZipFile):
        return set()
    ids = set()
    direct = manifest.get("request_id")
    if isinstance(direct, str):
        ids.add(direct)
    for action in manifest.get("runtime_actions", []):
        if isinstance(action, dict) and isinstance(action.get("request_id"), str):
            ids.add(action["request_id"])
    return ids


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
    expected_ids = {str(send_first.get("request_id") or "")}
    require_send_first = staging_dir == project_staging_dir
    matching_zips = [
        path for path in staged_zips
        if expected_ids.intersection(runtime_request_ids(path))
        or (require_send_first and (path.name == expected_name or path.name.endswith(f"__{expected_name}")))
    ]
    if require_send_first and len(matching_zips) != 1:
        print(f"[FAIL] staged zips mismatch: got {[path.name for path in staged_zips]}, expected a matching {expected_name}")
        return 1
    if not staged_zips:
        print("[FAIL] pending runtime trace requests exist, but staging has no runtime zip")
        return 1

    for staged_zip in staged_zips:
        matching_rows = []
        staged_ids = runtime_request_ids(staged_zip)
        if not require_send_first and not staged_ids:
            print(f"[FAIL] NAS runtime zip has no manifest request_id: {staged_zip.name}")
            return 1
        for row in rows:
            pending_package = repo / Path(row["package"])
            row_ids = {str(row.get("request_id") or "")}
            name_match = staged_zip.name == pending_package.name or staged_zip.name.endswith(f"__{pending_package.name}")
            identity_match = row_ids.intersection(staged_ids)
            if identity_match or (require_send_first and name_match):
                matching_rows.append((row, pending_package))
        if len(matching_rows) != 1:
            print(f"[FAIL] staged runtime zip is not uniquely pending: {staged_zip.name}")
            return 1
        _, pending_package = matching_rows[0]
        if sha256(staged_zip) != sha256(pending_package):
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
        if "## Why This One\n\n- \n" in readme or "{'note':" in readme:
            print("[FAIL] README contains an empty reason or raw hard-lane mapping")
            return 1

    mode = "send-first" if require_send_first else "active-NAS-exchange"
    print(f"[OK] Windows staging mode={mode} contains {len(staged_zips)} pending runtime package(s); queue head={send_first['request_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
