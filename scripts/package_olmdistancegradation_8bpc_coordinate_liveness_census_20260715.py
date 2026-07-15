#!/usr/bin/env python3
"""Build the fail-closed DG 8bpc PF8 coordinate-liveness census package."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712"
REQUEST_ID = "olmdistancegradation_8bpc_coordinate_liveness_census_20260715"
PROFILE = "distancegradation-8bpc-coordinate-liveness-census"
AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
AE_VERSION = "25.2x131"
CASES = ("case_0001", "case_0015", "case_0029")
INPUT_SHA256 = {case: "9d96a359d987774a398ec27e224650fda83fa00ae3c14bd04b87e2402ea34265" for case in CASES}
OUTPUT_SHA256 = {
    "case_0001": "7d8a37e51743efe9d9aa8dd8c70c220749039194c196828a5dc288885cd16f0f",
    "case_0015": "226fb67d4c527bc4aacc2f428cab9d6a8b1c5cb3c149f8abba21d20ab05c2ca7",
    "case_0029": "a47f26dc730fb37280656511ef9835f6165f1997fa544f39410255094f923a58",
}
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)

README = f"""# OLMDistanceGradation 8bpc Coordinate Liveness Census

Status: ready and sendable. This is a bounded observation request, not an AE
exactness claim. It deliberately does not arm or retry an exact-coordinate
condition. The PF8 callback is observed for every callback in each serial
case, with a bounded CDB timeout and bounded first/sample retention.

Each case is pinned to AE `{AE_VERSION}`, Software rendering, 8bpc, the
current AEX SHA-256 `{AEX_SHA256}`, the fixed input SHA-256, and the expected
output SHA-256 in the manifest. The return is `answered` only when all three
cases share one request run ID and each fresh AE process has complete identity,
PF8 total/min-max/first16/target-
neighborhood/count/output-pointer samples, PF32 count, and matching AE result
hashes. Any missing or inconsistent field is `exact_bind_failure`; it must not
be interpreted as AE exact or algorithm evidence.

The callback census reports `x/y` from the observed PF8 entry arguments. The
target neighborhood is the inclusive radius-2 window around `(397,281)` and is
reported as a count only. No callback is required to equal the target.

