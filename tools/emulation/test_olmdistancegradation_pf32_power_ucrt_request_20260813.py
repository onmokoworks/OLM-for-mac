#!/usr/bin/env python3
"""Build and validate the hostless PF32 Power UCRT-boundary request.

This intentionally does not promote PF32 Power.  It reconstructs the eight
fixed production cells, captures the exact production powf input bit patterns,
binds the host-substituted exported-AEX outputs, and packages the unique input
vectors for later native Windows ucrtbase.dll!powf evaluation.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import shutil
import struct
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
FIELDGEN = ROOT / "core/olmdistancegradation_fieldgen.cpp"
HARNESS = ROOT / "tools/emulation/dg_pf32_power_powf_census_harness_20260813.cpp"
SHIM = ROOT / "tools/emulation/dg_renderbits_real_harness_20260716_sdk_shim.h"
MATRIX = ROOT / "refs/conformance/olmdistancegradation_exported_typed_owner_matrix_20260811.json"
REPORT = ROOT / "refs/conformance/olmdistancegradation_pf32_power_ucrt_request_20260813.json"
DOC = REPORT.with_suffix(".md")
ANALYZER = ROOT / "scripts/analyze_olmdistancegradation_pf32_power_ucrt_return_20260813.py"
UNIT = ROOT / "tests/test_olmdistancegradation_pf32_power_ucrt_request_20260813.py"
XMM_CLOSURE = ROOT / "refs/conformance/olmdistancegradation_actual_aex_powf_xmm_closure_20260814.json"
PACKAGE_DIR = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_pf32_power_ucrt_powf_20260813"
PACKAGE_ZIP = PACKAGE_DIR.with_suffix(".zip")
REQUEST_ID = "olm_runtime_trace_olmdistancegradation_pf32_power_ucrt_powf_20260813"

AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
WORKER_SHA256 = "46ab907d286ad4e0e1c2065557100f02c37e0b68df4c22202a825f3fea13ef61"
SOURCE_SHA256 = "06ffc5b7a2af5cf54a2503d3bf03f9baf2269acbf1277f034937ac79c4a7aba5"
EXPECTED_CELL_SHA256 = {
    "mode2.bg0": "3e04fab22152eb32638a4864f256f76bd118ffbb6315b0c7a8b852b27509fc39",
    "mode2.bg1": "6c86caeab878b256f933d03e105085f86810f255296cc2fa5ac434dc5067e496",
    "mode3.bg0": "12bdf0c207bff9fb8c0390f848883281b8484802baea72c82f98db96c3176849",
    "mode3.bg1": "dfeb76265a320e6aae3945fdb2aaa76cd9e77f7e63f586046bca744bfad9cb07",
    "mode4.bg0": "849be120ac0c5e4990c8a19135ebfccdb2f6350ffe53cd0bb1a9f6aafb486c2a",
    "mode4.bg1": "0d8860db7bffd87c6737298482eb60d0378b2dc63841d861ee8e174aaee0a81c",
    "mode5.bg0": "40b5d262cdc0ab372036c9d2774fa9400f74daa7895c75c2222a246b01c485a5",
    "mode5.bg1": "fe715e7973fa79d6043cbe86dcfce3205869fb23ac9d69a8d98b288ab20ad6d7",
}
EXPECTED_VECTOR_DIGEST = "5fb5f5f7d6303e05bf1ed9219465901ae6f9f41f2a1f66ecb07d874eaff7432c"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def run_census() -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, str]]:
    require(sha(SOURCE) == SOURCE_SHA256, "production source identity drift")
    with tempfile.TemporaryDirectory(prefix="dg_pf32_power_ucrt_") as temporary:
        work = Path(temporary)
        executable = work / "census"
        build = subprocess.run(
            [
                "clang++", "-std=c++17", "-O0",
                "-I", str(ROOT / "tools/emulation/dg_renderbits_real_harness_20260716"),
                str(HARNESS), str(FIELDGEN), "-o", str(executable),
            ],
            text=True, capture_output=True,
        )
        require(build.returncode == 0, f"census build failed: {build.stderr}")
        run = subprocess.run([str(executable), str(work)], text=True, capture_output=True)
        require(run.returncode == 0, f"census run failed: {run.stderr}")
        calls: list[dict[str, object]] = []
        for row in csv.DictReader(io.StringIO(run.stdout)):
            calls.append({
                "blur_mode": int(row["blur_mode"]),
                "use_background": bool(int(row["use_background"])),
                "pixel_index": int(row["pixel_index"]),
                "input_bits": "0x" + row["input_bits"],
                "exponent_bits": "0x" + row["exponent_bits"],
                "host_result_bits": "0x" + row["host_result_bits"],
            })
        require(len(calls) == 8 * 17 * 11, "expected 1496 powf calls")
        for mode in range(2, 6):
            for background in (False, True):
                selected = [row for row in calls if row["blur_mode"] == mode and row["use_background"] == background]
                require([row["pixel_index"] for row in selected] == list(range(187)), "pixel order drift")
                require({row["exponent_bits"] for row in selected} == {"0x40100000"}, "power exponent drift")
        vectors_by_key: dict[tuple[str, str], dict[str, object]] = {}
        for row in calls:
            key = (str(row["input_bits"]), str(row["exponent_bits"]))
            current = vectors_by_key.setdefault(key, {
                "input_bits": key[0],
                "exponent_bits": key[1],
                "host_result_bits": row["host_result_bits"],
                "occurrences": 0,
            })
            require(current["host_result_bits"] == row["host_result_bits"], "host powf result inconsistency")
            current["occurrences"] = int(current["occurrences"]) + 1
        vectors = sorted(vectors_by_key.values(), key=lambda row: (row["input_bits"], row["exponent_bits"]))
        require(len(vectors) == 63, "unique vector count drift")
        vector_digest = sha_bytes(canonical(vectors))
        require(vector_digest == EXPECTED_VECTOR_DIGEST, "canonical vector digest drift")
        cell_hashes = {
            f"mode{mode}.bg{background}": sha(work / f"power.mode{mode}.bg{background}.raw")
            for mode in range(2, 6) for background in (0, 1)
        }
        require(cell_hashes == EXPECTED_CELL_SHA256, "production diagnostic cell hashes drift")
        return calls, vectors, cell_hashes


CS_SOURCE = r'''using System;
using System.Runtime.InteropServices;

public static class UcrtPowfCapture
{
    [DllImport("ucrtbase.dll", CallingConvention = CallingConvention.Cdecl,
        ExactSpelling = true, EntryPoint = "powf")]
    public static extern float Powf(float x, float y);

    public static uint Evaluate(uint inputBits, uint exponentBits)
    {
        float input = BitConverter.ToSingle(BitConverter.GetBytes(inputBits), 0);
        float exponent = BitConverter.ToSingle(BitConverter.GetBytes(exponentBits), 0);
        float result = Powf(input, exponent);
        return BitConverter.ToUInt32(BitConverter.GetBytes(result), 0);
    }
}
'''


PS_SOURCE = r'''param([string]$OutputDir = "")
$ErrorActionPreference = "Stop"
$requestId = "olm_runtime_trace_olmdistancegradation_pf32_power_ucrt_powf_20260813"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runRoot = if ($OutputDir) { $OutputDir } else { Join-Path $root "return" }
$runDir = Join-Path $runRoot $requestId
$zipPath = Join-Path $runRoot ($requestId + "_return_windows.zip")
$ucrtPath = Join-Path $env:WINDIR "System32\ucrtbase.dll"

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  [IO.File]::WriteAllText($Path, $Content, (New-Object Text.UTF8Encoding($false)))
}
function Sha([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Hex32([uint32]$Value) { "0x{0:x8}" -f $Value }

if (-not [Environment]::Is64BitProcess -or $env:PROCESSOR_ARCHITECTURE -ne "AMD64") {
  throw "Run from 64-bit x64 PowerShell"
}
if (-not (Test-Path -LiteralPath $ucrtPath)) { throw "Missing $ucrtPath" }
if (Test-Path -LiteralPath $runDir) { Remove-Item -LiteralPath $runDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $runRoot | Out-Null
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
Add-Type -LiteralPath (Join-Path $root "UcrtPowfCapture.cs")
$vectors = Get-Content -Raw -LiteralPath (Join-Path $root "powf_vectors.json") | ConvertFrom-Json
$ucrtInfo = [Diagnostics.FileVersionInfo]::GetVersionInfo($ucrtPath)
$ucrt = [ordered]@{ path=$ucrtPath; file_version=$ucrtInfo.FileVersion; product_version=$ucrtInfo.ProductVersion; sha256=(Sha $ucrtPath) }
$rows = @()
foreach ($vector in $vectors) {
  $inputBits = [Convert]::ToUInt32($vector.input_bits.Substring(2), 16)
  $exponentBits = [Convert]::ToUInt32($vector.exponent_bits.Substring(2), 16)
  $resultBits = [UcrtPowfCapture]::Evaluate($inputBits, $exponentBits)
  $rows += [ordered]@{
    input_bits=$vector.input_bits; exponent_bits=$vector.exponent_bits
    native_ucrt_result_bits=(Hex32 $resultBits); occurrences=[int]$vector.occurrences
    ucrtbase_path=$ucrt.path; ucrtbase_file_version=$ucrt.file_version
    ucrtbase_product_version=$ucrt.product_version; ucrtbase_sha256=$ucrt.sha256
  }
}
$summary = [ordered]@{
  schema="olmdistancegradation.pf32-power-ucrt-powf-return/1"; request_id=$requestId
  status="answered_native_windows_ucrt_powf"; process_bitness=([IntPtr]::Size*8)
  processor_architecture=$env:PROCESSOR_ARCHITECTURE; ucrtbase=$ucrt
  vector_count=$rows.Count; vectors_sha256=(Sha (Join-Path $root "powf_vectors.json")); rows=$rows
}
$summaryPath = Join-Path $runDir "run_summary.json"
Write-Utf8NoBom $summaryPath (($summary | ConvertTo-Json -Depth 8) + "`n")
Copy-Item -LiteralPath (Join-Path $root "request_manifest.json") -Destination $runDir
Copy-Item -LiteralPath (Join-Path $root "powf_vectors.json") -Destination $runDir
if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
Compress-Archive -Path (Join-Path $runDir "*") -DestinationPath $zipPath
Write-Output ($summary | ConvertTo-Json -Depth 8)
'''


def package_files(vectors: list[dict[str, object]]) -> dict[str, bytes]:
    vector_bytes = canonical(vectors)
    request = {
        "schema": "olmdistancegradation.pf32-power-ucrt-powf-request/1",
        "request_id": REQUEST_ID,
        "status": "ready_native_windows_no_ae_required",
        "target": {"path": "%WINDIR%\\System32\\ucrtbase.dll", "symbol": "powf", "process": "64-bit x64 PowerShell"},
        "vectors": {"count": len(vectors), "sha256": sha_bytes(vector_bytes), "input_field": "input_bits", "exponent_field": "exponent_bits"},
        "provenance": {
            "production_source_sha256": SOURCE_SHA256,
            "production_census_harness_sha256": sha(HARNESS),
            "request_generator_sha256": sha(Path(__file__)),
            "return_analyzer_sha256": sha(ANALYZER),
            "actual_aex_sha256": AEX_SHA256,
            "aexcompat_worker_sha256": WORKER_SHA256,
            "aex_import_module": "api-ms-win-crt-math-l1-1-0.dll",
            "aex_import_symbol": "powf",
            "aex_pf32_callsite": "0x181170ea3",
            "actual_aex_xmm_closure_sha256": sha(XMM_CLOSURE),
        },
        "acceptance": "Exactly 63 keyed float32 vectors evaluated by native System32 ucrtbase.dll!powf with bit-exact result words and DLL identity. Actual-AEX pre-pow XMM input equivalence is separately bound; eight native-UCRT-derived final public outputs remain required before promotion.",
        "claims_not_made": [
            "No native After Effects execution",
            "No claim that the seven production-only transparent-pixel pairs are actual-AEX calls; their final-output irrelevance is separately proven",
            "No PF32 Power production admission from this package alone",
        ],
    }
    readme = f"""# OLMDistanceGradation PF32 Power native UCRT powf request

