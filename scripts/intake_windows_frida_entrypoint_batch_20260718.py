#!/usr/bin/env python3
"""Fail-closed intake for the six-lane Windows Frida entrypoint batch."""

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


SCHEMA_VERSION = 1
BATCH_KIND = "olm_frida_entrypoint_batch_return"
LANE_COUNT = 6
SHA256 = re.compile(r"^[0-9a-f]{64}$")
HEX = re.compile(r"^(?:0x)?[0-9a-fA-F]+$")
ENTRY_READ_TYPE = "i32"


class IntakeError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise IntakeError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_member(name: str) -> str:
    require(isinstance(name, str) and name, f"unsafe ZIP member: {name!r}")
    value = name.replace("\\", "/")
    require(not value.startswith("/"), f"unsafe ZIP member: {name!r}")
    path = PurePosixPath(value)
    require(all(part not in ("", ".", "..") for part in path.parts), f"unsafe ZIP member: {name!r}")
    require(not (path.parts and ":" in path.parts[0]), f"unsafe ZIP member: {name!r}")
    return path.as_posix()


def read_zip(path: Path, label: str) -> tuple[bytes, dict[str, bytes]]:
    try:
        raw = path.read_bytes()
        with zipfile.ZipFile(path) as archive:
            files: dict[str, bytes] = {}
            folded: set[str] = set()
            for info in archive.infolist():
                if info.is_dir():
                    continue
                name = canonical_member(info.filename)
                key = name.casefold()
                require(key not in folded, f"{label}: casefold ZIP collision: {name}")
                folded.add(key)
                files[name] = archive.read(info)
    except (OSError, zipfile.BadZipFile) as exc:
        raise IntakeError(f"{label}: invalid ZIP: {exc}") from exc
    return raw, files


