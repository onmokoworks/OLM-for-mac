#!/usr/bin/env python3
"""Build a self-contained, hash-pinned Windows OLMBlur dual-depth recapture ZIP."""

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
SOURCE_32_SPEC = ROOT / "refs/reference_requests/olmblur_32bpc_mac_windows_float_focus_20260711.json"
SOURCE_32_DIR = ROOT / "refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMBlur"
PLUGIN_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
PACKAGE_STEM = "olmblur_windows_software_dual_depth_canonical_recapture_20260711"
SOURCE_PREFIX = "ae_pixel_olmblur_20260606/"
CASE_IDS = tuple(f"case_{index:04d}" for index in range(1, 8))
EXR_TEMPLATE = "OLMBlur OpenEXR RGBA Float32 No Compression"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    return digest(path.read_bytes())


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path} is not a JSON object")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, default=SOURCE_ZIP)
    parser.add_argument("--source-32-spec", type=Path, default=SOURCE_32_SPEC)
    parser.add_argument("--source-32-dir", type=Path, default=SOURCE_32_DIR)
    parser.add_argument("--output", type=Path, default=ROOT / f"refs/reference_requests/{PACKAGE_STEM}.zip")
    return parser.parse_args()


def load_8bpc(source: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, bytes]]:
    with zipfile.ZipFile(source) as archive:
        names = set(archive.namelist())
        request_name = SOURCE_PREFIX + "request_manifest.json"
        reference_name = SOURCE_PREFIX + "reference_manifest.json"
        required = {SOURCE_PREFIX + "AE_PIXEL_VALIDATION_REQUEST.md", request_name, reference_name}
        required |= {SOURCE_PREFIX + f"input/{case}_before_effects.png" for case in CASE_IDS}
        required |= {SOURCE_PREFIX + f"expected/{case}.png" for case in CASE_IDS}
        missing = sorted(required - names)
        if missing:
            raise SystemExit("8bpc source ZIP is missing:\n" + "\n".join(missing))
        request = json.loads(archive.read(request_name))
        reference = json.loads(archive.read(reference_name))
        cases = tuple(case["id"] for case in reference.get("cases", []))
        if cases != CASE_IDS:
            raise SystemExit(f"8bpc source cases are not canonical: {cases!r}")
        return request, reference, {name: archive.read(name) for name in required}


