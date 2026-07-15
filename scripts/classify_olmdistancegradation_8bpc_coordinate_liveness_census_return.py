#!/usr/bin/env python3
"""Fail-closed classifier for the DG8 coordinate-liveness census return ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

REQUEST_ID = "olmdistancegradation_8bpc_coordinate_liveness_census_20260715"
CANONICAL_KIND = "coordinate_liveness_census"
FIXTURE_KIND = "coordinate_liveness_census_parser_fixture"
SCHEMA = "olmdg_8bpc_coordinate_liveness_census_v1"
AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
AE_VERSION = "25.2x131"
CASES = ("case_0001", "case_0015", "case_0029")
INPUT_SHA256 = {case: "9d96a359d987774a398ec27e224650fda83fa00ae3c14bd04b87e2402ea34265" for case in CASES}
OUTPUT_SHA256 = {
    "case_0001": "7d8a37e51743efe9d9aa8dd8c70c220749039194c196828a5dc288885cd16f0f",
    "case_0015": "226fb67d4c527bc4aacc2f428cab9d6a8b1c5cb3c149f8abba21d20ab05c2ca7",
    "case_0029": "a47f26dc730fb37280656511ef9835f6165f1997fa544f39410255094f923a58",
}
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
HEX_ADDRESS = re.compile(r"^0x[0-9a-fA-F]+$")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def text(value: object, field: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{field} is missing")
    return value


def integer(value: object, field: str, *, minimum: int = 0) -> int:
    require(isinstance(value, int) and not isinstance(value, bool) and value >= minimum, f"{field} is invalid")
    return value


def address(value: object, field: str) -> str:
    value = text(value, field)
    require(HEX_ADDRESS.fullmatch(value) is not None and int(value, 16) > 0, f"{field} is invalid")
    return value.lower()


def sha(value: object, field: str) -> str:
    value = text(value, field).lower()
    require(HEX64.fullmatch(value) is not None, f"{field} is not SHA-256")
    return value


def safe_path(value: object, field: str) -> str:
    value = text(value, field).replace("\\", "/")
    parsed = PurePosixPath(value)
    require(not parsed.is_absolute() and all(part not in ("", ".", "..") for part in parsed.parts), f"{field} is unsafe")
    return parsed.as_posix()


def identity(row: dict[str, Any], field: str, case: str) -> dict[str, str | int]:
    require(row.get("case_id") == case, f"{field}.case_id mismatch")
    run_id = text(row.get("run_id"), f"{field}.run_id")
    pid = integer(row.get("ae_pid"), f"{field}.ae_pid", minimum=1)
    base = address(row.get("module_base"), f"{field}.module_base")
    require(text(row.get("aex_sha256"), f"{field}.aex_sha256").lower() == AEX_SHA256, f"{field}.aex_sha256 mismatch")
    require(row.get("ae_version") == AE_VERSION, f"{field}.ae_version mismatch")
    require(row.get("renderer") == "Software", f"{field}.renderer mismatch")
    require(row.get("project_bits_per_channel") == 8, f"{field}.project_bits_per_channel mismatch")
    require(sha(row.get("input_sha256"), f"{field}.input_sha256") == INPUT_SHA256[case], f"{field}.input_sha256 mismatch")
    require(sha(row.get("output_sha256"), f"{field}.output_sha256") == OUTPUT_SHA256[case], f"{field}.output_sha256 mismatch")
    return {"run_id": run_id, "ae_pid": pid, "module_base": base}


def validate_sample(row: object, field: str, *, index: int | None = None, neighborhood: bool = False) -> dict[str, Any]:
    require(isinstance(row, dict), f"{field} is not an object")
    callback_index = integer(row.get("callback_index"), f"{field}.callback_index")
    if index is not None:
        require(callback_index == index, f"{field}.callback_index is not sequential")
    x, y = row.get("x"), row.get("y")
    require(isinstance(x, int) and not isinstance(x, bool) and isinstance(y, int) and not isinstance(y, bool), f"{field}.coordinate is invalid")
    if neighborhood:
        require(395 <= x <= 399 and 279 <= y <= 283, f"{field} is outside target neighborhood")
    return {"callback_index": callback_index, "x": x, "y": y, "output_addr": address(row.get("output_addr"), f"{field}.output_addr")}


def validate_case(row: object, expected_case: str, global_run: str | None) -> dict[str, Any]:
    require(isinstance(row, dict), f"{expected_case} case is not an object")
    require(row.get("status") == "answered", f"{expected_case} is not answered")
    ident = identity(row, expected_case, expected_case)
    require(global_run is None or ident["run_id"] == global_run, f"{expected_case}.run_id differs")
    pf8, pf32 = row.get("pf8"), row.get("pf32")
    require(isinstance(pf8, dict), f"{expected_case}.pf8 is missing")
    require(isinstance(pf32, dict), f"{expected_case}.pf32 is missing")
    total = integer(pf8.get("total_count"), f"{expected_case}.pf8.total_count", minimum=1)
    min_x, max_x = integer(pf8.get("min_x"), f"{expected_case}.pf8.min_x"), integer(pf8.get("max_x"), f"{expected_case}.pf8.max_x")
    min_y, max_y = integer(pf8.get("min_y"), f"{expected_case}.pf8.min_y"), integer(pf8.get("max_y"), f"{expected_case}.pf8.max_y")
    require(min_x <= max_x and min_y <= max_y, f"{expected_case}.pf8 envelope is inverted")
    first16 = pf8.get("first16")
    require(isinstance(first16, list) and len(first16) == min(16, total), f"{expected_case}.pf8.first16 count mismatch")
    samples = [validate_sample(item, f"{expected_case}.pf8.first16[{i}]", index=i) for i, item in enumerate(first16)]
    require(all(min_x <= item["x"] <= max_x and min_y <= item["y"] <= max_y for item in samples), f"{expected_case}.pf8.first16 outside envelope")
    neighbor_count = integer(pf8.get("target_neighborhood_count"), f"{expected_case}.pf8.target_neighborhood_count")
    require(neighbor_count <= total, f"{expected_case}.pf8 neighborhood exceeds total")
    neighbors = pf8.get("target_neighborhood_samples")
    require(isinstance(neighbors, list) and len(neighbors) == min(64, neighbor_count), f"{expected_case}.pf8 neighborhood sample count mismatch")
    neighbor_rows = [validate_sample(item, f"{expected_case}.pf8.target_neighborhood_samples[{i}]", neighborhood=True) for i, item in enumerate(neighbors)]
    require(all(neighbor_rows[i]["callback_index"] < neighbor_rows[i + 1]["callback_index"] for i in range(len(neighbor_rows) - 1)), f"{expected_case}.pf8 neighborhood indexes are not ordered")
    pointers = pf8.get("output_pointer_sample")
    require(isinstance(pointers, list) and len(pointers) == len(samples), f"{expected_case}.pf8 output pointer sample mismatch")
    require([item["output_addr"] for item in samples] == [address(item, f"{expected_case}.pf8.output_pointer_sample") for item in pointers], f"{expected_case}.pf8 pointer samples disagree")
    require(isinstance(pf8.get("target_coordinate_observed"), bool), f"{expected_case}.pf8 target observation missing")
    require(integer(pf32.get("count"), f"{expected_case}.pf32.count") == 0, f"{expected_case}.pf32 count is not zero")
    return {"case_id": expected_case, "run_id": ident["run_id"], "pf8": {"total_count": total, "min_x": min_x, "max_x": max_x, "min_y": min_y, "max_y": max_y, "first16": samples, "target_neighborhood_count": neighbor_count, "target_neighborhood_samples": neighbor_rows, "output_pointer_sample": [item["output_addr"] for item in samples]}, "pf32": {"count": 0}, "input_sha256": INPUT_SHA256[expected_case], "output_sha256": OUTPUT_SHA256[expected_case]}


def archive_entries(path: Path) -> tuple[zipfile.ZipFile, dict[str, str]]:
    require(path.suffix.lower() == ".zip", "return must be a ZIP")
    archive = zipfile.ZipFile(path)
    names: dict[str, str] = {}
    for name in archive.namelist():
        normalized = name.replace("\\", "/")
        require(normalized not in names, f"duplicate archive entry: {normalized}")
        names[normalized] = name
    return archive, names


def load_return(path: Path) -> tuple[dict[str, Any], zipfile.ZipFile, dict[str, str]]:
    archive, names = archive_entries(path)
    candidates = [name for name in names if PurePosixPath(name).name == "RETURN_RUNTIME_TRACE.json"]
    require(len(candidates) == 1, "expected one RETURN_RUNTIME_TRACE.json")
    payload = json.loads(archive.read(names[candidates[0]]).decode("utf-8-sig"))
    require(isinstance(payload, dict), "return JSON is not an object")
    return payload, archive, names


def verify_artifacts(payload: dict[str, Any], archive: zipfile.ZipFile, names: dict[str, str]) -> None:
    logs = payload.get("raw_logs")
    if logs is not None:
        require(isinstance(logs, dict) and logs and all(isinstance(value, str) and value.strip() for value in logs.values()), "raw log contents are missing")
    combined = [name for name in names if PurePosixPath(name).name == "combined_cdb_trace.txt"]
    require(len(combined) == 1, "combined CDB trace is missing or ambiguous")
    require(bool(archive.read(names[combined[0]]).strip()), "combined CDB trace is empty")
    case_paths: list[str] = []
    for case in payload["cases"]:
        case_id = case["case_id"]
        result = case.get("ae_result")
        if result is not None:
            require(isinstance(result, dict), f"{case_id}.ae_result is invalid")
            path_value = result.get("output_png_archive_path") or result.get("archive_path") or result.get("output_png")
            output_path = safe_path(path_value, f"{case_id}.ae_result.output_png")
            case_prefix = None
        else:
            candidates = [
                name for name in names
                if PurePosixPath(name).name == f"{case_id}.png"
                and "/output/" in f"/{name}"
            ]
            require(len(candidates) == 1, f"{case_id} output PNG is missing or ambiguous")
            output_path = candidates[0]
            case_prefix = output_path.rsplit("/output/", 1)[0]
        require(output_path in names, f"missing output file: {output_path}")
        require(hashlib.sha256(archive.read(names[output_path])).hexdigest() == case["output_sha256"], f"output hash mismatch: {case_id}")
        if case_prefix is not None:
            for filename in ("AE_SINGLE_CASE.log", "AE_SINGLE_CASE_RESULT.json", "cdb_trace.txt"):
                artifact_path = f"{case_prefix}/{filename}"
                require(artifact_path in names, f"missing {case_id} artifact: {filename}")
                require(bool(archive.read(names[artifact_path]).strip()), f"empty {case_id} artifact: {filename}")
            ae_result = json.loads(archive.read(names[f"{case_prefix}/AE_SINGLE_CASE_RESULT.json"]).decode("utf-8-sig"))
            require(ae_result.get("status") == "ok", f"{case_id} AE result is not ok")
            require(ae_result.get("project_bits_per_channel") == 8, f"{case_id} AE result depth mismatch")
            cdb_text = archive.read(names[f"{case_prefix}/cdb_trace.txt"]).decode("utf-8-sig", errors="replace")
            require("DG8_PF8_SUMMARY" in cdb_text and f"case_id={case_id}" in cdb_text, f"{case_id} CDB trace lacks census summary")
        case_paths.append(output_path)
    require([name for name in names if ("log" in name.lower() or "trace" in name.lower()) and name not in case_paths], "ZIP has no raw log/trace file")


def validate_payload(payload: dict[str, Any], archive: zipfile.ZipFile | None = None, names: dict[str, str] | None = None) -> dict[str, Any]:
    require(payload.get("status") == "answered", f"return is not answered: {payload.get('status')}")
    require(payload.get("request_id") == REQUEST_ID, "request_id mismatch")
    require(payload.get("exactness_claim") is False, "exactness claim must be false")
    kind = payload.get("kind") or CANONICAL_KIND
    require(kind in (CANONICAL_KIND, FIXTURE_KIND), "unexpected return kind")
    schema = payload.get("schema")
    require(schema == SCHEMA or (schema is None and kind == FIXTURE_KIND), "schema mismatch")
    require(payload.get("request_satisfied") is True, "request is not satisfied")
    cases = payload.get("cases")
    require(isinstance(cases, list) and len(cases) == 3 and {row.get("case_id") for row in cases if isinstance(row, dict)} == set(CASES), "case set is incomplete or duplicated")
    by_case = {row["case_id"]: row for row in cases}
    validated: list[dict[str, Any]] = []
    run_id: str | None = None
    for case in CASES:
        result = validate_case(by_case[case], case, run_id)
        run_id = result["run_id"]
        validated.append(result)
    if kind == CANONICAL_KIND:
        require(payload.get("run_id") == run_id, "top-level run_id mismatch")
        require(str(payload.get("aex_sha256", "")).lower() == AEX_SHA256, "top-level AEX SHA256 mismatch")
        require(payload.get("renderer") == "Software" and payload.get("project_bits_per_channel") == 8, "top-level host contract mismatch")
    else:
        require(payload.get("run_id") in (None, run_id), "top-level run_id mismatch")
        require(payload.get("aex_sha256") is None or str(payload["aex_sha256"]).lower() == AEX_SHA256, "top-level AEX SHA256 mismatch")
        require(payload.get("renderer") in (None, "Software") and payload.get("project_bits_per_channel") in (None, 8), "top-level host contract mismatch")
    if archive is not None and names is not None:
        verify_artifacts(payload, archive, names)
    format_drift = kind == FIXTURE_KIND or schema is None or payload.get("raw_logs") is None or any(row.get("ae_result") is None for row in cases)
    return {"schema": "olmdg8-coordinate-liveness-census-return-classification.v1", "kind": CANONICAL_KIND, "source_kind": kind, "format_drift": format_drift, "status": "accepted_coordinate_liveness_census", "request_id": REQUEST_ID, "request_satisfied": True, "exactness_claim": False, "run_id": run_id, "aex_sha256": AEX_SHA256, "ae_version": AE_VERSION, "renderer": "Software", "project_bits_per_channel": 8, "cases": validated, "next_action": "Use the census only as PF8 coordinate-liveness evidence; keep exact-coordinate claims closed and require a separate exact-bound witness."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("return_zip", type=Path, nargs="?")
    parser.add_argument("--runtime-summary-json", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    archive = None
    if args.runtime_summary_json:
        report = {"schema": "olmdg8-coordinate-liveness-census-return-classification.v1", "kind": CANONICAL_KIND, "status": "blocked_return_zip_required", "request_id": REQUEST_ID, "request_satisfied": False, "exactness_claim": False, "format_drift": False, "source_kind": "runtime_summary", "source": str(args.runtime_summary_json), "likely_next_focus": "return-zip-artifact-verification", "next_action": "Classify the actual Windows return ZIP; a runtime summary alone cannot prove raw log/output file presence."}
    else:
        require(args.return_zip is not None, "return ZIP is required")
        try:
            payload, archive, names = load_return(args.return_zip)
            report = validate_payload(payload, archive, names)
        finally:
            if archive is not None:
                archive.close()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text("\n".join(["# OLMDistanceGradation 8bpc Coordinate Liveness Census", "", f"- Status: `{report['status']}`", f"- Source kind: `{report['source_kind']}`", f"- Format drift: `{str(report['format_drift']).lower()}`", "- Request satisfied: yes", "- Exactness claim: no", "", "## Next Action", "", report["next_action"], ""]), encoding="utf-8")
    print(f"status={report['status']}")
    print(f"format_drift={str(report['format_drift']).lower()}")
    print(f"json={args.output_json}")
    print(f"md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
