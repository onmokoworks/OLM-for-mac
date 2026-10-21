#!/usr/bin/env python3
"""Strictly validate the combined native-Windows UCRT expf/powf return."""
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
PACKAGES = ROOT / "refs/runtime_trace_packages"
BATCH_ID = "olm_runtime_trace_olm_math_ucrt_batch_20260814"
DIRECTIONAL_ID = "olm_runtime_trace_olmdirectionalblur_remaining6_ucrt_expf_20260814"
DIRECTIONAL_POWF_ID = "olm_runtime_trace_olmdirectionalblur_remaining6_ucrt_powf_20260814"
DISTANCE_ID = "olm_runtime_trace_olmdistancegradation_pf32_power_ucrt_powf_20260813"
BATCH_PACKAGE = PACKAGES / BATCH_ID
DIRECTIONAL_PACKAGE = PACKAGES / DIRECTIONAL_ID
DIRECTIONAL_POWF_PACKAGE = PACKAGES / DIRECTIONAL_POWF_ID
DISTANCE_PACKAGE = PACKAGES / DISTANCE_ID
OUTPUT = ROOT / "refs/conformance/olm_math_ucrt_batch_native_return_20260814.json"
DISTANCE_XMM_CLOSURE = ROOT / "refs/conformance/olmdistancegradation_actual_aex_powf_xmm_closure_20260814.json"
DISTANCE_XMM_CLOSURE_SHA256 = "741dce6e7a1dd852d237072502341b40721b7cc7a9000c279f6234c10f07108a"
HEX32 = re.compile(r"^0x[0-9a-f]{8}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
UCRT_PATH = re.compile(r"^[a-z]:\\windows\\system32\\ucrtbase\.dll$", re.IGNORECASE)


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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_members(path: Path) -> dict[str, bytes]:
    if path.is_dir():
        return {item.relative_to(path).as_posix(): item.read_bytes()
                for item in path.rglob("*") if item.is_file()}
    require(path.is_file() and zipfile.is_zipfile(path), "return must be a directory or ZIP")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "duplicate ZIP members")
        normalized: dict[str, str] = {}
        casefolded: set[str] = set()
        for name in names:
            # Compress-Archive on Windows writes child members with backslash
            # separators.  Normalize that one platform difference in memory;
            # never rewrite the returned evidence ZIP.
            require(not ("/" in name and "\\" in name), "mixed ZIP separators")
            canonical_name = name.replace("\\", "/")
            pure = PurePosixPath(canonical_name)
            require(not pure.is_absolute() and ".." not in pure.parts and
                    ":" not in canonical_name, "unsafe ZIP member")
            require(pure.as_posix() == canonical_name.rstrip("/"),
                    "noncanonical ZIP member")
            require(canonical_name not in normalized, "normalized duplicate ZIP members")
            folded = canonical_name.casefold()
            require(folded not in casefolded, "case-colliding ZIP members")
            normalized[canonical_name] = name
            casefolded.add(folded)
        return {canonical: archive.read(original)
                for canonical, original in normalized.items()
                if not canonical.endswith("/")}


def suffix_member(members: dict[str, bytes], suffix: str) -> tuple[str, bytes]:
    found = [(name, data) for name, data in members.items() if name.endswith(suffix)]
    require(len(found) == 1, f"expected exactly one {suffix}")
    return found[0]


def validate_ucrt(value: object) -> dict[str, object]:
    require(isinstance(value, dict), "UCRT identity object")
    ucrt = value
    require(set(ucrt) == {"path", "file_version", "product_version", "sha256"}, "UCRT identity schema")
    require(isinstance(ucrt["path"], str) and UCRT_PATH.fullmatch(ucrt["path"]) is not None,
            "UCRT canonical System32 path")
    require(isinstance(ucrt["file_version"], str) and ucrt["file_version"], "UCRT file version")
    require(isinstance(ucrt["product_version"], str) and ucrt["product_version"], "UCRT product version")
    require(isinstance(ucrt["sha256"], str) and SHA256.fullmatch(ucrt["sha256"]) is not None,
            "UCRT SHA-256")
    return ucrt


