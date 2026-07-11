#!/usr/bin/env python3
"""Build the hash-pinned Windows OLMBlur 8bpc canonical recapture package."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ZIP = ROOT / "refs/reports/ae_host_validation_20260618_232926/normalized_ae_pixel_requests_20260619_003631/olmblur_request.zip"
EXPECTED_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
PACKAGE_STEM = "olmblur_windows_software_8bpc_aex_canonical_recapture_20260711"
SOURCE_PREFIX = "ae_pixel_olmblur_20260606/"
CASES = tuple(f"case_{index:04d}" for index in range(1, 8))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, default=SOURCE_ZIP)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / f"refs/reference_requests/{PACKAGE_STEM}.zip",
    )
    return parser.parse_args()


def load_source(source_zip: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, bytes]]:
    with zipfile.ZipFile(source_zip) as archive:
        names = set(archive.namelist())
        request_name = SOURCE_PREFIX + "request_manifest.json"
        reference_name = SOURCE_PREFIX + "reference_manifest.json"
        if request_name not in names or reference_name not in names:
            raise SystemExit("source ZIP is missing request/reference manifests")
        request = json.loads(archive.read(request_name))
        reference = json.loads(archive.read(reference_name))
        required = {
            SOURCE_PREFIX + "AE_PIXEL_VALIDATION_REQUEST.md",
            request_name,
            reference_name,
        }
        for case_id in CASES:
            required.add(SOURCE_PREFIX + f"input/{case_id}_before_effects.png")
            required.add(SOURCE_PREFIX + f"expected/{case_id}.png")
        missing = sorted(required - names)
        if missing:
            raise SystemExit("source ZIP is missing:\n" + "\n".join(missing))
        payload = {name: archive.read(name) for name in required}
    actual_cases = tuple(case["id"] for case in reference.get("cases", []))
    if actual_cases != CASES:
        raise SystemExit(f"source cases are not the canonical seven-case order: {actual_cases!r}")
    return request, reference, payload


def build_manifest(request: dict[str, Any], reference: dict[str, Any], files: dict[str, bytes]) -> dict[str, Any]:
    cases = []
    for case in reference["cases"]:
        effect = case["effects"][0]
        cases.append(
            {
                "id": case["id"],
                "time": case["time"],
                "input": f"inputs/{case['id']}_before_effects.png",
                "expected": f"expected/{case['id']}.png",
                "effect_name": effect["name"],
                "effect_match_name": effect["match_name"],
                "params": {param["name"]: param["value"] for param in effect["params"]},
            }
        )
    return {
        "kind": "olmblur_windows_software_8bpc_canonical_recapture",
        "schema": 1,
        "created_at": "2026-07-11",
        "source_profile": request["reference_profile"],
        "platform": "windows",
        "ae_version_required": "26.2x49 or current installed Windows AE (record exact)",
        "project": {"width": 1920, "height": 1080, "frame_rate": 24, "duration": 6.16666666666667, "bits_per_channel": 8},
        "renderer_required": "Software",
        "color_settings_required": "record working space, linear blending, and bits per channel from the AE project",
        "plugin": {
            "name": "OLMBlur.aex",
            "required_sha256": EXPECTED_SHA256,
            "path_rule": "record the exact installed absolute path; a missing or mismatched hash is hash_mismatch and forbids rendering",
            "record": ["path", "size_bytes", "last_write_time_utc", "sha256"],
        },
        "controls": {
            "no_effect": "render one disabled-effect control per case or record a clearly identified no-effect control result",
            "adbe_force_cpu_gpu": "metadata only; never infer renderer from this control",
        },
        "required_outputs": ["provenance.json", "run_summary.json", "seven case PNGs", "no-effect control evidence"],
        "cases": cases,
        "package_files_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())},
    }


def powershell_asset() -> str:
    return r'''param(
    [Parameter(Mandatory=$false)][string]$AfterFX = "",
    [Parameter(Mandatory=$false)][string]$PluginPath = "",
    [Parameter(Mandatory=$false)][string]$OutputDir = ""
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Manifest = Join-Path $Root "manifest.json"
$ExpectedHash = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
$RunDir = if ($OutputDir) { $OutputDir } else { Join-Path $Root "run" }
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
$Provenance = Join-Path $RunDir "provenance.json"
$Summary = Join-Path $RunDir "run_summary.json"

function Write-Json($Path, $Value) { $Value | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $Path }
function Stop-FailClosed([string]$Status, [string]$Message) {
    $record = [ordered]@{ kind="olmblur_windows_recapture_run"; status=$Status; error=$Message; rendered=$false; required_sha256=$ExpectedHash }
    Write-Json $Summary $record
    Write-Host "$Status`: $Message" -ForegroundColor Red
    exit 2
}

if (-not (Test-Path $Manifest)) { Stop-FailClosed "missing_manifest" "manifest.json not found" }
$searchRoots = @()
if ($PluginPath) { $searchRoots += $PluginPath }
$searchRoots += @(
    (Join-Path ${env:ProgramFiles} "Adobe\Common\Plug-ins\7.0\MediaCore"),
    (Join-Path ${env:ProgramFiles} "Adobe\After Effects 2026\Support Files\Plug-ins"),
    (Join-Path ${env:ProgramFiles} "Adobe\After Effects 2025\Support Files\Plug-ins")
)
$candidates = @()
foreach ($root in ($searchRoots | Select-Object -Unique)) {
    if (Test-Path $root) { $candidates += Get-ChildItem -LiteralPath $root -Filter "OLMBlur.aex" -File -Recurse -ErrorAction SilentlyContinue }
}
$candidates = @($candidates | Sort-Object FullName -Unique)
if ($candidates.Count -eq 0) { Stop-FailClosed "missing_plugin" "no installed OLMBlur.aex found" }
if ($candidates.Count -gt 1 -and -not $PluginPath) { Stop-FailClosed "ambiguous_plugin_path" "multiple installed OLMBlur.aex files; pass -PluginPath for the exact installed path" }
$plugin = if ($PluginPath) { Get-Item -LiteralPath $PluginPath -ErrorAction SilentlyContinue } else { $candidates[0] }
if (-not $plugin -or $plugin.Name -ne "OLMBlur.aex") { Stop-FailClosed "missing_plugin" "-PluginPath is not an OLMBlur.aex file" }
$hash = (Get-FileHash -LiteralPath $plugin.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
$pluginRecord = [ordered]@{
    path=$plugin.FullName; size_bytes=[int64]$plugin.Length; last_write_time_utc=$plugin.LastWriteTimeUtc.ToString("o"); sha256=$hash; required_sha256=$ExpectedHash
}
$provenance = [ordered]@{ kind="olmblur_aex_provenance"; status="verified"; plugin=$pluginRecord; ae_version="pending_from_AE"; renderer="Software"; project_bits_per_channel=8; color_settings="pending_from_AE"; no_effect_control="required" }
if ($hash -ne $ExpectedHash) { $provenance.status="hash_mismatch"; Write-Json $Provenance $provenance; Stop-FailClosed "hash_mismatch" "installed OLMBlur.aex SHA-256 $hash does not equal required $ExpectedHash" }
Write-Json $Provenance $provenance

if (-not $AfterFX) {
    $AfterFX = (Get-ChildItem (Join-Path ${env:ProgramFiles} "Adobe") -Filter "AfterFX.exe" -File -Recurse -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1).FullName
}
if (-not $AfterFX -or -not (Test-Path $AfterFX)) { Stop-FailClosed "missing_afterfx" "AfterFX.exe was not found; no render was started" }
$caseIds = 1..7 | ForEach-Object { "case_{0:D4}" -f $_ }
$caseResults = @()
foreach ($caseId in $caseIds) {
    $env:OLM_AE_REQUEST_DIR = $Root
    $env:OLM_AE_CASE_ID = $caseId
    $env:OLM_AE_OUTPUT_DIR = (Join-Path $RunDir "rendered")
    $env:OLM_AE_LOG_PATH = (Join-Path $RunDir "$caseId.log")
    $env:OLM_AE_RESULT_JSON = (Join-Path $RunDir "$caseId.result.json")
    $env:OLM_AE_PROVENANCE_JSON = $Provenance
    $env:OLM_AE_FORCE_SOFTWARE = "1"
    & $AfterFX -r (Join-Path $Root "render_olmblur_case.jsx")
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path (Join-Path (Join-Path $RunDir "rendered") "$caseId.png"))) { Stop-FailClosed "render_failed" "$caseId did not produce a PNG" }
    $caseResults += Get-Content $env:OLM_AE_RESULT_JSON -Raw | ConvertFrom-Json
}
$firstResult = $caseResults[0]
$provenance = Get-Content $Provenance -Raw | ConvertFrom-Json
$provenance.ae_version = $firstResult.ae_version
$provenance.project_bits_per_channel = $firstResult.project_bits_per_channel
$provenance.color_settings = [ordered]@{ working_space=$firstResult.project_working_space; linear_blending=$firstResult.project_linear_blending; bits_per_channel=$firstResult.project_bits_per_channel }
Write-Json $Provenance $provenance
$env:OLM_AE_CASE_ID = "case_0001"
$env:OLM_AE_OUTPUT_DIR = (Join-Path $RunDir "no_effect_control")
$env:OLM_AE_LOG_PATH = (Join-Path $RunDir "no_effect_control.log")
$env:OLM_AE_RESULT_JSON = (Join-Path $RunDir "no_effect_control.result.json")
$env:OLM_AE_DISABLE_EFFECT = "1"
& $AfterFX -r (Join-Path $Root "render_olmblur_case.jsx")
if ($LASTEXITCODE -ne 0 -or -not (Test-Path (Join-Path $RunDir "no_effect_control\case_0001.png"))) { Stop-FailClosed "no_effect_control_failed" "no-effect control did not produce a PNG" }
$control = Get-Content $env:OLM_AE_RESULT_JSON -Raw | ConvertFrom-Json
Remove-Item Env:OLM_AE_DISABLE_EFFECT -ErrorAction SilentlyContinue
$summaryRecord = [ordered]@{ kind="olmblur_windows_recapture_run"; status="rendered"; rendered=$true; renderer="Software"; project_bits_per_channel=8; color_settings="recorded in AE result"; provenance=(Get-Content $Provenance -Raw | ConvertFrom-Json); no_effect_control=$control; cases=$caseResults; outputs=(Get-ChildItem (Join-Path $RunDir "rendered") -Filter "case_*.png" | Select-Object -ExpandProperty FullName) }
Write-Json $Summary $summaryRecord
Write-Host "OK: seven OLMBlur 8bpc Software PNGs written to $RunDir\rendered"
'''


def jsx_asset() -> str:
    source = (ROOT / "scripts/ae_render_single_case.jsx").read_text(encoding="utf-8")
    return source.replace("requestDir + \"/\" + requestManifest.input_dir + \"/\" + requestCase.before_effects_frame", "requestDir + \"/inputs/\" + caseId + \"_before_effects.png\"")


def build(args: argparse.Namespace) -> Path:
    source = args.source_zip.resolve()
    request, reference, source_files = load_source(source)
    with tempfile.TemporaryDirectory(prefix="olmblur_recapture_") as temp_name:
        stage = Path(temp_name) / PACKAGE_STEM
        (stage / "inputs").mkdir(parents=True)
        (stage / "expected").mkdir()
        (stage / "run" / "rendered").mkdir(parents=True)
        for name, data in source_files.items():
            if "/input/" in name:
                target = stage / "inputs" / Path(name).name
            elif "/expected/" in name:
                target = stage / "expected" / Path(name).name
            else:
                target = stage / Path(name).name
            target.write_bytes(data)
        manifest = build_manifest(request, reference, source_files)
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (stage / "README.md").write_text(
            "# OLMBlur Windows Software 8bpc canonical recapture\n\n"
            "Run `run_olmblur_recapture.ps1 -PluginPath <exact installed OLMBlur.aex>` from a clean Windows AE session. "
            "The script records path, size, UTC timestamp, SHA-256, AE version, Software renderer, 8bpc project, color settings, "
            "the no-effect control, and all seven PNGs. A missing or mismatched AEX exits as `hash_mismatch` before AE is launched.\n\n"
            "The effect's `GPU Rendering` parameter is replayed from the normalized cases but is not used to infer the project renderer. "
            "`ADBE Force CPU GPU` is metadata-only and is never accepted as renderer evidence.\n",
            encoding="utf-8",
        )
        (stage / "run_olmblur_recapture.ps1").write_text(powershell_asset(), encoding="utf-8")
        (stage / "render_olmblur_case.jsx").write_text(jsx_asset(), encoding="utf-8")
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    archive.write(path, f"{PACKAGE_STEM}/{path.relative_to(stage).as_posix()}")
    print(f"[OK] {output}")
    print(f"[SUMMARY] cases=7 required_sha256={EXPECTED_SHA256} renderer=Software bpc=8")
    return output


if __name__ == "__main__":
    build(parse_args())
