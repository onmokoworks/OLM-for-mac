#!/usr/bin/env python3
"""Build and validate the AE-free native-Windows UCRT request for Radial Strength 290."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset

import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[2]
REQUEST_ID = "olm_runtime_trace_olmradialblur_strength290_ucrt_math_20260814"
PACKAGE = ROOT / "refs/runtime_trace_packages" / REQUEST_ID
PACKAGE_ZIP = PACKAGE.with_suffix(".zip")
REPORT = ROOT / "refs/conformance/olmradialblur_strength290_ucrt_math_request_20260814.json"
NOTE = REPORT.with_suffix(".md")
BOUNDARY = ROOT / "refs/conformance/olmradialblur_strength290_exported_math_boundary_20260814.json"
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
AEX = resolve_asset(ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex")
IMPORT_PATCH = ROOT / "tools/emulation/aexcompat_olmradialblur_float_math_imports_20260814.patch"
TRACE_PATCH = ROOT / "tools/emulation/aexcompat_olmradialblur_float_math_trace_20260814.patch"

FILES = (
    "README.md",
    "UcrtRadialMathCapture.cs",
    "math_vectors.json",
    "request_manifest.json",
    "run_olmradialblur_strength290_ucrt_math.ps1",
)

LEFT_BITS = (
    "00000000", "3f800000", "40000000", "40400000", "40800000", "40a00000",
    "40c00000", "40e00000", "41000000", "bf800000", "c0000000", "c0400000",
    "c0800000", "c0a00000", "c0c00000", "c0e00000", "c1000000", "c1100000",
)
RIGHT_BITS = (
    "00000000", "3f800000", "40000000", "40400000", "40800000", "40a00000",
    "40c00000", "40e00000", "41000000", "41100000", "41200000", "41300000",
    "41400000", "41500000", "41600000", "41700000", "bf800000", "c0000000",
    "c0400000", "c0800000", "c0a00000", "c0c00000", "c0e00000", "c1000000",
    "c1100000", "c1200000", "c1300000", "c1400000", "c1500000", "c1600000",
    "c1700000", "c1800000",
)

EXPECTED_PROVENANCE = {
    "actual_aex_sha256": "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb",
    "production_source_sha256": "b74b3d2c7ea6724593b28f82d36615e071e18d813e5b99cc948e26a447fdb0d1",
    "exported_math_boundary_sha256": "fd164d69cac9d7f92f5bc109aff744e2426846d17de823bd9fbe7519d9d2927a",
    "float_import_patch_sha256": "04147344b71c3f08a5e7e796d9d50f65845def15e924a2836a9e89ae249f81e3",
    "float_trace_patch_sha256": "a1dc5e91cb2a9c9c2e332c7ce2361c97eee6134e9b89f3bf0e9bd890b8038684",
    "aexcompat_head": "28d535469f84f67236ef3425afe4291ea2fb0991",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def vectors() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [{
        "function": "log2f", "argument_bits": "0x4f800000", "call_count": 149,
    }]
    rows.extend({
        "function": "atan2f", "left_bits": "0x" + left,
        "right_bits": "0x" + right, "call_count": 1,
    } for left in LEFT_BITS for right in RIGHT_BITS)
    if len(rows) != 577 or sum(int(row["call_count"]) for row in rows) != 725:
        raise ValueError("Radial math vector census drift")
    return rows


def manifest() -> dict[str, object]:
    return {
        "schema": "olmradialblur.strength290-ucrt-math-request/1",
        "status": "ready_native_windows_no_ae_required",
        "request_id": REQUEST_ID,
        "target": {
            "path": "%WINDIR%\\System32\\ucrtbase.dll",
            "process": "64-bit x64 PowerShell",
            "symbols": ["atan2f", "log2f"],
        },
        "vectors": {
            "unique": 577,
            "original_call_count": 725,
            "log2f_unique": 1,
            "log2f_calls": 149,
            "atan2f_unique": 576,
            "atan2f_calls": 576,
            "atan2f_cartesian_dimensions": [18, 32],
            "canonical_sha256": digest(vectors()),
        },
        "provenance": EXPECTED_PROVENANCE,
        "acceptance": (
            "All 577 exact float32 keys are hash-checked before evaluation in one AMD64 process "
            "against one exact loaded System32 ucrtbase.dll path and SHA-256 identity, returning "
            "bit-exact float32 result words."
        ),
        "claims_not_made": [
            "No native After Effects execution",
            "No production admission from returned math words alone",
            "No claim that AEXCompat, Rust, Python, or macOS libSystem results are Windows UCRT results",
            "No extrapolation beyond the exact 577 unique vectors",
            "No Strength-290 promotion until native results drive both exported AEX and Mac public final RAW comparisons",
        ],
    }


def csharp() -> str:
    return '''using System;
using System.Runtime.InteropServices;
using System.Text;

public static class UcrtRadialMathCapture
{
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    private delegate float Log2fDelegate(float value);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    private delegate float Atan2fDelegate(float left, float right);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern IntPtr LoadLibraryEx(string path, IntPtr file, uint flags);

    [DllImport("kernel32.dll", CharSet = CharSet.Ansi, ExactSpelling = true,
        SetLastError = true)]
    private static extern IntPtr GetProcAddress(IntPtr module, string name);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern uint GetModuleFileName(IntPtr module, StringBuilder path, int size);

    private static IntPtr module;
    private static Log2fDelegate log2f;
    private static Atan2fDelegate atan2f;

    public static string Initialize(string absoluteSystem32Path)
    {
        module = LoadLibraryEx(absoluteSystem32Path, IntPtr.Zero, 0);
        if (module == IntPtr.Zero)
            throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
        IntPtr log2fAddress = GetProcAddress(module, "log2f");
        IntPtr atan2fAddress = GetProcAddress(module, "atan2f");
        if (log2fAddress == IntPtr.Zero || atan2fAddress == IntPtr.Zero)
            throw new InvalidOperationException("ucrtbase.dll is missing log2f or atan2f");
        log2f = (Log2fDelegate)Marshal.GetDelegateForFunctionPointer(
            log2fAddress, typeof(Log2fDelegate));
        atan2f = (Atan2fDelegate)Marshal.GetDelegateForFunctionPointer(
            atan2fAddress, typeof(Atan2fDelegate));
        StringBuilder loadedPath = new StringBuilder(32768);
        if (GetModuleFileName(module, loadedPath, loadedPath.Capacity) == 0)
            throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
        return loadedPath.ToString();
    }

    private static float FromBits(uint bits)
    {
        return BitConverter.ToSingle(BitConverter.GetBytes(bits), 0);
    }

    private static uint ToBits(float value)
    {
        return BitConverter.ToUInt32(BitConverter.GetBytes(value), 0);
    }

    public static uint EvaluateLog2f(uint argumentBits)
    {
        if (log2f == null) throw new InvalidOperationException("Initialize must run first");
        return ToBits(log2f(FromBits(argumentBits)));
    }

    public static uint EvaluateAtan2f(uint leftBits, uint rightBits)
    {
        if (atan2f == null) throw new InvalidOperationException("Initialize must run first");
        return ToBits(atan2f(FromBits(leftBits), FromBits(rightBits)));
    }
}
'''


def powershell() -> str:
    template = r'''param([string]$OutputDir = "")
$ErrorActionPreference = "Stop"
$requestId = "olm_runtime_trace_olmradialblur_strength290_ucrt_math_20260814"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runRoot = if ($OutputDir) { $OutputDir } else { Join-Path $root "return" }
$runDir = Join-Path $runRoot $requestId
$zipPath = Join-Path $runRoot ($requestId + "_return_windows.zip")
$ucrtPath = Join-Path $env:WINDIR "System32\ucrtbase.dll"
$csharpPath = Join-Path $root "UcrtRadialMathCapture.cs"
$vectorsPath = Join-Path $root "math_vectors.json"
$manifestPath = Join-Path $root "request_manifest.json"
$expectedCsharpSha256 = "__CSHARP_SHA256__"
$expectedVectorsSha256 = "__VECTORS_SHA256__"
$expectedManifestSha256 = "__MANIFEST_SHA256__"

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  [IO.File]::WriteAllText($Path, $Content, (New-Object Text.UTF8Encoding($false)))
}
function Sha([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Hex32([uint32]$Value) { "0x{0:x8}" -f $Value }

if (-not [Environment]::Is64BitProcess -or $env:PROCESSOR_ARCHITECTURE -ne "AMD64") {
  throw "Run from 64-bit x64 PowerShell"
}
if (-not (Test-Path -LiteralPath $ucrtPath)) { throw "Missing $ucrtPath" }
if ((Sha $csharpPath) -ne $expectedCsharpSha256) { throw "C# capture source SHA-256 mismatch" }
if ((Sha $vectorsPath) -ne $expectedVectorsSha256) { throw "Exact 577-vector table SHA-256 mismatch" }
if ((Sha $manifestPath) -ne $expectedManifestSha256) { throw "Request manifest SHA-256 mismatch" }
if (Test-Path -LiteralPath $runDir) { throw "Refusing to overwrite existing return directory: $runDir" }
if (Test-Path -LiteralPath $zipPath) { throw "Refusing to overwrite existing return ZIP: $zipPath" }
Add-Type -LiteralPath $csharpPath
$loadedUcrtPath = [UcrtRadialMathCapture]::Initialize($ucrtPath)
$requestedFullPath = [IO.Path]::GetFullPath($ucrtPath)
$loadedFullPath = [IO.Path]::GetFullPath($loadedUcrtPath)
if (-not [String]::Equals($requestedFullPath, $loadedFullPath, [StringComparison]::OrdinalIgnoreCase)) {
  throw "Loaded UCRT is not the requested System32 DLL: $loadedFullPath"
}
$ucrtSha256 = Sha $ucrtPath
if ((Sha $loadedFullPath) -ne $ucrtSha256) { throw "Loaded UCRT identity mismatch" }
$vectors = Get-Content -Raw -LiteralPath $vectorsPath | ConvertFrom-Json
if ($vectors.Count -ne 577) { throw "Exact vector count mismatch" }
$ucrtInfo = [Diagnostics.FileVersionInfo]::GetVersionInfo($ucrtPath)
$ucrt = [ordered]@{
  requested_path=$ucrtPath; loaded_path=$loadedFullPath; file_version=$ucrtInfo.FileVersion
  product_version=$ucrtInfo.ProductVersion; sha256=$ucrtSha256
}
New-Item -ItemType Directory -Force -Path $runRoot | Out-Null
New-Item -ItemType Directory -Path $runDir | Out-Null
$rows = @()
foreach ($vector in $vectors) {
  if ($vector.function -eq "log2f") {
    $argumentBits = [Convert]::ToUInt32($vector.argument_bits.Substring(2), 16)
    $resultBits = [UcrtRadialMathCapture]::EvaluateLog2f($argumentBits)
    $rows += [ordered]@{
      function="log2f"; argument_bits=$vector.argument_bits
      call_count=[int]$vector.call_count; native_ucrt_result_bits=(Hex32 $resultBits)
    }
  } elseif ($vector.function -eq "atan2f") {
    $leftBits = [Convert]::ToUInt32($vector.left_bits.Substring(2), 16)
    $rightBits = [Convert]::ToUInt32($vector.right_bits.Substring(2), 16)
    $resultBits = [UcrtRadialMathCapture]::EvaluateAtan2f($leftBits, $rightBits)
    $rows += [ordered]@{
      function="atan2f"; left_bits=$vector.left_bits; right_bits=$vector.right_bits
      call_count=[int]$vector.call_count; native_ucrt_result_bits=(Hex32 $resultBits)
    }
  } else { throw "Unknown function in vector table: $($vector.function)" }
}
$summary = [ordered]@{
  schema="olmradialblur.strength290-ucrt-math-return/1"; request_id=$requestId
  status="answered_native_windows_ucrt_atan2f_log2f"; process_bitness=([IntPtr]::Size*8)
  processor_architecture=$env:PROCESSOR_ARCHITECTURE; ucrtbase=$ucrt
  vector_count=$rows.Count; original_call_count=725; vectors_sha256=(Sha $vectorsPath); rows=$rows
}
$summaryPath = Join-Path $runDir "run_summary.json"
Write-Utf8NoBom $summaryPath (($summary | ConvertTo-Json -Depth 8) + [Environment]::NewLine)
Copy-Item -LiteralPath $manifestPath -Destination $runDir
Copy-Item -LiteralPath $vectorsPath -Destination $runDir
Compress-Archive -Path (Join-Path $runDir "*") -DestinationPath $zipPath
Write-Output ($summary | ConvertTo-Json -Depth 8)
'''
    payload = lambda value: hashlib.sha256(value).hexdigest()
    vectors_raw = (json.dumps(vectors(), indent=2, sort_keys=True) + "\n").encode()
    manifest_raw = (json.dumps(manifest(), indent=2, sort_keys=True) + "\n").encode()
    return (template
            .replace("__CSHARP_SHA256__", payload(csharp().encode()))
            .replace("__VECTORS_SHA256__", payload(vectors_raw))
            .replace("__MANIFEST_SHA256__", payload(manifest_raw)))


def readme() -> str:
    return """# OLMRadialBlur Strength 290 native UCRT math request