def analyze(path: Path) -> dict[str, object]:
    require(sha_bytes(DISTANCE_XMM_CLOSURE.read_bytes()) == DISTANCE_XMM_CLOSURE_SHA256,
            "Distance actual-AEX XMM closure drift")
    xmm_closure = json.loads(DISTANCE_XMM_CLOSURE.read_text())
    require(str(xmm_closure.get("status", "")).startswith("PASS_ACTUAL_AEX_POWER8_XMM_INPUTS"),
            "Distance actual-AEX XMM closure status")
    members = load_members(path)
    require(len(members) == 11, "batch return must contain exactly eleven files")
    relative_names = {
        "run_summary.json",
        "request_manifest.json",
        "directional/run_summary.json",
        "directional/request_manifest.json",
        "directional/expf_vectors.json",
        "directional_powf/run_summary.json",
        "directional_powf/request_manifest.json",
        "directional_powf/powf_vectors.json",
        "distance/run_summary.json",
        "distance/request_manifest.json",
        "distance/powf_vectors.json",
    }
    if set(members) == relative_names:
        root = ""
    elif set(members) == {f"{BATCH_ID}/{name}" for name in relative_names}:
        root = BATCH_ID + "/"
    else:
        raise ValueError("batch exact member set")
    expected_names = {root + name for name in relative_names}
    require(set(members) == expected_names, "batch exact member set")

    batch_summary = strict_json(members[root + "run_summary.json"], "batch summary")
    directional = strict_json(members[root + "directional/run_summary.json"], "directional summary")
    directional_powf = strict_json(members[root + "directional_powf/run_summary.json"], "directional powf summary")
    distance = strict_json(members[root + "distance/run_summary.json"], "distance summary")
    require(isinstance(batch_summary, dict) and isinstance(directional, dict) and isinstance(directional_powf, dict) and isinstance(distance, dict),
            "summary objects")
    require(members[root + "request_manifest.json"] == (BATCH_PACKAGE / "request_manifest.json").read_bytes(),
            "batch manifest drift")
    require(members[root + "directional/request_manifest.json"] == (DIRECTIONAL_PACKAGE / "request_manifest.json").read_bytes(),
            "directional manifest drift")
    require(members[root + "directional/expf_vectors.json"] == (DIRECTIONAL_PACKAGE / "expf_vectors.json").read_bytes(),
            "directional vectors drift")
    require(members[root + "directional_powf/request_manifest.json"] == (DIRECTIONAL_POWF_PACKAGE / "request_manifest.json").read_bytes(),
            "directional powf manifest drift")
    require(members[root + "directional_powf/powf_vectors.json"] == (DIRECTIONAL_POWF_PACKAGE / "powf_vectors.json").read_bytes(),
            "directional powf vectors drift")
    require(members[root + "distance/request_manifest.json"] == (DISTANCE_PACKAGE / "request_manifest.json").read_bytes(),
            "distance manifest drift")
    require(members[root + "distance/powf_vectors.json"] == (DISTANCE_PACKAGE / "powf_vectors.json").read_bytes(),
            "distance vectors drift")

    batch_keys = {"schema", "request_id", "status", "process_bitness", "processor_architecture",
                  "ucrtbase", "vectors", "children"}
    require(set(batch_summary) == batch_keys, "batch summary schema")
    require(batch_summary["schema"] == "olm.math-ucrt-batch-return/1", "batch schema")
    require(batch_summary["request_id"] == BATCH_ID, "batch request id")
    require(batch_summary["status"] == "answered_native_windows_ucrt_expf_powf", "batch status")
    require(batch_summary["process_bitness"] == 64 and batch_summary["processor_architecture"] == "AMD64",
            "batch architecture")
    require(batch_summary["vectors"] == {"directional_expf": 494, "directional_powf": 787, "distance_powf": 63, "total": 1344},
            "batch vector summary")
    ucrt = validate_ucrt(batch_summary["ucrtbase"])
    children = batch_summary["children"]
    require(isinstance(children, dict) and set(children) == {"directional", "directional_powf", "distance"}, "child schema")
    for key, child_id, child_bytes in (
        ("directional", DIRECTIONAL_ID, members[root + "directional/run_summary.json"]),
        ("directional_powf", DIRECTIONAL_POWF_ID, members[root + "directional_powf/run_summary.json"]),
        ("distance", DISTANCE_ID, members[root + "distance/run_summary.json"]),
    ):
        child = children[key]
        require(isinstance(child, dict) and set(child) == {"request_id", "summary_sha256"}, "child identity schema")
        require(child["request_id"] == child_id and child["summary_sha256"] == sha_bytes(child_bytes),
                "child summary identity")

    directional_keys = {"schema", "request_id", "status", "process_bitness", "processor_architecture",
                        "ucrtbase", "counts", "vector_count", "vectors_sha256", "rows"}
    require(set(directional) == directional_keys, "directional summary schema")
    require(directional["schema"] == "olmdirectionalblur.remaining6-ucrt-expf-return/1", "directional schema")
    require(directional["request_id"] == DIRECTIONAL_ID and directional["status"] == "answered_native_windows_ucrt_expf",
            "directional identity")
    require(directional["process_bitness"] == 64 and directional["processor_architecture"] == "AMD64",
            "directional architecture")
    require(directional["counts"] == [8, 50, 96, 100, 240] and directional["vector_count"] == 494,
            "directional counts")
    directional_vectors_bytes = members[root + "directional/expf_vectors.json"]
    require(directional["vectors_sha256"] == sha_bytes(directional_vectors_bytes), "directional vector hash")
    require(validate_ucrt(directional["ucrtbase"]) == ucrt, "directional UCRT identity")
    expected_directional = json.loads(directional_vectors_bytes)
    rows = directional["rows"]
    require(isinstance(rows, list) and len(rows) == 494, "directional rows")
    dkeys = {"count", "index", "ratio_bits", "ratio_square_bits", "denominator_bits", "numerator_bits",
             "argument_bits", "native_ucrt_result_bits", "ucrtbase_path", "ucrtbase_file_version",
             "ucrtbase_product_version", "ucrtbase_sha256"}
    directional_values: dict[int, list[tuple[int, str, float]]] = {}
    repeated_arguments: dict[str, str] = {}
    for expected, row in zip(expected_directional, rows, strict=True):
        require(isinstance(row, dict) and set(row) == dkeys, "directional row schema")
        for key, value in expected.items():
            require(row[key] == value, f"directional row input drift: {key}")
        require(isinstance(row["native_ucrt_result_bits"], str) and HEX32.fullmatch(row["native_ucrt_result_bits"]),
                "directional result bits")
        require((row["ucrtbase_path"], row["ucrtbase_file_version"], row["ucrtbase_product_version"], row["ucrtbase_sha256"]) ==
                (ucrt["path"], ucrt["file_version"], ucrt["product_version"], ucrt["sha256"]),
                "directional row UCRT identity")
        result = f32_from_hex(row["native_ucrt_result_bits"])
        require(math.isfinite(result) and 0.0 < result <= 1.0, "directional expf result range")
        argument = row["argument_bits"]
        if argument in repeated_arguments:
            require(repeated_arguments[argument] == row["native_ucrt_result_bits"],
                    "directional repeated argument is nondeterministic")
        repeated_arguments[argument] = row["native_ucrt_result_bits"]
        directional_values.setdefault(row["count"], []).append((row["index"], row["native_ucrt_result_bits"], result))
    for count, values in directional_values.items():
        values.sort()
        require(values[0][0] == 0 and values[0][1] == "0x3f800000", f"directional count {count} expf(-0)")
        require(all(left[2] >= right[2] for left, right in zip(values, values[1:])),
                f"directional count {count} monotonicity")
        require(values[-1][2] < values[0][2], f"directional count {count} nonconstant curve")

    directional_powf_keys = {"schema", "request_id", "status", "process_bitness", "processor_architecture",
                             "ucrtbase", "vector_count", "vectors_sha256", "rows"}
    require(set(directional_powf) == directional_powf_keys, "directional powf summary schema")
    require(directional_powf["schema"] == "olmdirectionalblur.remaining6-ucrt-powf-return/1", "directional powf schema")
    require(directional_powf["request_id"] == DIRECTIONAL_POWF_ID and directional_powf["status"] == "answered_native_windows_ucrt_powf",
            "directional powf identity")
    require(directional_powf["process_bitness"] == 64 and directional_powf["processor_architecture"] == "AMD64",
            "directional powf architecture")
    require(directional_powf["vector_count"] == 787, "directional powf count")
    directional_powf_vectors_bytes = members[root + "directional_powf/powf_vectors.json"]
    require(directional_powf["vectors_sha256"] == sha_bytes(directional_powf_vectors_bytes), "directional powf vector hash")
    require(validate_ucrt(directional_powf["ucrtbase"]) == ucrt, "directional powf UCRT identity")
    expected_directional_powf = json.loads(directional_powf_vectors_bytes)
    directional_powf_rows = directional_powf["rows"]
    require(isinstance(directional_powf_rows, list) and len(directional_powf_rows) == 787, "directional powf rows")
    dpkeys = {"input_bits", "exponent_bits", "native_ucrt_result_bits", "ucrtbase_path",
              "ucrtbase_file_version", "ucrtbase_product_version", "ucrtbase_sha256"}
    for expected, row in zip(expected_directional_powf, directional_powf_rows, strict=True):
        require(isinstance(row, dict) and set(row) == dpkeys, "directional powf row schema")
        require(row["input_bits"] == expected["input_bits"] and row["exponent_bits"] == expected["exponent_bits"],
                "directional powf row input drift")
        require(isinstance(row["native_ucrt_result_bits"], str) and HEX32.fullmatch(row["native_ucrt_result_bits"]),
                "directional powf result bits")
        require((row["ucrtbase_path"], row["ucrtbase_file_version"], row["ucrtbase_product_version"], row["ucrtbase_sha256"]) ==
                (ucrt["path"], ucrt["file_version"], ucrt["product_version"], ucrt["sha256"]),
                "directional powf row UCRT identity")
        input_value = f32_from_hex(row["input_bits"])
        result = f32_from_hex(row["native_ucrt_result_bits"])
        require(math.isfinite(input_value) and 0.0 <= input_value <= 1.0, "directional powf input range")
        require(math.isfinite(result) and 0.0 <= result <= 1.0, "directional powf result range")
        if row["exponent_bits"] == "0x00000000":
            require(row["native_ucrt_result_bits"] == "0x3f800000", "directional powf exponent-zero endpoint")
        if row["input_bits"] == "0x3f800000":
            require(row["native_ucrt_result_bits"] == "0x3f800000", "directional powf one endpoint")

    distance_keys = {"schema", "request_id", "status", "process_bitness", "processor_architecture",
                     "ucrtbase", "vector_count", "vectors_sha256", "rows"}
    require(set(distance) == distance_keys, "distance summary schema")
    require(distance["schema"] == "olmdistancegradation.pf32-power-ucrt-powf-return/1", "distance schema")
    require(distance["request_id"] == DISTANCE_ID and distance["status"] == "answered_native_windows_ucrt_powf",
            "distance identity")
    require(distance["process_bitness"] == 64 and distance["processor_architecture"] == "AMD64",
            "distance architecture")
    require(distance["vector_count"] == 63, "distance count")
    distance_vectors_bytes = members[root + "distance/powf_vectors.json"]
    require(distance["vectors_sha256"] == sha_bytes(distance_vectors_bytes), "distance vector hash")
    require(validate_ucrt(distance["ucrtbase"]) == ucrt, "distance UCRT identity")
    expected_distance = json.loads(distance_vectors_bytes)
    rows = distance["rows"]
    require(isinstance(rows, list) and len(rows) == 63, "distance rows")
    pkeys = {"input_bits", "exponent_bits", "native_ucrt_result_bits", "occurrences",
             "ucrtbase_path", "ucrtbase_file_version", "ucrtbase_product_version", "ucrtbase_sha256"}
    distance_values: list[tuple[float, str, float]] = []
    for expected, row in zip(expected_distance, rows, strict=True):
        require(isinstance(row, dict) and set(row) == pkeys, "distance row schema")
        for key in ("input_bits", "exponent_bits", "occurrences"):
            require(row[key] == expected[key], f"distance row input drift: {key}")
        require(isinstance(row["native_ucrt_result_bits"], str) and HEX32.fullmatch(row["native_ucrt_result_bits"]),
                "distance result bits")
        require((row["ucrtbase_path"], row["ucrtbase_file_version"], row["ucrtbase_product_version"], row["ucrtbase_sha256"]) ==
                (ucrt["path"], ucrt["file_version"], ucrt["product_version"], ucrt["sha256"]),
                "distance row UCRT identity")
        input_value = f32_from_hex(row["input_bits"])
        result = f32_from_hex(row["native_ucrt_result_bits"])
        require(math.isfinite(input_value) and 0.0 <= input_value <= 1.0, "distance powf input range")
        require(math.isfinite(result) and 0.0 <= result <= 1.0, "distance powf result range")
        if row["input_bits"] == "0x00000000":
            require(row["native_ucrt_result_bits"] == "0x00000000", "distance powf zero endpoint")
        if row["input_bits"] == "0x3f800000":
            require(row["native_ucrt_result_bits"] == "0x3f800000", "distance powf one endpoint")
        distance_values.append((input_value, row["native_ucrt_result_bits"], result))
    distance_values.sort()
    require(all(left[2] <= right[2] for left, right in zip(distance_values, distance_values[1:])),
            "distance powf monotonicity")

    return {
        "schema": "olm.math-ucrt-batch-return-analysis/1",
        "status": "PASS_NATIVE_WINDOWS_UCRT_BATCH_RETURN_VALIDATED_NO_PROMOTION",
        "request_id": BATCH_ID,
        "return_path": str(path.resolve()),
        "return_sha256": sha_bytes(path.read_bytes()) if path.is_file() else None,
        "ucrtbase": ucrt,
        "vectors": {"directional_expf": 494, "directional_powf": 787, "distance_powf": 63, "total": 1344},
        "child_summary_sha256": {
            "directional": sha_bytes(members[root + "directional/run_summary.json"]),
            "directional_powf": sha_bytes(members[root + "directional_powf/run_summary.json"]),
            "distance": sha_bytes(members[root + "distance/run_summary.json"]),
        },
        "distance_actual_aex_xmm_closure_sha256": DISTANCE_XMM_CLOSURE_SHA256,
        "result_semantics": {
            "directional_expf_finite_positive_unit_interval": True,
            "directional_expf_exact_zero_argument_and_monotonic_per_count": True,
            "directional_repeated_arguments_deterministic": True,
            "directional_powf_finite_unit_interval_and_exact_endpoints": True,
            "distance_powf_finite_unit_interval": True,
            "distance_powf_exact_zero_one_endpoints_and_monotonic": True,
        },
        "production_policy": {
            "directional_six": "fail_closed_pending_native-derived public output closure",
            "distance_power_eight": "fail_closed_pending native-derived final public output closure",
        },
        "claims_not_made": ["No production admission", "No After Effects execution"],
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
