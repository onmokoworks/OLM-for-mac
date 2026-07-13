#!/usr/bin/env python3
"""Validate and analyze a Windows UCRT expf Gaussian-table return on macOS."""

from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import hashlib
import json
import math
import shutil
import struct
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Callable


REQUEST_ID = "olm_runtime_trace_olmdirectionalblur_ucrt_expf_gaussian_tables_20260711"
EXPECTED_TABLES = {96: range(0, 96), 240: range(0, 240)}
REQUIRED_ROW_FIELDS = (
    "request_id",
    "n",
    "i",
    "numerator_int",
    "numerator_f32",
    "numerator_f32_hex",
    "ratio_f32",
    "ratio_f32_hex",
    "ratio_square_f32",
    "ratio_square_f32_hex",
    "denominator_f64",
    "denominator_f64_hex",
    "denominator_f32",
    "denominator_f32_hex",
    "arg_f32",
    "arg_f32_hex",
    "expf_result_f32",
    "expf_result_f32_hex",
    "os_description",
    "os_architecture",
    "process_architecture",
    "process_bitness",
    "framework_description",
    "clr_version",
    "powershell_edition",
    "powershell_version",
    "ucrtbase_path",
    "ucrtbase_file_version",
    "ucrtbase_product_version",
    "ucrtbase_sha256",
)


