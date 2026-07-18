#!/usr/bin/env python3
"""Smoke-test the Windows Send First staging surfaces.

The project-local staging folder remains the human handoff surface for the
legacy single-request runtime package workflow. The NAS `new/` surface may now
contain either those legacy runtime request zips or a unified outer Windows
witness batch request zip. The NAS validation stays fail-closed: only a
structurally valid request artifact counts, and every claimed pending request
must bind exactly.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


WINDOWS_WITNESS_BATCH_KIND = "windows_witness_batch_request"
WINDOWS_WITNESS_BATCH_MANIFEST_NAME = "batch-manifest.json"
WINDOWS_WITNESS_BATCH_README = "README.txt"
WINDOWS_WITNESS_BATCH_ONE_CLICK = "RUN_WINDOWS_WITNESS_BATCH.cmd"
WINDOWS_WITNESS_BATCH_LAUNCHER = "run_windows_witness_batch.ps1"
WINDOWS_WITNESS_GENERATED_PACKAGE_KIND = "windows_witness_generated_package"
EXCHANGE_SPLIT_SUBDIRS = ("mac_requests", "windows_processing", "mac_returns")


def validate_safe_id(value: Any, label: str) -> str:
    require(isinstance(value, str) and value, f"{label} is missing")
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    require(value not in {".", ".."} and all(char in allowed for char in value), f"unsafe {label}: {value!r}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def canonical_member(name: str) -> str:
    require(bool(name), f"unsafe ZIP member: {name!r}")
    normalized = name.replace("\\", "/")
    require(not normalized.startswith("/"), f"unsafe ZIP member: {name!r}")
    path = PurePosixPath(normalized)
    require(all(part not in ("", ".", "..") for part in path.parts), f"unsafe ZIP member: {name!r}")
    require(not (path.parts and ":" in path.parts[0]), f"unsafe ZIP member: {name!r}")
    return path.as_posix()


def load_json_bytes(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON: {label}") from exc
    require(isinstance(value, dict), f"JSON is not an object: {label}")
    return value


def read_zip_members(path: Path) -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(path) as archive:
            files: dict[str, bytes] = {}
            folded: set[str] = set()
            for info in archive.infolist():
                if info.is_dir():
                    continue
                name = canonical_member(info.filename)
                key = name.casefold()
                require(key not in folded, f"{path.name} has duplicate Windows ZIP member: {name}")
                folded.add(key)
                files[name] = archive.read(info)
    except (OSError, zipfile.BadZipFile) as exc:
        raise ValueError(f"invalid ZIP: {path.name}") from exc
    return files


def find_unique_by_basename(files: dict[str, bytes], basename: str) -> tuple[str, bytes] | None:
    matches = [(name, data) for name, data in files.items() if PurePosixPath(name).name == basename]
    if not matches:
        return None
    require(len(matches) == 1, f"expected exactly one {basename}")
    return matches[0]


def runtime_request_manifest(path: Path) -> dict[str, Any] | None:
    try:
        files = read_zip_members(path)
        entry = find_unique_by_basename(files, "runtime_trace_package_manifest.json")
        if entry is None:
            return None
        return load_json_bytes(entry[1], f"{path.name}:runtime_trace_package_manifest.json") if entry else None
    except (OSError, UnicodeError, json.JSONDecodeError, zipfile.BadZipFile):
        return None
    except ValueError as exc:
        if str(exc).startswith("invalid ZIP:"):
            return None
        raise


def parse_runtime_request_package(path: Path) -> dict[str, Any] | None:
    manifest = runtime_request_manifest(path)
    if not isinstance(manifest, dict) or manifest.get("kind") != "olm_runtime_trace_request_package":
        return None
    try:
        with zipfile.ZipFile(path) as archive:
            basenames = {
                name.replace("\\", "/").split("/")[-1]
                for name in archive.namelist()
            }
    except (OSError, zipfile.BadZipFile):
        return None
    if basenames.intersection({
        "RETURN_RUNTIME_TRACE_RESULT.json",
        "RETURN_RUNTIME_TRACE.json",
        "AE_RUNTIME_TRACE_RESULT.json",
    }):
        return None
    ids = set()
    direct = manifest.get("request_id")
    if isinstance(direct, str) and direct:
        ids.add(direct)
    for action in manifest.get("runtime_actions", []):
        if isinstance(action, dict) and isinstance(action.get("request_id"), str) and action["request_id"]:
            ids.add(action["request_id"])
    return {"manifest": manifest, "path": path, "request_ids": ids}


def parse_windows_witness_generated_package(path: Path) -> dict[str, Any] | None:
    """Parse a compiler-generated package without weakening its file contract."""
    try:
        with zipfile.ZipFile(path) as archive:
            root_manifest = [info for info in archive.infolist() if info.filename == "package-manifest.json"]
            if not root_manifest:
                # A foreign archive may contain a package-manifest.json as an
                # ordinary nested payload. It is not ours to validate.
                return None
            require(len(root_manifest) == 1, f"{path.name} has duplicate root package-manifest.json")
            root_manifest_data = load_json_bytes(
                archive.read(root_manifest[0]), f"{path.name}:package-manifest.json"
            )
            if root_manifest_data.get("kind") != WINDOWS_WITNESS_GENERATED_PACKAGE_KIND:
                return None
    except (OSError, zipfile.BadZipFile):
        return None
    try:
        files = read_zip_members(path)
    except ValueError as exc:
        if str(exc).startswith("invalid ZIP:"):
            return None
        raise
    manifest_entry = find_unique_by_basename(files, "package-manifest.json")
    if manifest_entry is None:
        return None
    manifest_name, manifest_bytes = manifest_entry
    require(manifest_name == "package-manifest.json", f"{path.name} package manifest must be at ZIP root")
    manifest = load_json_bytes(manifest_bytes, f"{path.name}:{manifest_name}")
    if manifest.get("kind") != WINDOWS_WITNESS_GENERATED_PACKAGE_KIND:
        return None
    require(manifest.get("schema_version") == 1, f"{path.name} package schema_version mismatch")
    request_id = validate_safe_id(manifest.get("request_id"), f"{path.name} package request_id")

    def package_member(value: Any, label: str) -> str:
        require(isinstance(value, str) and value, f"{path.name} package {label} is missing")
        member = canonical_member(value)
        require(member == value, f"{path.name} package {label} must be canonical")
        return member

    contract_name = package_member(manifest.get("contract"), "contract")
    entrypoint_name = package_member(manifest.get("entrypoint"), "entrypoint")
    require(contract_name == "witness-contract.json", f"{path.name} package contract path mismatch")
    require(entrypoint_name == "artifacts/run_witness.ps1", f"{path.name} package entrypoint path mismatch")
    require(contract_name in files, f"{path.name} package contract is missing: {contract_name}")
    require(entrypoint_name in files, f"{path.name} package entrypoint is missing: {entrypoint_name}")
    request_manifest_name = "request/request_manifest.json"
    require(request_manifest_name in files, f"{path.name} package request manifest is missing: {request_manifest_name}")
    contract = load_json_bytes(files[contract_name], f"{path.name}:{contract_name}")
    require(contract.get("request_id") == request_id, f"{path.name} contract request_id mismatch")
    request_manifest = load_json_bytes(files[request_manifest_name], f"{path.name}:{request_manifest_name}")
    require(request_manifest.get("request_id") == request_id, f"{path.name} request manifest request_id mismatch")

    inventory = manifest.get("files")
    require(isinstance(inventory, list) and inventory, f"{path.name} package files are missing")
    listed: set[str] = set()
    for index, item in enumerate(inventory, start=1):
        require(isinstance(item, dict), f"{path.name} package files[{index}] is invalid")
        member = package_member(item.get("path"), f"files[{index}].path")
        key = member.casefold()
        require(key not in listed, f"{path.name} package has duplicate file: {member}")
        listed.add(key)
        require(member in files, f"{path.name} package file is missing: {member}")
        digest = item.get("sha256")
        require(isinstance(digest, str) and len(digest) == 64 and all(ch in "0123456789abcdef" for ch in digest), f"{path.name} package files[{index}].sha256 is invalid")
        size = item.get("size_bytes")
        require(isinstance(size, int) and not isinstance(size, bool) and size >= 0, f"{path.name} package files[{index}].size_bytes is invalid")
        require(len(files[member]) == size, f"{path.name} package file size mismatch: {member}")
        require(sha256_bytes(files[member]) == digest, f"{path.name} package file SHA-256 mismatch: {member}")

    actual = {name.casefold() for name in files if name != manifest_name}
    require(actual == listed, f"{path.name} package file inventory mismatch")
    return {"manifest": manifest, "path": path, "request_ids": {request_id}, "package_kind": WINDOWS_WITNESS_GENERATED_PACKAGE_KIND}


def parse_staged_request_package(path: Path) -> dict[str, Any] | None:
    """Recognize both legacy runtime requests and generated witness packages."""
    generated = parse_windows_witness_generated_package(path)
    if generated is not None:
        return generated
    try:
        with zipfile.ZipFile(path) as archive:
            has_nested_package_manifest = any(
                info.filename.replace("\\", "/") != "package-manifest.json"
                and PurePosixPath(info.filename.replace("\\", "/")).name == "package-manifest.json"
                for info in archive.infolist()
                if not info.is_dir()
            )
    except (OSError, zipfile.BadZipFile):
        has_nested_package_manifest = False
    if has_nested_package_manifest:
        return None
    return parse_runtime_request_package(path)


def inner_job_request_id(data: bytes, label: str) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            files: dict[str, bytes] = {}
            folded: set[str] = set()
            for info in archive.infolist():
                if info.is_dir():
                    continue
                name = canonical_member(info.filename)
                key = name.casefold()
                require(key not in folded, f"{label} has duplicate Windows ZIP member: {name}")
                folded.add(key)
                files[name] = archive.read(info)
    except zipfile.BadZipFile as exc:
        raise ValueError(f"{label} is not a valid inner job ZIP") from exc
    manifest_entry = find_unique_by_basename(files, "package-manifest.json")
    require(manifest_entry is not None, f"{label} is missing package-manifest.json")
    _, manifest_bytes = manifest_entry
    manifest = load_json_bytes(manifest_bytes, f"{label}:package-manifest.json")
    request_id = manifest.get("request_id")
    require(isinstance(request_id, str) and request_id, f"{label} package-manifest.json request_id is missing")
    return request_id


def parse_windows_witness_batch(path: Path) -> dict[str, Any]:
    files = read_zip_members(path)
    basenames = {PurePosixPath(name).name for name in files}
    manifest_entry = find_unique_by_basename(files, WINDOWS_WITNESS_BATCH_MANIFEST_NAME)
    require(manifest_entry is not None, f"{path.name} is missing {WINDOWS_WITNESS_BATCH_MANIFEST_NAME}")
    one_click_entry = find_unique_by_basename(files, WINDOWS_WITNESS_BATCH_ONE_CLICK)
    readme_entry = find_unique_by_basename(files, WINDOWS_WITNESS_BATCH_README)
    launcher_entry = find_unique_by_basename(files, WINDOWS_WITNESS_BATCH_LAUNCHER)
    require(one_click_entry is not None, f"{path.name} is missing {WINDOWS_WITNESS_BATCH_ONE_CLICK}")
    require(readme_entry is not None, f"{path.name} is missing {WINDOWS_WITNESS_BATCH_README}")
    require(launcher_entry is not None, f"{path.name} is missing {WINDOWS_WITNESS_BATCH_LAUNCHER}")
    manifest_name, manifest_bytes = manifest_entry
    manifest = load_json_bytes(manifest_bytes, f"{path.name}:{manifest_name}")
    require(manifest.get("kind") == WINDOWS_WITNESS_BATCH_KIND, f"{path.name} manifest kind mismatch")
    require(manifest.get("schema_version") == 1, f"{path.name} manifest schema_version mismatch")
    require(manifest.get("one_click_launcher") == WINDOWS_WITNESS_BATCH_ONE_CLICK, f"{path.name} one_click_launcher mismatch")
    require(manifest.get("readme") == WINDOWS_WITNESS_BATCH_README, f"{path.name} readme mismatch")
    require(manifest.get("launcher") == WINDOWS_WITNESS_BATCH_LAUNCHER, f"{path.name} launcher mismatch")
    batch_id = manifest.get("batch_id")
    require(isinstance(batch_id, str) and batch_id, f"{path.name} batch_id is missing")

    prefix = PurePosixPath(manifest_name).parent
    for required_name, entry in (
        (WINDOWS_WITNESS_BATCH_ONE_CLICK, one_click_entry),
        (WINDOWS_WITNESS_BATCH_README, readme_entry),
        (WINDOWS_WITNESS_BATCH_LAUNCHER, launcher_entry),
    ):
        require(entry is not None, f"{path.name} is missing {required_name}")
        entry_name, _ = entry
        require(PurePosixPath(entry_name).parent == prefix, f"{path.name} {required_name} is outside the batch root")

    jobs = manifest.get("jobs")
    require(isinstance(jobs, list) and jobs, f"{path.name} jobs are missing")
    seen_job_ids: set[str] = set()
    seen_request_ids: set[str] = set()
    seen_archive_paths: set[str] = set()
    request_ids: list[str] = []
    satisfied_request_ids: set[str] = set()
    for index, job in enumerate(jobs, start=1):
        require(isinstance(job, dict), f"{path.name} job[{index}] is invalid")
        order = job.get("order")
        job_id = job.get("id")
        request_id = job.get("request_id")
        archive_path = job.get("archive_path")
        package_sha256 = job.get("package_sha256")
        size_bytes = job.get("size_bytes")
        require(order == index, f"{path.name} job[{index}] order mismatch")
        job_id = validate_safe_id(job_id, f"{path.name} job[{index}] id")
        require(job_id.casefold() not in seen_job_ids, f"{path.name} duplicate job id: {job_id}")
        seen_job_ids.add(job_id.casefold())
        request_id = validate_safe_id(request_id, f"{path.name} job {job_id} request_id")
        require(request_id.casefold() not in seen_request_ids, f"{path.name} duplicate request_id: {request_id}")
        seen_request_ids.add(request_id.casefold())
        require(isinstance(archive_path, str) and archive_path, f"{path.name} job {job_id} archive_path is missing")
        archive_path = canonical_member(archive_path)
        require(archive_path.startswith("jobs/") and archive_path.lower().endswith(".zip"), f"{path.name} job {job_id} archive_path is invalid")
        require(archive_path.casefold() not in seen_archive_paths, f"{path.name} duplicate archive_path: {archive_path}")
        seen_archive_paths.add(archive_path.casefold())
        require(isinstance(package_sha256, str) and len(package_sha256) == 64 and all(ch in "0123456789abcdef" for ch in package_sha256), f"{path.name} job {job_id} package_sha256 is invalid")
        require(isinstance(size_bytes, int) and not isinstance(size_bytes, bool), f"{path.name} job {job_id} size_bytes is invalid")
        member_name = (prefix / archive_path).as_posix() if prefix.parts else archive_path
        require(member_name in files, f"{path.name} job {job_id} payload is missing: {archive_path}")
        payload = files[member_name]
        require(len(payload) == size_bytes, f"{path.name} job {job_id} size mismatch")
        require(sha256_bytes(payload) == package_sha256, f"{path.name} job {job_id} SHA-256 mismatch")
        require(inner_job_request_id(payload, f"{path.name}:{archive_path}") == request_id, f"{path.name} job {job_id} inner request_id mismatch")
        request_ids.append(request_id)
        raw_satisfies = job.get("satisfies_request_ids")
        if raw_satisfies is None:
            job_satisfied_ids = [request_id]
        else:
            require(isinstance(raw_satisfies, list) and raw_satisfies, f"{path.name} job {job_id} satisfies_request_ids is invalid")
            job_satisfied_ids = []
            seen_satisfied_ids: set[str] = set()
            for alias_index, alias in enumerate(raw_satisfies, start=1):
                alias_id = validate_safe_id(alias, f"{path.name} job {job_id} satisfies_request_ids[{alias_index}]")
                require(alias_id.casefold() not in seen_satisfied_ids, f"{path.name} job {job_id} duplicate satisfies_request_id: {alias_id}")
                seen_satisfied_ids.add(alias_id.casefold())
                job_satisfied_ids.append(alias_id)
            require(request_id.casefold() in seen_satisfied_ids, f"{path.name} job {job_id} satisfies_request_ids omits own request_id")
        satisfied_request_ids.update(job_satisfied_ids)

    hints = {
        WINDOWS_WITNESS_BATCH_MANIFEST_NAME,
        WINDOWS_WITNESS_BATCH_ONE_CLICK,
        WINDOWS_WITNESS_BATCH_LAUNCHER,
        WINDOWS_WITNESS_BATCH_README,
        "windows_witness_batch_return.json",
    }
    require(basenames.intersection(hints), f"{path.name} does not look like a Windows witness batch")
    return {
        "batch_id": batch_id,
        "path": path,
        "request_ids": request_ids,
        "satisfied_request_ids": sorted(satisfied_request_ids),
    }


def canonical_windows_witness_batch_path(repo: Path, batch_id: str) -> Path | None:
    canonical_path = repo / "refs" / "runtime_trace_packages" / f"{batch_id}.zip"
    return canonical_path if canonical_path.is_file() else None


def looks_like_windows_witness_batch(path: Path) -> bool:
    lowered = path.name.lower()
    if "witness_batch" in lowered:
        return True
    try:
        with zipfile.ZipFile(path) as archive:
            basenames = {
                name.replace("\\", "/").split("/")[-1]
                for name in archive.namelist()
            }
    except (OSError, zipfile.BadZipFile):
        return False
    return bool(basenames.intersection({
        WINDOWS_WITNESS_BATCH_MANIFEST_NAME,
        WINDOWS_WITNESS_BATCH_README,
        WINDOWS_WITNESS_BATCH_ONE_CLICK,
        WINDOWS_WITNESS_BATCH_LAUNCHER,
        "windows_witness_batch_return.json",
    }))


def parse_windows_witness_batch_return(path: Path) -> dict[str, Any] | None:
    files = read_zip_members(path)
    return_entry = find_unique_by_basename(files, "windows_witness_batch_return.json")
    if return_entry is None:
        return None
    manifest_entry = find_unique_by_basename(files, WINDOWS_WITNESS_BATCH_MANIFEST_NAME)
    launcher_log = find_unique_by_basename(files, "windows_witness_batch_launcher.log")
    require(manifest_entry is not None, f"{path.name} return is missing {WINDOWS_WITNESS_BATCH_MANIFEST_NAME}")
    require(launcher_log is not None, f"{path.name} return is missing windows_witness_batch_launcher.log")
    request_launchers = {
        WINDOWS_WITNESS_BATCH_README,
        WINDOWS_WITNESS_BATCH_ONE_CLICK,
        WINDOWS_WITNESS_BATCH_LAUNCHER,
    }
    basenames = {PurePosixPath(name).name for name in files}
    require(not basenames.intersection(request_launchers), f"{path.name} ambiguously contains request and return launchers")
    _, return_bytes = return_entry
    _, manifest_bytes = manifest_entry
    returned = load_json_bytes(return_bytes, f"{path.name}:windows_witness_batch_return.json")
    manifest = load_json_bytes(manifest_bytes, f"{path.name}:{WINDOWS_WITNESS_BATCH_MANIFEST_NAME}")
    require(returned.get("schema_version") == 1, f"{path.name} return schema_version mismatch")
    require(returned.get("kind") == "windows_witness_batch_return", f"{path.name} return kind mismatch")
    require(manifest.get("schema_version") == 1, f"{path.name} returned manifest schema_version mismatch")
    require(manifest.get("kind") == WINDOWS_WITNESS_BATCH_KIND, f"{path.name} returned manifest kind mismatch")
    require(returned.get("batch_id") == manifest.get("batch_id"), f"{path.name} return batch_id mismatch")
    require(returned.get("manifest_sha256") == sha256_bytes(manifest_bytes), f"{path.name} return manifest SHA-256 mismatch")
    requested_jobs = manifest.get("jobs")
    returned_jobs = returned.get("jobs")
    require(isinstance(requested_jobs, list) and requested_jobs, f"{path.name} returned manifest jobs are missing")
    require(isinstance(returned_jobs, list) and len(returned_jobs) == len(requested_jobs), f"{path.name} return job count mismatch")
    return {"batch_id": manifest.get("batch_id"), "path": path, "status": returned.get("status")}


def split_exchange_layout(staging_dir: Path) -> tuple[Path, ...] | None:
    lanes = tuple(staging_dir / name for name in EXCHANGE_SPLIT_SUBDIRS if (staging_dir / name).is_dir())
    return lanes or None


def staging_zip_paths(staging_dir: Path) -> list[Path]:
    split_lanes = split_exchange_layout(staging_dir)
    if split_lanes is None:
        return sorted(path for path in staging_dir.glob("*.zip") if path.is_file())
    zip_paths: list[Path] = []
    for lane in split_lanes:
        zip_paths.extend(path for path in sorted(lane.glob("*.zip")) if path.is_file())
    return zip_paths


def refresh_project_send_first_staging(repo: Path, staging_dir: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            "scripts/materialize_windows_send_first_staging.py",
            "--staging-dir",
            str(staging_dir),
        ],
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def validate_project_send_first(rows: list[dict[str, Any]], staging_dir: Path, repo: Path, readme_path: Path | None) -> tuple[bool, str]:
    send_first = rows[0]
    package_rel = Path(send_first["package"])
    package_path = repo / package_rel
    expected_name = package_path.name
    staged_packages = [
        package for path in sorted(staging_dir.glob("*.zip"))
        if (package := parse_staged_request_package(path)) is not None
    ]
    expected_ids = {str(send_first.get("request_id") or "")}
    matching = [
        package for package in staged_packages
        if expected_ids.intersection(package["request_ids"])
        or package["path"].name == expected_name
        or package["path"].name.endswith(f"__{expected_name}")
    ]
    if len(matching) != 1:
        return False, f"[FAIL] staged zips mismatch: got {[package['path'].name for package in staged_packages]}, expected a matching {expected_name}"
    for package in staged_packages:
        staged_zip = package["path"]
        staged_ids = package["request_ids"]
        matching_rows = []
        for row in rows:
            pending_package = repo / Path(row["package"])
            row_ids = {str(row.get("request_id") or "")}
            name_match = staged_zip.name == pending_package.name or staged_zip.name.endswith(f"__{pending_package.name}")
            identity_match = row_ids.intersection(staged_ids)
            if identity_match or name_match:
                matching_rows.append((row, pending_package))
        if len(matching_rows) != 1:
            return False, f"[FAIL] staged runtime zip is not uniquely pending: {staged_zip.name}"
        _, pending_package = matching_rows[0]
        if sha256(staged_zip) != sha256(pending_package):
            return False, f"[FAIL] staged zip hash mismatch: {staged_zip}"
    if readme_path is None:
        return False, "[FAIL] project-local staging README is missing"
    readme = readme_path.read_text(encoding="utf-8")
    required_needles = [send_first["request_id"], expected_name, sha256(package_path)]
    for needle in required_needles:
        if needle not in readme:
            return False, f"[FAIL] README missing current Send First detail: {needle}"
    if "## Why This One\n\n- \n" in readme or "{'note':" in readme:
        return False, "[FAIL] README contains an empty reason or raw hard-lane mapping"
    return True, f"[OK] Windows staging mode=send-first contains {len(staged_packages)} pending runtime package(s); queue head={send_first['request_id']}"


def validate_nas_staging(rows: list[dict[str, Any]], staging_dir: Path, repo: Path) -> tuple[bool, str]:
    zip_paths = staging_zip_paths(staging_dir)
    staged_runtime_packages = []
    staged_batches = []
    staged_returns = []
    covered_pending_ids: set[str] = set()
    pending_by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        request_id = row.get("request_id")
        if isinstance(request_id, str) and request_id:
            require(request_id not in pending_by_id, f"duplicate pending request_id: {request_id}")
            pending_by_id[request_id] = row

    for path in zip_paths:
        if looks_like_windows_witness_batch(path):
            try:
                returned_batch = parse_windows_witness_batch_return(path)
                if returned_batch is not None:
                    staged_returns.append(returned_batch)
                    continue
                batch = parse_windows_witness_batch(path)
            except ValueError as exc:
                return False, f"[FAIL] invalid NAS unified batch {path.name}: {exc}"
            canonical_path = canonical_windows_witness_batch_path(repo, batch["batch_id"])
            if canonical_path is None:
                return False, (
                    "[FAIL] NAS unified batch has no repo canonical request: "
                    f"batch_id={batch['batch_id']} staged={path}"
                )
            staged_sha256 = sha256(path)
            canonical_sha256 = sha256(canonical_path)
            if staged_sha256 != canonical_sha256:
                return False, (
                    "[FAIL] NAS unified batch canonical mismatch: "
                    f"staged {path} sha256={staged_sha256}, "
                    f"canonical {canonical_path} sha256={canonical_sha256}"
                )
            claimed_pending_ids = {request_id for request_id in batch["satisfied_request_ids"] if request_id in pending_by_id}
            if not claimed_pending_ids:
                return False, f"[FAIL] NAS unified batch claims no currently pending request_id: {path.name}"
            duplicate_ids = covered_pending_ids.intersection(claimed_pending_ids)
            if duplicate_ids:
                dup_text = ", ".join(sorted(duplicate_ids))
                return False, f"[FAIL] staged request_id is duplicated across NAS artifacts: {dup_text}"
            covered_pending_ids.update(claimed_pending_ids)
            staged_batches.append((batch, claimed_pending_ids))
            continue

        package = parse_runtime_request_package(path)
        if package is None:
            continue
        staged_ids = package["request_ids"]
        if not staged_ids:
            return False, f"[FAIL] NAS runtime zip has no manifest request_id: {path.name}"
        matching_rows = []
        for row in rows:
            pending_package = repo / Path(row["package"])
            row_ids = {str(row.get("request_id") or "")}
            identity_match = row_ids.intersection(staged_ids)
            if identity_match:
                matching_rows.append((row, pending_package))
        if len(matching_rows) != 1:
            return False, f"[FAIL] staged runtime zip is not uniquely pending: {path.name}"
        row, pending_package = matching_rows[0]
        request_id = str(row.get("request_id") or "")
        if request_id in covered_pending_ids:
            return False, f"[FAIL] staged request_id is duplicated across NAS artifacts: {request_id}"
        covered_pending_ids.add(request_id)
        if sha256(path) != sha256(pending_package):
            return False, f"[FAIL] staged zip hash mismatch: {path}"
        staged_runtime_packages.append(package)

    if not staged_runtime_packages and not staged_batches and not staged_returns:
        return False, "[FAIL] pending runtime trace requests exist, but staging has no runtime zip or valid unified batch"

    batch_count = len(staged_batches)
    return_count = len(staged_returns)
    package_count = len(staged_runtime_packages)
    covered = sorted(covered_pending_ids)
    return True, (
        "[OK] Windows staging mode=active-NAS-exchange contains "
        f"{package_count} legacy runtime package(s), {batch_count} unified request batch(es), "
        f"and {return_count} verified return batch(es); "
        f"covered pending request_ids={covered}; queue head={rows[0]['request_id']}"
    )


def build_synthetic_witness_job_zip(path: Path, request_id: str) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, body in sorted({
            f"{request_id}/artifacts/run_witness.ps1": b"exit 0\n",
            f"{request_id}/package-manifest.json": (
                json.dumps({"contract": "witness-contract.json", "entrypoint": "artifacts/run_witness.ps1", "request_id": request_id}, sort_keys=True)
                + "\n"
            ).encode("ascii"),
            f"{request_id}/witness-contract.json": (
                json.dumps({"request_id": request_id, "return_bundle": {"json_name": "RETURN.json", "zip_name": "RETURN.zip"}}, sort_keys=True)
                + "\n"
            ).encode("ascii"),
        }.items()):
            archive.writestr(name, body)
    return path.read_bytes()


def build_synthetic_batch(
    path: Path,
    inner_name: str,
    inner_bytes: bytes,
    request_id: str,
    *,
    batch_id: str = "synthetic_windows_witness_batch_selftest_20260713",
    include_launchers: bool = True,
    satisfies_request_ids: list[str] | None = None,
) -> None:
    job_sha = sha256_bytes(inner_bytes)
    manifest = {
        "batch_id": batch_id,
        "jobs": [
            {
                "archive_path": f"jobs/{inner_name}",
                "id": request_id,
                "order": 1,
                "package_sha256": job_sha,
                "request_id": request_id,
                **({"satisfies_request_ids": satisfies_request_ids} if satisfies_request_ids is not None else {}),
                "size_bytes": len(inner_bytes),
            }
        ],
        "kind": WINDOWS_WITNESS_BATCH_KIND,
        "launcher": WINDOWS_WITNESS_BATCH_LAUNCHER,
        "one_click_launcher": WINDOWS_WITNESS_BATCH_ONE_CLICK,
        "readme": WINDOWS_WITNESS_BATCH_README,
        "schema_version": 1,
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        prefix = "windows_witness_batch_20260713"
        archive.writestr(f"{prefix}/{WINDOWS_WITNESS_BATCH_MANIFEST_NAME}", (json.dumps(manifest, sort_keys=True) + "\n").encode("ascii"))
        archive.writestr(f"{prefix}/jobs/{inner_name}", inner_bytes)
        if include_launchers:
            archive.writestr(f"{prefix}/{WINDOWS_WITNESS_BATCH_README}", b"README\n")
            archive.writestr(f"{prefix}/{WINDOWS_WITNESS_BATCH_ONE_CLICK}", b"@echo off\r\n")
            archive.writestr(f"{prefix}/{WINDOWS_WITNESS_BATCH_LAUNCHER}", b"exit 0\n")


def run_self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="smoke_windows_send_first_staging_") as raw:
        tmp = Path(raw)
        repo = tmp / "repo"
        staging = tmp / "staging"
        canonical_dir = repo / "refs" / "runtime_trace_packages"
        repo.mkdir()
        staging.mkdir()
        canonical_dir.mkdir(parents=True)

        repo_root = Path(__file__).resolve().parents[2]
        generated_fixture = repo_root / (
            "refs/runtime_trace_packages/"
            "windows_witness_olmdirectionalblur_writer_entry_20260716.zip"
        )
        legacy_fixture = repo_root / (
            "refs/runtime_trace_packages/"
            "olm_runtime_trace_olmblur_case0006_same_run_internal_20260713.zip"
        )
        generated = parse_staged_request_package(generated_fixture)
        require(generated is not None, "DirectionalBlur generated fixture was not recognized")
        require(
            generated["request_ids"] == {"olmdirectionalblur_writer_entry_20260716"},
            "generated fixture request identity drifted",
        )
        require(parse_staged_request_package(legacy_fixture) is not None, "legacy runtime fixture was not recognized")

        def write_generated_variant(
            destination: Path,
            *,
            request_manifest_id: str | None = None,
            contract_id: str | None = None,
            unsafe_member: str | None = None,
            digest_mismatch: bool = False,
            size_mismatch: bool = False,
            missing_member: str | None = None,
            extra_member: str | None = None,
        ) -> None:
            files = read_zip_members(generated_fixture)
            package_manifest = load_json_bytes(files["package-manifest.json"], "self-test package-manifest.json")
            if request_manifest_id is not None:
                request_manifest = load_json_bytes(files["request/request_manifest.json"], "self-test request_manifest.json")
                request_manifest["request_id"] = request_manifest_id
                files["request/request_manifest.json"] = (json.dumps(request_manifest, sort_keys=True) + "\n").encode("ascii")
            if contract_id is not None:
                contract = load_json_bytes(files["witness-contract.json"], "self-test witness-contract.json")
                contract["request_id"] = contract_id
                files["witness-contract.json"] = (json.dumps(contract, sort_keys=True) + "\n").encode("ascii")
            for item in package_manifest["files"]:
                member = item["path"]
                item["size_bytes"] = len(files[member])
                item["sha256"] = sha256_bytes(files[member])
            if digest_mismatch:
                package_manifest["files"][0]["sha256"] = "0" * 64
            if size_mismatch:
                package_manifest["files"][0]["size_bytes"] += 1
            if missing_member is not None:
                files.pop(missing_member)
            files.pop("package-manifest.json")
            with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                for name, data in sorted(files.items()):
                    archive.writestr(name, data)
                if unsafe_member is not None:
                    archive.writestr(unsafe_member, b"unsafe\n")
                if extra_member is not None:
                    archive.writestr(extra_member, b"extra\n")
                # Rewrite the manifest after all mutations so the intended
                # negative case is the contract failure under test.
                archive.writestr("package-manifest.json", (json.dumps(package_manifest, sort_keys=True) + "\n").encode("ascii"))

        def require_generated_failure(path: Path, needle: str, message: str) -> None:
            try:
                parse_staged_request_package(path)
            except ValueError as exc:
                require(needle in str(exc), f"unexpected {message} failure: {exc}")
            else:
                raise AssertionError(f"{message} must fail closed")

        unsafe_generated = tmp / "unsafe_generated.zip"
        write_generated_variant(unsafe_generated, unsafe_member="jobs/../request_manifest.json")
        try:
            parse_staged_request_package(unsafe_generated)
        except ValueError as exc:
            require("unsafe ZIP member" in str(exc), f"unexpected unsafe-member failure: {exc}")
        else:
            raise AssertionError("unsafe generated package must fail closed")

        digest_mismatch = tmp / "digest_mismatch.zip"
        write_generated_variant(digest_mismatch, digest_mismatch=True)
        require_generated_failure(digest_mismatch, "SHA-256 mismatch", "digest mismatch")

        size_mismatch = tmp / "size_mismatch.zip"
        write_generated_variant(size_mismatch, size_mismatch=True)
        require_generated_failure(size_mismatch, "size mismatch", "size mismatch")

        missing_listed = tmp / "missing_listed.zip"
        write_generated_variant(missing_listed, missing_member="README.md")
        require_generated_failure(missing_listed, "file is missing", "missing listed file")

        extra_canonical = tmp / "extra_canonical.zip"
        write_generated_variant(extra_canonical, extra_member="extra.txt")
        require_generated_failure(extra_canonical, "inventory mismatch", "extra canonical member")

        unrelated_nested = tmp / "unrelated_nested.zip"
        with zipfile.ZipFile(unrelated_nested, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("foreign/package-manifest.json", b'{"kind":"other_package"}\n')
            archive.writestr("jobs/../unsafe.txt", b"unsafe\n")
        require(parse_staged_request_package(unrelated_nested) is None, "unrelated nested package must be ignored")

        request_identity_mismatch = tmp / "request_identity_mismatch.zip"
        write_generated_variant(request_identity_mismatch, request_manifest_id="other_request")
        try:
            parse_staged_request_package(request_identity_mismatch)
        except ValueError as exc:
            require("request manifest request_id mismatch" in str(exc), f"unexpected request identity failure: {exc}")
        else:
            raise AssertionError("request manifest identity mismatch must fail closed")

        contract_identity_mismatch = tmp / "contract_identity_mismatch.zip"
        write_generated_variant(contract_identity_mismatch, contract_id="other_request")
        try:
            parse_staged_request_package(contract_identity_mismatch)
        except ValueError as exc:
            require("contract request_id mismatch" in str(exc), f"unexpected contract identity failure: {exc}")
        else:
            raise AssertionError("witness contract identity mismatch must fail closed")

        generated_staging = tmp / "generated_staging"
        generated_staging.mkdir()
        staged_generated = generated_staging / generated_fixture.name
        shutil.copy2(generated_fixture, staged_generated)
        generated_package_rel = Path("refs/runtime_trace_packages") / generated_fixture.name
        readme = generated_staging / "README.md"
        readme.write_text(
            "olmdirectionalblur_writer_entry_20260716\n"
            f"{generated_fixture.name}\n"
            f"{sha256(generated_fixture)}\n",
            encoding="utf-8",
        )
        ok, message = validate_project_send_first(
            [{"package": generated_package_rel.as_posix(), "request_id": "olmdirectionalblur_writer_entry_20260716"}],
            generated_staging,
            repo_root,
            readme,
        )
        require(ok, message)

        inner_path = tmp / "inner.zip"
        inner_bytes = build_synthetic_witness_job_zip(inner_path, "batch_pending_request")
        batch_path = staging / "olm_windows_witness_batch_test.zip"
        build_synthetic_batch(
            batch_path,
            "001_batch_pending_request.zip",
            inner_bytes,
            "batch_pending_request",
            satisfies_request_ids=["batch_pending_request", "legacy_queue_alias"],
        )
        (staging / "unrelated.zip").write_bytes(b"not a zip")
        unsafe_legacy = staging / "unsafe_legacy_request.zip"
        with zipfile.ZipFile(unsafe_legacy, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "jobs\\..\\runtime_trace_package_manifest.json",
                b'{"kind":"olm_runtime_trace_request_package"}\n',
            )
        try:
            runtime_request_manifest(unsafe_legacy)
        except ValueError:
            pass
        else:
            raise AssertionError("unsafe legacy request must fail closed")
        unsafe_legacy.unlink()
        ok, message = validate_nas_staging(
            [
                {"package": "unused.zip", "priority": 5, "request_id": "batch_pending_request", "status": "pending"},
                {"package": "unused.zip", "priority": 6, "request_id": "legacy_queue_alias", "status": "pending"},
            ],
            staging,
            repo,
        )
        require(not ok and "no repo canonical request" in message, f"unexpected unknown-batch mode: {message}")
        batch_path.unlink()

        pinned_batch_id = "synthetic_windows_witness_batch_pinned_selftest_20260713"
        pinned_batch = staging / "olm_windows_witness_batch_pinned_test.zip"
        build_synthetic_batch(
            pinned_batch,
            "001_batch_pending_request.zip",
            inner_bytes,
            "batch_pending_request",
            batch_id=pinned_batch_id,
        )
        canonical_batch = canonical_dir / f"{pinned_batch_id}.zip"
        canonical_batch.write_bytes(pinned_batch.read_bytes())
        ok, message = validate_nas_staging(
            [{"package": "unused.zip", "priority": 5, "request_id": "batch_pending_request", "status": "pending"}],
            staging,
            repo,
        )
        require(ok, message)
        returned_batch = staging / "olm_windows_witness_batch_pinned_test_RETURN.zip"
        pinned_files = read_zip_members(pinned_batch)
        pinned_manifest_entry = find_unique_by_basename(pinned_files, WINDOWS_WITNESS_BATCH_MANIFEST_NAME)
        require(pinned_manifest_entry is not None, "self-test request manifest missing")
        _, pinned_manifest_bytes = pinned_manifest_entry
        returned_status = {
            "schema_version": 1,
            "kind": "windows_witness_batch_return",
            "batch_id": pinned_batch_id,
            "status": "partial_success",
            "manifest_sha256": sha256_bytes(pinned_manifest_bytes),
            "jobs": [{"order": 1, "id": "batch_pending_request", "status": "failed"}],
        }
        with zipfile.ZipFile(returned_batch, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            archive.writestr("jobs\\001_batch_pending_request\\entrypoint_stdout.log", b"done\n")
            archive.writestr(WINDOWS_WITNESS_BATCH_MANIFEST_NAME, pinned_manifest_bytes)
            archive.writestr("windows_witness_batch_launcher.log", b"done\n")
            archive.writestr("windows_witness_batch_return.json", (json.dumps(returned_status, sort_keys=True) + "\n").encode("ascii"))
        ok, message = validate_nas_staging(
            [{"package": "unused.zip", "priority": 5, "request_id": "batch_pending_request", "status": "pending"}],
            staging,
            repo,
        )
        require(ok, message)
        returned_batch.unlink()
        pinned_batch.unlink()
        canonical_batch.unlink()

        mismatch_batch_id = "synthetic_windows_witness_batch_mismatch_selftest_20260713"
        mismatch_batch = staging / "olm_windows_witness_batch_mismatch_test.zip"
        build_synthetic_batch(
            mismatch_batch,
            "001_batch_pending_request.zip",
            inner_bytes,
            "batch_pending_request",
            batch_id=mismatch_batch_id,
        )
        mismatch_canonical = canonical_dir / f"{mismatch_batch_id}.zip"
        build_synthetic_batch(
            mismatch_canonical,
            "001_batch_pending_request.zip",
            inner_bytes + b"mismatch",
            "batch_pending_request",
            batch_id=mismatch_batch_id,
        )
        ok, message = validate_nas_staging(
            [{"package": "unused.zip", "priority": 5, "request_id": "batch_pending_request", "status": "pending"}],
            staging,
            repo,
        )
        require(not ok and "canonical mismatch" in message, f"unexpected canonical mismatch mode: {message}")
        mismatch_batch.unlink()
        mismatch_canonical.unlink()

        return_like = staging / "returned_windows_witness_batch.zip"
        build_synthetic_batch(return_like, "001_batch_pending_request.zip", inner_bytes, "batch_pending_request", include_launchers=False)
        ok, message = validate_nas_staging(
            [{"package": "unused.zip", "priority": 5, "request_id": "batch_pending_request", "status": "pending"}],
            staging,
            repo,
        )
        require(not ok and "invalid NAS unified batch" in message, f"unexpected failure mode: {message}")

        split_staging = tmp / "split_staging"
        for lane in EXCHANGE_SPLIT_SUBDIRS:
            (split_staging / lane).mkdir(parents=True, exist_ok=True)
        split_batch_id = "synthetic_windows_witness_batch_split_selftest_20260715"
        split_batch = split_staging / "mac_requests" / "olm_windows_witness_batch_split_test.zip"
        build_synthetic_batch(
            split_batch,
            "001_batch_pending_request.zip",
            inner_bytes,
            "batch_pending_request",
            batch_id=split_batch_id,
        )
        split_canonical = canonical_dir / f"{split_batch_id}.zip"
        split_canonical.write_bytes(split_batch.read_bytes())
        split_return = split_staging / "mac_returns" / "olm_windows_witness_batch_split_test_RETURN.zip"
        split_files = read_zip_members(split_batch)
        split_manifest_entry = find_unique_by_basename(split_files, WINDOWS_WITNESS_BATCH_MANIFEST_NAME)
        require(split_manifest_entry is not None, "split self-test request manifest missing")
        _, split_manifest_bytes = split_manifest_entry
        split_return_status = {
            "schema_version": 1,
            "kind": "windows_witness_batch_return",
            "batch_id": split_batch_id,
            "status": "partial_success",
            "manifest_sha256": sha256_bytes(split_manifest_bytes),
            "jobs": [{"order": 1, "id": "batch_pending_request", "status": "failed"}],
        }
        with zipfile.ZipFile(split_return, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            archive.writestr(WINDOWS_WITNESS_BATCH_MANIFEST_NAME, split_manifest_bytes)
            archive.writestr("windows_witness_batch_launcher.log", b"done\n")
            archive.writestr("windows_witness_batch_return.json", (json.dumps(split_return_status, sort_keys=True) + "\n").encode("ascii"))
        ok, message = validate_nas_staging(
            [{"package": "unused.zip", "priority": 5, "request_id": "batch_pending_request", "status": "pending"}],
            split_staging,
            repo,
        )
        require(ok, message)
    print("[OK] smoke_windows_send_first_staging self-test passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run a focused batch-validation self-test")
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()

    repo = Path(__file__).resolve().parents[2]
    pending_path = repo / "refs" / "reports" / "pending_runtime_trace_packages.json"
    project_staging_dir = repo / "refs" / "share_staging" / "20260707_windows_send_first"
    configured_share_root = os.environ.get("OLM_PR_SHARE_ROOT")
    mounted_share_dirs = sorted(Path("/Volumes").glob("*/olm_pr/new"))
    share_staging_dir = Path(configured_share_root) / "new" if configured_share_root else (
        mounted_share_dirs[0] if len(mounted_share_dirs) == 1 else project_staging_dir
    )
    staging_dir = share_staging_dir if share_staging_dir.is_dir() else project_staging_dir

    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    rows = [row for row in pending.get("requests", []) if isinstance(row, dict) and row.get("status") == "pending"]
    rows.sort(key=lambda row: (int(row.get("priority") or 999999), str(row.get("request_id") or "")))
    using_project_staging = staging_dir == project_staging_dir
    temporary_staging: tempfile.TemporaryDirectory[str] | None = None
    if using_project_staging:
        temporary_staging = tempfile.TemporaryDirectory(prefix="olm_send_first_smoke_")
        staging_dir = Path(temporary_staging.name)
        try:
            refresh_project_send_first_staging(repo, staging_dir)
        except subprocess.CalledProcessError as exc:
            output = (exc.stdout or "").strip()
            detail = f"\n{output}" if output else ""
            print(f"[FAIL] could not refresh project-local Send First staging{detail}")
            return 1

    readme_candidates = [staging_dir / "README.md", *sorted(staging_dir.glob("*README*.txt"))]
    readme_path = next((path for path in readme_candidates if path.is_file()), None)
    if not rows:
        stale_artifacts = []
        try:
            for path in staging_zip_paths(staging_dir):
                returned_batch = parse_windows_witness_batch_return(path) if looks_like_windows_witness_batch(path) else None
                if returned_batch is not None:
                    continue
                if parse_staged_request_package(path) is not None or looks_like_windows_witness_batch(path):
                    stale_artifacts.append(path.name)
        except ValueError as exc:
            print(f"[FAIL] {exc}")
            return 1
        if stale_artifacts:
            print(f"[FAIL] no pending runtime trace requests, but stale staged zips remain: {stale_artifacts}")
            return 1
        print("[OK] Windows Send First staging has no pending runtime trace zip")
        return 0

    try:
        if using_project_staging:
            ok, message = validate_project_send_first(rows, staging_dir, repo, readme_path)
        else:
            ok, message = validate_nas_staging(rows, staging_dir, repo)
    except ValueError as exc:
        print(f"[FAIL] {exc}")
        return 1
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
