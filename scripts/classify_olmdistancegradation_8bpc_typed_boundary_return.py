#!/usr/bin/env python3
"""Fail-closed classifier for the DG 8bpc typed-boundary v4 return."""

from __future__ import annotations

import argparse
import json
import math
import re
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA = "olmdg_8bpc_current_aex_typed_boundary_v4"
REQUEST_ID = "olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712"
AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
PROJECT_BPC = 8
CASES = ("case_0001", "case_0015", "case_0029")
STAGES = ("FIELD_IN", "FIELD_OUT", "COMPOSE_IN", "COMPOSE_OUT", "HOST_STORE")
XY = (397, 281)
EXPECTED_RVAS = ("1170870", "1170c90")
ADDRESS_FORMULA = "base+y*rowbytes+x*4"
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
ADDRESS = re.compile(r"^0x[0-9a-fA-F]+$")
HEX_WORD = re.compile(r"^(?:0x)?[0-9a-fA-F]+$")
MARKER = re.compile(r"^DG8_([A-Z0-9_]+)(?:\s+(.*))?$")
FIELD = re.compile(r"^([a-z0-9_]+)=([^\s]+)$")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def nonempty(value: object, field: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{field} is missing")
    return value.strip()


def integer(value: object, field: str, *, positive: bool = False) -> int:
    require(not isinstance(value, bool), f"{field} is invalid")
    if isinstance(value, int):
        parsed = value
    else:
        text = nonempty(value, field)
        require(text.isdigit(), f"{field} is not an integer")
        parsed = int(text)
    require(not positive or parsed > 0, f"{field} must be positive")
    return parsed


def address(value: object, field: str) -> str:
    text = nonempty(value, field)
    require(ADDRESS.fullmatch(text) is not None and int(text, 16) > 0, f"{field} is invalid")
    return f"0x{int(text, 16):x}"


def hex_word(value: object, field: str) -> int:
    text = nonempty(value, field)
    require(HEX_WORD.fullmatch(text) is not None, f"{field} is not hexadecimal")
    parsed = int(text.removeprefix("0x").removeprefix("0X"), 16)
    require(parsed >= 0, f"{field} is invalid")
    return parsed


def finite_float(value: object, field: str) -> float:
    require(not isinstance(value, bool), f"{field} is invalid")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} is not numeric") from error
    require(math.isfinite(parsed), f"{field} is not finite")
    return parsed


def rgba(value: object, field: str) -> tuple[str, str, str, str]:
    text = nonempty(value, field)
    parts = tuple(part.strip() for part in text.split(","))
    require(len(parts) == 4 and all(parts), f"{field} must contain four values")
    return parts[0], parts[1], parts[2], parts[3]


def identity(row: dict[str, Any], field: str) -> tuple[str, int, str, str, int]:
    run_id = nonempty(row.get("run_id"), f"{field}.run_id")
    pid = integer(row.get("ae_pid"), f"{field}.ae_pid", positive=True)
    base = address(row.get("module_base"), f"{field}.module_base")
    digest = nonempty(row.get("aex_sha256"), f"{field}.aex_sha256")
    require(HEX64.fullmatch(digest) is not None and digest.lower() == AEX_SHA256,
            f"{field}.aex_sha256 mismatch")
    depth = integer(row.get("project_bpc"), f"{field}.project_bpc")
    require(depth == PROJECT_BPC, f"{field}.project_bpc is not 8")
    return run_id, pid, base, digest.lower(), depth


