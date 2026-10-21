#!/usr/bin/env python3
"""Build and validate the AE-free DirectionalBlur powf request child."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REQUEST_ID = "olm_runtime_trace_olmdirectionalblur_remaining6_ucrt_powf_20260814"
PACKAGE = ROOT / "refs/runtime_trace_packages" / REQUEST_ID
REPORT = ROOT / "refs/conformance/olmdirectionalblur_remaining6_ucrt_powf_request_20260814.json"
MARKDOWN = REPORT.with_suffix(".md")
CENSUS = ROOT / "refs/conformance/olmdirectionalblur_remaining6_ucrt_powf_census_20260814.json"
EXPECTED_CENSUS_SHA256 = "091d41969f5617452666e976f038913ebe2dad96c656f1cd75e4e9b7093e0dac"
FILES = ("README.md", "UcrtPowfCapture.cs", "powf_vectors.json", "request_manifest.json",
         "run_olmdirectionalblur_remaining6_ucrt_powf.ps1")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vectors() -> list[dict[str, str]]:
    if sha256(CENSUS) != EXPECTED_CENSUS_SHA256:
        raise RuntimeError("Directional powf census identity drift")
    value = json.loads(CENSUS.read_text(encoding="utf-8"))
    rows = value.get("powf_pairs")
    if not isinstance(rows, list) or len(rows) != 787:
        raise RuntimeError("Directional powf census rows drift")
    if any(not isinstance(row, dict) or set(row) != {"input_bits", "exponent_bits"} for row in rows):
        raise RuntimeError("Directional powf census row schema drift")
    return rows


def manifest() -> dict[str, object]:
    return {
        "schema": "olmdirectionalblur.remaining6-ucrt-powf-request/1",
        "status": "ready_native_windows_no_ae_required",
        "request_id": REQUEST_ID,
        "acceptance": "Exactly 787 actual exported-Smart powf keys evaluated by native 64-bit System32 ucrtbase.dll!powf under one bound DLL identity.",
        "provenance": {
            "powf_census_path": str(CENSUS.relative_to(ROOT)),
            "powf_census_sha256": EXPECTED_CENSUS_SHA256,
            "actual_exported_cells": 6,
            "observed_powf_occurrences": 47514,
        },
        "target": {"path": "%WINDIR%\\System32\\ucrtbase.dll", "process": "64-bit x64 PowerShell", "symbol": "powf"},
        "vectors": {"count": 787, "fields": ["input_bits", "exponent_bits"]},
        "claims_not_made": [
            "No native After Effects execution",
            "No production admission from returned math words alone",
            "No host-substituted powf result accepted as Windows UCRT",
            "No extrapolation beyond the exact 787 request keys",
        ],
    }


CSHARP = r'''using System;
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


POWERSHELL = r'''param([string]$OutputDir = "")
$ErrorActionPreference = "Stop"
$requestId = "olm_runtime_trace_olmdirectionalblur_remaining6_ucrt_powf_20260814"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runRoot = if ($OutputDir) { $OutputDir } else { Join-Path $root "return" }
$runDir = Join-Path $runRoot $requestId
$zipPath = Join-Path $runRoot ($requestId + "_return_windows.zip")
$ucrtPath = Join-Path $env:WINDIR "System32\ucrtbase.dll"
function Write-Utf8NoBom([string]$Path, [string]$Content) { [IO.File]::WriteAllText($Path, $Content, (New-Object Text.UTF8Encoding($false))) }
function Sha([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Hex32([uint32]$Value) { "0x{0:x8}" -f $Value }
if (-not [Environment]::Is64BitProcess -or $env:PROCESSOR_ARCHITECTURE -ne "AMD64") { throw "Run from 64-bit x64 PowerShell" }
if (-not (Test-Path -LiteralPath $ucrtPath)) { throw "Missing $ucrtPath" }
if (Test-Path -LiteralPath $runDir) { Remove-Item -LiteralPath $runDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $runRoot | Out-Null
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
Add-Type -LiteralPath (Join-Path $root "UcrtPowfCapture.cs")
$vectorsPath = Join-Path $root "powf_vectors.json"
$vectors = Get-Content -Raw -LiteralPath $vectorsPath | ConvertFrom-Json
$ucrtInfo = [Diagnostics.FileVersionInfo]::GetVersionInfo($ucrtPath)
$ucrt = [ordered]@{ path=$ucrtPath; file_version=$ucrtInfo.FileVersion; product_version=$ucrtInfo.ProductVersion; sha256=(Sha $ucrtPath) }
$rows = @()
foreach ($vector in $vectors) {
  $inputBits = [Convert]::ToUInt32($vector.input_bits.Substring(2), 16)
  $exponentBits = [Convert]::ToUInt32($vector.exponent_bits.Substring(2), 16)
  $resultBits = [UcrtPowfCapture]::Evaluate($inputBits, $exponentBits)
  $rows += [ordered]@{ input_bits=$vector.input_bits; exponent_bits=$vector.exponent_bits; native_ucrt_result_bits=(Hex32 $resultBits); ucrtbase_path=$ucrt.path; ucrtbase_file_version=$ucrt.file_version; ucrtbase_product_version=$ucrt.product_version; ucrtbase_sha256=$ucrt.sha256 }
}
$summary = [ordered]@{ schema="olmdirectionalblur.remaining6-ucrt-powf-return/1"; request_id=$requestId; status="answered_native_windows_ucrt_powf"; process_bitness=([IntPtr]::Size*8); processor_architecture=$env:PROCESSOR_ARCHITECTURE; ucrtbase=$ucrt; vector_count=$rows.Count; vectors_sha256=(Sha $vectorsPath); rows=$rows }
$summaryPath = Join-Path $runDir "run_summary.json"
Write-Utf8NoBom $summaryPath (($summary | ConvertTo-Json -Depth 8) + [Environment]::NewLine)
Copy-Item -LiteralPath (Join-Path $root "request_manifest.json") -Destination $runDir
Copy-Item -LiteralPath $vectorsPath -Destination $runDir
if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
Compress-Archive -Path (Join-Path $runDir "*") -DestinationPath $zipPath
Write-Output ($summary | ConvertTo-Json -Depth 8)
'''


def readme() -> str:
    return """# DirectionalBlur remaining-six native UCRT powf request