class AnalysisError(RuntimeError):
    """Raised when the return does not satisfy the acceptance contract."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Windows return zip or extracted directory.")
    parser.add_argument("--output-json", type=Path, required=True, help="Write analysis JSON here.")
    parser.add_argument("--output-md", type=Path, required=True, help="Write analysis Markdown here.")
    parser.add_argument(
        "--emit-table-json",
        type=Path,
        default=None,
        help="Optional validated UCRT result-word export containing provenance only.",
    )
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AnalysisError(message)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def extract_if_zip(source: Path, dest: Path) -> tuple[Path, bool]:
    source = source.resolve()
    if source.is_dir():
        return source, False
    if not source.exists() or not zipfile.is_zipfile(source):
        raise AnalysisError(f"source is neither a directory nor a zip: {source}")
    with zipfile.ZipFile(source) as archive:
        for member in archive.infolist():
            normalized = member.filename.replace("\\", "/")
            parts = [
                part
                for part in normalized.split("/")
                if part and part not in {".", ".."} and not part.startswith("._")
            ]
            if not parts or "__MACOSX" in parts:
                continue
            target = dest.joinpath(*parts)
            if member.is_dir() or normalized.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
    visible = [
        child
        for child in dest.iterdir()
        if child.name != "__MACOSX" and not child.name.startswith("._")
    ]
    roots = [child for child in visible if child.is_dir()]
    if len(visible) == 1 and len(roots) == 1:
        return roots[0], True
    return dest, True


def find_unique(root: Path, filename: str) -> Path:
    matches = sorted(
        path
        for path in root.rglob(filename)
        if "__MACOSX" not in path.parts and not path.name.startswith("._")
    )
    ensure(matches, f"missing required artifact: {filename}")
    ensure(len(matches) == 1, f"expected exactly one {filename}, found {len(matches)}")
    return matches[0]


def load_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    ensure(isinstance(data, dict), f"{path} must contain a top-level JSON object")
    return data


def sha256_hex(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def f64(value: float) -> float:
    return struct.unpack("<d", struct.pack("<d", float(value)))[0]


def u32_from_f32(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", float(value)))[0]


def f32_from_u32(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits))[0]


def u64_from_f64(value: float) -> int:
    return struct.unpack("<Q", struct.pack("<d", float(value)))[0]


def parse_u32_hex(value: Any, field: str) -> int:
    try:
        parsed = int(str(value), 16)
    except Exception as exc:  # noqa: BLE001
        raise AnalysisError(f"{field} must be a hex uint32: {value!r}") from exc
    ensure(0 <= parsed <= 0xFFFFFFFF, f"{field} out of uint32 range: {value!r}")
    return parsed


def parse_u64_hex(value: Any, field: str) -> int:
    try:
        parsed = int(str(value), 16)
    except Exception as exc:  # noqa: BLE001
        raise AnalysisError(f"{field} must be a hex uint64: {value!r}") from exc
    ensure(0 <= parsed <= 0xFFFFFFFFFFFFFFFF, f"{field} out of uint64 range: {value!r}")
    return parsed


def parse_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise AnalysisError(f"{field} must be an integer, got bool")
    try:
        return int(value)
    except Exception as exc:  # noqa: BLE001
        raise AnalysisError(f"{field} must be an integer: {value!r}") from exc


def parse_float_text(value: Any, field: str) -> float:
    try:
        return float(value)
    except Exception as exc:  # noqa: BLE001
        raise AnalysisError(f"{field} must be a float-compatible value: {value!r}") from exc


def format_u32(bits: int) -> str:
    return f"0x{bits:08X}"


def ulp_distance_u32(a: int, b: int) -> int:
    return abs(a - b)


def load_local_expf() -> tuple[Callable[[float], int] | None, str | None]:
    libraries = (
        None,
        "/usr/lib/libSystem.B.dylib",
        "/usr/lib/libm.dylib",
    )
    for library in libraries:
        try:
            handle = ctypes.CDLL(None if library is None else library)
            symbol = handle.expf
            symbol.argtypes = [ctypes.c_float]
            symbol.restype = ctypes.c_float
        except Exception:
            continue

        def call(bits: float, _symbol: Any = symbol) -> int:
            return u32_from_f32(float(_symbol(ctypes.c_float(bits))))

        label = "ctypes.CDLL(None).expf" if library is None else f"ctypes.CDLL({library!r}).expf"
        return call, label
    return None, None


def local_double_exp_bits(arg_value: float) -> int:
    return u32_from_f32(f32(math.exp(float(arg_value))))


def normalize_rows_document(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = data.get("rows")
    ensure(isinstance(rows, list), "gaussian_rows.json must contain a rows list")
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        ensure(isinstance(row, dict), f"row #{index} must be a JSON object")
        normalized.append(row)
    return normalized


def validate_status_and_identity(summary: dict[str, Any], runtime: dict[str, Any]) -> None:
    ensure(summary.get("request_id") == REQUEST_ID, "run_summary.json request_id mismatch")
    ensure(runtime.get("request_id") == REQUEST_ID, "RETURN_RUNTIME_TRACE.json request_id mismatch")
    ensure(summary.get("status") == "answered", "run_summary.json status must be answered")
    ensure(runtime.get("status") == "answered", "RETURN_RUNTIME_TRACE.json status must be answered")
    for field in ("run_id", "created_at_utc", "host", "ucrtbase", "lengths", "total_rows", "artifacts"):
        ensure(summary.get(field) == runtime.get(field), f"run_summary.json and RETURN_RUNTIME_TRACE.json differ at {field}")


def validate_host(summary: dict[str, Any]) -> dict[str, Any]:
    host = summary.get("host")
    ensure(isinstance(host, dict), "run_summary.json host must be an object")
    ensure(host.get("os_architecture") == "X64", "os_architecture must be X64")
    ensure(host.get("process_architecture") == "X64", "process_architecture must be X64")
    ensure(parse_int(host.get("process_bitness"), "host.process_bitness") == 64, "process_bitness must be 64")
    return host


def validate_ucrt(summary: dict[str, Any]) -> dict[str, Any]:
    ucrt = summary.get("ucrtbase")
    ensure(isinstance(ucrt, dict), "run_summary.json ucrtbase must be an object")
    for field in ("path", "file_version", "product_version", "sha256"):
        ensure(isinstance(ucrt.get(field), str) and ucrt.get(field), f"ucrtbase.{field} must be present")
    return ucrt


def validate_lengths(summary: dict[str, Any]) -> dict[int, int]:
    lengths = summary.get("lengths")
    ensure(isinstance(lengths, list), "run_summary.json lengths must be a list")
    found: dict[int, int] = {}
    for index, row in enumerate(lengths, start=1):
        ensure(isinstance(row, dict), f"lengths[{index}] must be an object")
        n = parse_int(row.get("n"), f"lengths[{index}].n")
        row_count = parse_int(row.get("row_count"), f"lengths[{index}].row_count")
        found[n] = row_count
    ensure(found == {96: 96, 240: 240}, f"length counts mismatch: {found}")
    ensure(parse_int(summary.get("total_rows"), "total_rows") == 336, "total_rows must be 336")
    return found


def basename_map(root: Path) -> dict[str, list[Path]]:
    mapping: dict[str, list[Path]] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if "__MACOSX" in path.parts or path.name.startswith("._"):
            continue
        mapping.setdefault(path.name, []).append(path)
    return mapping


def validate_artifacts(summary: dict[str, Any], search_root: Path, rows_json_path: Path) -> list[dict[str, Any]]:
    artifacts = summary.get("artifacts")
    ensure(isinstance(artifacts, list), "run_summary.json artifacts must be a list")
    by_name = basename_map(search_root)
    validated: list[dict[str, Any]] = []
    expected_names = {"gaussian_rows.json", "gaussian_rows.csv"}
    found_names: set[str] = set()
    for index, artifact in enumerate(artifacts, start=1):
        ensure(isinstance(artifact, dict), f"artifacts[{index}] must be an object")
        raw_path = artifact.get("path")
        ensure(isinstance(raw_path, str) and raw_path, f"artifacts[{index}].path must be present")
        # Return summaries are produced on Windows but validated on macOS.
        # pathlib on POSIX treats backslashes as ordinary characters, so
        # normalize both separator styles before selecting the archive member.
        name = raw_path.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
        ensure(name, f"artifacts[{index}].path has no basename")
        candidates = by_name.get(name, [])
        ensure(candidates, f"summary artifact {name} not found in extracted return")
        ensure(len(candidates) == 1, f"summary artifact {name} is ambiguous in extracted return")
        actual_path = candidates[0]
        actual_size = actual_path.stat().st_size
        actual_hash = sha256_hex(actual_path)
        expected_size = parse_int(artifact.get("size_bytes"), f"artifacts[{index}].size_bytes")
        expected_hash = str(artifact.get("sha256") or "").lower()
        ensure(expected_hash, f"artifacts[{index}].sha256 must be present")
        ensure(actual_size == expected_size, f"artifact size mismatch for {name}: summary={expected_size} actual={actual_size}")
        ensure(
            actual_hash == expected_hash,
            f"artifact sha256 mismatch for {name}: summary={expected_hash} actual={actual_hash}",
        )
        validated.append(
            {
                "basename": name,
                "recorded_path": raw_path,
                "actual_path": str(actual_path.resolve()),
                "size_bytes": actual_size,
                "sha256": actual_hash,
            }
        )
        found_names.add(name)
    ensure(found_names == expected_names, f"artifact set mismatch: expected {sorted(expected_names)}, found {sorted(found_names)}")
    ensure(any(item["actual_path"] == str(rows_json_path.resolve()) for item in validated), "gaussian_rows.json not covered by summary artifacts")
    return sorted(validated, key=lambda row: row["basename"])


def validate_float_value(field: str, raw_value: Any, expected_bits: int) -> None:
    parsed_bits = u32_from_f32(parse_float_text(raw_value, field))
    ensure(parsed_bits == expected_bits, f"{field} text does not match {format_u32(expected_bits)}")


def validate_double_value(field: str, raw_value: Any, expected_bits: int) -> None:
    parsed_bits = u64_from_f64(parse_float_text(raw_value, field))
    ensure(parsed_bits == expected_bits, f"{field} text does not match 0x{expected_bits:016X}")


def recompute_row_bits(n: int, i: int) -> dict[str, int]:
    numerator_int = -(i * i)
    numerator_f32 = f32(float(numerator_int))
    ratio_f32 = f32(float(n) / f32(3.0))
    ratio_square_f32 = f32(ratio_f32 * ratio_f32)
    denominator_f64 = f64(float(ratio_square_f32))
    denominator_f64 = f64(denominator_f64 + denominator_f64 + 1.0e-5)
    denominator_f32 = f32(denominator_f64)
    arg_f32 = f32(numerator_f32 / denominator_f32)
    return {
        "numerator_int": numerator_int,
        "numerator_f32_bits": u32_from_f32(numerator_f32),
        "ratio_f32_bits": u32_from_f32(ratio_f32),
        "ratio_square_f32_bits": u32_from_f32(ratio_square_f32),
        "denominator_f64_bits": u64_from_f64(denominator_f64),
        "denominator_f32_bits": u32_from_f32(denominator_f32),
        "arg_f32_bits": u32_from_f32(arg_f32),
    }


def validate_rows(rows: list[dict[str, Any]], host: dict[str, Any], ucrt: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    ensure(len(rows) == 336, f"gaussian_rows.json rows length must be 336, got {len(rows)}")
    seen: set[tuple[int, int]] = set()
    by_n: dict[int, list[dict[str, Any]]] = {96: [], 240: []}
    for index, row in enumerate(rows, start=1):
        missing = [field for field in REQUIRED_ROW_FIELDS if field not in row]
        ensure(not missing, f"row #{index} missing fields: {', '.join(missing)}")
        ensure(row.get("request_id") == REQUEST_ID, f"row #{index} request_id mismatch")
        n = parse_int(row.get("n"), f"row #{index}.n")
        i = parse_int(row.get("i"), f"row #{index}.i")
        ensure(n in EXPECTED_TABLES, f"row #{index} unexpected n={n}")
        ensure(i in EXPECTED_TABLES[n], f"row #{index} unexpected i={i} for n={n}")
        key = (n, i)
        ensure(key not in seen, f"duplicate row for n={n} i={i}")
        seen.add(key)

        recomputed = recompute_row_bits(n, i)
        ensure(
            parse_int(row.get("numerator_int"), f"row #{index}.numerator_int") == recomputed["numerator_int"],
            f"row #{index} numerator_int mismatch",
        )
        numerator_f32_bits = parse_u32_hex(row.get("numerator_f32_hex"), f"row #{index}.numerator_f32_hex")
        ratio_bits = parse_u32_hex(row.get("ratio_f32_hex"), f"row #{index}.ratio_f32_hex")
        ratio_square_bits = parse_u32_hex(row.get("ratio_square_f32_hex"), f"row #{index}.ratio_square_f32_hex")
        denominator_f64_bits = parse_u64_hex(row.get("denominator_f64_hex"), f"row #{index}.denominator_f64_hex")
        denominator_f32_bits = parse_u32_hex(row.get("denominator_f32_hex"), f"row #{index}.denominator_f32_hex")
        arg_bits = parse_u32_hex(row.get("arg_f32_hex"), f"row #{index}.arg_f32_hex")
        result_bits = parse_u32_hex(row.get("expf_result_f32_hex"), f"row #{index}.expf_result_f32_hex")
        ensure(
            numerator_f32_bits == recomputed["numerator_f32_bits"],
            f"row #{index} numerator_f32 bits mismatch: {format_u32(numerator_f32_bits)}",
        )
        ensure(ratio_bits == recomputed["ratio_f32_bits"], f"row #{index} ratio_f32 bits mismatch")
        ensure(ratio_square_bits == recomputed["ratio_square_f32_bits"], f"row #{index} ratio_square_f32 bits mismatch")
        ensure(denominator_f64_bits == recomputed["denominator_f64_bits"], f"row #{index} denominator_f64 bits mismatch")
        ensure(denominator_f32_bits == recomputed["denominator_f32_bits"], f"row #{index} denominator_f32 bits mismatch")
        ensure(arg_bits == recomputed["arg_f32_bits"], f"row #{index} arg_f32 bits mismatch")

        validate_float_value(f"row #{index}.numerator_f32", row.get("numerator_f32"), numerator_f32_bits)
        validate_float_value(f"row #{index}.ratio_f32", row.get("ratio_f32"), ratio_bits)
        validate_float_value(f"row #{index}.ratio_square_f32", row.get("ratio_square_f32"), ratio_square_bits)
        validate_double_value(f"row #{index}.denominator_f64", row.get("denominator_f64"), denominator_f64_bits)
        validate_float_value(f"row #{index}.denominator_f32", row.get("denominator_f32"), denominator_f32_bits)
        validate_float_value(f"row #{index}.arg_f32", row.get("arg_f32"), arg_bits)
        validate_float_value(f"row #{index}.expf_result_f32", row.get("expf_result_f32"), result_bits)

        ensure(row.get("os_description") == host.get("os_description"), f"row #{index} os_description mismatch")
        ensure(row.get("os_architecture") == host.get("os_architecture"), f"row #{index} os_architecture mismatch")
        ensure(
            row.get("process_architecture") == host.get("process_architecture"),
            f"row #{index} process_architecture mismatch",
        )
        ensure(
            parse_int(row.get("process_bitness"), f"row #{index}.process_bitness") == parse_int(host.get("process_bitness"), "host.process_bitness"),
            f"row #{index} process_bitness mismatch",
        )
        ensure(row.get("framework_description") == host.get("framework_description"), f"row #{index} framework_description mismatch")
        ensure(row.get("clr_version") == host.get("clr_version"), f"row #{index} clr_version mismatch")
        ensure(row.get("powershell_edition") == host.get("powershell_edition"), f"row #{index} powershell_edition mismatch")
        ensure(row.get("powershell_version") == host.get("powershell_version"), f"row #{index} powershell_version mismatch")
        ensure(row.get("ucrtbase_path") == ucrt.get("path"), f"row #{index} ucrtbase_path mismatch")
        ensure(row.get("ucrtbase_file_version") == ucrt.get("file_version"), f"row #{index} ucrtbase_file_version mismatch")
        ensure(row.get("ucrtbase_product_version") == ucrt.get("product_version"), f"row #{index} ucrtbase_product_version mismatch")
        ensure(row.get("ucrtbase_sha256") == ucrt.get("sha256"), f"row #{index} ucrtbase_sha256 mismatch")

        by_n[n].append(
            {
                "i": i,
                "arg_bits": arg_bits,
                "arg_value": f32_from_u32(arg_bits),
                "result_bits": result_bits,
            }
        )

    ensure(seen == {(n, i) for n, rng in EXPECTED_TABLES.items() for i in rng}, "row set does not exactly match the expected 336 unique (n, i) pairs")
    for n, entries in by_n.items():
        entries.sort(key=lambda row: row["i"])
        expected_count = len(EXPECTED_TABLES[n])
        ensure(len(entries) == expected_count, f"table n={n} row count mismatch: expected {expected_count}, got {len(entries)}")
    return by_n


def compare_tables(by_n: dict[int, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    local_expf, local_expf_label = load_local_expf()
    comparison_env = {
        "local_macos_expf_available": local_expf is not None,
        "local_macos_expf_label": local_expf_label,
        "double_exp_then_float_label": "float32(math.exp(float(arg_f32)))",
    }
    tables: list[dict[str, Any]] = []
    for n in sorted(by_n):
        rows = by_n[n]
        mac_diffs: list[dict[str, Any]] = []
        mac_equal_count = 0
        double_diffs: list[dict[str, Any]] = []
        double_equal_count = 0
        for row in rows:
            arg_value = row["arg_value"]
            result_bits = row["result_bits"]
            if local_expf is not None:
                mac_bits = local_expf(arg_value)
                if mac_bits == result_bits:
                    mac_equal_count += 1
                else:
                    mac_diffs.append(
                        {
                            "i": row["i"],
                            "ucrt_result_f32_hex": format_u32(result_bits),
                            "local_result_f32_hex": format_u32(mac_bits),
                            "ulp_delta": ulp_distance_u32(result_bits, mac_bits),
                        }
                    )
            double_bits = local_double_exp_bits(arg_value)
            if double_bits == result_bits:
                double_equal_count += 1
            else:
                double_diffs.append(
                    {
                        "i": row["i"],
                        "ucrt_result_f32_hex": format_u32(result_bits),
                        "local_result_f32_hex": format_u32(double_bits),
                        "ulp_delta": ulp_distance_u32(result_bits, double_bits),
                    }
                )
        tables.append(
            {
                "n": n,
                "row_count": len(rows),
                "local_macos_expf_float": {
                    "available": local_expf is not None,
                    "equal_count": mac_equal_count if local_expf is not None else None,
                    "different_count": len(mac_diffs) if local_expf is not None else None,
                    "differing_indices_with_ulp": mac_diffs if local_expf is not None else [],
                },
                "double_exp_then_float": {
                    "equal_count": double_equal_count,
                    "different_count": len(double_diffs),
                    "differing_indices_with_ulp": double_diffs,
                },
            }
        )
    return tables, comparison_env


def build_validated_table_export(
    summary: dict[str, Any],
    ucrt: dict[str, Any],
    tables: list[dict[str, Any]],
    artifact_records: list[dict[str, Any]],
    by_n: dict[int, list[dict[str, Any]]],
) -> dict[str, Any]:
    return {
        "kind": "olmdirectionalblur_ucrt_expf_validated_tables",
        "request_id": REQUEST_ID,
        "generated_at_utc": utc_now(),
        "run_id": summary.get("run_id"),
        "created_at_utc": summary.get("created_at_utc"),
        "ucrtbase": {
            "path": ucrt.get("path"),
            "file_version": ucrt.get("file_version"),
            "product_version": ucrt.get("product_version"),
            "sha256": ucrt.get("sha256"),
        },
        "artifacts": [
            {
                "basename": artifact["basename"],
                "size_bytes": artifact["size_bytes"],
                "sha256": artifact["sha256"],
            }
            for artifact in artifact_records
        ],
        "tables": [
            {
                "n": table["n"],
                "row_count": table["row_count"],
                "words": [format_u32(row["result_bits"]) for row in by_n[table["n"]]],
            }
            for table in tables
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMDirectionalBlur UCRT `expf` Return Analysis",
        "",
        "This intake validates the returned artifact set and compares the captured UCRT result words against local macOS math behavior. It does not claim Windows exactness beyond the return's own recorded provenance and internal consistency checks.",
        "",
        "## Validation",
        "",
        f"- Request id: `{report['request_id']}`",
        f"- Status: `{report['status']}`",
        f"- Run id: `{report['run_id']}`",
        f"- Source archive: `{report['source']['archive_name']}`",
        f"- Input kind: `{'zip' if report['source']['was_zip'] else 'directory'}`",
        f"- Process architecture gate: `{report['host']['process_architecture']}` / `{report['host']['process_bitness']}`-bit",
        f"- OS architecture gate: `{report['host']['os_architecture']}`",
        f"- UCRT: `{report['ucrtbase']['path']}` `{report['ucrtbase']['file_version']}`",
        "",
        "## Artifact Hashes",
        "",
    ]
    for artifact in report["artifacts"]:
        lines.append(f"- `{artifact['basename']}`: `{artifact['sha256']}`")
    lines.extend(
        [
            "",
            "## Table Summary",
            "",
            "| n | rows | macOS `expf(float)` matches | double-exp-then-float matches |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for table in report["tables"]:
        mac = table["local_macos_expf_float"]
        mac_count = "unavailable" if not mac["available"] else str(mac["equal_count"])
        dbl = table["double_exp_then_float"]
        lines.append(f"| {table['n']} | {table['row_count']} | {mac_count} | {dbl['equal_count']} |")

    for table in report["tables"]:
        lines.extend(
            [
                "",
                f"## n={table['n']}",
                "",
            ]
        )
        mac = table["local_macos_expf_float"]
        if not mac["available"]:
            lines.append("- Local macOS `expf(float)` via `ctypes` was unavailable on this machine.")
        elif not mac["differing_indices_with_ulp"]:
            lines.append("- Local macOS `expf(float)` matches every captured result word.")
        else:
            lines.append("- Local macOS `expf(float)` diffs:")
            for diff in mac["differing_indices_with_ulp"]:
                lines.append(
                    f"  - `i={diff['i']}` UCRT `{diff['ucrt_result_f32_hex']}` vs macOS `{diff['local_result_f32_hex']}` (`ulp={diff['ulp_delta']}`)"
                )
        dbl = table["double_exp_then_float"]
        if not dbl["differing_indices_with_ulp"]:
            lines.append("- Double-exp-then-float matches every captured result word.")
        else:
            lines.append("- Double-exp-then-float diffs:")
            for diff in dbl["differing_indices_with_ulp"]:
                lines.append(
                    f"  - `i={diff['i']}` UCRT `{diff['ucrt_result_f32_hex']}` vs local `{diff['local_result_f32_hex']}` (`ulp={diff['ulp_delta']}`)"
                )
    return "\n".join(lines) + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    with tempfile.TemporaryDirectory(prefix="analyze_dblur_ucrt_expf_return_") as tmp:
        extracted_root, was_zip = extract_if_zip(args.source, Path(tmp) / "extract")
        summary_path = find_unique(extracted_root, "run_summary.json")
        runtime_path = find_unique(extracted_root, "RETURN_RUNTIME_TRACE.json")
        rows_json_path = find_unique(extracted_root, "gaussian_rows.json")

        summary = load_json_object(summary_path)
        runtime = load_json_object(runtime_path)
        rows_document = load_json_object(rows_json_path)
        rows = normalize_rows_document(rows_document)

        validate_status_and_identity(summary, runtime)
        host = validate_host(summary)
        ucrt = validate_ucrt(summary)
        validate_lengths(summary)
        artifact_records = validate_artifacts(summary, extracted_root, rows_json_path)
        by_n = validate_rows(rows, host, ucrt)
        tables, comparison_env = compare_tables(by_n)

        report = {
            "kind": "olmdirectionalblur_ucrt_expf_return_analysis",
            "request_id": REQUEST_ID,
            "status": "answered",
            "generated_at_utc": utc_now(),
            "run_id": summary.get("run_id"),
            "created_at_utc": summary.get("created_at_utc"),
            "source": {
                "archive_name": args.source.name,
                "was_zip": was_zip,
            },
            "host": host,
            "ucrtbase": ucrt,
            "artifacts": [
                {
                    "basename": artifact["basename"],
                    "size_bytes": artifact["size_bytes"],
                    "sha256": artifact["sha256"],
                }
                for artifact in artifact_records
            ],
            "comparison_environment": comparison_env,
            "tables": tables,
        }

        write_json(args.output_json, report)
        write_text(args.output_md, render_markdown(report))

        if args.emit_table_json is not None:
            table_export = build_validated_table_export(summary, ucrt, tables, artifact_records, by_n)
            write_json(args.emit_table_json, table_export)

    print(f"[OK] wrote {args.output_json}")
    print(f"[OK] wrote {args.output_md}")
    if args.emit_table_json is not None:
        print(f"[OK] wrote {args.emit_table_json}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AnalysisError as exc:
        raise SystemExit(fail(str(exc)))