Run `run_olmradialblur_strength290_ucrt_math.ps1` from 64-bit AMD64 Windows
PowerShell. It directly evaluates one `log2f` key and the 18x32 Cartesian grid
of 576 `atan2f` keys against `%WINDIR%\\System32\\ucrtbase.dll`. It does not
launch After Effects, aerender, or any Adobe process.

The return must retain the exact UCRT DLL identity and all 577 result words.
The script rejects changed C# source, vectors, or request manifest before loading
the DLL, then requires the loaded module path and SHA-256 to match the requested
System32 file.
Those words are not sufficient for production promotion: they must first drive
the pinned exported AEX and the Mac public route, whose final PF32 RAW buffers
must agree exactly while input, padding, and lifecycle guards remain intact.
"""


def file_payloads() -> dict[str, bytes]:
    return {
        "README.md": readme().encode(),
        "UcrtRadialMathCapture.cs": csharp().encode(),
        "math_vectors.json": (json.dumps(vectors(), indent=2, sort_keys=True) + "\n").encode(),
        "request_manifest.json": (json.dumps(manifest(), indent=2, sort_keys=True) + "\n").encode(),
        "run_olmradialblur_strength290_ucrt_math.ps1": powershell().encode(),
    }


def deterministic_zip_bytes(payloads: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, raw in sorted(payloads.items()):
            info = zipfile.ZipInfo(f"{REQUEST_ID}/{name}", (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    return output.getvalue()


def validate_live_provenance() -> None:
    actual = {
        "actual_aex_sha256": sha256(AEX),
        "production_source_sha256": sha256(SOURCE),
        "exported_math_boundary_sha256": sha256(BOUNDARY),
        "float_import_patch_sha256": sha256(IMPORT_PATCH),
        "float_trace_patch_sha256": sha256(TRACE_PATCH),
    }
    for key, value in actual.items():
        if EXPECTED_PROVENANCE[key] != value:
            raise ValueError(f"provenance drift: {key}")


def write_package() -> None:
    PACKAGE.mkdir(parents=True, exist_ok=True)
    payloads = file_payloads()
    for name, raw in payloads.items():
        (PACKAGE / name).write_bytes(raw)
    PACKAGE_ZIP.write_bytes(deterministic_zip_bytes(payloads))


def validate_package(*, live: bool = True) -> dict[str, object]:
    if live:
        validate_live_provenance()
    expected = file_payloads()
    actual_names = tuple(sorted(path.name for path in PACKAGE.iterdir() if path.is_file()))
    if actual_names != FILES:
        raise ValueError(f"package file-set drift: {actual_names}")
    for name, raw in expected.items():
        if (PACKAGE / name).read_bytes() != raw:
            raise ValueError(f"package content drift: {name}")
    if PACKAGE_ZIP.read_bytes() != deterministic_zip_bytes(expected):
        raise ValueError("deterministic transfer ZIP bytes drift")
    if not zipfile.is_zipfile(PACKAGE_ZIP):
        raise ValueError("transfer ZIP missing")
    with zipfile.ZipFile(PACKAGE_ZIP) as archive:
        names = archive.namelist()
        expected_names = [f"{REQUEST_ID}/{name}" for name in sorted(expected)]
        if names != expected_names or len(names) != len(set(names)):
            raise ValueError("transfer ZIP member-set drift")
        for name, raw in expected.items():
            if archive.read(f"{REQUEST_ID}/{name}") != raw:
                raise ValueError(f"transfer ZIP content drift: {name}")
    ps = powershell()
    for token in (
        '$env:PROCESSOR_ARCHITECTURE -ne "AMD64"',
        'Join-Path $env:WINDIR "System32\\ucrtbase.dll"',
        '"Exact 577-vector table SHA-256 mismatch"',
        '[UcrtRadialMathCapture]::Initialize($ucrtPath)',
        '[StringComparison]::OrdinalIgnoreCase',
        '"Loaded UCRT identity mismatch"',
        "[UcrtRadialMathCapture]::EvaluateLog2f($argumentBits)",
        "[UcrtRadialMathCapture]::EvaluateAtan2f($leftBits, $rightBits)",
        'schema="olmradialblur.strength290-ucrt-math-return/1"',
        "vector_count=$rows.Count", "original_call_count=725",
    ):
        if token not in ps:
            raise ValueError(f"PowerShell contract drift: {token}")
    if any(token.lower() in ps.lower() for token in ("AfterFX", "aerender", "DoScript", "Start-Process")):
        raise ValueError("capture script launches a host process")
    return {
        "files": {name: sha256(PACKAGE / name) for name in FILES},
        "zip_sha256": sha256(PACKAGE_ZIP),
    }


def build_report(*, live: bool = True) -> dict[str, object]:
    package = validate_package(live=live)
    return {
        "schema": "olmradialblur.strength290-ucrt-math-request-closure/1",
        "status": "READY_NATIVE_WINDOWS_UCRT_577_VECTORS_AE_FREE",
        "request_id": REQUEST_ID,
        "package": {
            "path": str(PACKAGE.relative_to(ROOT)),
            "files": package["files"],
            "transfer_zip": str(PACKAGE_ZIP.relative_to(ROOT)),
            "transfer_zip_sha256": package["zip_sha256"],
        },
        "vectors": manifest()["vectors"],
        "target": manifest()["target"],
        "provenance": EXPECTED_PROVENANCE,
        "return_contract": {
            "schema": "olmradialblur.strength290-ucrt-math-return/1",
            "all_577_rows_required": True,
            "one_amd64_process_required": True,
            "same_system32_ucrt_identity_required": True,
            "input_dependency_sha256_checked_before_load": True,
            "loaded_module_path_matches_system32_required": True,
            "loaded_module_sha256_matches_recorded_required": True,
            "unknown_keys_rejected": True,
        },
        "boundary": {
            "native_return_included": False,
            "after_effects_required": False,
            "production_admission_changed": False,
            "strength290_remains_fail_closed": True,
            "returned_words_alone_sufficient_for_promotion": False,
        },
    }


def note(value: dict[str, object]) -> str:
    return (
        "# OLMRadialBlur Strength 290 native UCRT request\n\n"
        f"Status: `{value['status']}`.\n\n"
        "The deterministic package evaluates 577 unique float32 vectors (one `log2f` key "
        "representing 149 calls and a complete 18x32 `atan2f` grid representing 576 calls) in "
        "one 64-bit AMD64 process after dependency SHA-256 checks, explicitly loads the System32 "
        "`ucrtbase.dll`, and requires its loaded path and SHA-256 identity to match. It launches no "
        "Adobe process. Native return words alone cannot promote Strength 290; exported-AEX and "
        "Mac-public final RAW equality remains mandatory.\n"
    )


def validate_persisted() -> None:
    expected = build_report()
    actual = json.loads(REPORT.read_text(encoding="utf-8"))
    if actual != expected:
        raise ValueError("persisted request report drift")
    if NOTE.read_text(encoding="utf-8") != note(actual):
        raise ValueError("persisted request note drift")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.write:
        write_package()
        value = build_report()
        REPORT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        NOTE.write_text(note(value), encoding="utf-8")
    validate_persisted()
    print("PASS_OLMRADIALBLUR_STRENGTH290_UCRT_REQUEST_READY_AE_FREE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