Entrypoint: `artifacts/run_olmdistancegradation_8bpc_coordinate_liveness_census_20260715.ps1`
"""

RUNNER_SOURCE = ROOT / "refs/runtime_trace_requests/olmdistancegradation_8bpc_coordinate_liveness_census_20260715.ps1"

def fixture(case: str, pid: int = 5936, base: str = "0x7fffcd660000", hash_value: str = AEX_SHA256) -> str:
    common = f"run_id=fixture-census ae_pid={pid} module_base={base} aex_sha256={hash_value} ae_version={AE_VERSION} renderer=Software project_bpc=8 case_id={case} input_sha256={INPUT_SHA256[case]} output_sha256={OUTPUT_SHA256[case]}"
    coord = f"DG8_COORD {common} x=397 y=281 callback_index=0 output_addr=0x1000"
    neighbor = f"DG8_NEIGHBOR {common} x=397 y=281 callback_index=0 output_addr=0x1000"
    pf8 = f"DG8_PF8_SUMMARY {common} total_count=1 min_x=397 max_x=397 min_y=281 max_y=281 target_neighborhood_count=1"
    pf32 = f"DG8_PF32_SUMMARY {common} count=0"
    return "\n".join((coord, neighbor, pf8, pf32)) + "\n"

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("/tmp/olmdistancegradation_8bpc_coordinate_liveness_census_20260715.zip"))
    args = parser.parse_args()
    if not SOURCE.is_dir() or not RUNNER_SOURCE.is_file():
        raise FileNotFoundError(SOURCE if not SOURCE.is_dir() else RUNNER_SOURCE)
    with tempfile.TemporaryDirectory(prefix="olmdg8_census_") as raw:
        package = Path(raw) / "olm_runtime_trace_olmdistancegradation_8bpc_coordinate_liveness_census_20260715"
        (package / "artifacts").mkdir(parents=True); (package / "scripts").mkdir(); (package / "request").mkdir()
        (package / "README_RUNTIME_TRACE.md").write_text(README, encoding="utf-8")
        shutil.copy2(RUNNER_SOURCE, package / "artifacts/run_olmdistancegradation_8bpc_coordinate_liveness_census_20260715.ps1")
        for name in ("ae_render_olmdistancegradation_8bpc_queue.jsx", "ae_render_single_case.jsx"):
            shutil.copy2(SOURCE / "scripts" / name, package / "scripts" / name)
        single_case_jsx = package / "scripts/ae_render_single_case.jsx"
        single_case_text = single_case_jsx.read_text(encoding="utf-8")
        ready_marker = '"ready case_id=" + caseId + " pid_host=AfterFX effect_loaded=1 parameters_applied=1\\n"'
        versioned_ready_marker = '"ready case_id=" + caseId + " pid_host=AfterFX ae_version=" + app.version + " effect_loaded=1 parameters_applied=1\\n"'
        if single_case_text.count(ready_marker) != 1:
            raise ValueError("single-case JSX ready marker contract changed")
        single_case_jsx.write_text(
            single_case_text.replace(ready_marker, versioned_ready_marker),
            encoding="utf-8",
        )
        shutil.copytree(SOURCE / "request", package / "request", dirs_exist_ok=True)
        manifest = {
            "schema": 1,
            "kind": "olm_runtime_trace_request_package",
            "request_id": REQUEST_ID,
            "profile": PROFILE,
            "submission_status": "ready",
            "exactness_claim": "forbidden",
            "supersedes": [
                "olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712",
            ],
            "runtime_actions": [
                {
                    "request_id": REQUEST_ID,
                    "plugin_area": "OLMDistanceGradation PF8 host-coordinate liveness census",
                    "command": "Run the packaged PowerShell entrypoint once with AE fully closed.",
                    "stop_condition": (
                        "Answered requires all three fresh-process cases with hash-pinned AEX, "
                        "Software/8bpc host identity, actual input/output hashes, PF8 total/min/max/first16/"
                        "target-neighborhood/output-pointer samples, PF32 count, and retained raw logs."
                    ),
                }
            ],
            "aex_sha256": AEX_SHA256,
            "ae_version": AE_VERSION,
            "renderer": "Software",
            "project_bits_per_channel": 8,
            "target_coordinate": [397, 281],
            "target_coordinate_required": False,
            "target_neighborhood": {
                "center": [397, 281],
                "radius": 2,
                "predicate": "397-2 <= x <= 397+2 and 281-2 <= y <= 281+2",
            },
            "cases": [
                {
                    "case_id": case,
                    "input_sha256": INPUT_SHA256[case],
                    "output_sha256": OUTPUT_SHA256[case],
                }
                for case in CASES
            ],
            "callback_contract": {
                "pf8_rva": "1170870",
                "pf32_rva": "1170c90",
                "pf8_fields": [
                    "total_count",
                    "min_x",
                    "max_x",
                    "min_y",
                    "max_y",
                    "first16",
                    "target_neighborhood_count",
                    "output_pointer_sample",
                ],
                "pf32_field": "count",
                "bounded": True,
            },
            "required_identity": [
                "run_id",
                "ae_pid",
                "module_base",
                "aex_sha256",
                "ae_version",
                "renderer",
                "project_bpc",
                "input_sha256",
                "output_sha256",
            ],
        }
        (package / "runtime_trace_package_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        template = {"schema": "olmdg_8bpc_coordinate_liveness_census_v1", "status": "answered | exact_bind_failure", "request_id": REQUEST_ID, "exactness_claim": False, "cases": [{"case_id": c, "pf8": None, "pf32": None} for c in CASES], "raw_logs": {"launcher_stdout": None, "launcher_stderr": None, "combined_cdb_trace": None}}
        (package / "RETURN_RUNTIME_TRACE_TEMPLATE.json").write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
        (package / "fixtures/complete_census.txt").parent.mkdir()
        (package / "fixtures/complete_census.txt").write_text("".join(fixture(c) for c in CASES), encoding="utf-8")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(p for p in package.rglob("*") if p.is_file()):
                info = zipfile.ZipInfo(path.relative_to(package).as_posix(), FIXED_ZIP_TIME); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        print(json.dumps({"status": "ok", "zip": str(args.output), "sha256": sha256(args.output), "files": sorted(p.relative_to(package).as_posix() for p in package.rglob('*') if p.is_file())}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