def load_json(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntakeError(f"{label}: invalid JSON") from exc
    require(isinstance(value, dict), f"{label}: JSON must be an object")
    return value


def one_named(files: dict[str, bytes], basename: str, label: str) -> tuple[str, bytes]:
    rows = [(name, data) for name, data in files.items() if PurePosixPath(name).name.casefold() == basename.casefold()]
    require(len(rows) == 1, f"{label}: expected exactly one {basename}, found {len(rows)}")
    return rows[0]


def one_under(files: dict[str, bytes], root: str, basename: str, label: str) -> tuple[str, bytes]:
    root = canonical_member(root).rstrip("/").casefold()
    rows = [
        (name, data)
        for name, data in files.items()
        if name.casefold().startswith(root + "/") and PurePosixPath(name).name.casefold() == basename.casefold()
    ]
    require(len(rows) == 1, f"{label}: expected exactly one {basename} below {root}, found {len(rows)}")
    return rows[0]


def relative_run_path(value: Any) -> str:
    require(isinstance(value, str) and value, "run_dir is missing")
    path = canonical_member(value)
    if path.casefold().startswith("runs/"):
        path = path[6:]
    require(path and "/" not in path and path.casefold() not in {".", ".."}, f"unsafe run_dir: {value!r}")
    return "runs/" + path


def text(value: Any, label: str) -> str:
    require(isinstance(value, str) and value, f"{label} is missing")
    return value


def sha(value: Any, label: str) -> str:
    require(isinstance(value, str) and SHA256.fullmatch(value) is not None, f"{label} is not a SHA-256")
    return value.lower()


def package_contract(package_bytes: bytes, label: str) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(io.BytesIO(package_bytes)) as archive:
            files: dict[str, bytes] = {}
            folded: set[str] = set()
            for info in archive.infolist():
                if info.is_dir():
                    continue
                name = canonical_member(info.filename)
                require(name.casefold() not in folded, f"{label}: casefold ZIP collision: {name}")
                folded.add(name.casefold())
                files[name] = archive.read(info)
    except (OSError, zipfile.BadZipFile) as exc:
        raise IntakeError(f"{label}: invalid inner package ZIP") from exc
    _, manifest_bytes = one_named(files, "package-manifest.json", label)
    manifest = load_json(manifest_bytes, f"{label}:package-manifest.json")
    require(manifest.get("schema_version") == 1, f"{label}: package manifest schema mismatch")
    require(manifest.get("kind") == "windows_witness_generated_package", f"{label}: package manifest kind mismatch")
    inventory = manifest.get("files")
    require(isinstance(inventory, list), f"{label}: package inventory is missing")
    inventory_paths: set[str] = set()
    for index, item in enumerate(inventory):
        require(isinstance(item, dict), f"{label}: inventory[{index}] is invalid")
        path = canonical_member(text(item.get("path"), f"{label}: inventory[{index}].path"))
        require(path.casefold() not in inventory_paths, f"{label}: duplicate inventory path: {path}")
        inventory_paths.add(path.casefold())
        expected_size = item.get("size_bytes")
        require(type(expected_size) is int and expected_size >= 0, f"{label}: inventory[{index}].size_bytes is invalid")
        expected_sha = sha(item.get("sha256"), f"{label}: inventory[{index}].sha256")
        require(path in files, f"{label}: inventory member is missing: {path}")
        require(len(files[path]) == expected_size and sha256_bytes(files[path]) == expected_sha, f"{label}: inventory hash mismatch: {path}")
    request_id = text(manifest.get("request_id"), f"{label}: package request_id")
    contract_name = canonical_member(text(manifest.get("contract"), f"{label}: package contract"))
    require(contract_name in files, f"{label}: package contract member is absent")
    contract = load_json(files[contract_name], f"{label}:{contract_name}")
    require(contract.get("schema_version") == 1, f"{label}: contract schema mismatch")
    require(text(contract.get("request_id"), f"{label}: contract request_id") == request_id, f"{label}: request_id mismatch")
    plugin = contract.get("plugin")
    project = contract.get("project")
    cases = contract.get("cases")
    transport = contract.get("transport")
    require(isinstance(plugin, dict) and isinstance(project, dict) and isinstance(cases, list) and len(cases) == 1, f"{label}: incomplete contract")
    require(isinstance(transport, dict) and transport.get("kind") == "frida", f"{label}: transport is not Frida")
    module = text(plugin.get("module_filename"), f"{label}: module_filename")
    aex_sha = sha(plugin.get("aex_sha256"), f"{label}: aex_sha256")
    renderer = text(project.get("renderer"), f"{label}: renderer")
    bpc = project.get("bits_per_channel")
    require(type(bpc) is int and bpc in (8, 16, 32), f"{label}: invalid project bits_per_channel")
    case = cases[0]
    case_id = text(case.get("id"), f"{label}: case id")
    config = transport.get("agent_config")
    require(isinstance(config, dict), f"{label}: agent_config is missing")
    exports = config.get("exports")
    require(isinstance(exports, list) and len(exports) >= 1 and isinstance(exports[0], dict), f"{label}: entry export is missing")
    entry = exports[0]
    entry_name = text(entry.get("name") or entry.get("export"), f"{label}: entry hook name")
    reads = entry.get("reads")
    require(isinstance(reads, list) and any(isinstance(item, dict) and item.get("name") == "pf_cmd" and item.get("type") == ENTRY_READ_TYPE for item in reads), f"{label}: typed pf_cmd i32 read is missing")
    static_files = {name: data for name, data in files.items() if name.casefold() != "package-manifest.json"}
    require(set(static_files) == {next(name for name in files if name.casefold() == path) for path in inventory_paths}, f"{label}: inventory does not cover package files")
    return {
        "request_id": request_id,
        "module": module,
        "aex_sha256": aex_sha,
        "renderer": renderer,
        "bpc": bpc,
        "case_id": case_id,
        "entry_name": entry_name,
        "contract_sha256": sha256_bytes(files[contract_name]),
        "manifest_sha256": sha256_bytes(manifest_bytes),
        "package_sha256": sha256_bytes(package_bytes),
        "manifest_bytes": manifest_bytes,
        "contract_bytes": files[contract_name],
        "static_files": static_files,
        "inventory": inventory,
    }


def request_batch(path: Path) -> dict[str, Any]:
    raw, files = read_zip(path, "request batch")
    _, manifest_bytes = one_named(files, "batch-manifest.json", "request batch")
    manifest = load_json(manifest_bytes, "request batch:batch-manifest.json")
    require(manifest.get("schema_version") == 1 and manifest.get("kind") == "olm_frida_entrypoint_batch_request", "request batch manifest kind/schema mismatch")
    jobs = manifest.get("jobs")
    require(isinstance(jobs, list) and len(jobs) == LANE_COUNT, "request batch manifest must contain six jobs")
    packages = [(name, data) for name, data in files.items() if name.casefold().startswith("packages/") and name.casefold().endswith(".zip")]
    require(len(packages) == LANE_COUNT, f"request batch must contain exactly {LANE_COUNT} inner packages")
    jobs_by_name: dict[str, dict[str, Any]] = {}
    for index, job in enumerate(jobs):
        require(isinstance(job, dict), f"request batch manifest job[{index}] is invalid")
        package_name = text(job.get("package"), f"request batch manifest job[{index}].package")
        require(package_name.casefold() not in jobs_by_name, f"request batch manifest duplicate package: {package_name}")
        jobs_by_name[package_name.casefold()] = job
    rows: list[dict[str, Any]] = []
    names: set[str] = set()
    for name, data in sorted(packages, key=lambda item: item[0].casefold()):
        basename = PurePosixPath(name).name
        require(basename.casefold() not in names, f"request batch package collision: {basename}")
        names.add(basename.casefold())
        job = jobs_by_name.get(basename.casefold())
        require(job is not None, f"request batch manifest has no job for {basename}")
        require(sha(job.get("package_sha256"), f"request batch manifest {basename}.package_sha256") == sha256_bytes(data), f"request package SHA mismatch: {basename}")
        identity = package_contract(data, f"request:{name}")
        require(text(job.get("request_id"), f"request batch manifest {basename}.request_id") == identity["request_id"], f"request_id mismatch: {basename}")
        rows.append({"package": basename, **identity})
    require(len({row["request_id"].casefold() for row in rows}) == LANE_COUNT, "request batch has duplicate request IDs")
    require(set(jobs_by_name) == names, "request batch manifest does not cover exactly the six packages")
    return {"outer_zip_sha256": sha256_bytes(raw), "manifest_bytes": manifest_bytes, "manifest_sha256": sha256_bytes(manifest_bytes), "packages": rows}


def event_rows(data: bytes, label: str) -> list[dict[str, Any]]:
    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise IntakeError(f"{label}: events are not UTF-8") from exc
    rows: list[dict[str, Any]] = []
    sequence: int | None = None
    for index, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise IntakeError(f"{label}: invalid JSON at line {index}") from exc
        require(isinstance(row, dict), f"{label}: event {index} is not an object")
        event = str(row.get("event", row.get("kind", ""))).casefold()
        require(event not in {"error", "agent_error", "exception"} and "error" not in row, f"{label}: error event at line {index}")
        if "sequence" in row:
            require(type(row["sequence"]) is int and row["sequence"] > 0, f"{label}: invalid sequence at line {index}")
            require(sequence is None or row["sequence"] > sequence, f"{label}: non-monotonic sequence at line {index}")
            sequence = row["sequence"]
        rows.append(row)
    require(rows, f"{label}: events are empty")
    return rows


def identity_value(value: Any, label: str) -> str:
    require(value is not None and str(value), f"{label} is missing")
    return str(value)


def numeric_equal(value: Any, expected: int, label: str) -> None:
    require((type(value) is int and value == expected) or (isinstance(value, str) and value.isdigit() and int(value) == expected), f"{label} mismatch")


def validate_returned_static_package(files: dict[str, bytes], run_root: str, expected: dict[str, Any], label: str) -> bytes:
    _, returned_manifest = one_under(files, run_root, "package-manifest.json", label)
    require(returned_manifest == expected["manifest_bytes"], f"{label}: returned package-manifest.json differs from request package")
    _, returned_contract = one_under(files, run_root, "witness-contract.json", label)
    require(returned_contract == expected["contract_bytes"], f"{label}: returned witness-contract.json differs from request package")
    for path, data in expected["static_files"].items():
        member = f"{run_root}/{path}"
        require(member in files, f"{label}: returned static member is missing: {path}")
        require(files[member] == data, f"{label}: returned static member differs: {path}")
    return returned_contract


def validate_lane(files: dict[str, bytes], run_root: str, expected: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    label = f"{expected['package']}:{run_root}"
    contract_bytes = validate_returned_static_package(files, run_root, expected, label)
    contract = load_json(contract_bytes, f"{label}:witness-contract.json")
    require(text(contract.get("request_id"), f"{label}: contract request_id") == expected["request_id"], f"{label}: stale request_id")
    plugin = contract.get("plugin")
    project = contract.get("project")
    cases = contract.get("cases")
    require(isinstance(plugin, dict) and isinstance(project, dict) and isinstance(cases, list) and len(cases) == 1, f"{label}: returned contract incomplete")
    require(text(plugin.get("module_filename"), f"{label}: returned module") .casefold() == expected["module"].casefold(), f"{label}: module mismatch")
    require(sha(plugin.get("aex_sha256"), f"{label}: returned AEX SHA") == expected["aex_sha256"], f"{label}: AEX SHA mismatch")
    require(project.get("renderer", "").casefold() == "software" and project.get("renderer") == expected["renderer"], f"{label}: renderer mismatch")
    require(project.get("bits_per_channel") == expected["bpc"], f"{label}: bpc mismatch")
    require(text(cases[0].get("id"), f"{label}: returned case") == expected["case_id"], f"{label}: case mismatch")

    _, armed_bytes = one_under(files, run_root, "armed.json", label)
    armed = load_json(armed_bytes, f"{label}:armed.json")
    _, result_bytes = one_under(files, run_root, "result-manifest.json", label)
    result = load_json(result_bytes, f"{label}:result-manifest.json")
    _, events_bytes = one_under(files, run_root, "events.jsonl", label)
    events = event_rows(events_bytes, f"{label}:events.jsonl")
    _, ae_log = one_under(files, run_root, f"ae_{expected['case_id']}.log", label)
    try:
        ae_log_text = ae_log.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise IntakeError(f"{label}: AE log is not UTF-8") from exc
    require(re.search(r"(?m)^gpuAccelType=SOFTWARE\s*$", ae_log_text) is not None, f"{label}: Software renderer evidence is missing")

    require(text(armed.get("module"), f"{label}: armed module").replace("\\", "/").rsplit("/", 1)[-1].casefold() == expected["module"].casefold(), f"{label}: armed module mismatch")
    require(sha(armed.get("aex_sha256"), f"{label}: armed AEX SHA") == expected["aex_sha256"], f"{label}: armed AEX SHA mismatch")
    require(text(result.get("module"), f"{label}: result module").replace("\\", "/").rsplit("/", 1)[-1].casefold() == expected["module"].casefold(), f"{label}: result module mismatch")
    require(sha(result.get("aex_sha256"), f"{label}: result AEX SHA") == expected["aex_sha256"], f"{label}: result AEX SHA mismatch")
    run_id = text(armed.get("run_id"), f"{label}: run_id")
    require(text(armed.get("case_id"), f"{label}: armed case") == expected["case_id"], f"{label}: armed case mismatch")
    require(text(result.get("run_id"), f"{label}: result run_id") == run_id, f"{label}: run_id mismatch")
    pid = armed.get("ae_pid")
    require(type(pid) is int and pid > 0, f"{label}: invalid AE PID")
    identity = result.get("identity")
    require(isinstance(identity, dict), f"{label}: result identity is missing")
    numeric_equal(identity.get("ae_pid"), pid, f"{label}: result AE PID")
    module_base = text(armed.get("module_base"), f"{label}: module_base")
    require(text(identity.get("module_base"), f"{label}: result module_base").casefold() == module_base.casefold(), f"{label}: module_base mismatch")
    require(armed.get("renderer") == expected["renderer"], f"{label}: armed renderer mismatch")
    numeric_equal(armed.get("project_bpc"), expected["bpc"], f"{label}: armed project_bpc")
    require(identity.get("renderer") == expected["renderer"], f"{label}: result renderer mismatch")
    numeric_equal(identity.get("project_bpc"), expected["bpc"], f"{label}: result project_bpc")
    require(result.get("status") == "answered", f"{label}: result is not answered")

    event_names = {str(item.get("event", "")) for item in events}
    require("module_loaded" in event_names, f"{label}: module_loaded event is missing")
    entry_events = [item for item in events if item.get("hook") == expected["entry_name"] or item.get("event") == expected["entry_name"]]
    require(entry_events, f"{label}: entrypoint event is missing")
    for event in events:
        for key, expected_value in (("run_id", run_id), ("ae_pid", str(pid)), ("module_base", module_base), ("aex_sha256", expected["aex_sha256"]), ("renderer", expected["renderer"]), ("project_bpc", str(expected["bpc"])), ("case_id", expected["case_id"])):
            require(str(event.get(key, "")).casefold() == str(expected_value).casefold(), f"{label}: mixed event identity {key}")
    for event in entry_events:
        reads = event.get("reads")
        require(isinstance(reads, dict) and isinstance(reads.get("pf_cmd"), dict), f"{label}: entry event lacks typed pf_cmd read")
        read = reads["pf_cmd"]
        require(read.get("type") == ENTRY_READ_TYPE and type(read.get("value")) is int, f"{label}: pf_cmd is not typed i32")

    return {
        "package": expected["package"],
        "status": "answered",
        "request_id": expected["request_id"],
        "run_id": run_id,
        "case_id": expected["case_id"],
        "ae_pid": pid,
        "module": expected["module"],
        "module_base": module_base,
        "aex_sha256": expected["aex_sha256"],
        "project_bpc": expected["bpc"],
        "renderer": expected["renderer"],
        "entrypoint_events": len(entry_events),
        "event_count": len(events),
        "request_package_sha256": expected["package_sha256"],
        "returned_contract_sha256": sha256_bytes(contract_bytes),
    }


def validate_return(return_path: Path, request: dict[str, Any]) -> dict[str, Any]:
    _, files = read_zip(return_path, "return batch")
    _, returned_batch_manifest = one_named(files, "batch-manifest.json", "return batch")
    require(returned_batch_manifest == request["manifest_bytes"], "returned batch-manifest.json differs from request")
    _, status_bytes = one_named(files, "batch_status.json", "return batch")
    status = load_json(status_bytes, "batch batch_status.json")
    require(status.get("schema_version") == SCHEMA_VERSION, "batch_status schema_version mismatch")
    require(status.get("kind") == BATCH_KIND, "batch_status kind mismatch")
    require(status.get("status") in {"answered", "partial", "failed"}, "batch_status status is invalid")
    require(sha(status.get("request_manifest_sha256"), "batch_status request manifest SHA") == request["manifest_sha256"], "batch_status request manifest SHA mismatch")
    rows = status.get("packages")
    require(isinstance(rows, list) and len(rows) == LANE_COUNT, "batch_status must contain six package rows")
    expected_by_name = {row["package"].casefold(): row for row in request["packages"]}
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for row in rows:
        require(isinstance(row, dict), "batch_status package row is invalid")
        package_name = text(row.get("package"), "batch package name")
        key = package_name.casefold()
        require(key in expected_by_name and key not in seen, f"unexpected or duplicate returned package: {package_name}")
        seen.add(key)
        expected = expected_by_name[key]
        lane_status = row.get("status")
        require(lane_status in {"answered", "failed"}, f"{package_name}: invalid lane status")
        run_root = ""
        package_sha = row.get("package_sha256", row.get("inner_package_sha256", row.get("observed_package_sha256")))
        diagnostic: dict[str, Any] = {"package": package_name, "status": "failed"}
        try:
            run_root = relative_run_path(row.get("run_dir"))
            diagnostic["run_dir"] = run_root
            require(package_sha is not None, f"{package_name}: returned package SHA identity is missing")
            require(sha(package_sha, f"{package_name}: returned package SHA") == expected["package_sha256"], f"{package_name}: package SHA mismatch")
            if lane_status == "answered":
                diagnostic = validate_lane(files, run_root, expected, row)
            else:
                diagnostic["reason"] = str(row.get("failure") or row.get("reason") or "Windows lane reported failed")
                diagnostic["diagnostics"] = [name for name in files if name.casefold().startswith(run_root.casefold() + "/") and (name.casefold().endswith(".txt") or name.casefold().endswith(".json"))]
        except (IntakeError, KeyError, TypeError) as exc:
            diagnostic["reason"] = str(exc)
            diagnostic["diagnostics"] = [name for name in files if name.casefold().startswith(run_root.casefold() + "/")]
        normalized.append(diagnostic)
    require(seen == set(expected_by_name), "batch_status does not cover exactly the six requested packages")
    answered = sum(item.get("status") == "answered" for item in normalized)
    expected_status = "answered" if answered == LANE_COUNT else ("failed" if answered == 0 else "partial")
    require(status.get("status") == expected_status, "batch_status aggregate status contradicts lane results")
    return {
        "schema_version": 1,
        "kind": "olm_frida_entrypoint_batch_intake",
        "classification": "accepted_all_answered" if answered == LANE_COUNT else "accepted_partial_evidence",
        "status": "answered" if answered == LANE_COUNT else "partial",
        "request_manifest_sha256": request["manifest_sha256"],
        "request_outer_zip_sha256": request["outer_zip_sha256"],
        "return_batch_sha256": sha256_bytes(return_path.read_bytes()),
        "lane_count": LANE_COUNT,
        "answered_count": answered,
        "failed_count": LANE_COUNT - answered,
        "packages": normalized,
    }


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def safe_extract(path: Path, destination: Path) -> None:
    _, files = read_zip(path, "return batch extraction")
    destination.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        target = destination / Path(*PurePosixPath(name).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("return_zip", type=Path)
    parser.add_argument("--request-batch", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--extract-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        request = request_batch(args.request_batch)
        if args.extract_dir is not None:
            safe_extract(args.return_zip, args.extract_dir)
        report = validate_return(args.return_zip, request)
    except (OSError, IntakeError, zipfile.BadZipFile) as exc:
        report = {
            "schema_version": 1,
            "kind": "olm_frida_entrypoint_batch_intake",
            "classification": "blocked_invalid_return",
            "status": "blocked",
            "reason": str(exc),
        }
        write_json(args.output_json, report)
        print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2), file=sys.stderr)
        return 2
    write_json(args.output_json, report)
    print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2))
    return 0 if report["status"] == "answered" else 2


if __name__ == "__main__":
    raise SystemExit(main())
