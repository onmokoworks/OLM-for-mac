#!/usr/bin/env python3
"""Validate the AE-free native-Windows UCRT expf request for DirectionalBlur."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys


ROOT = Path(__file__).resolve().parents[2]
REQUEST_ID = "olm_runtime_trace_olmdirectionalblur_remaining6_ucrt_expf_20260814"
PACKAGE = ROOT / "refs/runtime_trace_packages" / REQUEST_ID
REPORT = ROOT / "refs/conformance/olmdirectionalblur_remaining6_ucrt_expf_request_20260814.json"
NOTE = REPORT.with_suffix(".md")
SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
GAUSSIAN = ROOT / "core/dblur_gaussian.h"
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
OLDER_TABLE = ROOT / "refs/reports/dblur_ucrt_expf_return/olm_runtime_trace_olmdirectionalblur_ucrt_expf_gaussian_tables_20260711_return_windows_validated_tables.json"
BOUNDARY = ROOT / "refs/conformance/olmdirectionalblur_exported_smart_remaining6_census_20260814.json"

REQUEST_FILES = (
    "README.md",
    "UcrtExpfCapture.cs",
    "expf_vectors.json",
    "request_manifest.json",
    "run_olmdirectionalblur_remaining6_ucrt_expf.ps1",
)
COUNTS = (8, 50, 96, 100, 240)
VECTOR_KEYS = {
    "count", "index", "ratio_bits", "ratio_square_bits", "denominator_bits",
    "numerator_bits", "argument_bits",
}
EXPECTED_PROVENANCE = {
    "actual_aex_sha256": "d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e",
    "aex_import_symbol": "expf",
    "gaussian_header_sha256": "c51bfca6d7f8a3d30ac58f3a2605a2bade053876c42f1179c0e02f60adb8258c",
    "older_native_ucrt_table_sha256": "8282b5947a6688f4f26d4dd1783328b17559f163a1112b0c57a571bbd4f1965d",
    "production_source_sha256": "494116880d037a0d44a48b0e0ebe0fc5358b4cd8892b90ca8c61ea8a7bb2e845",
    "remaining_six_boundary_sha256": "5c8b2318fa66597c442e9a208e3848600e1f921f378e24563094bdd9591ae80e",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def bits(value: float) -> str:
    word = struct.unpack("<I", struct.pack("<f", value))[0]
    return f"0x{word:08x}"


def expected_vectors() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for count in COUNTS:
        ratio = f32(f32(float(count)) / f32(3.0))
        ratio_square = f32(ratio * ratio)
        denominator = f32(float(ratio_square) + float(ratio_square) + 1.0e-5)
        for index in range(count):
            numerator = f32(-float(index * index))
            argument = f32(numerator / denominator)
            rows.append({
                "count": count,
                "index": index,
                "ratio_bits": bits(ratio),
                "ratio_square_bits": bits(ratio_square),
                "denominator_bits": bits(denominator),
                "numerator_bits": bits(numerator),
                "argument_bits": bits(argument),
            })
    return rows


def expected_manifest() -> dict[str, object]:
    return {
        "acceptance": (
            "Exactly 494 Gaussian float32 arguments for counts 8, 50, 96, 100 and 240 evaluated by "
            "native System32 ucrtbase.dll!expf, with bit-exact result words and DLL identity."
        ),
        "claims_not_made": [
            "No native After Effects execution",
            "No production admission from this table alone",
            "No mixing with the older count-96/count-240 capture; all five counts are recaptured in this run",
            "No claim that AEXCompat native-f32 results are Windows UCRT results",
        ],
        "provenance": EXPECTED_PROVENANCE,
        "request_id": REQUEST_ID,
        "schema": "olmdirectionalblur.remaining6-ucrt-expf-request/1",
        "status": "ready_native_windows_no_ae_required",
        "target": {
            "path": "%WINDIR%\\System32\\ucrtbase.dll",
            "process": "64-bit x64 PowerShell",
            "symbol": "expf",
        },
        "vectors": {
            "counts": list(COUNTS),
            "count": sum(COUNTS),
            "fields": [
                "count", "index", "ratio_bits", "ratio_square_bits",
                "denominator_bits", "numerator_bits", "argument_bits",
            ],
        },
    }


def validate_live_provenance() -> None:
    live = {
        "actual_aex_sha256": sha256(AEX),
        "gaussian_header_sha256": sha256(GAUSSIAN),
        "older_native_ucrt_table_sha256": sha256(OLDER_TABLE),
        "production_source_sha256": sha256(SOURCE),
        "remaining_six_boundary_sha256": sha256(BOUNDARY),
    }
    for key, value in live.items():
        if EXPECTED_PROVENANCE[key] != value:
            raise ValueError(f"provenance drift: {key}")
    gaussian = GAUSSIAN.read_text()
    for token in (
        "const float ratio = static_cast<float>(count) / 3.0f;",
        "const float ratio_square = ratio * ratio;",
        "static_cast<double>(ratio_square) + 1.0e-5;",
        "const float numerator = static_cast<float>(-(index * index));",
        "const float argument = numerator / denominator;",
        "return ::expf(gaussian_argument(count, index));",
    ):
        if token not in gaussian:
            raise ValueError(f"gaussian formula drift: {token}")


def validate_package(package: Path = PACKAGE, *, live: bool = True) -> dict[str, object]:
    if not package.is_dir():
        raise ValueError("request package missing")
    files = tuple(sorted(path.name for path in package.iterdir() if path.is_file()))
    if files != REQUEST_FILES:
        raise ValueError(f"canonical request file set drift: {files}")

    vectors = json.loads((package / "expf_vectors.json").read_text())
    if not isinstance(vectors, list) or len(vectors) != sum(COUNTS):
        raise ValueError("vector count drift")
    if any(not isinstance(row, dict) or set(row) != VECTOR_KEYS for row in vectors):
        raise ValueError("vector schema drift")
    if vectors != expected_vectors():
        raise ValueError("float32 Gaussian argument vectors drift")

    manifest = json.loads((package / "request_manifest.json").read_text())
    if manifest != expected_manifest():
        raise ValueError("request manifest drift")

    csharp = (package / "UcrtExpfCapture.cs").read_text()
    required_csharp = (
        '[DllImport("ucrtbase.dll"',
        "CallingConvention = CallingConvention.Cdecl",
        'EntryPoint = "expf"',
        "public static extern float Expf(float value);",
        "public static uint Evaluate(uint argumentBits)",
    )
    if any(token not in csharp for token in required_csharp):
        raise ValueError("C# native expf binding drift")

    powershell = (package / "run_olmdirectionalblur_remaining6_ucrt_expf.ps1").read_text()
    required_powershell = (
        '$env:PROCESSOR_ARCHITECTURE -ne "AMD64"',
        'Join-Path $env:WINDIR "System32\\ucrtbase.dll"',
        "[UcrtExpfCapture]::Evaluate($argumentBits)",
        "native_ucrt_result_bits=(Hex32 $resultBits)",
        'schema="olmdirectionalblur.remaining6-ucrt-expf-return/1"',
        "vector_count=$rows.Count",
        "ucrtbase_sha256=$ucrt.sha256",
    )
    if any(token not in powershell for token in required_powershell):
        raise ValueError("PowerShell capture contract drift")
    forbidden = ("AfterFX", "aerender", "DoScript", "Start-Process")
    if any(token.lower() in powershell.lower() for token in forbidden):
        raise ValueError("capture script unexpectedly launches a host process")

    readme = (package / "README.md").read_text()
    for token in ("all 494 Gaussian source-expression rows", "System32\\ucrtbase.dll!expf",
                  "does not launch\nAfter Effects", "does not launch After Effects"):
        if token in readme:
            break
    else:
        raise ValueError("README scope drift")
    if "Production promotion still\nrequires" not in readme:
        raise ValueError("README promotion boundary drift")

    if live:
        validate_live_provenance()
    return {
        "files": {name: sha256(package / name) for name in REQUEST_FILES},
        "vectors": vectors,
        "manifest": manifest,
    }


def build_report(package: Path = PACKAGE, *, live: bool = True) -> dict[str, object]:
    package_data = validate_package(package, live=live)
    vectors = package_data["vectors"]
    return {
        "schema": "olmdirectionalblur.remaining6-ucrt-expf-request-closure/1",
        "status": "ready_native_windows_ucrt_capture_ae_free",
        "request_id": REQUEST_ID,
        "package": {
            "path": str(PACKAGE.relative_to(ROOT)),
            "canonical_top_level_files": list(REQUEST_FILES),
            "file_sha256": package_data["files"],
        },
        "target": expected_manifest()["target"],
        "vectors": {
            "counts": list(COUNTS),
            "count": len(vectors),
            "rows_sha256": digest(vectors),
            "first": vectors[0],
            "last": vectors[-1],
        },
        "provenance": EXPECTED_PROVENANCE,
        "acceptance": {
            "native_return_must_cover_all_494_rows": True,
            "native_return_must_bind_system32_ucrtbase_identity": True,
            "native_return_must_be_64_bit_amd64": True,
            "after_effects_required": False,
        },
        "boundary": {
            "production_admission_changed": False,
            "x86_remaining_six_currently_fail_closed": True,
            "native_windows_return_included": False,
            "aexcompat_substitute_accepted_as_windows_ucrt": False,
            "older_counts_96_240_extrapolated": False,
            "canonical_file_set_excludes_future_return_directory": True,
        },
    }


def render_note(report: dict[str, object]) -> str:
    return f"""# OLMDirectionalBlur remaining-six native UCRT request closure