def validate_stage(item: object, case: str, stage: str, field: str) -> dict[str, Any]:
    require(isinstance(item, dict), f"{field} is not an object")
    stage_identity = identity(item, field)
    require(item.get("case_id") == case, f"{field}.case_id mismatch")
    require((integer(item.get("x"), f"{field}.x"), integer(item.get("y"), f"{field}.y")) == XY,
            f"{field} coordinate mismatch")
    normalized: dict[str, Any] = {
        "identity": stage_identity,
        "case_id": case,
        "xy": XY,
        "output_addr": address(item.get("output_addr"), f"{field}.output_addr"),
        "typed_rgba": rgba(item.get("typed_rgba"), f"{field}.typed_rgba"),
    }
    if stage in ("FIELD_IN", "FIELD_OUT"):
        normalized.update(
            field_base=address(item.get("field_base"), f"{field}.field_base"),
            field_rowbytes=hex_word(item.get("field_rowbytes"), f"{field}.field_rowbytes"),
            field_addr=address(item.get("field_addr"), f"{field}.field_addr"),
            pixel_size=integer(item.get("pixel_size"), f"{field}.pixel_size"),
            address_formula=nonempty(item.get("address_formula"), f"{field}.address_formula"),
        )
        require(normalized["pixel_size"] == 4, f"{field}.pixel_size is not 4")
        require(normalized["address_formula"] == ADDRESS_FORMULA, f"{field}.address_formula mismatch")
    elif stage == "COMPOSE_IN":
        normalized.update(
            source_base=address(item.get("source_base"), f"{field}.source_base"),
            source_rowbytes=hex_word(item.get("source_rowbytes"), f"{field}.source_rowbytes"),
            source_addr=address(item.get("source_addr"), f"{field}.source_addr"),
            field_green=hex_word(item.get("field_green"), f"{field}.field_green"),
            x_before_invert=finite_float(item.get("x_before_invert"), f"{field}.x_before_invert"),
            x_after_invert=finite_float(item.get("x_after_invert"), f"{field}.x_after_invert"),
        )
    elif stage == "COMPOSE_OUT":
        values = rgba(item.get("pre_store_rgba_float"), f"{field}.pre_store_rgba_float")
        normalized["pre_store_rgba_float"] = tuple(
            finite_float(value, f"{field}.pre_store_rgba_float") for value in values
        )
    return normalized


def parse_fields(text: str | None, field: str) -> dict[str, str]:
    require(text is not None and bool(text.strip()), f"{field} has no fields")
    result: dict[str, str] = {}
    for token in text.split():
        match = FIELD.fullmatch(token)
        require(match is not None, f"{field} contains malformed token: {token}")
        key, value = match.groups()
        require(key not in result, f"{field} contains duplicate field: {key}")
        result[key] = value
    return result


def parse_trace(trace: object) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    text = nonempty(trace, "raw_logs.combined_cdb_trace")
    stages: dict[tuple[str, str], dict[str, Any]] = {}
    depths: dict[tuple[str, str], dict[str, Any]] = {}
    for line_number, line in enumerate(text.splitlines(), 1):
        match = MARKER.fullmatch(line.strip())
        if match is None:
            continue
        marker, body = match.groups()
        if marker in STAGES:
            fields = parse_fields(body, f"trace line {line_number} DG8_{marker}")
            case = fields.get("case_id", "")
            require(case in CASES, f"trace line {line_number} has unexpected stage case: {case}")
            key = (case, marker)
            require(key not in stages, f"duplicate trace stage: {case}:{marker}")
            stages[key] = validate_stage(fields, case, marker, f"trace {case}:{marker}")
        elif marker == "DEPTH_SUMMARY":
            fields = parse_fields(body, f"trace line {line_number} DG8_DEPTH_SUMMARY")
            case = fields.get("case_id", "")
            require(case in CASES, f"trace line {line_number} has unexpected depth case: {case}")
            rva = nonempty(fields.get("rva"), f"trace {case} depth rva").lower().removeprefix("0x")
            require(rva in EXPECTED_RVAS, f"unexpected trace depth RVA: {rva}")
            key = (case, rva)
            require(key not in depths, f"duplicate trace depth summary: {case}:{rva}")
            count = integer(fields.get("hit_count"), f"trace {case}:{rva}.hit_count")
            require(count >= 0, f"trace {case}:{rva}.hit_count is negative")
            depths[key] = {"identity": identity(fields, f"trace {case}:{rva}"), "hit_count": count}
    expected_stages = {(case, stage) for case in CASES for stage in STAGES}
    expected_depths = {(case, rva) for case in CASES for rva in EXPECTED_RVAS}
    require(set(stages) == expected_stages, "combined trace stage set is incomplete or mixed")
    require(set(depths) == expected_depths, "combined trace depth-summary set is incomplete or mixed")
    return stages, depths


