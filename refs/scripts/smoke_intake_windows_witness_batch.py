#!/usr/bin/env python3
"""Smoke-test fail-closed Windows witness batch intake."""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INTAKE = ROOT / "scripts/intake_windows_witness_batch.py"
FIXED = (2026, 1, 1, 0, 0, 0)
AEX_SHA256 = "a" * 64
MODULE_BASE = "0x10000000"
MISSING = object()


def packed(files: dict[str, bytes]) -> bytes:
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, FIXED)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return target.getvalue()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def request_package(
    request_id: str,
    case_id: str,
    *,
    artifact_path: str | None = None,
    aex_sha256: str = AEX_SHA256,
    bits_per_channel: int = 16,
    renderer: str = "Software",
) -> bytes:
    artifact_path = artifact_path or f"exports/{case_id}.bin"
    contract = {
        "request_id": request_id,
        "plugin": {"aex_sha256": aex_sha256},
        "project": {"bits_per_channel": bits_per_channel, "renderer": renderer},
        "cases": [{"id": case_id, "exports": [{"archive_path": artifact_path, "required": True}]}],
        "validation": {
            "identity_fields": ["run_id", "ae_pid", "module_base", "aex_sha256", "project_bpc", "renderer", "case_id"]
        },
    }
    manifest = {
        "contract": "witness-contract.json",
        "entrypoint": "artifacts/run_witness.ps1",
        "kind": "windows_witness_generated_package",
        "request_id": request_id,
        "schema_version": 1,
    }
    return packed(
        {
            "artifacts/run_witness.ps1": b"Write-Host synthetic witness\n",
            "witness-contract.json": canonical(contract),
            "package-manifest.json": canonical(manifest),
        }
    )


def inner_return(
    request_id: str,
    case_id: str,
    payload: bytes,
    *,
    artifact_path: str | None = None,
    status_request_id: str | None = None,
    run_overrides: dict[str, object] | None = None,
    event_field_overrides: dict[str, str] | None = None,
    artifacts: object = MISSING,
    logs: object = MISSING,
    events: object = MISSING,
    include_payload: bool = True,
) -> bytes:
    artifact_path = artifact_path or f"exports/{case_id}.bin"
    run = {
        "run_id": f"run_{request_id}",
        "ae_pid": 4242,
        "module_base": MODULE_BASE,
        "aex_sha256": AEX_SHA256,
        "project_bits_per_channel": 16,
        "renderer": "Software",
    }
    if run_overrides:
        run.update(run_overrides)
    fields = {
        "run_id": str(run["run_id"]),
        "ae_pid": str(run["ae_pid"]),
        "module_base": str(run["module_base"]),
        "aex_sha256": str(run["aex_sha256"]),
        "project_bpc": str(run["project_bits_per_channel"]),
        "renderer": str(run["renderer"]),
        "case_id": case_id,
        "sample": "synthetic",
        "value": "1",
    }
    if event_field_overrides:
        fields.update(event_field_overrides)
    artifact = {"archive_path": artifact_path, "sha256": sha256(payload), "size_bytes": len(payload)}
    status: dict[str, object] = {
        "schema_version": 1,
        "status": "answered",
        "request_id": status_request_id or request_id,
    }
    if run is not MISSING:
        status["run"] = run
    if events is MISSING:
        status["events"] = [{"event": "capture", "prefix": "SYNTH_CAPTURE", "fields": fields}]
    elif events is not None:
        status["events"] = events
    if artifacts is MISSING:
        status["artifacts"] = [artifact]
    elif artifacts is not None:
        status["artifacts"] = artifacts
    if logs is MISSING:
        status["logs"] = []
    elif logs is not None:
        status["logs"] = logs

    members = {"RETURN.json": canonical(status)}
    if include_payload:
        members[artifact_path] = payload
    return packed(members)


def inner_failure_return(request_id: str) -> bytes:
    log = b"synthetic readiness failure\n"
    status = {
        "schema_version": 1,
        "status": "exact_bind_failure",
        "request_id": request_id,
        "failure": {
            "stage": "readiness",
            "reason": "ready marker missing",
            "missing_fields": ["ready.marker"],
            "last_observation": "",
        },
        "artifacts": [],
        "logs": [{"archive_path": "logs/afterfx.txt", "sha256": sha256(log), "size_bytes": len(log)}],
    }
    return packed({"RETURN.json": canonical(status), "logs/afterfx.txt": log})