- Status: `{report['status']}`
- Request: `{report['request_id']}`
- Vectors: {report['vectors']['count']} exact source-expression rows for counts 8, 50, 96, 100, 240
- Target: 64-bit AMD64 `%WINDIR%\\System32\\ucrtbase.dll!expf`
- Vector digest: `{report['vectors']['rows_sha256']}`

This is an AE-free request package, not a numerical promotion. The current
x86_64 six-cell route remains fail-closed until a native Windows return is
validated and the six fixed public outputs are rebuilt from those returned
words. AEXCompat results are not accepted, and counts 96 and 240 are recaptured
in the same run rather than mixed from an older UCRT identity.
The index-zero source row is `-0`; after the strict return proves exact `+1`,
downstream replay normalizes only that value to production's materialized `+0`.
"""


def validate(report: dict[str, object], package: Path = PACKAGE, *, live: bool = True) -> bool:
    try:
        return report == build_report(package, live=live)
    except (OSError, ValueError, json.JSONDecodeError, struct.error):
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        current = build_report()
        if args.write:
            REPORT.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
            NOTE.write_text(render_note(current))
        persisted = json.loads(REPORT.read_text())
        if not validate(persisted) or persisted != current:
            raise ValueError("persisted request closure drift")
        print("PASS_OLMDIRECTIONALBLUR_REMAINING6_NATIVE_UCRT_REQUEST_READY_AE_FREE")
        return 0
    except Exception as exc:
        print(f"FAIL_OLMDIRECTIONALBLUR_REMAINING6_NATIVE_UCRT_REQUEST: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
