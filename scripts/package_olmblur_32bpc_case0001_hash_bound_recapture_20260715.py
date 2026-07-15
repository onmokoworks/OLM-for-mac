#!/usr/bin/env python3
"""Build the bounded Windows AE 26.3 OLMBlur case_0001 float-EXR package."""

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
REQUEST = ROOT / "refs/reference_requests/olmblur_32bpc_mac_windows_float_focus_20260711.json"
REFERENCE_SOURCE = ROOT / "refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMBlur/reference_manifest.json"
INPUT_SOURCE = REFERENCE_SOURCE.parent / "case_0001_before_effects.png"
RENDERER = ROOT / "scripts/ae_render_single_case.jsx"
PACKAGE_STEM = "olmblur_32bpc_case0001_hash_bound_recapture_20260715"
OUTPUT_DEFAULT = ROOT / "refs/reference_requests" / f"{PACKAGE_STEM}.zip"
REQUEST_ID = "olmblur_32bpc_case0001_hash_bound_recapture_20260715"
CASE_ID = "olmblur__case_0001"
CASE_FILE_ID = "case_0001"
REQUIRED_AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
EXR_TEMPLATE = "OLM EXR 32 Float"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def make_manifests(request: dict[str, Any], source: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    item = next(case for case in request["cases"] if case["id"] == CASE_ID)
    source_case = next(case for case in source["cases"] if case["id"] == CASE_FILE_ID)
    if item["input"] != "olmblur_case_0001_source":
        raise SystemExit("case_0001 input binding changed")
    if item["effect"] != {"name": "OLM Blur", "match_name": "OLM OLM Blur"}:
        raise SystemExit("case_0001 effect identity changed")
    expected_input_hash = next(row["sha256"] for row in request["inputs"] if row["id"] == item["input"])
    if sha256(INPUT_SOURCE) != expected_input_hash:
        raise SystemExit("case_0001 input SHA-256 does not match the request")

    params = []
    for index, row in enumerate(item["params_full"], 1):
        params.append({
            "name": row["name"],
            "match_name": row["match_name"],
            "property_index": row["property_index"],
            "property_value_type": row["property_value_type"],
            "value": row["value"],
            "path_full": [
                {"name": "OLM Blur", "match_name": "OLM OLM Blur", "property_index": 1},
                {"name": row["name"], "match_name": row["match_name"], "property_index": row["property_index"]},
            ],
        })
    reference = {
        "schema": "olm_windows_ae_reference_manifest/v1",
        "kind": "olmblur_case0001_float_exr_reference",
        "project": {
            "width": source["comp"]["width"], "height": source["comp"]["height"],
            "frame_rate": source["comp"]["frame_rate"], "duration": source["comp"]["duration"],
            "bits_per_channel": 32, "renderer": "SOFTWARE", "working_space": "", "linear_blending": False,
        },
        "comp": {"width": source["comp"]["width"], "height": source["comp"]["height"], "frame_rate": source["comp"]["frame_rate"], "duration": source["comp"]["duration"]},
        "output": {"format": "exr", "template": EXR_TEMPLATE, "compression": "none", "sample_type": "float", "bits_per_channel": 32, "channel_order": "RGBA", "channel_count": 4},
        "cases": [{
            "id": CASE_ID, "source_case_id": CASE_FILE_ID, "time": source_case["time"],
            "before_effects_frame": "case_0001_before_effects.png", "frame": "case_0001.exr",
            "input_sha256": expected_input_hash,
            "effects": [{"name": "OLM Blur", "match_name": "OLM OLM Blur", "property_index": 1, "enabled": True, "active": True, "params": params}],
        }],
    }
    request_manifest = {
        "schema": 1, "kind": "olm_ae_windows_case_request", "request_id": REQUEST_ID,
        "lane": "software_32bpc_float_exr", "effect_name": "OLM Blur", "effect_match_name": "OLM OLM Blur",
        "reference_manifest": "reference_manifest.json", "input_dir": "input",
        "render_set": {"id": "software_32bpc", "project_gpu_accel_type.current_name": "SOFTWARE", "project_gpu_accel_type.raw": "GpuAccelType.SOFTWARE", "bits_per_channel": 32, "required": True},
        "output": reference["output"],
        "cases": [{"id": CASE_ID, "before_effects_frame": "case_0001_before_effects.png", "frame": "case_0001.exr"}],
    }
    return request_manifest, reference


def powershell() -> str:
    return rf'''[CmdletBinding()]
param(
  [string]$PluginPath = 'C:\\Program Files\\Adobe\\Common\\Plug-ins\\7.0\\MediaCore\\OLM\\OLMBlur.aex',
  [string]$AfterFX = 'C:\\Program Files\\Adobe\\Adobe After Effects 2026\\Support Files\\AfterFX.exe',
  [string]$OutputDir = (Join-Path $PSScriptRoot 'return')
)
$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
$ExpectedHash = '{REQUIRED_AEX_SHA256}'
$ExpectedInputHash = 'cc1bf1aa128dea6197405ee722c66198fb5fcbc213bf2569c7af9f30be4fa4f4'
$ExpectedTemplate = '{EXR_TEMPLATE}'
$RequestId = '{REQUEST_ID}'
$RunId = 'olmblur-case0001-' + [guid]::NewGuid().ToString('N')
$RunDir = Join-Path $OutputDir $RunId
$ReturnZip = Join-Path $OutputDir ($RequestId + '-' + $RunId + '.zip')
$script:ActiveAePid = $null
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
$StatusPath = Join-Path $RunDir 'status.json'
$ManifestPath = Join-Path $RunDir 'return_manifest.json'
function Write-Json([string]$Path, [object]$Value) {{ $Value | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $Path -Encoding UTF8 }}
function Fail-Closed([string]$Stage, [string]$Reason, [object]$Detail=$null) {{
  if ($null -ne $script:ActiveAePid) {{ try {{ Stop-Process -Id $script:ActiveAePid -Force -ErrorAction SilentlyContinue; Wait-Process -Id $script:ActiveAePid -Timeout 30 -ErrorAction SilentlyContinue }} catch {{}}; $script:ActiveAePid = $null }}
  $body = [ordered]@{{ schema='olmblur-32bpc-case0001-return-v1'; request_id=$RequestId; run_id=$RunId; status='exact_bind_failure'; failure=[ordered]@{{stage=$Stage; reason=$Reason; detail=$Detail}} }}
  Write-Json $StatusPath $body; Write-Json $ManifestPath $body
  try {{ if (Test-Path -LiteralPath $ReturnZip) {{ Remove-Item -LiteralPath $ReturnZip -Force }}; Compress-Archive -Path (Join-Path $RunDir '*') -DestinationPath $ReturnZip -CompressionLevel Optimal }} catch {{ Write-Error "evidence_archive_failure: $($_.Exception.Message)"; exit 3 }}
  Write-Error "$Stage`: $Reason"; exit 2
}}
function Read-Json([string]$Path) {{ if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {{ throw "missing JSON: $Path" }}; Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json }}
function Find-LoadedAex([int]$ExpectedPid, [string]$ExpectedPath) {{
  try {{
    $process = Get-Process -Id $ExpectedPid -ErrorAction Stop
    if ($process.ProcessName -ine 'AfterFX') {{ return $null }}
    $module = @($process.Modules | Where-Object {{ $_.FileName -ieq $ExpectedPath }} | Select-Object -First 1)
    if ($module.Count -eq 1) {{ return [ordered]@{{process=$process;module=$module[0]}} }}
  }} catch {{}}
  return $null
}}
function Resolve-RenderedExr([object]$Result, [string]$Label, [string]$ExpectedRoot) {{
  $reported = [string]$Result.output_exr
  if ([string]::IsNullOrWhiteSpace($reported)) {{ throw "$Label result JSON did not report output_exr" }}
  $expectedPrefix = [IO.Path]::GetFullPath($ExpectedRoot).TrimEnd('\') + '\'
  $reportedFull = [IO.Path]::GetFullPath($reported)
  if (-not $reportedFull.StartsWith($expectedPrefix, [StringComparison]::OrdinalIgnoreCase)) {{ throw "$Label reported EXR escaped the current output directory: $reported" }}
  if (-not (Test-Path -LiteralPath $reported -PathType Leaf)) {{ throw "$Label reported EXR does not exist: $reported" }}
  $file = Get-Item -LiteralPath $reported
  if ($file.Extension -ine '.exr' -or $file.Length -le 0) {{ throw "$Label reported path is not a non-empty EXR: $reported" }}
  return $file
}}
try {{
  if (-not (Test-Path -LiteralPath $PluginPath -PathType Leaf)) {{ Fail-Closed 'preflight' 'missing OLMBlur.aex' $PluginPath }}
  $plugin = Get-Item -LiteralPath $PluginPath
  if ($plugin.Name -cne 'OLMBlur.aex') {{ Fail-Closed 'preflight' 'PluginPath must name OLMBlur.aex' $plugin.FullName }}
  $hash = (Get-FileHash -LiteralPath $plugin.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  $pluginRecord = [ordered]@{{path=$plugin.FullName;size_bytes=[int64]$plugin.Length;last_write_time_utc=$plugin.LastWriteTimeUtc.ToString('o');sha256=$hash;required_sha256=$ExpectedHash}}
  if ($hash -ne $ExpectedHash) {{ Fail-Closed 'preflight' 'OLMBlur.aex SHA-256 mismatch; AE was not started' $pluginRecord }}
  if (-not (Test-Path -LiteralPath $AfterFX -PathType Leaf)) {{ Fail-Closed 'preflight' 'AfterFX.exe is missing; AE was not started' $AfterFX }}
  $AfterFX = (Get-Item -LiteralPath $AfterFX).FullName
  $inputPath = Join-Path $Root 'input\case_0001_before_effects.png'
  if (-not (Test-Path -LiteralPath $inputPath -PathType Leaf)) {{ Fail-Closed 'preflight' 'packaged input is missing' $inputPath }}
  $inputHash = (Get-FileHash -LiteralPath $inputPath -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($inputHash -ne $ExpectedInputHash) {{ Fail-Closed 'preflight' 'packaged input SHA-256 mismatch; AE was not started' ([ordered]@{{expected=$ExpectedInputHash;actual=$inputHash}}) }}
  $preexisting = @(Get-Process -Name AfterFX -ErrorAction SilentlyContinue)
  if ($preexisting.Count -ne 0) {{ Fail-Closed 'preflight' 'close every existing AfterFX process before running this package' @($preexisting | ForEach-Object {{ $_.Id }}) }}
  $contractFiles = [ordered]@{{
    input = $inputPath
    request_manifest = (Join-Path $Root 'request_manifest.json')
    reference_manifest = (Join-Path $Root 'reference_manifest.json')
    renderer = (Join-Path $Root 'scripts\\ae_render_single_case.jsx')
    package_manifest = (Join-Path $Root 'manifest.json')
    runner = (Join-Path $Root 'run_olmblur_32bpc_case0001.ps1')
  }}
  $contractPath = Join-Path $Root 'package_contract.json'
  $contract = Read-Json $contractPath
  if ([string]$contract.request_id -ne $RequestId) {{ Fail-Closed 'preflight' 'package contract request ID mismatch' $contract.request_id }}
  $contractHashes = [ordered]@{{}}
  foreach ($entry in $contractFiles.GetEnumerator()) {{
    if (-not (Test-Path -LiteralPath $entry.Value -PathType Leaf)) {{ Fail-Closed 'preflight' "missing contract artifact $($entry.Key)" $entry.Value }}
    $actualContractHash = (Get-FileHash -LiteralPath $entry.Value -Algorithm SHA256).Hash.ToLowerInvariant()
    $expectedContractHash = [string]$contract.artifacts.($entry.Key).sha256
    if ([string]::IsNullOrWhiteSpace($expectedContractHash) -or $actualContractHash -ne $expectedContractHash) {{ Fail-Closed 'preflight' "contract artifact SHA-256 mismatch: $($entry.Key)" ([ordered]@{{expected=$expectedContractHash;actual=$actualContractHash}}) }}
    $contractHashes[$entry.Key] = $actualContractHash
  }}
  $packageContractHash = (Get-FileHash -LiteralPath $contractPath -Algorithm SHA256).Hash.ToLowerInvariant()
  $out = Join-Path $RunDir 'same_run'; New-Item -ItemType Directory -Force -Path $out | Out-Null
  $resultPath = Join-Path $RunDir 'same_run.result.json'; $logPath = Join-Path $RunDir 'same_run.log'
  $env:OLM_AE_REQUEST_DIR = $Root; $env:OLM_AE_CASE_ID = '{CASE_ID}'; $env:OLM_AE_OUTPUT_DIR = $out
  $env:OLM_AE_LOG_PATH = $logPath; $env:OLM_AE_RESULT_JSON = $resultPath; $env:OLM_AE_OUTPUT_MODE = 'exr_render_queue'; $env:OLM_AE_OUTPUT_TEMPLATE = $ExpectedTemplate
  $env:OLM_AE_FORCE_SOFTWARE = '1'; $env:OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT = '1'; $env:OLM_AE_FORCE_NEW_PROJECT = '1'; $env:OLM_AE_DISABLE_EFFECT = '0'; $env:OLM_AE_KEEP_OPEN = '0'
  $jsxPath = $contractFiles.renderer; $quotedJsxPath = '"' + $jsxPath + '"'
  $launch = Start-Process -FilePath $AfterFX -ArgumentList @('-r', $quotedJsxPath) -PassThru -WindowStyle Normal
  $script:ActiveAePid = $launch.Id
  $loaded = $null; $deadline = (Get-Date).AddSeconds(120)
  while ((Get-Date) -lt $deadline -and $null -eq $loaded) {{ $loaded = Find-LoadedAex $launch.Id $plugin.FullName; if ($null -eq $loaded) {{ Start-Sleep -Milliseconds 250 }} }}
  if ($null -eq $loaded) {{ Fail-Closed 'loaded_aex_gate' 'hash-pinned OLMBlur.aex was not observed in the launched AfterFX process before render acceptance' $pluginRecord }}
  $loadedHash = (Get-FileHash -LiteralPath $loaded.module.FileName -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($loadedHash -ne $ExpectedHash) {{ Fail-Closed 'loaded_aex_gate' 'loaded OLMBlur.aex SHA-256 mismatch' ([ordered]@{{expected_sha256=$ExpectedHash;actual_sha256=$loadedHash;path=$loaded.module.FileName;ae_pid=$loaded.process.Id}}) }}
  $loadedFile = Get-Item -LiteralPath $loaded.module.FileName
  $loadedRecord = [ordered]@{{path=$loaded.module.FileName;size_bytes=[int64]$loadedFile.Length;last_write_time_utc=$loadedFile.LastWriteTimeUtc.ToString('o');sha256=$loadedHash;ae_pid=[int]$loaded.process.Id}}
  if (-not $launch.WaitForExit(600000)) {{ try {{ $launch.Kill() }} catch {{}}; Fail-Closed 'render_timeout' 'same-run pair exceeded 600 seconds' $pluginRecord }}
  $script:ActiveAePid = $null
  if ($launch.ExitCode -ne 0) {{ Fail-Closed 'render' "same-run AfterFX exit $($launch.ExitCode)" $pluginRecord }}
  $result = Read-Json $resultPath
  if ([string]$result.status -ne 'ok' -or [string]$result.ae_version -ne '26.3x87' -or [int]$result.project_bits_per_channel -ne 32 -or [int]$result.project_gpu_accel_type_raw -ne 1816 -or [string]$result.project_working_space -ne '' -or [bool]$result.project_linear_blending) {{ Fail-Closed 'render' 'same-run AE result failed project contract' ($result | ConvertTo-Json -Compress) }}
  if (@($result.warnings).Count -ne 0) {{ Fail-Closed 'render' 'same-run result returned warnings' ($result | ConvertTo-Json -Compress) }}
  if ([bool]$result.effect_disabled -or [int]$result.effect_count_after_setup -ne 1 -or [string]$result.effect_identity_readback.match_name -ne 'OLM OLM Blur') {{ Fail-Closed 'effect_identity' 'effect-on identity/readback mismatch' ($result | ConvertTo-Json -Compress) }}
  $p=$result.effect_param_readback
  if ($null -eq $p -or [single]$p.blur_amount -ne [single]129.4 -or [single]$p.blur_smoothness -ne [single]100 -or [single]$p.number_of_repeat -ne [single]2 -or [single]$p.bias_direction -ne [single]1 -or [single]$p.legacy -ne [single]0) {{ Fail-Closed 'parameter_readback' 'effect-on live parameter readback mismatch' ($result | ConvertTo-Json -Compress) }}
  if (-not [bool]$result.no_effect_verified -or [int]$result.no_effect_count_after_removal -ne 0) {{ Fail-Closed 'no_effect_control' 'same-run control was not proven effect-free after removal' ($result | ConvertTo-Json -Compress) }}
  $results = @()
  foreach ($mode in @(@{{name='effect_on';enabled=$true;archive='return/effect_on.exr'}}, @{{name='no_effect';enabled=$false;archive='return/effect_no_effect.exr'}})) {{
    $branch = $result.outputs.($mode.name)
    if ($null -eq $branch) {{ Fail-Closed 'render' "missing same-run branch $($mode.name)" ($result | ConvertTo-Json -Compress) }}
    $om = $branch.output_module_readback
    if ([string]$om.format -ne 'OpenEXR Sequence' -or [string]$om.channels -ne 'RGB + Alpha' -or [string]$om.depth -ne 'Floating Point+' -or [string]$om.color -ne 'Premultiplied (Matted)') {{ Fail-Closed 'output_module_readback' "$($mode.name) output module readback mismatch" ($result | ConvertTo-Json -Compress) }}
    $exrCarrier = [pscustomobject]@{{output_exr=[string]$branch.output_exr}}
    $exr = Resolve-RenderedExr $exrCarrier $mode.name $out
    $archivePath = Join-Path $RunDir ($mode.archive -replace '/', '\\'); New-Item -ItemType Directory -Force -Path (Split-Path -Parent $archivePath) | Out-Null; Copy-Item -LiteralPath $exr.FullName -Destination $archivePath -Force
    $paramReadback = if ($mode.enabled) {{ $result.effect_param_readback }} else {{ $null }}
    $results += [ordered]@{{mode=$mode.name;effect_enabled=$mode.enabled;effect_param_readback=$paramReadback;output_module_readback=$om;archive_path=$mode.archive;exr_sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant();exr_size_bytes=[int64](Get-Item $archivePath).Length;ae_version=$result.ae_version;ae_pid=[int]$loadedRecord.ae_pid;project_bits_per_channel=[int]$result.project_bits_per_channel;project_working_space=[string]$result.project_working_space;project_linear_blending=[bool]$result.project_linear_blending;project_gpu_accel_type=[ordered]@{{current_name='SOFTWARE';raw=[int]$result.project_gpu_accel_type_raw}}}}
  }}
  foreach ($entry in $contractFiles.GetEnumerator()) {{ Copy-Item -LiteralPath $entry.Value -Destination (Join-Path $RunDir (Split-Path -Leaf $entry.Value)) -Force }}
  Copy-Item -LiteralPath $contractPath -Destination (Join-Path $RunDir 'package_contract.json') -Force
  $manifest = [ordered]@{{schema='olmblur-32bpc-case0001-return-v1';kind='olmblur_windows_case0001_float_exr_return';request_id=$RequestId;run_id=$RunId;status='answered_candidate_pending_exr_header_validation';same_ae_process_pair=$true;package_contract_sha256=$packageContractHash;contract_artifact_sha256=$contractHashes;return_zip=$ReturnZip;plugin=[ordered]@{{prelaunch=$pluginRecord;loaded=$loadedRecord}};input=[ordered]@{{path='input/case_0001_before_effects.png';sha256=$inputHash}};ae_version=$results[0].ae_version;project=[ordered]@{{bits_per_channel=32;gpu_accel_type=[ordered]@{{current_name='SOFTWARE';raw=1816}};working_space='';linear_blending=$false}};output=[ordered]@{{template=$ExpectedTemplate;container_format='OpenEXR';required_sample_type='FLOAT';bits_per_channel=32;channel_order='RGBA';required_compression='none';header_validated=$false;requires_post_intake_header_validation=$true}};effect_outputs=$results;fail_closed=$true}}
  Write-Json $ManifestPath $manifest; Write-Json $StatusPath $manifest
  if (Test-Path -LiteralPath $ReturnZip) {{ Remove-Item -LiteralPath $ReturnZip -Force }}
  Compress-Archive -Path (Join-Path $RunDir '*') -DestinationPath $ReturnZip -CompressionLevel Optimal
  Write-Host "OK: $ReturnZip"; exit 0
}} catch {{ Fail-Closed 'runtime' $_.Exception.Message $null }}
'''


def adapted_renderer() -> str:
    """Adapt the shared renderer only inside this ZIP with a live parameter readback."""
    source = RENDERER.read_text(encoding="utf-8")
    source = source.replace(
        '        effect_disabled: disableEffect,\n',
        '        effect_disabled: disableEffect,\n        effect_count_after_setup: -1,\n        no_effect_count_after_removal: -1,\n        no_effect_verified: false,\n        effect_identity_readback: { name: "", match_name: "" },\n        effect_param_readback: { match_name: "", name: "", value: null, blur_amount: null, blur_smoothness: null, number_of_repeat: null, bias_direction: null, legacy: null },\n        output_module_readback: { format: "", channels: "", depth: "", color: "" },\n        outputs: { effect_on: { output_exr: "", output_module_readback: { format: "", channels: "", depth: "", color: "" } }, no_effect: { output_exr: "", output_module_readback: { format: "", channels: "", depth: "", color: "" } } },\n        project_gpu_accel_type_raw: -1,\n',
        1,
    )
    software_anchor = '''        if (disableProjectColorManagement) {'''
    software_proof = '''        if (forceSoftware) {
            if (app.project.gpuAccelType !== GpuAccelType.SOFTWARE) {
                throw new Error("SOFTWARE renderer did not stick: " + app.project.gpuAccelType);
            }
            summary.project_gpu_accel_type_raw = Number(app.project.gpuAccelType);
        }
'''
    if software_anchor not in source:
        raise SystemExit("shared JSX anchor for SOFTWARE readback was not found")
    source = source.replace(software_anchor, software_proof + software_anchor, 1)
    effect_anchor = '''            if (!effect) {
                throw new Error("could not add effect: " + addErrors.join(" | "));
            }

            var params ='''
    effect_replacement = '''            if (!effect) {
                throw new Error("could not add effect: " + addErrors.join(" | "));
            }
            if (effect.matchName !== "OLM OLM Blur" || effect.name !== "OLM Blur") {
                throw new Error("effect identity mismatch: " + effect.name + " / " + effect.matchName);
            }

            var params ='''
    if effect_anchor not in source:
        raise SystemExit("shared JSX anchor for exact effect identity was not found")
    source = source.replace(effect_anchor, effect_replacement, 1)
    missing_property = '''            if (!prop) {
                summary.warnings.push("missing property " + (leaf.match_name || param.name));
                continue;
            }'''
    if missing_property not in source:
        raise SystemExit("shared JSX anchor for missing property was not found")
    source = source.replace(missing_property, '''            if (!prop) {
                throw new Error("missing property " + (leaf.match_name || param.name));
            }''', 1)
    anchor = '''        if (pauseBeforeRender) {'''
    readback = '''        var liveParade = layer.property("ADBE Effect Parade");
        summary.effect_count_after_setup = Number(liveParade.numProperties || 0);
        if (disableEffect) {
            summary.no_effect_verified = summary.effect_count_after_setup === 0;
            if (!summary.no_effect_verified) {
                throw new Error("disabled-effect control unexpectedly contains an effect");
            }
        } else {
            if (summary.effect_count_after_setup !== 1) {
                throw new Error("effect-on layer does not contain exactly one effect");
            }
            summary.effect_identity_readback = { name: String(effect.name || ""), match_name: String(effect.matchName || "") };
            function scalarReadback(matchName, name) {
                var property = childByMatchOrName(effect, matchName, name);
                if (!property || property.matchName !== matchName) {
                    throw new Error("missing exact live readback property " + matchName);
                }
                return Number(property.value);
            }
            summary.effect_param_readback = {
                match_name: "OLM OLM Blur-0003",
                name: "Number of Repeat",
                value: scalarReadback("OLM OLM Blur-0003", "Number of Repeat"),
                blur_amount: scalarReadback("OLM OLM Blur-0005", "Blur Amount"),
                blur_smoothness: scalarReadback("OLM OLM Blur-0006", "Blur Smoothness"),
                number_of_repeat: scalarReadback("OLM OLM Blur-0003", "Number of Repeat"),
                bias_direction: scalarReadback("OLM OLM Blur-0004", "Bias Direction"),
                legacy: scalarReadback("OLM OLM Blur-0007", "Legacy")
            };
        }

'''
    if anchor not in source:
        raise SystemExit("shared JSX anchor for live readback was not found")
    source = source.replace(anchor, readback + anchor, 1)
    exr_block = '''        if (outputMode === "exr_render_queue") {
            if (!outputTemplate) {
                throw new Error("OLM_AE_OUTPUT_TEMPLATE is required for exr_render_queue");
            }
            var exrBase = outputDir + "/" + caseId + ".exr";
            var exrSequence = exrBase.replace(/\\.exr$/i, "_[#####].exr");
            var rqItem = app.project.renderQueue.items.add(comp);
            rqItem.timeSpanStart = Number(caseRef.time || 0);
            rqItem.timeSpanDuration = 1.0 / Number(comp.frameRate || 24.0);
            var outputModule = rqItem.outputModule(1);
            outputModule.applyTemplate(outputTemplate);
            outputModule.file = new File(exrSequence);
            appendText(logPath, "renderQueue template=" + outputTemplate + " output=" + exrSequence + "\\n");
            app.project.renderQueue.render();
            var exr = new File(exrSequence.replace("[#####]", "00000"));
            if (!exr.exists) {
                throw new Error("EXR was not written: " + exrSequence);
            }
            summary.output_exr = exr.fsName;
            try { rqItem.remove(); } catch (_) {}
            appendText(logPath, "exr exists " + summary.output_exr + "\\n");
        } else {'''
    same_run_exr_block = '''        if (outputMode === "exr_render_queue") {
            if (!outputTemplate) {
                throw new Error("OLM_AE_OUTPUT_TEMPLATE is required for exr_render_queue");
            }
            if (disableEffect || !effect) {
                throw new Error("same-run renderer requires the effect-on branch first");
            }
            function outputSettingsReadback(outputModule) {
                if (!outputModule.getSettings || typeof GetSettingsFormat === "undefined" || typeof GetSettingsFormat.STRING === "undefined") {
                    throw new Error("OutputModule.getSettings(GetSettingsFormat.STRING) is unavailable");
                }
                var settings = outputModule.getSettings(GetSettingsFormat.STRING);
                if (!settings) {
                    throw new Error("Output Module settings readback is empty");
                }
                return {
                    format: String(settings["Format"] || ""),
                    channels: String(settings["Channels"] || ""),
                    depth: String(settings["Depth"] || ""),
                    color: String(settings["Color"] || "")
                };
            }
            function renderExrBranch(branchName) {
                var exrBase = outputDir + "/" + caseId + "__" + branchName + ".exr";
                var exrSequence = exrBase.replace(/\\.exr$/i, "_[#####].exr");
                var rqItem = app.project.renderQueue.items.add(comp);
                rqItem.timeSpanStart = Number(caseRef.time || 0);
                rqItem.timeSpanDuration = 1.0 / Number(comp.frameRate || 24.0);
                var outputModule = rqItem.outputModule(1);
                outputModule.applyTemplate(outputTemplate);
                var settings = outputSettingsReadback(outputModule);
                outputModule.file = new File(exrSequence);
                appendText(logPath, "renderQueue branch=" + branchName + " template=" + outputTemplate + " output=" + exrSequence + "\\n");
                app.project.renderQueue.render();
                var exr = new File(exrSequence.replace("[#####]", "00000"));
                if (!exr.exists) {
                    throw new Error("EXR was not written: " + exrSequence);
                }
                var result = { output_exr: exr.fsName, output_module_readback: settings };
                try { rqItem.remove(); } catch (_) {}
                appendText(logPath, "exr exists branch=" + branchName + " path=" + result.output_exr + "\\n");
                return result;
            }
            summary.outputs.effect_on = renderExrBranch("effect_on");
            effect.remove();
            summary.no_effect_count_after_removal = Number(liveParade.numProperties || 0);
            summary.no_effect_verified = summary.no_effect_count_after_removal === 0;
            if (!summary.no_effect_verified) {
                throw new Error("effect-free control still has an Effect Parade entry after removal");
            }
            summary.outputs.no_effect = renderExrBranch("no_effect");
            summary.output_exr = summary.outputs.effect_on.output_exr;
            summary.output_module_readback = summary.outputs.effect_on.output_module_readback;
        } else {'''
    if exr_block not in source:
        raise SystemExit("shared JSX EXR block for same-run replacement was not found")
    source = source.replace(exr_block, same_run_exr_block, 1)
    json_anchor = '            "  \\\"effect_disabled\\\": " + (summary.effect_disabled ? "true" : "false") + ",\\n" +\n'
    json_lines = (
        '            "  \\\"effect_count_after_setup\\\": " + summary.effect_count_after_setup + ",\\n" +\n'
        '            "  \\\"no_effect_count_after_removal\\\": " + summary.no_effect_count_after_removal + ",\\n" +\n'
        '            "  \\\"no_effect_verified\\\": " + (summary.no_effect_verified ? "true" : "false") + ",\\n" +\n'
        '            "  \\\"effect_identity_readback\\\": {\\\"name\\\": \\\"" + esc(summary.effect_identity_readback.name) + "\\\", \\\"match_name\\\": \\\"" + esc(summary.effect_identity_readback.match_name) + "\\\"},\\n" +\n'
        '            "  \\\"effect_param_readback\\\": {\\\"match_name\\\": \\\"" + esc(summary.effect_param_readback.match_name) + "\\\", \\\"name\\\": \\\"" + esc(summary.effect_param_readback.name) + "\\\", \\\"value\\\": " + (summary.effect_param_readback.value === null ? "null" : summary.effect_param_readback.value) + ", \\\"blur_amount\\\": " + (summary.effect_param_readback.blur_amount === null ? "null" : summary.effect_param_readback.blur_amount) + ", \\\"blur_smoothness\\\": " + (summary.effect_param_readback.blur_smoothness === null ? "null" : summary.effect_param_readback.blur_smoothness) + ", \\\"number_of_repeat\\\": " + (summary.effect_param_readback.number_of_repeat === null ? "null" : summary.effect_param_readback.number_of_repeat) + ", \\\"bias_direction\\\": " + (summary.effect_param_readback.bias_direction === null ? "null" : summary.effect_param_readback.bias_direction) + ", \\\"legacy\\\": " + (summary.effect_param_readback.legacy === null ? "null" : summary.effect_param_readback.legacy) + "},\\n" +\n'
        '            "  \\\"output_module_readback\\\": {\\\"format\\\": \\\"" + esc(summary.output_module_readback.format) + "\\\", \\\"channels\\\": \\\"" + esc(summary.output_module_readback.channels) + "\\\", \\\"depth\\\": \\\"" + esc(summary.output_module_readback.depth) + "\\\", \\\"color\\\": \\\"" + esc(summary.output_module_readback.color) + "\\\"},\\n" +\n'
        '            "  \\\"outputs\\\": {\\\"effect_on\\\": {\\\"output_exr\\\": \\\"" + esc(summary.outputs.effect_on.output_exr) + "\\\", \\\"output_module_readback\\\": {\\\"format\\\": \\\"" + esc(summary.outputs.effect_on.output_module_readback.format) + "\\\", \\\"channels\\\": \\\"" + esc(summary.outputs.effect_on.output_module_readback.channels) + "\\\", \\\"depth\\\": \\\"" + esc(summary.outputs.effect_on.output_module_readback.depth) + "\\\", \\\"color\\\": \\\"" + esc(summary.outputs.effect_on.output_module_readback.color) + "\\\"}}, \\\"no_effect\\\": {\\\"output_exr\\\": \\\"" + esc(summary.outputs.no_effect.output_exr) + "\\\", \\\"output_module_readback\\\": {\\\"format\\\": \\\"" + esc(summary.outputs.no_effect.output_module_readback.format) + "\\\", \\\"channels\\\": \\\"" + esc(summary.outputs.no_effect.output_module_readback.channels) + "\\\", \\\"depth\\\": \\\"" + esc(summary.outputs.no_effect.output_module_readback.depth) + "\\\", \\\"color\\\": \\\"" + esc(summary.outputs.no_effect.output_module_readback.color) + "\\\"}}},\\n" +\n'
        '            "  \\\"project_gpu_accel_type_raw\\\": " + summary.project_gpu_accel_type_raw + ",\\n" +\n'
    )
    if json_anchor not in source:
        raise SystemExit("shared JSX JSON output anchor for live readback was not found")
    source = source.replace(json_anchor, json_anchor + json_lines, 1)
    warnings_anchor = '            "  \\\"warnings\\\": [\\\"" + esc(summary.warnings.join("\\\" , \\\"")) + "\\\"]\\n" +\n'
    warnings_line = '            "  \\\"warnings\\\": " + (summary.warnings.length ? "[\\\"" + esc(summary.warnings.join("\\\" , \\\"")) + "\\\"]" : "[]") + "\\n" +\n'
    if warnings_anchor not in source:
        raise SystemExit("shared JSX JSON output anchor for empty warnings was not found")
    source = source.replace(warnings_anchor, warnings_line, 1)
    return source


README = f"""# OLMBlur case_0001 Windows 32bpc FLOAT EXR recapture

This is a single-case, Windows-only Adobe After Effects 26.3 package for request ID `{REQUEST_ID}`. It embeds only the case_0001 input and exact request parameters from the focused 32bpc request. The runner requires OLMBlur.aex SHA-256 `{REQUIRED_AEX_SHA256}` and checks that hash before starting AE.

The entrypoint uses `GpuAccelType.SOFTWARE`, 32bpc, an empty working space, linear blending off, and the exact Output Module template `{EXR_TEMPLATE}`. One AE process, project, comp, and input render the effect-on branch first; the runner then removes the effect, proves the Effect Parade is empty, and renders the no-effect branch in that same process. The actual EXR source filenames are taken from the AE result JSON; the runner never assumes a sequence filename.

Run `run_olmblur_32bpc_case0001.ps1`. The returned `return/return_manifest.json` records the request ID, one launched AE PID, loaded plugin path/size/mtime/hash, contract-artifact hashes, AE/project state, actual effect parameter and Output Module readbacks, archive paths, sizes, and hashes. The copied input/manifests/JSX allow intake to verify the executed contract. `return/status.json` is written for both success and every failure; errors are `exact_bind_failure` and no partial render is claimed. EXR FLOAT/uncompressed header acceptance remains a mandatory Mac-side intake gate. All paths inside this ZIP are package-relative or Windows runtime paths; no personal Mac absolute path is embedded.
"""


def build(output: Path) -> Path:
    request = load_json(REQUEST)
    source = load_json(REFERENCE_SOURCE)
    request_manifest, reference = make_manifests(request, source)
    with tempfile.TemporaryDirectory(prefix="olmblur_case0001_package_") as raw:
        stage = Path(raw) / PACKAGE_STEM
        (stage / "input").mkdir(parents=True)
        (stage / "scripts").mkdir()
        (stage / "return").mkdir()
        shutil.copy2(INPUT_SOURCE, stage / "input/case_0001_before_effects.png")
        (stage / "scripts/ae_render_single_case.jsx").write_text(adapted_renderer(), encoding="utf-8")
        (stage / "request_manifest.json").write_text(json.dumps(request_manifest, indent=2) + "\n", encoding="utf-8")
        (stage / "reference_manifest.json").write_text(json.dumps(reference, indent=2) + "\n", encoding="utf-8")
        manifest = {"schema": 1, "kind": "olmblur_windows_case0001_float_exr_recapture", "request_id": REQUEST_ID, "platform": "windows", "entrypoint": "run_olmblur_32bpc_case0001.ps1", "same_ae_process_pair_required": True, "plugin": {"name": "OLMBlur.aex", "required_sha256": REQUIRED_AEX_SHA256, "record": ["path", "size_bytes", "last_write_time_utc", "sha256"]}, "project": {"bits_per_channel": 32, "gpu_accel_type": {"current_name": "SOFTWARE", "raw": "GpuAccelType.SOFTWARE"}, "working_space": "", "linear_blending": False}, "output_template": EXR_TEMPLATE, "cases": [CASE_ID], "effect_outputs": ["return/effect_on.exr", "return/effect_no_effect.exr"], "fail_closed_status": "return/status.json", "windows_return": "<OutputDir>/request-run.zip"}
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (stage / "run_olmblur_32bpc_case0001.ps1").write_text(powershell(), encoding="utf-8")
        (stage / "README.md").write_text(README, encoding="utf-8")
        contract_paths = {
            "input": stage / "input/case_0001_before_effects.png",
            "request_manifest": stage / "request_manifest.json",
            "reference_manifest": stage / "reference_manifest.json",
            "renderer": stage / "scripts/ae_render_single_case.jsx",
            "package_manifest": stage / "manifest.json",
            "runner": stage / "run_olmblur_32bpc_case0001.ps1",
        }
        package_contract = {
            "schema": "olmblur_case0001_package_contract/v1",
            "request_id": REQUEST_ID,
            "artifacts": {
                name: {"path": path.relative_to(stage).as_posix(), "sha256": sha256(path), "size_bytes": path.stat().st_size}
                for name, path in contract_paths.items()
            },
        }
        (stage / "package_contract.json").write_text(json.dumps(package_contract, indent=2) + "\n", encoding="utf-8")
        output.parent.mkdir(parents=True, exist_ok=True)
        fixed = (2026, 7, 15, 0, 0, 0)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    info = zipfile.ZipInfo(f"{PACKAGE_STEM}/{path.relative_to(stage).as_posix()}", fixed)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, path.read_bytes())
    print(f"[OK] {output}")
    print(f"[SUMMARY] request_id={REQUEST_ID} case={CASE_ID} bpc=32 renderer=SOFTWARE template={EXR_TEMPLATE} hash={REQUIRED_AEX_SHA256}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    build(args.output if args.output.is_absolute() else ROOT / args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