def load_return(path: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    require(path.suffix.lower() == ".zip", "typed-boundary returns must be ZIP archives with raw logs")
    try:
        with zipfile.ZipFile(path) as archive:
            files = [info for info in archive.infolist() if not info.is_dir()]
            result = [
                info for info in files
                if PurePosixPath(info.filename.replace("\\", "/")).name == "RETURN_RUNTIME_TRACE.json"
            ]
            require(len(result) == 1, "expected one RETURN_RUNTIME_TRACE.json")
            payload = json.loads(archive.read(result[0]).decode("utf-8-sig"))
            require(isinstance(payload, dict), "return JSON is not an object")
            return payload, {info.filename: archive.read(info) for info in files}
    except zipfile.BadZipFile as error:
        raise ValueError("return is not a valid ZIP archive") from error


def require_raw_logs(payload: dict[str, Any], files: dict[str, bytes]) -> None:
    raw = payload.get("raw_logs")
    require(isinstance(raw, dict), "raw_logs is missing")
    required: list[tuple[str, str, object]] = [
        ("launcher_stdout", "afterfx_launcher_stdout.txt", raw.get("launcher_stdout")),
        ("launcher_stderr", "afterfx_launcher_stderr.txt", raw.get("launcher_stderr")),
        ("queue_log", "AE_TYPED_QUEUE.log", raw.get("queue_log")),
        ("combined_cdb_trace", "combined_cdb_trace.txt", raw.get("combined_cdb_trace")),
    ]
    case_rows = raw.get("cases")
    require(isinstance(case_rows, list) and len(case_rows) == len(CASES),
            "raw_logs.cases must contain all three cases")
    by_case: dict[str, dict[str, object]] = {}
    for index, case in enumerate(case_rows):
        require(isinstance(case, dict), f"raw_logs.cases[{index}] is not an object")
        case_id = nonempty(case.get("case_id"), f"raw_logs.cases[{index}].case_id")
        require(case_id in CASES and case_id not in by_case,
                f"unexpected or duplicate raw log case: {case_id}")
        by_case[case_id] = case
        required.extend((
            (f"{case_id}.ready_marker", f"ae_ready_{case_id}.marker", case.get("ready_marker")),
            (f"{case_id}.cdb_trace", f"cdb_trace_{case_id}.txt", case.get("cdb_trace")),
            (f"{case_id}.cdb_stdout", f"cdb_stdout_{case_id}.txt", case.get("cdb_stdout")),
            (f"{case_id}.cdb_stderr", f"cdb_stderr_{case_id}.txt", case.get("cdb_stderr")),
            (f"{case_id}.ae_log", f"AE_SINGLE_CASE_{case_id}.log", case.get("ae_log")),
            (f"{case_id}.ae_result", f"AE_SINGLE_CASE_{case_id}.json", case.get("ae_result")),
        ))
    require(set(by_case) == set(CASES), "raw log case set mismatch")
    names_by_base: dict[str, list[str]] = {}
    for name in files:
        names_by_base.setdefault(PurePosixPath(name.replace("\\", "/")).name, []).append(name)
    for field, expected_name, value in required:
        require(isinstance(value, str), f"raw_logs.{field} is missing")
        matches = names_by_base.get(expected_name, [])
        require(len(matches) == 1, f"raw log ZIP member missing or duplicated: {expected_name}")
        try:
            archived = files[matches[0]].decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"raw log is not UTF-8: {expected_name}") from error
        require(archived == value, f"raw log bytes differ: {expected_name}")


def payload_rvas(payload: dict[str, Any]) -> dict[str, int]:
    rows = payload.get("rvas")
    require(isinstance(rows, list) and len(rows) == len(EXPECTED_RVAS),
            "expected exactly two RVA summaries")
    counts: dict[str, int] = {}
    for row in rows:
        require(isinstance(row, dict), "RVA summary is not an object")
        rva = nonempty(row.get("rva"), "RVA").lower().removeprefix("0x")
        require(rva in EXPECTED_RVAS and rva not in counts, f"unexpected or duplicate RVA: {rva}")
        count = integer(row.get("hit_count"), f"RVA {rva}.hit_count")
        require(count >= 0, f"RVA {rva}.hit_count is negative")
        counts[rva] = count
    require(set(counts) == set(EXPECTED_RVAS), "RVA set mismatch")
    require(counts["1170870"] > 0, "PF8 depth RVA did not execute")
    require(counts["1170c90"] == 0, "PF32 depth RVA executed")
    return counts