Run `run_olmdirectionalblur_remaining6_ucrt_powf.ps1` from 64-bit x64 PowerShell.
It evaluates all 787 exact `powf` keys observed in the six pinned exported-Smart
cells against `%WINDIR%\\System32\\ucrtbase.dll`. It does not launch After Effects.
Returned words still require same-table exported-AEX and Mac public replay before
any production promotion.
"""


def write_package() -> None:
    PACKAGE.mkdir(parents=True, exist_ok=True)
    (PACKAGE / "README.md").write_text(readme(), encoding="utf-8")
    (PACKAGE / "UcrtPowfCapture.cs").write_text(CSHARP, encoding="utf-8")
    (PACKAGE / "powf_vectors.json").write_text(json.dumps(vectors(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (PACKAGE / "request_manifest.json").write_text(json.dumps(manifest(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (PACKAGE / "run_olmdirectionalblur_remaining6_ucrt_powf.ps1").write_text(POWERSHELL, encoding="utf-8")


def validate_package() -> dict[str, str]:
    if tuple(sorted(path.name for path in PACKAGE.iterdir() if path.is_file())) != FILES:
        raise RuntimeError("Directional powf request file set drift")
    if json.loads((PACKAGE / "powf_vectors.json").read_text()) != vectors():
        raise RuntimeError("Directional powf request vectors drift")
    if json.loads((PACKAGE / "request_manifest.json").read_text()) != manifest():
        raise RuntimeError("Directional powf request manifest drift")
    if (PACKAGE / "UcrtPowfCapture.cs").read_text() != CSHARP or (PACKAGE / "run_olmdirectionalblur_remaining6_ucrt_powf.ps1").read_text() != POWERSHELL:
        raise RuntimeError("Directional powf executable contract drift")
    if (PACKAGE / "README.md").read_text() != readme():
        raise RuntimeError("Directional powf README drift")
    return {name: sha256(PACKAGE / name) for name in FILES}


def build_report() -> dict[str, object]:
    return {
        "schema": "olmdirectionalblur.remaining6-ucrt-powf-request-closure/1",
        "status": "ready_native_windows_ucrt_powf_capture_ae_free",
        "request_id": REQUEST_ID,
        "package": {"path": str(PACKAGE.relative_to(ROOT)), "files": validate_package()},
        "vectors": {"count": 787, "rows_sha256": hashlib.sha256(json.dumps(vectors(), sort_keys=True, separators=(",", ":")).encode()).hexdigest()},
        "provenance": manifest()["provenance"],
        "acceptance": {"all_787_rows_required": True, "same_system32_ucrt_identity_required": True, "after_effects_required": False},
        "boundary": {"native_return_included": False, "production_changed": False, "same_table_aex_and_mac_replay_still_required": True},
    }


def note(value: dict[str, object]) -> str:
    return f"""# DirectionalBlur remaining-six native UCRT powf request

Status: `{value['status']}`. The AE-free child contains 787 exact `powf` keys
from the actual exported-Smart six-cell census. Native returned words are not a
promotion by themselves; the same table must drive exported AEX and Mac public
replays.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        write_package()
    current = build_report()
    if args.write:
        REPORT.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        MARKDOWN.write_text(note(current), encoding="utf-8")
    if json.loads(REPORT.read_text()) != current or MARKDOWN.read_text() != note(current):
        raise RuntimeError("persisted Directional powf request drift")
    print("PASS_DIRECTIONAL_REMAINING6_UCRT_POWF_REQUEST_READY_AE_FREE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