def build_fixture(
    root: Path,
    *,
    answered_second: bool,
    include_manifest_request_ids: bool = True,
    inner_request_id_overrides: dict[str, str] | None = None,
    status_request_id_overrides: dict[str, str] | None = None,
    job_result_overrides: dict[str, dict[str, object]] | None = None,
    satisfies_overrides: dict[str, list[str]] | None = None,
    inner_return_overrides: dict[str, dict[str, object]] | None = None,
    return_member_separator: str | None = None,
) -> tuple[Path, Path]:
    inner_request_id_overrides = inner_request_id_overrides or {}
    status_request_id_overrides = status_request_id_overrides or {}
    job_result_overrides = job_result_overrides or {}
    satisfies_overrides = satisfies_overrides or {}
    inner_return_overrides = inner_return_overrides or {}
    jobs = []
    result_jobs = []
    request_files: dict[str, bytes] = {}
    return_files: dict[str, bytes] = {"windows_witness_batch_launcher.log": b"batch log\n"}
    for order, job_id in ((1, "first"), (2, "second")):
        request_id = f"request_{job_id}"
        case_id = f"case_{job_id}"
        package_bytes = request_package(request_id, case_id)
        archive_path = f"jobs/{order:03d}_{job_id}.zip"
        job = {
            "archive_path": archive_path,
            "entrypoint": "artifacts/run_witness.ps1",
            "id": job_id,
            "order": order,
            "package_sha256": sha256(package_bytes),
            "required": True,
            "size_bytes": len(package_bytes),
        }
        if include_manifest_request_ids:
            job["request_id"] = request_id
            job["satisfies_request_ids"] = satisfies_overrides.get(job_id, [request_id])
        jobs.append(job)
        request_files[f"windows_witness_batch_20260713/{archive_path}"] = package_bytes

        answered = order == 1 or answered_second
        prefix = f"jobs/{order:03d}_{job_id}/"
        evidence = []
        statuses = []
        if answered:
            inner_request_id = inner_request_id_overrides.get(job_id, request_id)
            status_request_id = status_request_id_overrides.get(job_id, request_id)
            inner = inner_return(
                inner_request_id,
                case_id,
                f"payload-{job_id}".encode("utf-8"),
                status_request_id=status_request_id,
                **inner_return_overrides.get(job_id, {}),
            )
            inner_path = "package/work/RETURN.zip"
            status_body = {"schema_version": 1, "status": "answered", "request_id": status_request_id}
            status_data = canonical(status_body)
            status_path = "package/work/validation_status.json"
            auxiliary_path = f"package/work/ae_result_{case_id}.json"
            auxiliary_data = canonical({
                "kind": "olm_ae_single_case_result",
                "case_id": case_id,
                "status": "ok",
                "request_id": "",
            })
            return_files[prefix + inner_path] = inner
            return_files[prefix + status_path] = status_data
            return_files[prefix + auxiliary_path] = auxiliary_data
            evidence.extend(
                [
                    {"path": inner_path, "sha256": sha256(inner), "size_bytes": len(inner)},
                    {"path": status_path, "sha256": sha256(status_data), "size_bytes": len(status_data)},
                    {"path": auxiliary_path, "sha256": sha256(auxiliary_data), "size_bytes": len(auxiliary_data)},
                ]
            )
            statuses.append({"path": status_path, "status": "answered", "sha256": sha256(status_data)})
            statuses.append({"path": auxiliary_path, "status": "ok", "sha256": sha256(auxiliary_data)})
        else:
            inner = inner_failure_return(request_id)
            inner_path = "package/work/RETURN.zip"
            status_body = {
                "schema_version": 1,
                "status": "exact_bind_failure",
                "request_id": request_id,
                "failure": {"stage": "readiness", "reason": "ready marker missing"},
            }
            status_data = canonical(status_body)
            status_path = "package/work/validation_status.json"
            return_files[prefix + inner_path] = inner
            return_files[prefix + status_path] = status_data
            evidence.extend(
                [
                    {"path": inner_path, "sha256": sha256(inner), "size_bytes": len(inner)},
                    {"path": status_path, "sha256": sha256(status_data), "size_bytes": len(status_data)},
                ]
            )
            statuses.append({"path": status_path, "status": "exact_bind_failure", "sha256": sha256(status_data)})
        result = {
            "order": order,
            "id": job_id,
            "required": True,
            "status": "answered" if answered else "failed",
            "package_sha256": job["package_sha256"],
            "observed_package_sha256": job["package_sha256"],
            "entrypoint": "artifacts/run_witness.ps1",
            "exit_code": 0 if answered else 2,
            "afterfx_before": [],
            "afterfx_after": [],
            "cdb_before": [],
            "cdb_after": [],
            "failure": None if answered else "synthetic failure",
            "returned_statuses": statuses,
            "evidence": evidence,
        }
        result.update(job_result_overrides.get(job_id, {}))
        result_jobs.append(result)

    manifest = {
        "batch_id": "windows_witness_batch_20260713",
        "jobs": jobs,
        "kind": "windows_witness_batch_request",
        "launcher": "run_windows_witness_batch.ps1",
        "schema_version": 1,
        "success_status": "answered",
        "failure_status": "partial_success",
    }
    manifest_data = canonical(manifest)
    returned = {
        "schema_version": 1,
        "kind": "windows_witness_batch_return",
        "batch_id": manifest["batch_id"],
        "status": "answered" if answered_second else "partial_success",
        "manifest_sha256": sha256(manifest_data),
        "jobs": result_jobs,
    }
    request_files["windows_witness_batch_20260713/batch-manifest.json"] = manifest_data
    request_files["windows_witness_batch_20260713/run_windows_witness_batch.ps1"] = b"launcher"
    normalized_return_files = {
        (name.replace("/", return_member_separator) if return_member_separator is not None else name): data
        for name, data in return_files.items()
    }
    normalized_return_files["batch-manifest.json"] = manifest_data
    normalized_return_files["windows_witness_batch_return.json"] = canonical(returned)
    request_zip = root / "request.zip"
    return_zip = root / "return.zip"
    request_zip.write_bytes(packed(request_files))
    return_zip.write_bytes(packed(normalized_return_files))
    return request_zip, return_zip


