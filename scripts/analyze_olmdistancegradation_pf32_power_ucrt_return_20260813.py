#!/usr/bin/env python3
"""Strictly validate a native Windows UCRT powf return for DG PF32 Power."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_pf32_power_ucrt_powf_20260813"
XMM_CLOSURE = ROOT / "refs/conformance/olmdistancegradation_actual_aex_powf_xmm_closure_20260814.json"
XMM_CLOSURE_SHA256 = "35f908a8f0f85b5fa39ebc21ba32abcc6e30245cbc7b7ba5bd11cb66d324978d"
REQUEST_ID = "olm_runtime_trace_olmdistancegradation_pf32_power_ucrt_powf_20260813"
OUTPUT = ROOT / "refs/conformance/olmdistancegradation_pf32_power_ucrt_native_return_20260813.json"
HEX32 = re.compile(r"^0x[0-9a-f]{8}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
UCRT_PATH = re.compile(r"^[a-z]:\\windows\\system32\\ucrtbase\.dll$", re.IGNORECASE)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_return(path: Path) -> tuple[dict[str, object], dict[str, bytes]]:
    if path.is_dir():
        members = {item.relative_to(path).as_posix(): item.read_bytes() for item in path.rglob("*") if item.is_file()}
    else:
        require(path.is_file() and zipfile.is_zipfile(path), "return must be a directory or ZIP")
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            require(len(names) == len(set(names)), "duplicate ZIP members")
            for name in names:
                pure = PurePosixPath(name)
                require(not pure.is_absolute() and ".." not in pure.parts, "unsafe ZIP member")
            members = {name: archive.read(name) for name in names if not name.endswith("/")}
    candidates = [name for name in members if PurePosixPath(name).name == "run_summary.json"]
    require(len(candidates) == 1, "return must contain exactly one run_summary.json")
    summary = json.loads(members[candidates[0]])
    require(isinstance(summary, dict), "run summary must be an object")
    return summary, members


def analyze(path: Path) -> dict[str, object]:
    require(sha_bytes(XMM_CLOSURE.read_bytes()) == XMM_CLOSURE_SHA256, "actual-AEX XMM closure drift")
    xmm = json.loads(XMM_CLOSURE.read_text())
    require(str(xmm.get("status", "")).startswith("PASS_ACTUAL_AEX_POWER8_XMM_INPUTS"), "actual-AEX XMM closure status")
    summary, members = load_return(path)
    expected_vectors_bytes = (PACKAGE / "powf_vectors.json").read_bytes()
    expected_request_bytes = (PACKAGE / "request_manifest.json").read_bytes()
    expected_vectors = json.loads(expected_vectors_bytes)
    summary_keys = {
        "schema", "request_id", "status", "process_bitness",
        "processor_architecture", "ucrtbase", "vector_count",
        "vectors_sha256", "rows",
    }
    require(set(summary) == summary_keys, "return summary schema")
    require(summary.get("schema") == "olmdistancegradation.pf32-power-ucrt-powf-return/1", "return schema")
    require(summary.get("request_id") == REQUEST_ID, "return request id")
    require(summary.get("status") == "answered_native_windows_ucrt_powf", "return status")
    require(summary.get("process_bitness") == 64, "return process bitness")
    require(summary.get("processor_architecture") == "AMD64", "return process architecture")
    require(summary.get("vector_count") == 63, "return vector count")
    require(summary.get("vectors_sha256") == sha_bytes(expected_vectors_bytes), "return vector file hash")
    request_members = [name for name in members if PurePosixPath(name).name == "request_manifest.json"]
    vector_members = [name for name in members if PurePosixPath(name).name == "powf_vectors.json"]
    summary_members = [name for name in members if PurePosixPath(name).name == "run_summary.json"]
    require(len(members) == 3, "return must contain exactly three files")
    require(len(summary_members) == 1, "return summary member")
    parents = {PurePosixPath(name).parent for name in members}
    require(len(parents) == 1 and next(iter(parents)).name == REQUEST_ID,
            "return members must share the exact request directory")
    require(len(request_members) == 1 and members[request_members[0]] == expected_request_bytes, "returned request manifest drift")
    require(len(vector_members) == 1 and members[vector_members[0]] == expected_vectors_bytes, "returned vectors drift")

    ucrt = summary.get("ucrtbase")
    require(isinstance(ucrt, dict) and set(ucrt) == {"path", "file_version", "product_version", "sha256"}, "UCRT identity schema")
    require(isinstance(ucrt["path"], str) and UCRT_PATH.fullmatch(ucrt["path"]) is not None,
            "UCRT canonical System32 path")
    require(isinstance(ucrt["file_version"], str) and ucrt["file_version"], "UCRT file version")
    require(isinstance(ucrt["product_version"], str) and ucrt["product_version"], "UCRT product version")
    require(isinstance(ucrt["sha256"], str) and SHA256.fullmatch(ucrt["sha256"]) is not None, "UCRT SHA-256")

    rows = summary.get("rows")
    require(isinstance(rows, list) and len(rows) == 63, "return rows")
    expected_by_key = {(row["input_bits"], row["exponent_bits"]): row for row in expected_vectors}
    returned_by_key: dict[tuple[str, str], dict[str, object]] = {}
    exact_keys = {
        "input_bits", "exponent_bits", "native_ucrt_result_bits", "occurrences",
        "ucrtbase_path", "ucrtbase_file_version", "ucrtbase_product_version", "ucrtbase_sha256",
    }
    for row in rows:
        require(isinstance(row, dict) and set(row) == exact_keys, "return row schema")
        require(isinstance(row["input_bits"], str) and HEX32.fullmatch(row["input_bits"]) is not None,
                "input bits")
        require(isinstance(row["exponent_bits"], str) and HEX32.fullmatch(row["exponent_bits"]) is not None,
                "exponent bits")
        key = (row["input_bits"], row["exponent_bits"])
        require(key in expected_by_key and key not in returned_by_key, "unknown or duplicate return vector")
        require(row["occurrences"] == expected_by_key[key]["occurrences"], "return occurrence count")
        require(isinstance(row["native_ucrt_result_bits"], str) and HEX32.fullmatch(row["native_ucrt_result_bits"]) is not None, "native result bits")
        require(row["ucrtbase_path"] == ucrt["path"], "row UCRT path")
        require(row["ucrtbase_file_version"] == ucrt["file_version"], "row UCRT file version")
        require(row["ucrtbase_product_version"] == ucrt["product_version"], "row UCRT product version")
        require(row["ucrtbase_sha256"] == ucrt["sha256"], "row UCRT hash")
        returned_by_key[key] = row
    require(set(returned_by_key) == set(expected_by_key), "return vector keyset")

    differences = []
    for key in sorted(expected_by_key):
        expected = expected_by_key[key]
        returned = returned_by_key[key]
        if returned["native_ucrt_result_bits"] != expected["host_result_bits"]:
            differences.append({
                "input_bits": key[0],
                "exponent_bits": key[1],
                "host_substituted_result_bits": expected["host_result_bits"],
                "native_ucrt_result_bits": returned["native_ucrt_result_bits"],
                "occurrences": expected["occurrences"],
            })
    return {
        "schema": "olmdistancegradation.pf32-power-ucrt-return-analysis/1",
        "status": "PASS_NATIVE_UCRT_RETURN_VALIDATED_POWER_STILL_NOT_PROMOTED",
        "request_id": REQUEST_ID,
        "return_path": str(path.resolve()),
        "return_sha256": sha_bytes(path.read_bytes()) if path.is_file() else None,
        "request_manifest_sha256": sha_bytes(expected_request_bytes),
        "vectors_sha256": sha_bytes(expected_vectors_bytes),
        "vector_count": 63,
        "ucrtbase": ucrt,
        "native_vs_host_substituted": {
            "equal_vectors": 63 - len(differences),
            "different_vectors": len(differences),
            "differences": differences,
        },
        "actual_aex_xmm_closure_sha256": XMM_CLOSURE_SHA256,
        "production_policy": "PF32 Power remains fail-closed until all eight native-UCRT-derived final public outputs are proven",
        "claims_not_made": [
            "The UCRT-only return does not itself prove XMM inputs; the separately pinned actual-AEX closure supplies that relation",
            "No final PF32 Power public output exactness",
            "No production admission",
            "No After Effects execution",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("return_path", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    report = analyze(args.return_path)
    if args.write:
        args.output.write_bytes(canonical(report))
    print(report["status"])
    print(json.dumps(report["native_vs_host_substituted"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
