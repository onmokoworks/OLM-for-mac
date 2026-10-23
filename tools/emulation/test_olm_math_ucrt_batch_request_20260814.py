#!/usr/bin/env python3
"""Validate the combined AE-free Windows UCRT expf/powf request."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset

import argparse
import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[2]
REQUEST_ID = "olm_runtime_trace_olm_math_ucrt_batch_20260814"
PACKAGE_ROOT = ROOT / "refs/runtime_trace_packages"
PACKAGE = PACKAGE_ROOT / REQUEST_ID
PACKAGE_ZIP = PACKAGE.with_suffix(".zip")
REPORT = ROOT / "refs/conformance/olm_math_ucrt_batch_request_20260814.json"
NOTE = REPORT.with_suffix(".md")
RETURN_ANALYZER = ROOT / "scripts/analyze_olm_math_ucrt_batch_return_20260814.py"
DIRECTIONAL_ID = "olm_runtime_trace_olmdirectionalblur_remaining6_ucrt_expf_20260814"
DIRECTIONAL_POWF_ID = "olm_runtime_trace_olmdirectionalblur_remaining6_ucrt_powf_20260814"
DISTANCE_ID = "olm_runtime_trace_olmdistancegradation_pf32_power_ucrt_powf_20260813"

BATCH_FILES = {
    "README.md": "8167018bc5f1d01320971440ab6c2ae71a0b5f952b30ac634c1263c8d000152a",
    "request_manifest.json": "d7bff1ce9056949cd66d973727b0921460bf7192e47fd7be28e447446a11f2ce",
    "run_olm_math_ucrt_batch.ps1": "1230dcd4a654c933e524424de9f1f630d1ed0d9f2a05877d7042d7f27cd708cd",
}
DIRECTIONAL_POWF_FILES = {
    "README.md": "dd25461847cce962091b2765b53256fe9a55770b9c92ffc3e9377e3721b95fc9",
    "UcrtPowfCapture.cs": "86828ea99baded5fbde42269436290788dde0cad91cb592cd5cc3ec081005d03",
    "powf_vectors.json": "1f090f4c2b640150cd555acba94d71548ae5e5598616a33dcf19360c30715894",
    "request_manifest.json": "21c5927720116b95623971a54bb06264c81ef4b6a146d43da1c7cb3c02892faf",
    "run_olmdirectionalblur_remaining6_ucrt_powf.ps1": "5ba2b6e889fcb18fabd9f8657ae8485ccc7fd14c23d417d3d1848765355d9f70",
}
DIRECTIONAL_FILES = {
    "README.md": "e5de4d10dea896aa8f9c024db9435b7d4ab3703ce2e3eca87bdbae9626f24e09",
    "UcrtExpfCapture.cs": "abba08ce55644ac7ace25bdca91aa938c4efc73e94290b046f99e60fec1f3515",
    "expf_vectors.json": "f48aa088fe1040d3985a7b8eeb66211c082ff716b07ba1ac002129d7dd18b1a8",
    "request_manifest.json": "2979fc4de8813b5838f966305c06c1af1b2cc050b5f1fa3641fa9f94c65b3c53",
    "run_olmdirectionalblur_remaining6_ucrt_expf.ps1": "39f3b18674a73d83e1d8f1a968ba7359ee00c996c9c76e78cee483fc20a9fd3d",
}
DISTANCE_FILES = {
    "README.md": "b2edf84165a85f4d0a7aa6e26483bd0463057c296aa343d264630295f70d6d5c",
    "SHA256SUMS.txt": "d8f6275edfcd8c5f72ede238d3db1bf93ffc2add28b5c1f55b531a55590b03ed",
    "UcrtPowfCapture.cs": "86828ea99baded5fbde42269436290788dde0cad91cb592cd5cc3ec081005d03",
    "powf_vectors.json": "5fb5f5f7d6303e05bf1ed9219465901ae6f9f41f2a1f66ecb07d874eaff7432c",
    "request_manifest.json": "bfb3353d74943e57747f737e57aa4222b7c8e92af73f4eef88cd6e6f072dbcb2",
    "run_olmdistancegradation_pf32_power_ucrt_powf.ps1": "674c3c83c612a8926e0d3c93835b6712422dea033c96c52968894c7f42fe7b60",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(resolve_asset(path).read_bytes()).hexdigest()


def expected_manifest() -> dict[str, object]:
    return {
        "acceptance": "One 64-bit x64 PowerShell invocation returns all 494 DirectionalBlur expf rows, all 787 DirectionalBlur powf keys, and all 63 DistanceGradation powf rows against one exact System32 ucrtbase.dll identity.",
        "child_requests": {"directional": DIRECTIONAL_ID, "directional_powf": DIRECTIONAL_POWF_ID, "distance": DISTANCE_ID},
        "claims_not_made": [
            "No native After Effects execution",
            "No production admission from returned math words alone",
            "No substitution of AEXCompat or macOS libSystem for Windows UCRT",
            "No extrapolation beyond the exact 1344 request vectors",
        ],
        "request_id": REQUEST_ID,
        "schema": "olm.math-ucrt-batch-request/1",
        "status": "ready_native_windows_no_ae_required",
        "target": {
            "path": "%WINDIR%\\System32\\ucrtbase.dll",
            "process": "64-bit x64 PowerShell",
            "symbols": ["expf", "powf"],
        },
        "vectors": {"directional_expf": 494, "directional_powf": 787, "distance_powf": 63, "total": 1344},
    }


def check_files(directory: Path, expected: dict[str, str]) -> None:
    directory = resolve_asset(directory)
    actual = sorted(path.name for path in directory.iterdir() if path.is_file())
    if actual != sorted(expected):
        raise ValueError(f"file-set drift: {directory}")
    for name, expected_hash in expected.items():
        if sha256(directory / name) != expected_hash:
            raise ValueError(f"hash drift: {directory.name}/{name}")


def zip_sources() -> dict[str, bytes]:
    sources = {}
    for request_id, expected in ((REQUEST_ID, BATCH_FILES), (DIRECTIONAL_ID, DIRECTIONAL_FILES),
                                 (DIRECTIONAL_POWF_ID, DIRECTIONAL_POWF_FILES),
                                 (DISTANCE_ID, DISTANCE_FILES)):
        directory = PACKAGE_ROOT / request_id
        for name in expected:
            sources[f"{request_id}/{name}"] = resolve_asset(directory / name).read_bytes()
    return sources


def write_zip() -> None:
    with zipfile.ZipFile(PACKAGE_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(zip_sources().items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)


def validate_zip() -> str:
    archive_path = resolve_asset(PACKAGE_ZIP)
    if not archive_path.is_file() or not zipfile.is_zipfile(archive_path):
        raise ValueError("batch transfer ZIP missing")
    expected = zip_sources()
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError("batch transfer ZIP member set")
        for name, data in expected.items():
            if archive.read(name) != data:
                raise ValueError(f"batch transfer ZIP content: {name}")
    return sha256(PACKAGE_ZIP)


def validate_package(package: Path = PACKAGE) -> dict[str, object]:
    package = resolve_asset(package)
    check_files(package, BATCH_FILES)
    check_files(PACKAGE_ROOT / DIRECTIONAL_ID, DIRECTIONAL_FILES)
    check_files(PACKAGE_ROOT / DIRECTIONAL_POWF_ID, DIRECTIONAL_POWF_FILES)
    check_files(PACKAGE_ROOT / DISTANCE_ID, DISTANCE_FILES)
    if json.loads((package / "request_manifest.json").read_text()) != expected_manifest():
        raise ValueError("batch manifest drift")
    script = (package / "run_olm_math_ucrt_batch.ps1").read_text()
    required = (
        '$env:PROCESSOR_ARCHITECTURE -ne "AMD64"',
        "run_olmdirectionalblur_remaining6_ucrt_expf.ps1",
        "run_olmdirectionalblur_remaining6_ucrt_powf.ps1",
        "run_olmdistancegradation_pf32_power_ucrt_powf.ps1",
        "$directional.vector_count -ne 494",
        "$directionalPowf.vector_count -ne 787",
        "$distance.vector_count -ne 63",
        "$directional.ucrtbase.sha256 -ne $distance.ucrtbase.sha256",
        'schema="olm.math-ucrt-batch-return/1"',
        'status="answered_native_windows_ucrt_expf_powf"',
        "Compress-Archive",
    )
    if any(token not in script for token in required):
        raise ValueError("batch script contract drift")
    forbidden = ("AfterFX", "aerender", "DoScript", "Start-Process")
    if any(token.lower() in script.lower() for token in forbidden):
        raise ValueError("batch script launches a host process")
    zip_sha256 = validate_zip()
    return {
        "batch": BATCH_FILES,
        "directional": DIRECTIONAL_FILES,
        "directional_powf": DIRECTIONAL_POWF_FILES,
        "distance": DISTANCE_FILES,
        "zip_sha256": zip_sha256,
    }


def build_report(package: Path = PACKAGE) -> dict[str, object]:
    files = validate_package(package)
    return {
        "schema": "olm.math-ucrt-batch-request-closure/1",
        "status": "ready_native_windows_ucrt_batch_ae_free",
        "request_id": REQUEST_ID,
        "package": {
            "path": str(package.relative_to(ROOT)),
            "files": files["batch"],
            "transfer_zip": str(PACKAGE_ZIP.relative_to(ROOT)),
            "transfer_zip_sha256": files["zip_sha256"],
        },
        "children": {
            "directional": {"request_id": DIRECTIONAL_ID, "files": files["directional"], "vectors": 494, "symbol": "expf"},
            "directional_powf": {"request_id": DIRECTIONAL_POWF_ID, "files": files["directional_powf"], "vectors": 787, "symbol": "powf"},
            "distance": {"request_id": DISTANCE_ID, "files": files["distance"], "vectors": 63, "symbol": "powf"},
        },
        "acceptance": {
            "one_amd64_process": True,
            "same_system32_ucrt_identity_required": True,
            "all_1344_rows_required": True,
            "after_effects_required": False,
        },
        "return_validation": {
            "path": str(RETURN_ANALYZER.relative_to(ROOT)),
            "sha256": sha256(RETURN_ANALYZER),
            "exact_child_manifests_and_vectors_required": True,
            "exact_child_summary_hashes_required": True,
            "same_ucrt_identity_required": True,
            "unknown_members_and_keys_rejected": True,
        },
        "boundary": {
            "native_windows_return_included": False,
            "production_admission_changed": False,
            "directional_six_remain_fail_closed": True,
            "distance_power_eight_remain_fail_closed": True,
            "returned_words_alone_sufficient_for_promotion": False,
        },
    }


def validate(report: dict[str, object], package: Path = PACKAGE) -> bool:
    try:
        return report == build_report(package)
    except (OSError, ValueError, json.JSONDecodeError):
        return False


def render_note(report: dict[str, object]) -> str:
    return f"""# OLM native UCRT math batch request

- Status: `{report['status']}`
- DirectionalBlur: 494 exact `expf` source-expression rows
- DirectionalBlur: 787 exact actual-call `powf` keys
- DistanceGradation: 63 exact `powf` pairs
- Total: 1,344 rows in one 64-bit AMD64 process
- After Effects required: no

The batch requires both child results to report the same exact System32
`ucrtbase.dll` identity. It changes no production admission: DirectionalBlur's
six x86_64 cells and DistanceGradation's eight PF32 Power cells remain
fail-closed until their respective downstream public-output evidence is also
complete.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.write:
            write_zip()
        current = build_report()
        if args.write:
            REPORT.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
            NOTE.write_text(render_note(current))
        persisted = json.loads(REPORT.read_text())
        if persisted != current or not validate(persisted):
            raise ValueError("persisted batch request drift")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL_OLM_MATH_UCRT_BATCH_REQUEST: {exc}")
        return 1
    print("PASS_OLM_MATH_UCRT_BATCH_REQUEST_READY_AE_FREE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