def make_32bpc(reference_8: dict[str, Any], spec: dict[str, Any], input_hashes: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    if spec.get("scope") != {"bit_depth": "32bpc", "plugin_filters": ["OLMBlur"], "feature_filters": [], "plugin_count": 1, "case_count": 7}:
        raise SystemExit("focused 32bpc spec scope changed")
    cases = []
    for item in spec.get("cases", []):
        case_id = item.get("source_case_id")
        if case_id not in CASE_IDS:
            raise SystemExit(f"unexpected 32bpc source case: {case_id!r}")
        params = []
        for row in item.get("params_full", []):
            param = dict(row)
            param["path_full"] = [
                {"name": item["effect"]["name"], "match_name": item["effect"]["match_name"], "property_index": 1},
                {"name": row["name"], "match_name": row["match_name"], "property_index": row["property_index"]},
            ]
            params.append(param)
        cases.append({
            "id": case_id,
            "frame": f"{case_id}.exr",
            "time": reference_8["cases"][CASE_IDS.index(case_id)]["time"],
            "before_effects_frame": f"{case_id}_before_effects.png",
            "effects": [{"name": item["effect"]["name"], "match_name": item["effect"]["match_name"], "property_index": 1, "enabled": True, "active": True, "params": params}],
            "input_sha256": input_hashes[case_id],
        })
    if tuple(case["id"] for case in cases) != CASE_IDS:
        raise SystemExit("32bpc spec cases are not canonical seven-case order")
    reference = {
        "schema": "olm_windows_ae_reference_manifest/v1",
        "kind": "olmblur_windows_float32_rgba_exr_reference",
        "project": {"width": 1920, "height": 1080, "frame_rate": 24, "duration": 6.16666666666667, "bits_per_channel": 32, "renderer": "SOFTWARE", "working_space": "", "linear_blending": False},
        "comp": {"width": 1920, "height": 1080, "frame_rate": 24, "duration": 6.16666666666667},
        "output": {"format": "exr", "template": EXR_TEMPLATE, "compression": "none", "sample_type": "float", "bits_per_channel": 32, "channel_order": "RGBA", "channel_count": 4},
        "cases": cases,
    }
    request = {
        "kind": "olm_ae_windows_dual_depth_request",
        "lane": "32bpc",
        "effect_name": "OLM Blur",
        "effect_match_name": "OLM OLM Blur",
        "reference_manifest": "reference_manifest.json",
        "input_dir": "../inputs",
        "render_set": {"id": "software_32bpc", "project_gpu_accel_type.current_name": "SOFTWARE", "bits_per_channel": 32, "required": True},
        "output": reference["output"],
        "cases": [{"id": case["id"], "before_effects_frame": case["before_effects_frame"], "frame": case["frame"]} for case in cases],
    }
    return request, reference


def make_8bpc(reference: dict[str, Any], input_hashes: dict[str, str]) -> dict[str, Any]:
    cases = []
    for source_case in reference["cases"]:
        effect = source_case["effects"][0]
        cases.append({
            "id": source_case["id"], "frame": source_case["frame"], "time": source_case["time"],
            "before_effects_frame": source_case["before_effects_frame"], "input_sha256": input_hashes[source_case["id"]],
            "effects": [effect],
        })
    return {
        "schema": "olm_windows_ae_reference_manifest/v1", "kind": "olmblur_windows_8bpc_png_reference",
        "project": {"width": 1920, "height": 1080, "frame_rate": 24, "duration": 6.16666666666667, "bits_per_channel": 8, "renderer": "SOFTWARE", "working_space": "", "linear_blending": False},
        "comp": {"width": 1920, "height": 1080, "frame_rate": 24, "duration": 6.16666666666667}, "output": {"format": "png", "bits_per_channel": 8, "channel_order": "RGBA"}, "cases": cases,
    }


def powershell_asset() -> str:
    return f'''param(
    [Parameter(Mandatory=$true)][string]$PluginPath,
    [Parameter(Mandatory=$true)][string]$AfterFX,
    [Parameter(Mandatory=$true)][string]$ExrOutputTemplate,
    [Parameter(Mandatory=$false)][string]$OutputDir = ""
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExpectedHash = "{PLUGIN_SHA256}"
$RequiredExrTemplate = "{EXR_TEMPLATE}"
$RunDir = if ($OutputDir) {{ New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null; (Resolve-Path -LiteralPath $OutputDir).Path }} else {{ Join-Path $Root "run" }}
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
$SummaryPath = Join-Path $RunDir "return_manifest.json"
function Write-Json($Path, $Value) {{ $Value | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -Path $Path }}
function Fail-Closed([string]$Status, [string]$Message, $Provenance = $null) {{
    $record = [ordered]@{{ kind="olmblur_windows_dual_depth_return"; status=$Status; rendered=$false; error=$Message; plugin=$Provenance; required_sha256=$ExpectedHash }}
    Write-Json $SummaryPath $record
    Write-Error "$Status`: $Message"
    exit 2
}}
if (-not (Test-Path -LiteralPath $PluginPath -PathType Leaf)) {{ Fail-Closed "missing_plugin" "PluginPath does not name a file" }}
$plugin = Get-Item -LiteralPath $PluginPath
if ($plugin.Name -ne "OLMBlur.aex") {{ Fail-Closed "missing_plugin" "PluginPath must name OLMBlur.aex" }}
$hash = (Get-FileHash -LiteralPath $plugin.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
$provenance = [ordered]@{{ path=$plugin.FullName; size_bytes=[int64]$plugin.Length; last_write_time_utc=$plugin.LastWriteTimeUtc.ToString("o"); sha256=$hash; required_sha256=$ExpectedHash }}
if ($hash -ne $ExpectedHash) {{ Fail-Closed "hash_mismatch" "installed OLMBlur.aex SHA-256 $hash does not equal required $ExpectedHash" $provenance }}
if (-not (Test-Path -LiteralPath $AfterFX -PathType Leaf)) {{ Fail-Closed "missing_afterfx" "AfterFX.exe was not found; no render was started" $provenance }}
if ($ExrOutputTemplate -cne $RequiredExrTemplate) {{ Fail-Closed "wrong_exr_template" "ExrOutputTemplate must be exactly '$RequiredExrTemplate' (no compression, FLOAT32, RGBA)" $provenance }}
$lanes = @(@{{ name="8bpc_png"; bits=8; mode="png"; dir=(Join-Path $Root "lanes\\8bpc"); output=(Join-Path $RunDir "8bpc_png") }}, @{{ name="32bpc_float32_rgba_exr"; bits=32; mode="exr_render_queue"; dir=(Join-Path $Root "lanes\\32bpc"); output=(Join-Path $RunDir "32bpc_float32_rgba_exr") }})
$results = @()
foreach ($lane in $lanes) {{
    New-Item -ItemType Directory -Force -Path $lane.output | Out-Null
    foreach ($caseNumber in 1..7) {{
        $caseId = "case_{{0:D4}}" -f $caseNumber
        $env:OLM_AE_REQUEST_DIR = $lane.dir; $env:OLM_AE_CASE_ID = $caseId; $env:OLM_AE_OUTPUT_DIR = $lane.output
        $env:OLM_AE_LOG_PATH = Join-Path $RunDir "$($lane.name)_$caseId.log"; $env:OLM_AE_RESULT_JSON = Join-Path $RunDir "$($lane.name)_$caseId.result.json"
        $env:OLM_AE_OUTPUT_MODE = $lane.mode; $env:OLM_AE_OUTPUT_TEMPLATE = $ExrOutputTemplate; $env:OLM_AE_FORCE_SOFTWARE = "1"; $env:OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT = "1"; $env:OLM_AE_FORCE_NEW_PROJECT = "1"; $env:OLM_AE_DISABLE_EFFECT = ""
        & $AfterFX -r (Join-Path $Root "render_olmblur_case.jsx")
        if ($LASTEXITCODE -ne 0) {{ Fail-Closed "render_failed" "$($lane.name) $caseId AfterFX exit $LASTEXITCODE" $provenance }}
        $result = Get-Content $env:OLM_AE_RESULT_JSON -Raw | ConvertFrom-Json
        if ($result.status -ne "ok") {{ Fail-Closed "render_failed" "$($lane.name) $caseId reported $($result.error)" $provenance }}
        if ($lane.bits -eq 8 -and -not (Test-Path (Join-Path $lane.output "$caseId.png"))) {{ Fail-Closed "missing_output" "$($lane.name) $caseId PNG missing" $provenance }}
        if ($lane.bits -eq 32 -and -not (Test-Path (Join-Path $lane.output "$caseId.exr"))) {{ Fail-Closed "missing_output" "$($lane.name) $caseId EXR missing" $provenance }}
        $results += [ordered]@{{ lane=$lane.name; case_id=$caseId; result=$result }}
    }}
    $controlDir = Join-Path $RunDir "$($lane.name)_no_effect_control"; New-Item -ItemType Directory -Force -Path $controlDir | Out-Null
    $env:OLM_AE_CASE_ID = "case_0001"; $env:OLM_AE_OUTPUT_DIR = $controlDir; $env:OLM_AE_LOG_PATH = Join-Path $RunDir "$($lane.name)_no_effect_control.log"; $env:OLM_AE_RESULT_JSON = Join-Path $RunDir "$($lane.name)_no_effect_control.result.json"; $env:OLM_AE_DISABLE_EFFECT = "1"
    & $AfterFX -r (Join-Path $Root "render_olmblur_case.jsx")
    if ($LASTEXITCODE -ne 0) {{ Fail-Closed "no_effect_control_failed" "$($lane.name) control AfterFX exit $LASTEXITCODE" $provenance }}
    $control = Get-Content $env:OLM_AE_RESULT_JSON -Raw | ConvertFrom-Json
    if ($control.status -ne "ok" -or -not $control.effect_disabled) {{ Fail-Closed "no_effect_control_failed" "$($lane.name) control was not recorded as disabled" $provenance }}
    if ($lane.bits -eq 8 -and -not (Test-Path (Join-Path $controlDir "case_0001.png"))) {{ Fail-Closed "no_effect_control_failed" "$($lane.name) control PNG missing" $provenance }}
    if ($lane.bits -eq 32 -and -not (Test-Path (Join-Path $controlDir "case_0001.exr"))) {{ Fail-Closed "no_effect_control_failed" "$($lane.name) control EXR missing" $provenance }}
    $results += [ordered]@{{ lane=$lane.name; case_id="case_0001"; no_effect_control=$control }}
}}
$env:OLM_AE_DISABLE_EFFECT = ""
$record = [ordered]@{{ kind="olmblur_windows_dual_depth_return"; status="rendered"; rendered=$true; plugin=$provenance; required_sha256=$ExpectedHash; ae_version=($results[0].result.ae_version); renderer="Software"; color_settings=[ordered]@{{ working_space=$results[0].result.project_working_space; linear_blending=$false; bits_per_channel=@(8,32) }}; exr_output_template=$ExrOutputTemplate; exr_header_required=[ordered]@{{ container_format="OpenEXR"; compression="none"; sample_type="float"; bits_per_channel=32; channel_order="RGBA"; channel_count=4 }}; results=$results }}
Write-Json $SummaryPath $record
Write-Host "OK: dual-depth OLMBlur recapture complete; return manifest $SummaryPath"
'''


def build(args: argparse.Namespace) -> Path:
    request_8, source_ref, source_files = load_8bpc(args.source_zip.resolve())
    spec = load_json(args.source_32_spec.resolve())
    input_hashes = {case: digest(source_files[SOURCE_PREFIX + f"input/{case}_before_effects.png"]) for case in CASE_IDS}
    for item in spec["inputs"]:
        if item["sha256"] != input_hashes[item["source_case_id"]]:
            raise SystemExit(f"32bpc input hash mismatch for {item['source_case_id']}")
        if file_digest(args.source_32_dir.resolve() / item["before_effects_frame"]) != item["sha256"]:
            raise SystemExit(f"normalized 32bpc source hash mismatch for {item['source_case_id']}")
    ref_8 = make_8bpc(source_ref, input_hashes)
    req_32, ref_32 = make_32bpc(source_ref, spec, input_hashes)
    req_8 = {"kind": "olm_ae_windows_dual_depth_request", "lane": "8bpc", "effect_name": request_8["effect_name"], "effect_match_name": request_8["effect_match_name"], "reference_manifest": "reference_manifest.json", "input_dir": "../inputs", "render_set": {"id": "software_8bpc", "project_gpu_accel_type.current_name": "SOFTWARE", "bits_per_channel": 8, "required": True}, "cases": [{"id": c, "before_effects_frame": f"{c}_before_effects.png", "frame": f"{c}.png"} for c in CASE_IDS]}
    manifest = {"kind": "olmblur_windows_software_dual_depth_canonical_recapture", "schema": 1, "created_at": "2026-07-11", "platform": "windows", "plugin": {"name": "OLMBlur.aex", "required_sha256": PLUGIN_SHA256, "record": ["path", "size_bytes", "last_write_time_utc", "sha256"]}, "lanes": {"8bpc_png": {"bits_per_channel": 8, "renderer": "Software", "linear_blending": False, "output": "PNG", "request": "lanes/8bpc/request_manifest.json"}, "32bpc_float32_rgba_exr": {"bits_per_channel": 32, "renderer": "Software", "linear_blending": False, "output": {"container_format": "OpenEXR", "compression": "none", "sample_type": "float", "channel_order": "RGBA", "channel_count": 4}, "request": "lanes/32bpc/request_manifest.json", "template": EXR_TEMPLATE}}, "cases": list(CASE_IDS), "input_sha256": input_hashes, "fail_closed": ["hash_mismatch", "missing_plugin", "missing_afterfx", "wrong_exr_template", "render_failed", "no_effect_control_failed"]}
    jsx = (ROOT / "scripts/ae_render_single_case.jsx").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="olmblur_dual_20260711_") as temp_name:
        stage = Path(temp_name) / PACKAGE_STEM
        (stage / "inputs").mkdir(parents=True); (stage / "expected_8bpc").mkdir(); (stage / "lanes/8bpc").mkdir(parents=True); (stage / "lanes/32bpc").mkdir(parents=True)
        for name, data in source_files.items():
            if "/input/" in name: (stage / "inputs" / Path(name).name).write_bytes(data)
            elif "/expected/" in name: (stage / "expected_8bpc" / Path(name).name).write_bytes(data)
        for lane, req, ref in (("8bpc", req_8, ref_8), ("32bpc", req_32, ref_32)):
            (stage / "lanes" / lane / "request_manifest.json").write_text(json.dumps(req, indent=2) + "\n", encoding="utf-8")
            (stage / "lanes" / lane / "reference_manifest.json").write_text(json.dumps(ref, indent=2) + "\n", encoding="utf-8")
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (stage / "render_olmblur_case.jsx").write_text(jsx, encoding="utf-8")
        (stage / "run_olmblur_dual_depth.ps1").write_text(powershell_asset(), encoding="utf-8")
        (stage / "README.md").write_text("# OLMBlur Windows dual-depth canonical recapture\n\nRun `run_olmblur_dual_depth.ps1 -PluginPath <exact OLMBlur.aex> -AfterFX <AfterFX.exe> -ExrOutputTemplate 'OLMBlur OpenEXR RGBA Float32 No Compression'`. The runner hashes the AEX before launching AE, uses Software rendering with linear blending off, renders seven 8bpc PNGs and seven 32bpc FLOAT32 RGBA no-compression OpenEXR files, runs one disabled-effect control per lane, and writes `run/return_manifest.json`. Any gate failure exits before claiming rendered output.\n", encoding="utf-8")
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(stage.rglob("*")):
                if path.is_file(): archive.write(path, f"{PACKAGE_STEM}/{path.relative_to(stage).as_posix()}")
    print(f"[OK] {output}")
    print(f"[SUMMARY] cases=7 lanes=8bpc_png,32bpc_float32_rgba_exr required_sha256={PLUGIN_SHA256}")
    return output


if __name__ == "__main__":
    build(parse_args())
