#!/usr/bin/env python3
"""Strictly validate the AE-free native-Windows UCRT return for Radial Strength 290."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
REQUEST_ID = "olm_runtime_trace_olmradialblur_strength290_ucrt_math_20260814"
PACKAGE = ROOT / "refs/runtime_trace_packages" / REQUEST_ID
OUTPUT = ROOT / "refs/conformance/olmradialblur_strength290_ucrt_math_native_return_20260814.json"
HEX32 = re.compile(r"^0x[0-9a-f]{8}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
UCRT_PATH = re.compile(r"^[a-z]:\\windows\\system32\\ucrtbase\.dll$", re.IGNORECASE)
F32_PI = struct.unpack("<f", bytes.fromhex("db0f4940"))[0]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def strict_json(raw: bytes, label: str) -> object:
    def pairs(values: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in values:
            require(key not in result, f"{label} duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        return json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(
                              ValueError(f"{label} invalid JSON constant: {value}")))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} invalid JSON") from error


def f32_from_hex(value: str) -> float:
    return struct.unpack("<f", int(value, 16).to_bytes(4, "little"))[0]


def load_members(path: Path) -> dict[str, bytes]:
    if path.is_dir():
        items = list(path.iterdir())
        require(all(item.is_file() and not item.is_symlink() for item in items),
                "return directory must contain only direct regular files")
        return {item.name: item.read_bytes() for item in items}
    require(path.is_file() and zipfile.is_zipfile(path), "return must be a directory or ZIP")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(all(not name.endswith("/") for name in names), "ZIP directory members are forbidden")
        require(len(names) == len(set(names)), "duplicate ZIP members")
        require(len(names) == len({name.casefold() for name in names}), "case-colliding ZIP members")
        for name in names:
            pure = PurePosixPath(name)
            require(not pure.is_absolute() and ".." not in pure.parts, "unsafe ZIP member")
        return {name: archive.read(name) for name in names}


def analyze(path: Path) -> dict[str, object]:
    members = load_members(path)
    relative_names = {"run_summary.json", "request_manifest.json", "math_vectors.json"}
    require(set(members) == relative_names, "Radial return exact flat member set")

    manifest_bytes = (PACKAGE / "request_manifest.json").read_bytes()
    vectors_bytes = (PACKAGE / "math_vectors.json").read_bytes()
    require(members["request_manifest.json"] == manifest_bytes, "request manifest drift")
    require(members["math_vectors.json"] == vectors_bytes, "math vectors drift")
    manifest = strict_json(manifest_bytes, "request manifest")
    expected_rows = strict_json(vectors_bytes, "math vectors")
    summary = strict_json(members["run_summary.json"], "run summary")

    summary_keys = {
        "schema", "request_id", "status", "process_bitness", "processor_architecture",
        "ucrtbase", "vector_count", "original_call_count", "vectors_sha256", "rows",
    }
    require(isinstance(summary, dict) and set(summary) == summary_keys, "return summary schema")
    require(summary["schema"] == "olmradialblur.strength290-ucrt-math-return/1", "return schema")
    require(summary["request_id"] == REQUEST_ID == manifest["request_id"], "request id mismatch")
    require(summary["status"] == "answered_native_windows_ucrt_atan2f_log2f", "return status")
    require(type(summary["process_bitness"]) is int and summary["process_bitness"] == 64 and
            summary["processor_architecture"] == "AMD64",
            "return architecture")
    require(type(summary["vector_count"]) is int and summary["vector_count"] == 577 and
            type(summary["original_call_count"]) is int and summary["original_call_count"] == 725,
            "return vector census")
    require(summary["vectors_sha256"] == sha_bytes(vectors_bytes), "vector table hash")

    ucrt = summary["ucrtbase"]
    require(isinstance(ucrt, dict) and set(ucrt) == {
        "requested_path", "loaded_path", "file_version", "product_version", "sha256"
    }, "UCRT identity schema")
    for key in ("requested_path", "loaded_path"):
        require(isinstance(ucrt[key], str) and UCRT_PATH.fullmatch(ucrt[key]) is not None,
                f"UCRT {key} must be canonical System32 ucrtbase.dll")
    require(ucrt["requested_path"].casefold() == ucrt["loaded_path"].casefold(),
            "requested and loaded UCRT paths differ")
    require(isinstance(ucrt["file_version"], str) and ucrt["file_version"], "UCRT file version")
    require(isinstance(ucrt["product_version"], str) and ucrt["product_version"], "UCRT product version")
    require(isinstance(ucrt["sha256"], str) and SHA256.fullmatch(ucrt["sha256"]) is not None,
            "UCRT SHA-256")

    rows = summary["rows"]
    require(isinstance(rows, list) and len(rows) == len(expected_rows) == 577, "exactly 577 rows required")
    observed_keys: set[tuple[str, ...]] = set()
    for index, (expected, row) in enumerate(zip(expected_rows, rows, strict=True)):
        require(isinstance(row, dict), f"row {index} object")
        function = expected["function"]
        if function == "log2f":
            keys = {"function", "argument_bits", "call_count", "native_ucrt_result_bits"}
            identity = (function, expected["argument_bits"])
            for key in ("function", "argument_bits", "call_count"):
                require(row.get(key) == expected[key], f"row {index} input drift: {key}")
        elif function == "atan2f":
            keys = {"function", "left_bits", "right_bits", "call_count", "native_ucrt_result_bits"}
            identity = (function, expected["left_bits"], expected["right_bits"])
            for key in ("function", "left_bits", "right_bits", "call_count"):
                require(row.get(key) == expected[key], f"row {index} input drift: {key}")
        else:
            raise ValueError(f"unknown expected function at row {index}")
        require(set(row) == keys, f"row {index} schema")
        require(type(row["call_count"]) is int, f"row {index} call count type")
        require(identity not in observed_keys, f"duplicate vector key at row {index}")
        observed_keys.add(identity)
        result_bits = row["native_ucrt_result_bits"]
        require(isinstance(result_bits, str) and HEX32.fullmatch(result_bits) is not None,
                f"row {index} result bits")
        result = f32_from_hex(result_bits)
        require(math.isfinite(result), f"row {index} non-finite result")
        if function == "log2f":
            require(result == 32.0, "log2f(2^32) endpoint")
        else:
            require(-F32_PI <= result <= F32_PI, f"row {index} atan2f range")
    require(len(observed_keys) == 577, "unique vector key census")

    return {
        "schema": "olmradialblur.strength290-ucrt-math-return-analysis/1",
        "status": "PASS_NATIVE_WINDOWS_UCRT_RADIAL_577_RETURN_VALIDATED_NO_PROMOTION",
        "request_id": REQUEST_ID,
        "return_path": str(path.resolve()),
        "return_sha256": sha_bytes(path.read_bytes()) if path.is_file() else None,
        "ucrtbase": ucrt,
        "vectors": {"unique": 577, "original_call_count": 725, "log2f": 1, "atan2f": 576},
        "production_policy": "Strength 290 remains fail-closed pending native-derived exported-AEX and Mac-public final RAW closure",
        "claims_not_made": ["No production admission", "No After Effects execution"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("return_path", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.output != OUTPUT and not args.write:
        parser.error("--output requires --write")
    report = analyze(args.return_path)
    if args.write:
        args.output.write_bytes(canonical(report))
    print(report["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
