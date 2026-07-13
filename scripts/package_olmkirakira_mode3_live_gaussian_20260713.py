#!/usr/bin/env python3
"""Build the Windows-only OLMKiraKira Mode 3 live Gaussian capture package."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Any

PACKAGE_STEM = "olmkirakira_mode3_live_gaussian_20260713"
REQUEST_ID = PACKAGE_STEM
SCHEMA = "olmkirakira-mode3-live-gaussian-return-v1"
SUPPORT_DIR = Path("refs/runtime_trace_support") / PACKAGE_STEM
OUTPUT_ZIP = Path("refs/runtime_trace_packages") / f"olm_runtime_trace_{PACKAGE_STEM}.zip"
REFERENCE = Path("refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMKiraKira/reference_manifest.json")
SOURCE_INPUT = Path(
    "handoff/ae_pixel_validation_20260618/requests/"
    "ae_pixel_olm_final_random10_olm_kira_kira_20260629/input/"
    "olm_final_random10_olm_kira_kira_20260629__software__fr24__"
    "final_random10_olm_kira_kira_03_before_effects.png"
)
JSX = Path("scripts/ae_render_single_case.jsx")
CASE_ID = "final_random10_olm_kira_kira_03"
AEX_PATH = r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\OLMKiraKira.aex"
AEX_SHA256 = "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"
AEX_SIZE = 25781248
OVERRIDES = {
    "OLM OLM Kira Kira-0003": 5,
    "OLM OLM Kira Kira-0004": 0,
    "OLM OLM Kira Kira-0005": 0,
    "OLM OLM Kira Kira-0026": 0,
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def reference_and_case(repo: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    reference = json.loads((repo / REFERENCE).read_text(encoding="utf-8"))
    case = next(c for c in reference["cases"] if c["id"] == CASE_ID)
    mode = next(p["value"] for p in case["effects"][0]["params"] if p["name"] == "Blur Mode")
    if mode != 3:
        raise SystemExit(f"reference case is not Blur Mode=3: {mode!r}")
    return reference, case


def request_manifest(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": 1,
        "request_id": REQUEST_ID,
        "reference_manifest": "reference_manifest.json",
        "input_dir": "input",
        "effect_name": case["effects"][0]["name"],
        "effect_match_name": case["effects"][0]["match_name"],
        "cases": [{"id": CASE_ID, "before_effects_frame": "case_03_before_effects.png", "frame": "case_03.png"}],
    }


def package_manifest(case: dict[str, Any]) -> dict[str, Any]:
    params = {p["name"]: p["value"] for p in case["effects"][0]["params"] if p.get("name")}
    return {
        "kind": "olm_windows_live_gaussian_capture_request",
        "package": PACKAGE_STEM,
        "request_id": REQUEST_ID,
        "schema": SCHEMA,
        "plugin": "OLMKiraKira",
        "case_id": CASE_ID,
        "case_selection": {"source": REFERENCE.as_posix(), "manifest_blur_mode": params["Blur Mode"]},
        "parameter_overrides": {
            "match_name": OVERRIDES,
            "expected": {"Vertical Length": 5, "Horizontal Length": 0, "Diagonal Length": 0, "Diagonal 2 length": 0},
        },
        "aex_pin": {"path": AEX_PATH, "sha256": AEX_SHA256, "size": AEX_SIZE},
        "rva": {"wrapper": "0x1272ec0", "create": "0x1266730", "getKernel": "0x12754a0"},
        "capture": {
            "first_getKernel": {"ecx": 21, "xmm1": 2.5, "r8": 5},
            "words": 21,
            "element": "float32",
            "encoding": "raw little-endian words",
            "source": "cv::Mat.data after getKernel return",
        },
        "preflight": {
            "script": "ae_jsx_ready_preflight.jsx",
            "marker": "ae_jsx_preflight_ready.marker",
            "scope": "AfterFX -r launch and inherited absolute marker path only; no AEX, case, render, CDB, or algorithm claim",
        },
        "required_markers": ["AE_JSX_PREFLIGHT_READY", "AE_READY", "MODULE", "BREAKPOINTS_READY", "KK_WRAPPER", "KK_CREATE", "KK_KERNEL_ENTRY", "KK_KERNEL_RETURN"],
        "failure_status": "exact_bind_failure",
        "forbidden_statuses": ["answered_partial", "partial", "unknown"],
    }


def runtime_manifest() -> dict[str, Any]:
    return {
        "kind": "olm_runtime_trace_request_package",
        "schema": 1,
        "profile": PACKAGE_STEM,
        "effect": "OLMKiraKira",
        "runtime_actions": [{
            "request_id": REQUEST_ID,
            "action": "run one fresh AE 26.3 Software 32bpc case_03 render and capture the first 21-tap Gaussian kernel in the same process run",
            "stop_condition": "answer only when AE ready, hash-pinned live module, absolute base+RVA hooks, first kernel args, return data pointer, 21 raw words, and one run id are all present",
            "forbidden": ["module-name breakpoints", "pre-load attach", "surrogate coefficient arrays", "answered_partial"],
        }],
    }


def return_template() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "request_id": REQUEST_ID,
        "status": "answered | exact_bind_failure",
        "preflight": {"status": None, "marker": None, "ae_pid": None, "powershell": None, "work_root": None},
        "run": {"run_id": None, "case_id": CASE_ID, "renderer": "software", "bits_per_channel": 32, "module": "OLMKiraKira.aex", "module_base": None, "aex_sha256": AEX_SHA256, "aex_size": AEX_SIZE},
        "binding": {"wrapper_rva": "0x1272ec0", "create_rva": "0x1266730", "getKernel_rva": "0x12754a0", "wrapper": None, "create": None, "getKernel": None},
        "case": {"blur_mode_manifest": 3, "case_id": CASE_ID, "overrides_match_name": OVERRIDES, "expected_first_kernel": {"ecx": 21, "xmm1": 2.5, "r8": 5}},
        "observation": {"wrapper_args": None, "create_seen": False, "first_getKernel": {"ecx": None, "xmm1": None, "r8": None, "output_mat": None}, "return_data": None, "raw_words_u32": [None] * 21, "raw_bytes": 84},
        "failure": {"stage": None, "reason": None, "missing": [], "same_run": None},
    }


def readme() -> str:
    return (
        "# OLMKiraKira Mode 3 live Gaussian capture\n\n"
        "Windows desktop-required, one fresh AE run. The selected manifest case is "
        f"{CASE_ID} and its manifest Blur Mode is 3. The runner applies match-name "
        f"overrides {json.dumps(OVERRIDES, sort_keys=True)} so the first Gaussian "
        "setup is expected to be kernel size 21, sigma 2.5, type 5.\n\n"
        "The runner relays through Windows PowerShell 5.1, requires an interactive "
        "desktop session, canonicalizes every work/marker path to an absolute path, and first "
        "runs a minimal AE JSX launch/ready preflight with no case, AEX, CDB, render, or algorithm "
        "claim. The runner waits the full marker deadline even if the Start-Process launcher exits, "
        "tracks the real AfterFX instance by executable path plus interactive session, and requires "
        "that true process to exit after app.quit before proceeding. If preflight, pause-ready, "
        "module lookup, or hook install fails, it releases pause markers and force-stops only "
        "run-owned observed AfterFX PIDs that match the exact executable path and session, never "
        "baseline PIDs. Only after that marker is "
        "observed and the preflight AE exits does it run the pause marker, fixed no-space JSX launch path, live "
        "hash-pinned module lookup, absolute base-plus-RVA breakpoints, and "
        "fail-closed marker policy from the 2026-07-13 retry harness. It captures "
        "the first getKernel output cv::Mat.data pointer after return and writes "
        "exactly 21 little-endian float32 words.\n\n"
        "Any missing AE ready/module/hook/argument/word/same-run field returns "
        "exact_bind_failure.\n"
    )


def cdb_template() -> str:
    return r""".logopen /t __TRACE__