def rewrite_member(path: Path, target_name: str, replacement: bytes) -> Path:
    with zipfile.ZipFile(path) as archive:
        files = {info.filename: archive.read(info) for info in archive.infolist() if not info.is_dir()}
    files[target_name] = replacement
    rewritten = path.with_name(f"{path.stem}_rewritten{path.suffix}")
    rewritten.write_bytes(packed(files))
    return rewritten


def rename_member(path: Path, target_name: str, replacement_name: str) -> Path:
    with zipfile.ZipFile(path) as archive:
        files = {info.filename: archive.read(info) for info in archive.infolist() if not info.is_dir()}
    files[replacement_name] = files.pop(target_name)
    rewritten = path.with_name(f"{path.stem}_renamed{path.suffix}")
    rewritten.write_bytes(packed(files))
    return rewritten


def run(
    path: Path,
    request: Path | None = None,
    *,
    allow_partial: bool = False,
    require_all: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(INTAKE), str(path)]
    if request is not None:
        command.extend(["--request-batch", str(request)])
    if allow_partial:
        command.append("--allow-partial-evidence")
    if require_all:
        command.append("--require-all-answered")
    return subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def stdout_json(proc: subprocess.CompletedProcess[str]) -> dict[str, object]:
    return json.loads(proc.stdout)