Run from 64-bit x64 PowerShell on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\\run_olmdistancegradation_pf32_power_ucrt_powf.ps1
```

This evaluates {len(vectors)} production-derived float32 input pairs with native
`%WINDIR%\\System32\\ucrtbase.dll!powf`, records exact result bits and DLL
identity, and creates a return ZIP. It does not launch After Effects.

The returned table is necessary but not sufficient for promotion. Actual-AEX
pre-call XMM inputs are separately bound as an in-order production subsequence,
with the seven production-only transparent-pixel pairs proven output-irrelevant.
Eight final outputs rebuilt from the returned native UCRT words must still be
raw-exact before PF32 Power can leave its current fail-closed policy.
""".encode()
    files = {
        "README.md": readme,
        "UcrtPowfCapture.cs": CS_SOURCE.encode(),
        "powf_vectors.json": vector_bytes,
        "request_manifest.json": canonical(request),
        "run_olmdistancegradation_pf32_power_ucrt_powf.ps1": PS_SOURCE.encode(),
    }
    sums = "".join(f"{sha_bytes(data)}  {name}\n" for name, data in sorted(files.items())).encode()
    files["SHA256SUMS.txt"] = sums
    return files


def write_package(files: dict[str, bytes]) -> None:
    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    PACKAGE_DIR.mkdir(parents=True)
    for name, data in files.items():
        (PACKAGE_DIR / name).write_bytes(data)
    if PACKAGE_ZIP.exists():
        PACKAGE_ZIP.unlink()
    with zipfile.ZipFile(PACKAGE_ZIP, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 8, 13, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)


def validate_matrix(cell_hashes: dict[str, str]) -> dict[str, object]:
    matrix = json.loads(MATRIX.read_text())
    require(matrix["actual_aex_sha256"] == AEX_SHA256, "matrix AEX drift")
    require(matrix["worker_sha256"] == WORKER_SHA256, "matrix worker drift")
    rows = [row for row in matrix["rows"] if row["depth"] == "PF32" and row["interpolation"] == "power"]
    require(len(rows) == 8, "matrix Power row count")
    for row in rows:
        key = f"mode{row['blur_mode']}.bg{int(row['use_background'])}"
        require(row["actual_exported_raw_sha256"] == cell_hashes[key], f"host-substituted exported hash mismatch: {key}")
        require(row["fail_closed"] and not row["exact"], f"Power policy drift: {key}")
    return matrix


def generate(write: bool) -> dict[str, object]:
    calls, vectors, cell_hashes = run_census()
    matrix = validate_matrix(cell_hashes)
    files = package_files(vectors)
    package_hashes = {name: sha_bytes(data) for name, data in sorted(files.items())}
    report = {
        "schema": "olmdistancegradation.pf32-power-ucrt-boundary/1",
        "status": "PASS_ACTUAL_XMM_BOUND_NATIVE_UCRT_REQUEST_READY_POWER_REMAINS_FAIL_CLOSED",
        "production_source_sha256": sha(SOURCE),
        "fieldgen_sha256": sha(FIELDGEN),
        "census_harness_sha256": sha(HARNESS),
        "generator_sha256": sha(Path(__file__)),
        "return_analyzer_sha256": sha(ANALYZER),
        "unit_sha256": sha(UNIT),
        "shim_sha256": sha(SHIM),
        "actual_aex_sha256": AEX_SHA256,
        "aexcompat_worker_sha256": WORKER_SHA256,
        "matrix_sha256": sha(MATRIX),
        "actual_aex_xmm_closure": {
            "path": str(XMM_CLOSURE.relative_to(ROOT)),
            "sha256": sha(XMM_CLOSURE),
            "status": json.loads(XMM_CLOSURE.read_text())["status"],
            "actual_aex_calls": 992,
            "actual_aex_unique_pairs": 56,
            "production_only_output_irrelevant_pairs": 7,
        },
        "production_census": {
            "cells": 8,
            "powf_calls": len(calls),
            "unique_vectors": len(vectors),
            "power_exponent_bits": "0x40100000",
            "canonical_vectors_sha256": sha_bytes(canonical(vectors)),
            "cell_output_sha256": cell_hashes,
        },
        "host_substituted_relation": {
            "exported_aex_cells_matching_production": 8,
            "scope": "pinned AEXCompat worker using host Rust/libSystem f32::powf, not native Windows UCRT",
            "actual_exported_sha256": cell_hashes,
            "matrix_status": matrix["status"],
        },
        "native_request": {
            "request_id": REQUEST_ID,
            "package_directory": str(PACKAGE_DIR.relative_to(ROOT)),
            "package_zip": str(PACKAGE_ZIP.relative_to(ROOT)),
            "package_files_sha256": package_hashes,
            "zip_sha256": None,
            "status": "ready_not_answered",
        },
        "production_policy": {
            "pf32_power_cells": 8,
            "behavior": "fail_closed_on_arm64_and_x86_64",
            "reason": "native Windows UCRT powf result and eight native-derived final RAW comparisons are absent",
        },
        "claims_not_made": [
            "No native Windows UCRT powf result",
            "No native After Effects execution",
            "No PF32 Power admission or arbitrary-input generalization",
        ],
    }
    if write:
        write_package(files)
        report["native_request"]["zip_sha256"] = sha(PACKAGE_ZIP)
        REPORT.write_bytes(canonical(report))
        DOC.write_text(
            "# OLMDistanceGradation PF32 Power UCRT boundary\n\n"
            "Status: **PASS_ACTUAL_XMM_BOUND_NATIVE_UCRT_REQUEST_READY_POWER_REMAINS_FAIL_CLOSED**.\n\n"
            "The live production body issued 1,496 `powf` calls across the eight fixed 17x11 PF32 Power cells; these reduce to 63 exact float32 input pairs with exponent bits `0x40100000`. Using the pinned AEXCompat host `f32::powf` substitution, all eight production outputs match the exported Smart AEX buffers byte-for-byte. That relation is diagnostic, not a Windows UCRT oracle.\n\n"
            "The packaged Windows request evaluates those 63 pairs with native `System32\\ucrtbase.dll!powf` and records exact return bits plus DLL identity without launching AE. Actual-AEX pre-call XMM inputs are now bound for all 992 real calls; the seven production-only pairs are output-irrelevant. PF32 Power remains fail-closed until the native result is returned and all eight native-derived public outputs are raw-exact.\n"
        )
    else:
        require(PACKAGE_DIR.is_dir() and PACKAGE_ZIP.is_file() and REPORT.is_file(), "persisted artifacts missing")
        require({path.name: path.read_bytes() for path in PACKAGE_DIR.iterdir() if path.is_file()} == files, "package directory drift")
        with zipfile.ZipFile(PACKAGE_ZIP) as archive:
            require({name: archive.read(name) for name in archive.namelist()} == files, "package ZIP drift")
        persisted = json.loads(REPORT.read_text())
        expected = json.loads(json.dumps(report))
        expected["native_request"]["zip_sha256"] = sha(PACKAGE_ZIP)
        require(persisted == expected, "persisted report drift")
    return report


def main() -> int:
    write = "--write" in os.sys.argv[1:]
    report = generate(write)
    print(report["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