.symfix
.effmach amd64
.expr /s masm
sxi e06d7363
r @$t0=0
r @$t1=0
r @$t2=0
.echo KK_RUN_START request_id=olmkirakira_mode3_live_gaussian_20260713 run_id=__RUN_ID__ case_id=final_random10_olm_kira_kira_03
.echo KK_MODULE run_id=__RUN_ID__ module=OLMKiraKira.aex module_base=__BASE__ sha256=60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7 size=25781248
bp __WRAPPER__ ".printf \"KK_WRAPPER run_id=__RUN_ID__ module_base=__BASE__ wrapper=__WRAPPER__ rcx=%p rdx=%p r8=%p r9=%p\n\", @rcx,@rdx,@r8,@r9; gc"
bp __CREATE__ ".printf \"KK_CREATE run_id=__RUN_ID__ module_base=__BASE__ create=__CREATE__ rcx=%p rdx=%p r8=%p r9=%p\n\", @rcx,@rdx,@r8,@r9; gc"
bp __KERNEL__ ".if (@$t0==0) { r @$t0=1; r @$t1=@r9; .printf \"KK_KERNEL_ENTRY run_id=__RUN_ID__ module_base=__BASE__ getKernel=__KERNEL__ ecx=%u xmm1=%g r8=%u output_mat=%p return_address=%p\n\", @ecx,@xmm1,@r8d,@r9,poi(@rsp); bp poi(@rsp) \".if (@$t0==1) { .if (@$t2==0) { r @$t2=1; r @$t3=poi(@$t1+0x10); .printf \\\"KK_KERNEL_RETURN run_id=__RUN_ID__ module_base=__BASE__ getKernel=__KERNEL__ output_mat=%p data=%p word_count=21 source=cv_Mat_data_after_return\\n\\\", @$t1, @$t3; .writemem \\\"__WORDS__\\\" @$t3 @$t3+0x53; .echo KK_CAPTURE_END; q } .else { gc } } .else { gc }\"; } .else { gc }"
.echo KK_BREAKPOINTS_READY run_id=__RUN_ID__ module_base=__BASE__ wrapper=__WRAPPER__ create=__CREATE__ getKernel=__KERNEL__
g
q
"""


def preflight_jsx() -> str:
    return r'''(function () {
    var markerPath = "";
    try {
        markerPath = $.getenv("OLM_AE_PREFLIGHT_READY_MARKER") || "";
        if (!markerPath || !/^(?:[A-Za-z]:[\\\/]|\\\\)/.test(markerPath)) {
            throw new Error("OLM_AE_PREFLIGHT_READY_MARKER must be absolute");
        }
        var marker = new File(markerPath);
        marker.encoding = "UTF-8";
        if (!marker.open("w")) {
            throw new Error("could not open preflight marker");
        }
        marker.write("AE_JSX_PREFLIGHT_READY ae_version=" + app.version + " jsx=" + File($.fileName).fsName + "\n");
        marker.close();
    } catch (error) {
        try {
            if (markerPath) {
                var failure = new File(markerPath + ".error.txt");
                failure.encoding = "UTF-8";
                if (failure.open("w")) {
                    failure.write(error.toString() + "\n");
                    failure.close();
                }
            }
        } catch (_) {}
    }
    try { app.quit(); } catch (_) {}
}());
'''


def runner_ps1() -> str:
    return r'''[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$AexPath,
  [string]$CdbPath='C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe',
  [string]$AfterFxPath='C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe',
  [string]$WorkRoot="$env:TEMP\olmkirakira_mode3_live_gaussian_20260713",
  [string]$PowerShell51='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
  [switch]$SkipPowerShell51Relay
)
$ErrorActionPreference='Stop'
$requestId='olmkirakira_mode3_live_gaussian_20260713'; $caseId='final_random10_olm_kira_kira_03'; $expectedHash='60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7'; $expectedSize=25781248L
if(![IO.Path]::IsPathRooted($WorkRoot)){$WorkRoot=Join-Path ([Environment]::CurrentDirectory) $WorkRoot}; $WorkRoot=[IO.Path]::GetFullPath($WorkRoot)
$runId='kk-mode3-'+[guid]::NewGuid().ToString('N'); $work=Join-Path $WorkRoot $runId; New-Item -ItemType Directory -Force -Path $work | Out-Null; $work=(Get-Item -LiteralPath $work).FullName
function Finish([string]$status,[hashtable]$extra,[int]$code){$body=[ordered]@{schema='olmkirakira-mode3-live-gaussian-return-v1';request_id=$requestId;status=$status;run_id=$runId}; foreach($x in $extra.GetEnumerator()){$body[$x.Key]=$x.Value}; $json=$body|ConvertTo-Json -Depth 20; $json|Set-Content -LiteralPath (Join-Path $work 'RETURN_RUNTIME_TRACE.json') -Encoding UTF8; $json; exit $code}
function Get-AfterFxProcessState([string]$ExecutablePath,[int]$TargetSessionId){
  $items=@()
  try{
    $items=@(
      Get-CimInstance Win32_Process -Filter "Name='AfterFX.exe'" -ErrorAction Stop |
      Where-Object{
        $_.SessionId -eq $TargetSessionId -and
        $_.ExecutablePath -and
        [string]::Equals([IO.Path]::GetFullPath($_.ExecutablePath),$ExecutablePath,[System.StringComparison]::OrdinalIgnoreCase)
      } |
      Sort-Object CreationDate,ProcessId |
      ForEach-Object{
        $startedUtc=$null
        if($_.CreationDate){
          try{$startedUtc=[System.Management.ManagementDateTimeConverter]::ToDateTime($_.CreationDate).ToUniversalTime().ToString('o')}catch{$startedUtc=$_.CreationDate}
        }
        [pscustomobject]@{
          Id=[int]$_.ProcessId
          ParentProcessId=[int]$_.ParentProcessId
          SessionId=[int]$_.SessionId
          Path=$_.ExecutablePath
          CommandLine=$_.CommandLine
          StartedUtc=$startedUtc
        }
      }
    )
  }catch{$items=@()}
  @($items)
}
function Get-LauncherState([System.Diagnostics.Process]$Process){
  if($null -eq $Process){return $null}
  try{$Process.Refresh()}catch{}
  $exitCode=$null; $processName=$null
  try{$processName=$Process.ProcessName}catch{}
  if($Process.HasExited){try{$exitCode=$Process.ExitCode}catch{}}
  [ordered]@{pid=$Process.Id;process_name=$processName;has_exited=$Process.HasExited;exit_code=$exitCode}
}
function New-ProcessDiagnostics([string]$ExecutablePath,[int]$TargetSessionId,[int[]]$BaselinePids,[System.Diagnostics.Process]$Launcher,[System.Collections.IEnumerable]$ObservedPids){
  $baseline=@($BaselinePids|Sort-Object -Unique)
  $observed=@($ObservedPids|Sort-Object -Unique)
  [ordered]@{
    executable_path=$ExecutablePath
    session_id=$TargetSessionId
    launcher=Get-LauncherState $Launcher
    baseline_pids=$baseline
    observed_pids=$observed
    candidates=@(
      Get-AfterFxProcessState -ExecutablePath $ExecutablePath -TargetSessionId $TargetSessionId |
      ForEach-Object{
        [ordered]@{
          pid=$_.Id
          parent_pid=$_.ParentProcessId
          session_id=$_.SessionId
          started_utc=$_.StartedUtc
          path=$_.Path
          command_line=$_.CommandLine
        }
      }
    )
  }
}
function Wait-ForAfterFxMarker([string]$MarkerPath,[datetime]$Deadline,[string]$ExecutablePath,[int]$TargetSessionId,[int[]]$BaselinePids,[System.Diagnostics.Process]$Launcher){
  $observed=New-Object System.Collections.Generic.List[int]
  while((Get-Date) -lt $Deadline){
    foreach($candidate in @(Get-AfterFxProcessState -ExecutablePath $ExecutablePath -TargetSessionId $TargetSessionId)){
      if(($BaselinePids -notcontains $candidate.Id) -and ($observed -notcontains $candidate.Id)){[void]$observed.Add($candidate.Id)}
    }
    if(Test-Path -LiteralPath $MarkerPath){break}
    Start-Sleep -Milliseconds 250
  }
  $markerFound=Test-Path -LiteralPath $MarkerPath
  $current=@(Get-AfterFxProcessState -ExecutablePath $ExecutablePath -TargetSessionId $TargetSessionId)
  foreach($candidate in $current){
    if(($BaselinePids -notcontains $candidate.Id) -and ($observed -notcontains $candidate.Id)){[void]$observed.Add($candidate.Id)}
  }
  $runCandidates=@($current|Where-Object{($BaselinePids -notcontains $_.Id) -or ($observed -contains $_.Id)})
  $actual=@($runCandidates|Sort-Object StartedUtc,Id -Descending|Select-Object -First 1)
  [pscustomobject]@{
    MarkerFound=$markerFound
    ObservedPids=@($observed|Sort-Object -Unique)
    CurrentCandidates=@($current)
    RunCandidates=@($runCandidates)
    Actual=$actual
    Diagnostics=(New-ProcessDiagnostics -ExecutablePath $ExecutablePath -TargetSessionId $TargetSessionId -BaselinePids $BaselinePids -Launcher $Launcher -ObservedPids $observed)
  }
}
function Wait-ForAfterFxExit([datetime]$Deadline,[string]$ExecutablePath,[int]$TargetSessionId,[int[]]$BaselinePids,[int[]]$ObservedPids,[System.Diagnostics.Process]$Launcher){
  while((Get-Date) -lt $Deadline){
    $current=@(Get-AfterFxProcessState -ExecutablePath $ExecutablePath -TargetSessionId $TargetSessionId)
    $active=@($current|Where-Object{($BaselinePids -notcontains $_.Id) -or ($ObservedPids -contains $_.Id)})
    if($active.Count -eq 0){
      return [pscustomobject]@{
        Exited=$true
        Active=@()
        Diagnostics=(New-ProcessDiagnostics -ExecutablePath $ExecutablePath -TargetSessionId $TargetSessionId -BaselinePids $BaselinePids -Launcher $Launcher -ObservedPids $ObservedPids)
      }
    }
    Start-Sleep -Milliseconds 250
  }
  [pscustomobject]@{
    Exited=$false
    Active=@(Get-AfterFxProcessState -ExecutablePath $ExecutablePath -TargetSessionId $TargetSessionId|Where-Object{($BaselinePids -notcontains $_.Id) -or ($ObservedPids -contains $_.Id)})
    Diagnostics=(New-ProcessDiagnostics -ExecutablePath $ExecutablePath -TargetSessionId $TargetSessionId -BaselinePids $BaselinePids -Launcher $Launcher -ObservedPids $ObservedPids)
  }
}
function Cleanup-RunOwnedAfterFx([System.Diagnostics.Process]$Launcher,[int[]]$ObservedPids,[switch]$ReleasePauseMarkers){
  $observed=@($ObservedPids|Sort-Object -Unique)
  $cleanup=[ordered]@{
    attempted=$true
    release_pause_markers=$ReleasePauseMarkers.IsPresent
    continue_marker_released=$false
    abort_marker_released=$false
    continue_marker_path=$null
    abort_marker_path=$null
    targeted_pids=@()
    stopped_pids=@()
    remaining_pids=@()
    process_diagnostics=$null
  }
  if($ReleasePauseMarkers){
    if($continue){
      Set-Content -LiteralPath $continue -Value 'abort' -Encoding ASCII
      $cleanup.continue_marker_released=$true
      $cleanup.continue_marker_path=$continue
    }
    if($abort){
      Set-Content -LiteralPath $abort -Value 'abort' -Encoding ASCII
      $cleanup.abort_marker_released=$true
      $cleanup.abort_marker_path=$abort
    }
    Start-Sleep -Milliseconds 500
  }
  $targets=@(Get-AfterFxProcessState -ExecutablePath $AfterFxPath -TargetSessionId $sessionId|Where-Object{($baselineAfterFx -notcontains $_.Id) -and ($observed -contains $_.Id)})
  $cleanup.targeted_pids=@($targets|ForEach-Object{$_.Id}|Sort-Object -Unique)
  if($cleanup.targeted_pids.Count){
    foreach($pid in $cleanup.targeted_pids){
      try{Stop-Process -Id $pid -Force -ErrorAction Stop; [void]$cleanup.stopped_pids += $pid}catch{}
    }
    $stopDeadline=(Get-Date).AddSeconds(15)
    while((Get-Date) -lt $stopDeadline){
      $remaining=@(Get-AfterFxProcessState -ExecutablePath $AfterFxPath -TargetSessionId $sessionId|Where-Object{($baselineAfterFx -notcontains $_.Id) -and ($observed -contains $_.Id)})
      if($remaining.Count -eq 0){break}
      Start-Sleep -Milliseconds 250
    }
  }
  $cleanup.remaining_pids=@(Get-AfterFxProcessState -ExecutablePath $AfterFxPath -TargetSessionId $sessionId|Where-Object{($baselineAfterFx -notcontains $_.Id) -and ($observed -contains $_.Id)}|ForEach-Object{$_.Id}|Sort-Object -Unique)
  $cleanup.process_diagnostics=New-ProcessDiagnostics -ExecutablePath $AfterFxPath -TargetSessionId $sessionId -BaselinePids $baselineAfterFx -Launcher $Launcher -ObservedPids $observed
  $cleanup
}
function Fail([string]$stage,[string]$reason,[int]$code,[hashtable]$detail,[System.Diagnostics.Process]$Launcher,[int[]]$ObservedPids,[switch]$ReleasePauseMarkers){
  $failure=[ordered]@{stage=$stage;reason=$reason}
  if($detail){
    foreach($entry in $detail.GetEnumerator()){$failure[$entry.Key]=$entry.Value}
  }
  $failure.cleanup=Cleanup-RunOwnedAfterFx -Launcher $Launcher -ObservedPids $ObservedPids -ReleasePauseMarkers:$ReleasePauseMarkers
  Finish 'exact_bind_failure' @{failure=$failure} $code
}
if(-not $SkipPowerShell51Relay -and ($PSVersionTable.PSEdition -ne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5)){
  if(!(Test-Path -LiteralPath $PowerShell51 -PathType Leaf)){Finish 'exact_bind_failure' @{failure=@{stage='interactive_desktop';reason='Windows PowerShell 5.1 relay missing';path=$PowerShell51}} 3}
  & $PowerShell51 -NoProfile -ExecutionPolicy Bypass -File $PSCommandPath -AexPath $AexPath -CdbPath $CdbPath -AfterFxPath $AfterFxPath -WorkRoot $WorkRoot -PowerShell51 $PowerShell51 -SkipPowerShell51Relay
  exit $LASTEXITCODE
}
$sessionId=(Get-Process -Id $PID -ErrorAction Stop).SessionId
if($sessionId -eq 0){Finish 'exact_bind_failure' @{failure=@{stage='interactive_desktop';reason='runner must be launched from the logged-in interactive desktop, not SSH session 0';session_id=$sessionId}} 4}
if(!(Test-Path -LiteralPath $AexPath -PathType Leaf)){Finish 'exact_bind_failure' @{failure=@{stage='preflight';reason='AEX absent'}} 2}
$aex=Get-Item -LiteralPath $AexPath; $hash=(Get-FileHash -Algorithm SHA256 -LiteralPath $aex.FullName).Hash.ToLowerInvariant(); if($aex.Length -ne $expectedSize -or $hash -ne $expectedHash){Finish 'exact_bind_failure' @{failure=@{stage='aex_identity';reason='size or SHA256 mismatch';sha256=$hash;size=$aex.Length}} 2}
foreach($x in @($CdbPath,$AfterFxPath)){if(!(Test-Path -LiteralPath $x -PathType Leaf)){Finish 'exact_bind_failure' @{failure=@{stage='preflight';reason='required executable absent';path=$x}} 2}}
$CdbPath=(Get-Item -LiteralPath $CdbPath).FullName; $AfterFxPath=(Get-Item -LiteralPath $AfterFxPath).FullName
if(Get-Process -Name AfterFX -ErrorAction SilentlyContinue){Finish 'exact_bind_failure' @{failure=@{stage='preflight';reason='After Effects must be fully closed before this run'}} 2}
$caseRoot=(Get-Item -LiteralPath (Join-Path $PSScriptRoot 'case')).FullName; $jsx=Join-Path $caseRoot 'ae_render_single_case.jsx'; $preflightJsx=Join-Path $PSScriptRoot 'ae_jsx_ready_preflight.jsx'; $templatePath=Join-Path $PSScriptRoot 'mode3_live_gaussian.cdb.in'; $trace=Join-Path $work 'cdb_trace.log'; $stdout=Join-Path $work 'cdb_stdout.txt'; $stderr=Join-Path $work 'cdb_stderr.txt'; $ready=Join-Path $work 'ae_ready.marker'; $continue=Join-Path $work 'ae_continue.marker'; $abort=Join-Path $work 'ae_abort.marker'; $words=Join-Path $work 'gaussian_kernel_21_f32_le.bin'; $preflightReady=Join-Path $work 'ae_jsx_preflight_ready.marker'
foreach($x in @($jsx,$preflightJsx,$templatePath,(Join-Path $caseRoot 'request_manifest.json'),(Join-Path $caseRoot 'reference_manifest.json'),(Join-Path $caseRoot 'input\case_03_before_effects.png'))){if(!(Test-Path -LiteralPath $x -PathType Leaf)){Finish 'exact_bind_failure' @{failure=@{stage='package';reason='required package asset missing';path=$x}} 3}}
$absolutePaths=@($WorkRoot,$work,$caseRoot,$preflightReady,$ready,$continue,$abort,$trace,$stdout,$stderr,$words); if($absolutePaths|Where-Object{![IO.Path]::IsPathRooted($_)}){Finish 'exact_bind_failure' @{failure=@{stage='path_preflight';reason='all cross-process paths must be absolute';paths=$absolutePaths}} 3}
$launchDir=Join-Path $env:PUBLIC ('OLMTrace\'+$runId); New-Item -ItemType Directory -Force -Path $launchDir | Out-Null; $launchDir=(Get-Item -LiteralPath $launchDir).FullName; $jsxLaunch=Join-Path $launchDir 'runner.jsx'; $preflightLaunch=Join-Path $launchDir 'preflight.jsx'; Copy-Item -LiteralPath $jsx -Destination $jsxLaunch -Force; Copy-Item -LiteralPath $preflightJsx -Destination $preflightLaunch -Force; if(($jsxLaunch,$preflightLaunch)|Where-Object{$_ -match '\s'}){Finish 'exact_bind_failure' @{failure=@{stage='path_preflight';reason='no-space JSX launch path invariant failed';paths=@($jsxLaunch,$preflightLaunch)}} 3}
$baselineAfterFx=@(Get-AfterFxProcessState -ExecutablePath $AfterFxPath -TargetSessionId $sessionId|ForEach-Object{$_.Id})
$env:OLM_AE_PREFLIGHT_READY_MARKER=$preflightReady; $preflight=Start-Process -FilePath $AfterFxPath -ArgumentList @('-m','-r',$preflightLaunch) -PassThru; $deadline=(Get-Date).AddSeconds(120); $preflightInfo=Wait-ForAfterFxMarker -MarkerPath $preflightReady -Deadline $deadline -ExecutablePath $AfterFxPath -TargetSessionId $sessionId -BaselinePids $baselineAfterFx -Launcher $preflight; if(!$preflightInfo.MarkerFound){Fail 'ae_jsx_preflight' 'minimal AfterFX -r JSX did not emit ready marker' 4 @{marker=$preflightReady;marker_error=$(if(Test-Path -LiteralPath ($preflightReady+'.error.txt')){Get-Content -LiteralPath ($preflightReady+'.error.txt') -Raw}else{$null});launch=$preflightLaunch;argument_vector=@('-m','-r',$preflightLaunch);powershell=$PSVersionTable.PSVersion.ToString();work_root=$WorkRoot;process_diagnostics=$preflightInfo.Diagnostics} $preflight $preflightInfo.ObservedPids}; $preflightPid=$(if($preflightInfo.Actual){$preflightInfo.Actual.Id}else{$null}); $preflightExit=Wait-ForAfterFxExit -Deadline (Get-Date).AddSeconds(60) -ExecutablePath $AfterFxPath -TargetSessionId $sessionId -BaselinePids $baselineAfterFx -ObservedPids $preflightInfo.ObservedPids -Launcher $preflight; if(!$preflightExit.Exited){Fail 'ae_jsx_preflight' 'minimal JSX wrote ready but AfterFX path/session candidate did not exit after app.quit' 4 @{marker=$preflightReady;ae_pid=$preflightPid;process_diagnostics=$preflightExit.Diagnostics} $preflight $preflightInfo.ObservedPids}; Remove-Item Env:OLM_AE_PREFLIGHT_READY_MARKER -ErrorAction SilentlyContinue
$env:OLM_AE_REQUEST_DIR=($caseRoot -replace '\\','/'); $env:OLM_AE_CASE_ID=$caseId; $env:OLM_AE_OUTPUT_DIR=Join-Path $work 'render'; $env:OLM_AE_LOG_PATH=Join-Path $work 'ae_render.log'; $env:OLM_AE_RESULT_JSON=Join-Path $work 'ae_render_result.json'; $env:OLM_AE_PARAM_OVERRIDES_JSON='{"OLM OLM Kira Kira-0003":5,"OLM OLM Kira Kira-0004":0,"OLM OLM Kira Kira-0005":0,"OLM OLM Kira Kira-0026":0}'; $env:OLM_AE_FORCE_SOFTWARE='1'; $env:OLM_AE_FORCE_NEW_PROJECT='1'; $env:OLM_AE_KEEP_OPEN='0'; $env:OLM_AE_PAUSE_BEFORE_RENDER='1'; $env:OLM_AE_READY_MARKER=$ready; $env:OLM_AE_CONTINUE_MARKER=$continue; New-Item -ItemType Directory -Force -Path $env:OLM_AE_OUTPUT_DIR | Out-Null
$ae=Start-Process -FilePath $AfterFxPath -ArgumentList @('-m','-r',$jsxLaunch) -PassThru; $deadline=(Get-Date).AddSeconds(180); $aeInfo=Wait-ForAfterFxMarker -MarkerPath $ready -Deadline $deadline -ExecutablePath $AfterFxPath -TargetSessionId $sessionId -BaselinePids $baselineAfterFx -Launcher $ae; if(!$aeInfo.MarkerFound){Fail 'ae_ready' 'full case JSX did not emit ready after minimal JSX preflight passed' 4 @{preflight_marker=(Get-Content -LiteralPath $preflightReady -Raw);ae_log=$(if(Test-Path -LiteralPath $env:OLM_AE_LOG_PATH){Get-Content -LiteralPath $env:OLM_AE_LOG_PATH -Raw}else{$null});ae_result=$(if(Test-Path -LiteralPath $env:OLM_AE_RESULT_JSON){Get-Content -LiteralPath $env:OLM_AE_RESULT_JSON -Raw}else{$null});ready=$ready;request_dir=$env:OLM_AE_REQUEST_DIR;argument_vector=@('-m','-r',$jsxLaunch);process_diagnostics=$aeInfo.Diagnostics} $ae $aeInfo.ObservedPids -ReleasePauseMarkers}; if(!$aeInfo.Actual){Fail 'ae_ready' 'AfterFX ready marker was emitted but no live AfterFX process matched executable path and session' 4 @{ready=$ready;process_diagnostics=$aeInfo.Diagnostics} $ae $aeInfo.ObservedPids -ReleasePauseMarkers}; $aePid=$aeInfo.Actual.Id
$module=$null; $deadline=(Get-Date).AddSeconds(30); while((Get-Date)-lt $deadline -and $null -eq $module){try{$module=(Get-Process -Id $aePid -ErrorAction Stop).Modules|Where-Object{$_.FileName -ieq $aex.FullName}|Select-Object -First 1}catch{}; if($null -eq $module){Start-Sleep -Milliseconds 250}}; if($null -eq $module){Fail 'module_lookup' 'hash-pinned AEX not loaded at ready marker' 4 @{pid=$aePid;process_diagnostics=(New-ProcessDiagnostics -ExecutablePath $AfterFxPath -TargetSessionId $sessionId -BaselinePids $baselineAfterFx -Launcher $ae -ObservedPids $aeInfo.ObservedPids)} $ae $aeInfo.ObservedPids -ReleasePauseMarkers}
$base=('0x{0:x}' -f $module.BaseAddress.ToInt64()); $wrapper=('0x{0:x}' -f ($module.BaseAddress.ToInt64()+0x1272ec0)); $create=('0x{0:x}' -f ($module.BaseAddress.ToInt64()+0x1266730)); $kernel=('0x{0:x}' -f ($module.BaseAddress.ToInt64()+0x12754a0)); $cdb=Join-Path $work 'mode3_live_gaussian.cdb'; $text=(Get-Content -LiteralPath $templatePath -Raw).Replace('__TRACE__',$trace).Replace('__RUN_ID__',$runId).Replace('__BASE__',$base).Replace('__WRAPPER__',$wrapper).Replace('__CREATE__',$create).Replace('__KERNEL__',$kernel).Replace('__WORDS__',$words); if(($cdb,$words)|Where-Object{$_ -match '\s'}){Fail 'preflight' 'CDB artifact path contains whitespace' 3 @{} $ae $aeInfo.ObservedPids -ReleasePauseMarkers}; $text|Set-Content -LiteralPath $cdb -Encoding ASCII
$proc=Start-Process -FilePath $CdbPath -ArgumentList ('-cf "'+$cdb+'" -p '+$aePid) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -NoNewWindow -PassThru; $deadline=(Get-Date).AddSeconds(60); while((Get-Date)-lt $deadline){if((Test-Path $trace)-and((Get-Content $trace -Raw)-match 'KK_BREAKPOINTS_READY')){break}; Start-Sleep -Milliseconds 250}; if(!(Test-Path $trace)-or -not((Get-Content $trace -Raw)-match 'KK_BREAKPOINTS_READY')){Fail 'hook_install' 'absolute base+RVA breakpoints not armed' 4 @{base=$base;pid=$aePid;process_diagnostics=(New-ProcessDiagnostics -ExecutablePath $AfterFxPath -TargetSessionId $sessionId -BaselinePids $baselineAfterFx -Launcher $ae -ObservedPids $aeInfo.ObservedPids)} $ae $aeInfo.ObservedPids -ReleasePauseMarkers}; Set-Content -LiteralPath $continue -Value continue -Encoding ASCII; $proc|Wait-Process; $lines=if(Test-Path $trace){@(Get-Content -LiteralPath $trace)}else{@()}; $joined=$lines -join [Environment]::NewLine
function Marker([string]$n){$lines|Where-Object{$_ -match "^$n\s"}|Select-Object -Last 1}; function Field([string]$l,[string]$k){$m=[regex]::Match($l,"(?:^|\s)$k=([^\s]+)");if($m.Success){$m.Groups[1].Value}}
$start=Marker 'KK_RUN_START'; $mod=Marker 'KK_MODULE'; $wrap=Marker 'KK_WRAPPER'; $cr=Marker 'KK_CREATE'; $ke=Marker 'KK_KERNEL_ENTRY'; $kr=Marker 'KK_KERNEL_RETURN'; $missing=New-Object System.Collections.Generic.List[string]; foreach($p in @(@('run_start',$start),@('module',$mod),@('wrapper',$wrap),@('create',$cr),@('kernel_entry',$ke),@('kernel_return',$kr))){if(!$p[1]){[void]$missing.Add($p[0])}}
if(!$ke -or (Field $ke 'ecx') -ne '21'){[void]$missing.Add('kernel_ecx_21')}; if(!$ke -or (Field $ke 'r8') -ne '5'){[void]$missing.Add('kernel_r8_5')}; if(!$ke -or [double](Field $ke 'xmm1') -ne 2.5){[void]$missing.Add('kernel_xmm1_2.5')}; if(!$kr -or (Field $kr 'word_count') -ne '21'){[void]$missing.Add('word_count_21')}; if(!(Test-Path -LiteralPath $words)){[void]$missing.Add('raw_words_file')}; elseif((Get-Item -LiteralPath $words).Length -ne 84){[void]$missing.Add('raw_words_size_84')}; $ids=@($lines|ForEach-Object{if($_ -match '^KK_\S+.*run_id=([^\s]+)'){$Matches[1]}}|Sort-Object -Unique); if($ids.Count -ne 1){[void]$missing.Add('same_run_identity')}; if(!$start -or (Field $start 'case_id') -ne $caseId){[void]$missing.Add('case_identity')}; if($missing.Count){Finish 'exact_bind_failure' @{failure=@{stage='binding';reason='required live markers or exact first-kernel fields missing';missing=@($missing);same_run_ids=$ids;trace=$joined}} 4}
$raw=[IO.File]::ReadAllBytes($words); $u32=for($i=0;$i -lt 21;$i++){[BitConverter]::ToUInt32($raw,$i*4).ToString('x8')}; Finish 'answered' @{preflight=@{status='ready';marker=(Get-Content -LiteralPath $preflightReady -Raw);ae_pid=$preflightPid;powershell=$PSVersionTable.PSVersion.ToString();work_root=$WorkRoot};run=@{run_id=$ids[0];case_id=$caseId;module='OLMKiraKira.aex';module_base=$base;aex_sha256=$hash;aex_size=$aex.Length};binding=@{wrapper_rva='0x1272ec0';create_rva='0x1266730';getKernel_rva='0x12754a0';wrapper=$wrapper;create=$create;getKernel=$kernel};case=@{blur_mode_manifest=3;overrides_match_name=@{'OLM OLM Kira Kira-0003'=5;'OLM OLM Kira Kira-0004'=0;'OLM OLM Kira Kira-0005'=0;'OLM OLM Kira Kira-0026'=0}};observation=@{module_marker=$mod;wrapper_marker=$wrap;create_marker=$cr;first_getKernel=@{ecx=[int](Field $ke 'ecx');xmm1=[double](Field $ke 'xmm1');r8=[int](Field $ke 'r8');output_mat=(Field $ke 'output_mat')};return_data=(Field $kr 'data');raw_words_u32=$u32;raw_bytes=84};trace=$joined} 0
'''


def materialize(repo: Path, support: Path, output: Path) -> None:
    reference, case = reference_and_case(repo)
    files: dict[Path, bytes] = {
        support / "README.md": readme().encode(),
        support / "manifest.json": (json.dumps(package_manifest(case), indent=2) + "\n").encode(),
        support / "runtime_trace_package_manifest.json": (json.dumps(runtime_manifest(), indent=2) + "\n").encode(),
        support / "RETURN_RUNTIME_TRACE_TEMPLATE.json": (json.dumps(return_template(), indent=2) + "\n").encode(),
        support / "mode3_live_gaussian.cdb.in": cdb_template().encode(),
        support / "ae_jsx_ready_preflight.jsx": preflight_jsx().encode(),
        support / "run_olmkirakira_mode3_live_gaussian_20260713.ps1": runner_ps1().encode(),
        support / "case" / "request_manifest.json": (json.dumps(request_manifest(case), indent=2) + "\n").encode(),
        support / "case" / "reference_manifest.json": (json.dumps(reference, indent=2) + "\n").encode(),
        support / "case" / "ae_render_single_case.jsx": (repo / JSX).read_bytes(),
        support / "case" / "input" / "case_03_before_effects.png": (repo / SOURCE_INPUT).read_bytes(),
    }
    for path, data in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            name = f"{PACKAGE_STEM}/{path.relative_to(support).as_posix()}"
            if name.startswith("/") or re.match(r"^[A-Za-z]:", name):
                raise SystemExit(f"absolute archive member: {name}")
            archive.write(path, name)
    with zipfile.ZipFile(output) as archive:
        if any(" " in n for n in archive.namelist() if n.endswith(".ps1") or n.endswith(".cdb.in")):
            raise SystemExit("space-bearing control artifact name")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--support-dir", type=Path, default=SUPPORT_DIR)
    parser.add_argument("--output", type=Path, default=OUTPUT_ZIP)
    args = parser.parse_args()
    repo = repo_root()
    materialize(repo, repo / args.support_dir, repo / args.output)
    print(f"[OK] {repo / args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