def stderr_json(proc: subprocess.CompletedProcess[str]) -> dict[str, object]:
    return json.loads(proc.stderr)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="windows_witness_batch_intake_") as tmp:
        root = Path(tmp)

        full_root = root / "full"
        full_root.mkdir()
        full_request, full_return = build_fixture(full_root, answered_second=True)
        full = run(full_return, full_request, require_all=True)
        assert full.returncode == 0, full.stderr
        full_json = stdout_json(full)
        assert full_json["classification"] == "accepted_all_answered"
        assert full_json["jobs"][0]["status"] == "answered"
        missing_request = run(full_return)
        assert missing_request.returncode == 2, missing_request.stderr
        assert "--request-batch" in missing_request.stderr

        backslash_root = root / "backslash"
        backslash_root.mkdir()
        backslash_request, backslash_return = build_fixture(
            backslash_root,
            answered_second=True,
            return_member_separator="\\",
        )
        backslash_result = run(backslash_return, backslash_request, require_all=True)
        assert backslash_result.returncode == 0, backslash_result.stderr
        assert stdout_json(backslash_result)["classification"] == "accepted_all_answered"

        traversal_return = rename_member(
            backslash_return,
            r"jobs\001_first\package\work\RETURN.zip",
            r"jobs\001_first\package\work\..\RETURN.zip",
        )
        traversal_result = run(traversal_return, backslash_request)
        assert traversal_result.returncode == 2, traversal_result.stderr
        traversal_json = stderr_json(traversal_result)
        assert traversal_json["classification"] == "blocked_invalid_evidence"
        assert "unsafe ZIP member" in str(traversal_json["reason"])

        partial_root = root / "partial"
        partial_root.mkdir()
        partial_request, partial_return = build_fixture(partial_root, answered_second=False)
        partial_default = run(partial_return, partial_request)
        assert partial_default.returncode == 2, partial_default.stderr
        assert stderr_json(partial_default)["classification"] == "blocked_partial_evidence"
        partial_allowed = run(partial_return, partial_request, allow_partial=True)
        assert partial_allowed.returncode == 0, partial_allowed.stderr
        assert stdout_json(partial_allowed)["classification"] == "accepted_partial_evidence"

        tampered_request_name = "windows_witness_batch_20260713/jobs/001_first.zip"
        tampered_request = rewrite_member(full_request, tampered_request_name, request_package("request_first", "case_first") + b"tampered")
        tampered_result = run(full_return, tampered_request)
        assert tampered_result.returncode == 2, tampered_result.stderr
        assert stderr_json(tampered_result)["classification"] == "blocked_invalid_evidence"

        wrong_id_root = root / "wrong_request_id"
        wrong_id_root.mkdir()
        wrong_request, wrong_return = build_fixture(
            wrong_id_root,
            answered_second=True,
            status_request_id_overrides={"second": "request_foreign"},
        )
        wrong_result = run(wrong_return, wrong_request)
        assert wrong_result.returncode == 2, wrong_result.stderr
        assert stderr_json(wrong_result)["classification"] == "blocked_invalid_evidence"

        bad_alias_root = root / "bad_satisfies"
        bad_alias_root.mkdir()
        bad_alias_request, bad_alias_return = build_fixture(
            bad_alias_root,
            answered_second=True,
            satisfies_overrides={"second": ["legacy_second_only"]},
        )
        bad_alias_result = run(bad_alias_return, bad_alias_request)
        assert bad_alias_result.returncode == 2, bad_alias_result.stderr
        bad_alias_json = stderr_json(bad_alias_result)
        assert bad_alias_json["classification"] == "blocked_invalid_evidence"
        assert "omits its own request_id" in str(bad_alias_json["reason"])

        dirty_cdb_root = root / "dirty_cdb"
        dirty_cdb_root.mkdir()
        dirty_request, dirty_return = build_fixture(
            dirty_cdb_root,
            answered_second=True,
            job_result_overrides={"second": {"cdb_after": [4816]}},
        )
        dirty_result = run(dirty_return, dirty_request)
        assert dirty_result.returncode == 2, dirty_result.stderr
        dirty_json = stderr_json(dirty_result)
        assert dirty_json["classification"] == "blocked_invalid_evidence"
        assert "cdb_after" in str(dirty_json["reason"])

        missing_export_root = root / "missing_export"
        missing_export_root.mkdir()
        missing_export_request, missing_export_return = build_fixture(
            missing_export_root,
            answered_second=True,
            inner_return_overrides={"second": {"artifacts": []}},
        )
        missing_export_result = run(missing_export_return, missing_export_request)
        assert missing_export_result.returncode == 2, missing_export_result.stderr
        missing_export_json = stderr_json(missing_export_result)
        assert missing_export_json["classification"] == "blocked_invalid_evidence"
        assert "missing required export" in str(missing_export_json["reason"])

        event_mismatch_root = root / "event_mismatch"
        event_mismatch_root.mkdir()
        event_mismatch_request, event_mismatch_return = build_fixture(
            event_mismatch_root,
            answered_second=True,
            inner_return_overrides={"second": {"event_field_overrides": {"renderer": "GPU"}}},
        )
        event_mismatch_result = run(event_mismatch_return, event_mismatch_request)
        assert event_mismatch_result.returncode == 2, event_mismatch_result.stderr
        event_mismatch_json = stderr_json(event_mismatch_result)
        assert event_mismatch_json["classification"] == "blocked_invalid_evidence"
        assert "identity mismatch: renderer" in str(event_mismatch_json["reason"])

    print("[OK] Windows witness batch intake is fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