def payload_cases(payload: dict[str, Any]) -> tuple[dict[tuple[str, str], dict[str, Any]], tuple[str, int, str, str, int]]:
    rows = payload.get("cases")
    require(isinstance(rows, list) and len(rows) == len(CASES), "expected exactly three cases")
    normalized: dict[tuple[str, str], dict[str, Any]] = {}
    seen_cases: set[str] = set()
    shared: tuple[str, int, str, str, int] | None = None
    for index, row in enumerate(rows):
        require(isinstance(row, dict), f"case[{index}] is not an object")
        case = nonempty(row.get("case_id"), f"case[{index}].case_id")
        require(case in CASES and case not in seen_cases, f"unexpected or duplicate case: {case}")
        seen_cases.add(case)
        xy = row.get("xy")
        require(isinstance(xy, list) and len(xy) == 2, f"{case}.xy is not [x,y]")
        require((integer(xy[0], f"{case}.xy[0]"), integer(xy[1], f"{case}.xy[1]")) == XY,
                f"{case}.xy is not [397,281]")
        output = address(row.get("output_addr"), f"{case}.output_addr")
        stages = row.get("stages")
        require(isinstance(stages, dict) and set(stages) == set(STAGES),
                f"{case} stages are incomplete or mixed")
        for stage in STAGES:
            item = validate_stage(stages[stage], case, stage, f"{case}:{stage}")
            require(item["output_addr"] == output, f"{case}:{stage} output address differs")
            require(shared is None or item["identity"] == shared,
                    f"{case}:{stage} identity differs from the single run")
            shared = item["identity"]
            normalized[(case, stage)] = item
    require(seen_cases == set(CASES), "case set mismatch")
    require(shared is not None, "shared run identity is missing")
    return normalized, shared


def validate_payload(payload: dict[str, Any], files: dict[str, bytes]) -> dict[str, Any]:
    require(payload.get("schema") == SCHEMA, "schema mismatch")
    require(payload.get("request_id") == REQUEST_ID, "request_id mismatch")
    require(payload.get("status") == "answered", f"return is not answered: {payload.get('status')}")
    require(payload.get("kind") == "typed_boundary", "return kind mismatch")
    require_raw_logs(payload, files)

    top_identity = identity({
        "run_id": payload.get("run_id"),
        "ae_pid": payload.get("ae_pid"),
        "module_base": payload.get("module_base"),
        "aex_sha256": payload.get("aex_sha256"),
        "project_bpc": payload.get("project_bits_per_channel"),
    }, "return")
    counts = payload_rvas(payload)
    cases, shared = payload_cases(payload)
    require(shared == top_identity, "payload stage identity differs from top-level identity")

    raw = payload["raw_logs"]
    trace_stages, trace_depths = parse_trace(raw["combined_cdb_trace"])
    require(trace_stages == cases, "payload cases differ semantically from combined CDB trace")
    for key, summary in trace_depths.items():
        require(summary["identity"] == top_identity,
                f"trace depth identity differs from return: {key[0]}:{key[1]}")
        if key[1] == "1170870":
            require(summary["hit_count"] > 0, f"PF8 depth RVA did not execute for {key[0]}")
        else:
            require(summary["hit_count"] == 0, f"PF32 depth RVA executed for {key[0]}")
    trace_counts = {
        rva: sum(trace_depths[(case, rva)]["hit_count"] for case in CASES)
        for rva in EXPECTED_RVAS
    }
    require(counts == trace_counts, "payload RVA summaries differ from per-case trace summaries")

    normalized_cases = []
    for case in CASES:
        stage_rows = {stage: cases[(case, stage)] for stage in STAGES}
        normalized_cases.append({
            "case_id": case,
            "xy": list(XY),
            "output_addr": stage_rows[STAGES[0]]["output_addr"],
            "stages": {stage: {key: value for key, value in stage_rows[stage].items() if key != "identity"}
                       for stage in STAGES},
        })
    return {
        "schema": SCHEMA,
        "request_id": REQUEST_ID,
        "classification": "accepted_complete_evidence",
        "evidence_gate": "schema-request-hash-8bpc-rva-same-run-pid-base-three-case-five-stage-raw-trace",
        "run_id": shared[0],
        "ae_pid": shared[1],
        "module_base": shared[2],
        "aex_sha256": AEX_SHA256,
        "project_bits_per_channel": PROJECT_BPC,
        "hit_counts": counts,
        "cases": normalized_cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("return_path", type=Path)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()
    payload, files = load_return(args.return_path)
    result = validate_payload(payload, files)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
