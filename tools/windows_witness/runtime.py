#!/usr/bin/env python3
"""Dependency-free trace validation and deterministic return bundling.

This file is copied unchanged into every generated package.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any


PAIR_RE = re.compile(r"(?P<key>[a-zA-Z_][a-zA-Z0-9_]*)=(?P<value>[^\s]+)")
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)
DRIVE_PATH_RE = re.compile(r"^[A-Za-z]:")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")


def failure(request_id: str, stage: str, reason: str, missing: list[str], last: str = "") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "exact_bind_failure",
        "request_id": request_id,
        "failure": {
            "stage": stage,
            "reason": reason,
            "missing_fields": sorted(set(missing)),
            "last_observation": last,
        },
    }


def _archive_issue(value: str, label: str) -> str | None:
    if not isinstance(value, str) or not value:
        return f"{label}:{value!r} must be a non-empty relative ZIP path"
    if "\\" in value:
        return f"{label}:{value} may not contain backslashes"
    if value.startswith("/"):
        return f"{label}:{value} must be relative"
    if DRIVE_PATH_RE.match(value) is not None:
        return f"{label}:{value} may not be a drive path"
    for part in value.split("/"):
        if part in ("", ".", ".."):
            return f"{label}:{value} has unsafe path component {part!r}"
    return None


def _archive_key(value: str) -> str:
    return "/".join(part.casefold() for part in value.split("/"))


def _archive_collisions(entries: list[tuple[str, str]]) -> list[str]:
    seen: dict[str, tuple[str, str]] = {}
    collisions: list[str] = []
    for label, archive_path in entries:
        issue = _archive_issue(archive_path, label)
        if issue is not None:
            collisions.append(issue)
            continue
        key = _archive_key(archive_path)
        previous = seen.get(key)
        if previous is not None:
            previous_label, previous_path = previous
            collisions.append(
                f"{label}:{archive_path} collides with {previous_label}:{previous_path}"
            )
            continue
        seen[key] = (label, archive_path)
    return collisions


def _expected_identity(contract: dict[str, Any], runtime_identity: dict[str, Any]) -> dict[str, str]:
    expected = {
        "run_id": str(runtime_identity["run_id"]),
        "ae_pid": str(runtime_identity["ae_pid"]),
        "module_base": str(runtime_identity["module_base"]).lower(),
        "aex_sha256": contract["plugin"]["aex_sha256"].lower(),
        "project_bpc": str(contract["project"]["bits_per_channel"]),
        "renderer": contract["project"]["renderer"],
    }
    return expected


def validate_trace(contract: dict[str, Any], trace_text: str, runtime_identity: dict[str, Any]) -> dict[str, Any]:
    """Validate event cardinality, fields, constraints, and shared run identity."""

    request_id = contract["request_id"]
    event_by_prefix = {event["prefix"]: event for event in contract["validation"]["events"]}
    records: list[dict[str, Any]] = []
    issues: list[str] = []
    last = ""
    for line in trace_text.splitlines():
        last = line
        prefix = line.split(None, 1)[0] if line.strip() else ""
        event = event_by_prefix.get(prefix)
        if event is None:
            continue
        fields: dict[str, str] = {}
        duplicate_keys: list[str] = []
        for match in PAIR_RE.finditer(line):
            key = match.group("key")
            if key in fields:
                duplicate_keys.append(key)
                continue
            fields[key] = match.group("value")
        if duplicate_keys:
            for key in sorted(set(duplicate_keys)):
                issues.append(f"{event['name']}:duplicate_field:{key}")
            continue
        records.append({"event": event["name"], "prefix": prefix, "fields": fields})

    missing: list[str] = []
    case_ids = [case["id"] for case in contract["cases"]]
    expected_identity = _expected_identity(contract, runtime_identity)
    identity_fields = contract["validation"]["identity_fields"]
    by_event = {event["name"]: [row for row in records if row["event"] == event["name"]]
                for event in contract["validation"]["events"]}

    for event in contract["validation"]["events"]:
        rows = by_event[event["name"]]
        card = event["cardinality"]
        scopes = case_ids if card["scope"] == "per_case" else [None]
        for case_id in scopes:
            scoped = rows if case_id is None else [row for row in rows if row["fields"].get("case_id") == case_id]
            label = event["name"] if case_id is None else f"{case_id}:{event['name']}"
            if not card["min"] <= len(scoped) <= card["max"]:
                missing.append(f"{label}:cardinality={len(scoped)} expected={card['min']}..{card['max']}")
            for row_index, row in enumerate(scoped):
                fields = row["fields"]
                for field in event["required_fields"]:
                    if not fields.get(field):
                        missing.append(f"{label}[{row_index}]:{field}")
                for field, constraint in event.get("field_constraints", {}).items():
                    value = fields.get(field, "")
                    if "equals" in constraint and value != str(constraint["equals"]):
                        missing.append(f"{label}[{row_index}]:{field}=expected:{constraint['equals']}")
                    if "pattern" in constraint and re.fullmatch(constraint["pattern"], value) is None:
                        missing.append(f"{label}[{row_index}]:{field}=pattern")

    for row_index, row in enumerate(records):
        fields = row["fields"]
        for field in identity_fields:
            if field in expected_identity:
                actual = fields.get(field, "")
                expected = expected_identity[field]
                if field in ("module_base", "aex_sha256"):
                    actual = actual.lower()
                if actual != expected:
                    missing.append(f"record[{row_index}]:identity:{field}")
        if fields.get("case_id") not in case_ids:
            missing.append(f"record[{row_index}]:identity:case_id")

    for field in identity_fields:
        values = {row["fields"].get(field, "") for row in records if row["fields"].get(field, "")}
        if len(values) != 1 and field != "case_id":
            missing.append(f"shared_identity:{field}")

    missing.extend(issues)
    if missing:
        return failure(request_id, "trace_validation", "required events, fields, cardinality, constraints, or identity did not bind", missing, last)
    return {
        "schema_version": 1,
        "status": "answered",
        "request_id": request_id,
        "run": {
            "run_id": expected_identity["run_id"],
            "ae_pid": int(expected_identity["ae_pid"]),
            "module_base": expected_identity["module_base"],
            "aex_sha256": expected_identity["aex_sha256"],
            "project_bits_per_channel": int(expected_identity["project_bpc"]),
            "renderer": expected_identity["renderer"],
        },
        "events": records,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _expand_case_path(value: str, case_id: str) -> str:
    return value.replace("{case_id}", case_id)


def _zip_files(root: Path, output: Path, entries: list[tuple[Path, str]]) -> None:
    issues = _archive_collisions([(str(source), archive_path) for source, archive_path in entries])
    if issues:
        raise ValueError(f"unsafe ZIP entries: {'; '.join(issues)}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, archive_path in sorted(entries, key=lambda item: item[1]):
            info = zipfile.ZipInfo(archive_path, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def bundle_return(contract: dict[str, Any], status: dict[str, Any], work: Path) -> tuple[dict[str, Any], Path]:
    """Collect exports/logs and always emit a deterministic return ZIP."""

    work = work.resolve()
    bundle = contract["return_bundle"]
    exports: list[dict[str, Any]] = []
    missing_exports: list[str] = []
    zip_entries: list[tuple[Path, str]] = []
    configured_entries: list[tuple[str, str]] = [("return_bundle.json_name", bundle["json_name"])]
    for index, relative in enumerate(bundle.get("include_logs", [])):
        configured_entries.append((f"return_bundle.include_logs[{index}]", f"logs/{relative}"))
    for case in contract["cases"]:
        for export in case.get("exports", []):
            source_name = _expand_case_path(export["source"], case["id"])
            archive_name = _expand_case_path(export["archive_path"], case["id"])
            configured_entries.append((f"{case['id']}:{source_name}", archive_name))
            source = work / source_name
            if not source.is_file():
                if export["required"]:
                    missing_exports.append(f"{case['id']}:{source_name}")
                continue
            exports.append({
                "case_id": case["id"],
                "archive_path": archive_name,
                "sha256": sha256_file(source),
                "size_bytes": source.stat().st_size,
            })
            zip_entries.append((source, archive_name))

    if status.get("status") == "answered" and missing_exports:
        status = failure(contract["request_id"], "artifact_collection", "required exported artifacts are missing", missing_exports)
    status["artifacts"] = exports

    logs: list[dict[str, Any]] = []
    for relative in bundle.get("include_logs", []):
        source = work / relative
        if source.is_file():
            archive_name = f"logs/{relative}"
            logs.append({"archive_path": archive_name, "sha256": sha256_file(source), "size_bytes": source.stat().st_size})
            zip_entries.append((source, archive_name))
    status["logs"] = logs

    safe_zip_entries = list(zip_entries)
    configured_issues = _archive_collisions(configured_entries)
    if configured_issues:
        if status.get("status") == "answered":
            status = failure(
                contract["request_id"],
                "return_bundle_validation",
                "configured return archive paths are unsafe",
                configured_issues,
            )
        safe_zip_entries = []

    payload_issues = _archive_collisions([(str(source), archive_path) for source, archive_path in safe_zip_entries])
    if payload_issues:
        if status.get("status") == "answered":
            status = failure(
                contract["request_id"],
                "return_bundle_validation",
                "unsafe ZIP entries were rejected",
                payload_issues,
            )
        safe_zip_entries = []

    status_path = work / bundle["json_name"]
    write_json(status_path, status)
    zip_entries = safe_zip_entries + [(status_path, bundle["json_name"])]
    zip_path = work / bundle["zip_name"]
    _zip_files(work, zip_path, zip_entries)
    return status, zip_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--contract", type=Path, required=True)
    validate.add_argument("--trace", type=Path, required=True)
    validate.add_argument("--identity", type=Path, required=True)
    validate.add_argument("--output", type=Path, required=True)
    bundle = subparsers.add_parser("bundle")
    bundle.add_argument("--contract", type=Path, required=True)
    bundle.add_argument("--status", type=Path, required=True)
    bundle.add_argument("--work", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.command == "validate":
        contract = read_json(args.contract)
        identity = read_json(args.identity)
        trace = args.trace.read_text(encoding="utf-8", errors="replace") if args.trace.is_file() else ""
        result = validate_trace(contract, trace, identity)
        write_json(args.output, result)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "answered" else 2

    contract = read_json(args.contract)
    status = read_json(args.status)
    result, zip_path = bundle_return(contract, status, args.work)
    print(json.dumps({"status": result["status"], "return_zip": str(zip_path)}, sort_keys=True))
    return 0 if result["status"] == "answered" else 2


if __name__ == "__main__":
    raise SystemExit(main())
