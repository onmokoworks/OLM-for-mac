#!/usr/bin/env python3
"""Fail-closed intake for a one-click Windows witness batch return."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_JOB_STATUS = {"answered", "failed"}
COMMON_IDENTITY_FIELDS = ("run_id", "ae_pid", "module_base", "aex_sha256", "project_bpc", "renderer", "case_id")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def canonical_member(name: str) -> str:
    require(isinstance(name, str) and bool(name), f"unsafe ZIP member: {name!r}")
    normalized = name.replace("\\", "/")
    require(not normalized.startswith("/"), f"unsafe ZIP member: {name!r}")
    path = PurePosixPath(normalized)
    require(all(part not in ("", ".", "..") for part in path.parts), f"unsafe ZIP member: {name!r}")
    require(not (path.parts and ":" in path.parts[0]), f"unsafe ZIP member: {name!r}")
    return path.as_posix()


def read_archive(path: Path) -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(path) as archive:
            return read_zip_members(archive, f"{path}")
    except zipfile.BadZipFile as exc:
        raise ValueError(f"invalid ZIP: {path}") from exc


def read_zip_members(archive: zipfile.ZipFile, label: str) -> dict[str, bytes]:
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
    return files


def one_by_basename(files: dict[str, bytes], basename: str) -> tuple[str, bytes]:
    matches = [(name, data) for name, data in files.items() if PurePosixPath(name).name == basename]
    require(len(matches) == 1, f"expected exactly one {basename}")
    return matches[0]


def one_by_suffix(files: dict[str, bytes], relative_path: str) -> tuple[str, bytes]:
    matches = [(name, data) for name, data in files.items() if name == relative_path or name.endswith("/" + relative_path)]
    require(len(matches) == 1, f"expected exactly one {relative_path}")
    return matches[0]


def load_json_bytes(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON: {label}") from exc
    require(isinstance(value, dict), f"JSON is not an object: {label}")
    return value


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def optional_text(value: object) -> str | None:
    return value if isinstance(value, str) and bool(value) else None


def safe_relative(value: object, label: str) -> str:
    require(isinstance(value, str), f"{label} is missing")
    return canonical_member(value)


def case_archive_path(value: str, case_id: str) -> str:
    return value.replace("{case_id}", case_id)


def require_empty_list_field(row: dict[str, Any], field: str, label: str) -> None:
    require(field in row, f"{label} is missing")
    require(row[field] == [], f"{label} must be an empty array")


def verify_recorded_file(
    files: dict[str, bytes],
    archive_path: str,
    expected_sha: object,
    expected_size: object,
    label: str,
) -> bytes:
    _, data = one_by_suffix(files, archive_path)
    require(isinstance(expected_sha, str) and SHA256_RE.fullmatch(expected_sha) is not None, f"{label} SHA-256 is invalid")
    require(digest(data) == expected_sha, f"{label} SHA-256 mismatch: {archive_path}")
    require(isinstance(expected_size, int) and not isinstance(expected_size, bool), f"{label} size is invalid")
    require(len(data) == expected_size, f"{label} size mismatch: {archive_path}")
    return data


def parse_request_package(data: bytes, label: str) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = read_zip_members(archive, label)
    except zipfile.BadZipFile as exc:
        raise ValueError(f"{label} is not a valid job ZIP") from exc

    _, manifest_bytes = one_by_basename(members, "package-manifest.json")
    manifest = load_json_bytes(manifest_bytes, f"{label}:package-manifest.json")
    manifest_request_id = optional_text(manifest.get("request_id"))
    require(manifest_request_id is not None, f"{label} package-manifest.json request_id is missing")
    contract_path = safe_relative(manifest.get("contract"), f"{label} package-manifest.json contract")
    _, contract_bytes = one_by_suffix(members, contract_path)
    contract = load_json_bytes(contract_bytes, f"{label}:{contract_path}")
    contract_request_id = optional_text(contract.get("request_id"))
    require(contract_request_id is not None, f"{label} witness-contract request_id is missing")
    require(contract_request_id == manifest_request_id, f"{label} request_id contract mismatch")

    plugin = contract.get("plugin")
    require(isinstance(plugin, dict), f"{label} witness-contract plugin is missing")
    aex_sha256 = optional_text(plugin.get("aex_sha256"))
    require(aex_sha256 is not None and SHA256_RE.fullmatch(aex_sha256) is not None, f"{label} witness-contract plugin.aex_sha256 is invalid")

    project = contract.get("project")
    require(isinstance(project, dict), f"{label} witness-contract project is missing")
    bits_per_channel = project.get("bits_per_channel")
    require(isinstance(bits_per_channel, int) and not isinstance(bits_per_channel, bool), f"{label} witness-contract project.bits_per_channel is invalid")
    renderer = optional_text(project.get("renderer"))
    require(renderer is not None, f"{label} witness-contract project.renderer is missing")

    validation = contract.get("validation")
    require(isinstance(validation, dict), f"{label} witness-contract validation is missing")
    identity_fields = validation.get("identity_fields")
    require(isinstance(identity_fields, list), f"{label} witness-contract validation.identity_fields is invalid")
    normalized_identity_fields: set[str] = set()
    for index, field in enumerate(identity_fields):
        require(isinstance(field, str) and field, f"{label} witness-contract validation.identity_fields[{index}] is invalid")
        normalized_identity_fields.add(field)
    require(set(COMMON_IDENTITY_FIELDS) <= normalized_identity_fields, f"{label} witness-contract validation.identity_fields is incomplete")

    cases = contract.get("cases")
    require(isinstance(cases, list) and cases, f"{label} witness-contract cases are missing")
    case_ids: set[str] = set()
    case_keys: set[str] = set()
    required_exports: set[str] = set()
    export_keys: set[str] = set()
    for case_index, case in enumerate(cases):
        require(isinstance(case, dict), f"{label} witness-contract cases[{case_index}] is invalid")
        case_id = optional_text(case.get("id"))
        require(case_id is not None, f"{label} witness-contract cases[{case_index}].id is missing")
        require(case_id.casefold() not in case_keys, f"{label} witness-contract duplicate case id: {case_id}")
        case_keys.add(case_id.casefold())
        case_ids.add(case_id)
        exports = case.get("exports", [])
        require(isinstance(exports, list), f"{label} witness-contract {case_id}.exports is invalid")
        for export_index, export in enumerate(exports):
            require(isinstance(export, dict), f"{label} witness-contract {case_id}.exports[{export_index}] is invalid")
            archive_path = case_archive_path(
                safe_relative(export.get("archive_path"), f"{label} witness-contract {case_id}.exports[{export_index}].archive_path"),
                case_id,
            )
            require(archive_path.casefold() not in export_keys, f"{label} witness-contract duplicate export: {archive_path}")
            export_keys.add(archive_path.casefold())
            if export.get("required") is True:
                required_exports.add(archive_path)

    return {
        "request_id": manifest_request_id,
        "aex_sha256": aex_sha256,
        "project_bpc": bits_per_channel,
        "renderer": renderer,
        "case_ids": case_ids,
        "required_exports": required_exports,
    }


def verify_inner_return(data: bytes, label: str, request_contract: dict[str, Any]) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = read_zip_members(archive, label)
    except zipfile.BadZipFile as exc:
        raise ValueError(f"{label} is not a valid inner return ZIP") from exc

    root_statuses: list[dict[str, Any]] = []
    for name, member in members.items():
        if len(PurePosixPath(name).parts) != 1 or not name.lower().endswith(".json"):
            continue
        try:
            value = load_json_bytes(member, f"{label}:{name}")
        except ValueError:
            continue
        if value.get("status") in ("answered", "exact_bind_failure") and value.get("request_id"):
            root_statuses.append(value)
    require(len(root_statuses) == 1, f"{label} must contain exactly one terminal root status JSON")
    status = root_statuses[0]
    require(optional_text(status.get("request_id")) == request_contract["request_id"], f"{label} request_id mismatch")
    seen_artifacts: set[str] = set()
    for group in ("artifacts", "logs"):
        require(group in status, f"{label} {group} is missing")
        rows = status[group]
        require(isinstance(rows, list), f"{label} {group} is not an array")
        seen: set[str] = set()
        for index, row in enumerate(rows):
            require(isinstance(row, dict), f"{label} {group}[{index}] is not an object")
            path = safe_relative(row.get("archive_path"), f"{label} {group}[{index}].archive_path")
            require(path.casefold() not in seen, f"{label} duplicate recorded member: {path}")
            seen.add(path.casefold())
            verify_recorded_file(members, path, row.get("sha256"), row.get("size_bytes"), f"{label} {group}[{index}]")
            if group == "artifacts":
                seen_artifacts.add(path.casefold())

    if status.get("status") == "exact_bind_failure":
        failure = status.get("failure")
        require(isinstance(failure, dict), f"{label} failure is missing")
        require(optional_text(failure.get("stage")) is not None, f"{label} failure.stage is missing")
        require(optional_text(failure.get("reason")) is not None, f"{label} failure.reason is missing")
        return status

    missing_required_exports = sorted(
        archive_path for archive_path in request_contract["required_exports"] if archive_path.casefold() not in seen_artifacts
    )
    require(not missing_required_exports, f"{label} missing required export(s): {', '.join(missing_required_exports)}")

    run = status.get("run")
    require(isinstance(run, dict), f"{label} run is missing")
    run_id = optional_text(run.get("run_id"))
    require(run_id is not None, f"{label} run.run_id is missing")
    ae_pid = run.get("ae_pid")
    require(isinstance(ae_pid, int) and not isinstance(ae_pid, bool), f"{label} run.ae_pid is invalid")
    module_base = optional_text(run.get("module_base"))
    require(module_base is not None, f"{label} run.module_base is missing")
    run_aex_sha256 = optional_text(run.get("aex_sha256"))
    require(run_aex_sha256 is not None and SHA256_RE.fullmatch(run_aex_sha256) is not None, f"{label} run.aex_sha256 is invalid")
    require(run_aex_sha256 == request_contract["aex_sha256"], f"{label} run.aex_sha256 mismatch")
    project_bits_per_channel = run.get("project_bits_per_channel")
    require(
        isinstance(project_bits_per_channel, int) and not isinstance(project_bits_per_channel, bool),
        f"{label} run.project_bits_per_channel is invalid",
    )
    require(project_bits_per_channel == request_contract["project_bpc"], f"{label} run.project_bits_per_channel mismatch")
    run_renderer = optional_text(run.get("renderer"))
    require(run_renderer is not None, f"{label} run.renderer is missing")
    require(run_renderer == request_contract["renderer"], f"{label} run.renderer mismatch")

    events = status.get("events")
    require(isinstance(events, list) and events, f"{label} events are missing")
    expected_identity = {
        "run_id": run_id,
        "ae_pid": str(ae_pid),
        "module_base": module_base.casefold(),
        "aex_sha256": run_aex_sha256.casefold(),
        "project_bpc": str(project_bits_per_channel),
        "renderer": run_renderer,
    }
    case_ids = {case_id.casefold(): case_id for case_id in request_contract["case_ids"]}
    for index, row in enumerate(events):
        require(isinstance(row, dict), f"{label} events[{index}] is not an object")
        require(optional_text(row.get("event")) is not None, f"{label} events[{index}].event is missing")
        require(optional_text(row.get("prefix")) is not None, f"{label} events[{index}].prefix is missing")
        fields = row.get("fields")
        require(isinstance(fields, dict), f"{label} events[{index}].fields is invalid")
        for field, expected in expected_identity.items():
            value = optional_text(fields.get(field))
            require(value is not None, f"{label} events[{index}].fields.{field} is missing")
            actual = value.casefold() if field in ("module_base", "aex_sha256") else value
            require(actual == expected, f"{label} events[{index}] identity mismatch: {field}")
        case_id = optional_text(fields.get("case_id"))
        require(case_id is not None, f"{label} events[{index}].fields.case_id is missing")
        require(case_id.casefold() in case_ids, f"{label} events[{index}] case_id is undeclared")
    return status


def verify_request_batch_members(manifest: dict[str, Any], request_files: dict[str, bytes]) -> dict[tuple[int, str], dict[str, Any]]:
    jobs = manifest.get("jobs")
    require(isinstance(jobs, list) and jobs, "request jobs are missing")
    expected_request_contracts: dict[tuple[int, str], dict[str, Any]] = {}
    for index, job in enumerate(jobs):
        require(isinstance(job, dict), f"request job[{index}] is invalid")
        order = job.get("order")
        job_id = job.get("id")
        require(isinstance(order, int) and order == index + 1, f"request job[{index}] order mismatch")
        require(isinstance(job_id, str) and bool(job_id), f"request job[{index}] id missing")
        archive_path = safe_relative(job.get("archive_path"), f"{job_id} archive_path")
        require(archive_path.startswith("jobs/") and archive_path.lower().endswith(".zip"), f"{job_id} archive_path is invalid")
        package_sha = job.get("package_sha256")
        require(isinstance(package_sha, str) and SHA256_RE.fullmatch(package_sha) is not None, f"{job_id} package SHA invalid")
        job_bytes = verify_recorded_file(request_files, archive_path, package_sha, job.get("size_bytes"), f"{job_id} request package")
        request_contract = parse_request_package(job_bytes, f"{job_id} request package")
        inner_request_id = request_contract["request_id"]
        declared_request_id = optional_text(job.get("request_id"))
        if declared_request_id is not None:
            require(declared_request_id == inner_request_id, f"{job_id} request_id contract mismatch")
        satisfies = job.get("satisfies_request_ids", [inner_request_id])
        require(isinstance(satisfies, list) and satisfies, f"{job_id} satisfies_request_ids is invalid")
        seen_satisfied: set[str] = set()
        for alias_index, alias in enumerate(satisfies):
            require(isinstance(alias, str) and alias, f"{job_id} satisfies_request_ids[{alias_index}] is invalid")
            folded = alias.casefold()
            require(folded not in seen_satisfied, f"{job_id} has duplicate satisfies_request_id: {alias}")
            seen_satisfied.add(folded)
        require(inner_request_id.casefold() in seen_satisfied, f"{job_id} satisfies_request_ids omits its own request_id")
        expected_request_contracts[(order, job_id)] = request_contract
    return expected_request_contracts


def validate_batch(files: dict[str, bytes], request_files: dict[str, bytes] | None) -> dict[str, Any]:
    _, return_bytes = one_by_basename(files, "windows_witness_batch_return.json")
    _, manifest_bytes = one_by_basename(files, "batch-manifest.json")
    one_by_basename(files, "windows_witness_batch_launcher.log")
    returned = load_json_bytes(return_bytes, "windows_witness_batch_return.json")
    manifest = load_json_bytes(manifest_bytes, "batch-manifest.json")
    request_job_contracts: dict[tuple[int, str], dict[str, Any]] = {}
    if request_files is not None:
        _, request_manifest = one_by_basename(request_files, "batch-manifest.json")
        require(request_manifest == manifest_bytes, "returned batch manifest differs from request package")
        request_job_contracts = verify_request_batch_members(manifest, request_files)

    require(returned.get("schema_version") == 1, "return schema_version mismatch")
    require(returned.get("kind") == "windows_witness_batch_return", "return kind mismatch")
    require(manifest.get("schema_version") == 1, "manifest schema_version mismatch")
    require(manifest.get("kind") == "windows_witness_batch_request", "manifest kind mismatch")
    require(returned.get("batch_id") == manifest.get("batch_id"), "batch_id mismatch")
    require(returned.get("manifest_sha256") == digest(manifest_bytes), "manifest SHA-256 mismatch")
    require(returned.get("status") in ("answered", "partial_success"), "invalid overall status")

    requested_jobs = manifest.get("jobs")
    returned_jobs = returned.get("jobs")
    require(isinstance(requested_jobs, list) and requested_jobs, "request jobs are missing")
    require(isinstance(returned_jobs, list) and len(returned_jobs) == len(requested_jobs), "return job count mismatch")
    normalized: list[dict[str, Any]] = []
    required_failures = 0
    legacy_unbound_jobs = 0
    for index, (request, result) in enumerate(zip(requested_jobs, returned_jobs)):
        require(isinstance(request, dict) and isinstance(result, dict), f"job[{index}] is invalid")
        order = request.get("order")
        job_id = request.get("id")
        require(isinstance(order, int) and order == index + 1, f"job[{index}] order mismatch")
        require(isinstance(job_id, str) and bool(job_id), f"job[{index}] id missing")
        require(result.get("order") == order and result.get("id") == job_id, f"job[{index}] identity mismatch")
        package_sha = request.get("package_sha256")
        require(isinstance(package_sha, str) and SHA256_RE.fullmatch(package_sha) is not None, f"{job_id} package SHA invalid")
        require(result.get("package_sha256") == package_sha, f"{job_id} package SHA contract mismatch")
        request_contract = request_job_contracts.get((order, job_id))
        expected_request_id = request_contract["request_id"] if request_contract is not None else optional_text(request.get("request_id"))
        legacy_unbound = request_files is None and expected_request_id is None
        legacy_unbound_jobs += int(legacy_unbound)
        status = result.get("status")
        require(status in ALLOWED_JOB_STATUS, f"{job_id} status is invalid")
        if bool(request.get("required")) and status != "answered":
            required_failures += 1

        job_prefix = f"jobs/{order:03d}_{job_id}/"
        evidence = result.get("evidence")
        require(isinstance(evidence, list), f"{job_id} evidence is missing")
        evidence_paths: set[str] = set()
        verified_zips: list[dict[str, Any]] = []
        observed_request_ids: set[str] = set()
        for evidence_index, row in enumerate(evidence):
            require(isinstance(row, dict), f"{job_id} evidence[{evidence_index}] is invalid")
            relative = safe_relative(row.get("path"), f"{job_id} evidence[{evidence_index}].path")
            require(relative.casefold() not in evidence_paths, f"{job_id} duplicate evidence path: {relative}")
            evidence_paths.add(relative.casefold())
            archive_path = job_prefix + relative
            data = verify_recorded_file(files, archive_path, row.get("sha256"), row.get("size_bytes"), f"{job_id} evidence[{evidence_index}]")
            relative_lower = "/" + relative.lower()
            if relative_lower.endswith(".zip") and (
                "/work/" in relative_lower or PurePosixPath(relative).name.lower().startswith("return")
            ):
                require(request_contract is not None, f"{job_id} request contract is missing")
                inner_status = verify_inner_return(data, f"{job_id}:{relative}", request_contract)
                inner_request_id = optional_text(inner_status.get("request_id"))
                require(inner_request_id is not None, f"{job_id}:{relative} request_id is missing")
                if expected_request_id is not None:
                    require(inner_request_id == expected_request_id, f"{job_id}:{relative} request_id mismatch")
                if status == "answered":
                    require(inner_status.get("status") == "answered", f"{job_id}:{relative} is not an answered return")
                else:
                    require(inner_status.get("status") == "exact_bind_failure", f"{job_id}:{relative} contradicts failed job status")
                observed_request_ids.add(inner_request_id)
                verified_zips.append(inner_status)

        statuses = result.get("returned_statuses")
        require(isinstance(statuses, list), f"{job_id} returned_statuses is missing")
        answered_status_count = 0
        status_paths: set[str] = set()
        for status_index, row in enumerate(statuses):
            require(isinstance(row, dict), f"{job_id} returned_statuses[{status_index}] is invalid")
            relative = safe_relative(row.get("path"), f"{job_id} returned_statuses[{status_index}].path")
            require(relative.casefold() not in status_paths, f"{job_id} duplicate returned_statuses path: {relative}")
            status_paths.add(relative.casefold())
            archive_path = job_prefix + relative
            _, status_bytes = one_by_suffix(files, archive_path)
            require(digest(status_bytes) == row.get("sha256"), f"{job_id} status SHA mismatch: {relative}")
            status_json = load_json_bytes(status_bytes, f"{job_id}:{relative}")
            actual_status = status_json.get("status")
            require(actual_status == row.get("status"), f"{job_id} status JSON mismatch: {relative}")
            status_request_id = optional_text(status_json.get("request_id"))
            if expected_request_id is not None:
                require(status_request_id == expected_request_id, f"{job_id} status request_id mismatch: {relative}")
            elif status_request_id is not None:
                observed_request_ids.add(status_request_id)
            answered_status_count += int(actual_status == "answered")
        if observed_request_ids:
            require(len(observed_request_ids) == 1, f"{job_id} mixes request_id values across returned evidence")

        if status == "answered":
            require(result.get("exit_code") == 0, f"{job_id} answered with nonzero exit")
            require(result.get("failure") in (None, ""), f"{job_id} answered with a failure reason")
            require(result.get("observed_package_sha256") == package_sha, f"{job_id} observed package SHA mismatch")
            require_empty_list_field(result, "afterfx_before", f"{job_id} afterfx_before")
            require_empty_list_field(result, "afterfx_after", f"{job_id} afterfx_after")
            require_empty_list_field(result, "cdb_before", f"{job_id} cdb_before")
            require_empty_list_field(result, "cdb_after", f"{job_id} cdb_after")
            require(answered_status_count > 0, f"{job_id} has no answered status JSON")
            require(bool(verified_zips), f"{job_id} has no verified inner return ZIP")
        else:
            require(optional_text(result.get("failure")) is not None, f"{job_id} failed without a failure reason")
            require(answered_status_count == 0, f"{job_id} failed but carries an answered status JSON")
        normalized.append({
            "order": order,
            "id": job_id,
            "required": bool(request.get("required")),
            "status": status,
            "evidence_files": len(evidence),
            "verified_inner_returns": len(verified_zips),
            "request_id_bound": expected_request_id is not None,
        })

    expected_return_status = "answered" if required_failures == 0 else "partial_success"
    require(returned.get("status") == expected_return_status, "overall status does not match required job outcomes")
    accepted_status = "answered" if required_failures == 0 and legacy_unbound_jobs == 0 else "partial_success"
    return {
        "schema_version": 1,
        "classification": "accepted_all_answered" if accepted_status == "answered" else "accepted_partial_evidence",
        "batch_id": manifest["batch_id"],
        "status": accepted_status,
        "job_count": len(normalized),
        "required_failures": required_failures,
        "legacy_unbound_jobs": legacy_unbound_jobs,
        "jobs": normalized,
    }


def write_report(path: Path | None, value: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("return_zip", type=Path)
    parser.add_argument("--request-batch", type=Path, required=True)
    parser.add_argument("--allow-partial-evidence", action="store_true")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--require-all-answered", action="store_true")
    args = parser.parse_args()
    try:
        report = validate_batch(read_archive(args.return_zip), read_archive(args.request_batch) if args.request_batch else None)
    except (OSError, ValueError) as exc:
        report = {"schema_version": 1, "classification": "blocked_invalid_evidence", "reason": str(exc)}
        write_report(args.output_json, report)
        print(json.dumps(report, indent=2), file=sys.stderr)
        return 2
    if report["status"] != "answered" and not args.allow_partial_evidence:
        report = dict(report)
        report["classification"] = "blocked_partial_evidence"
        report["reason"] = "partial batch evidence requires --allow-partial-evidence"
        write_report(args.output_json, report)
        print(json.dumps(report, indent=2), file=sys.stderr)
        return 2
    write_report(args.output_json, report)
    print(json.dumps(report, indent=2))
    if args.require_all_answered and report["status"] != "answered":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
