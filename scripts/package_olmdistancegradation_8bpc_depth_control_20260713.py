#!/usr/bin/env python3
"""Build the DG current-AEX depth-control request package."""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TYPED = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712"
CURRENT_RENDERER = ROOT / "scripts/ae_render_single_case.jsx"
PACKAGE = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_depth_control_20260713"
SUPPORT = ROOT / "refs/runtime_trace_support/olmdistancegradation_8bpc_depth_control_20260713"
OUTPUT = PACKAGE.with_suffix(".zip")
REQUEST_ID = "olmdistancegradation_8bpc_current_aex_depth_control_20260713"
RVA = ("1170870", "1170c90")
EXPECTED_CURRENT_AEX_SHA256 = json.loads(
    (TYPED / "runtime_trace_package_manifest.json").read_text(encoding="utf-8")
)["accepted_depth_control"]["aex_sha256"].lower()


README = f"""# OLMDistanceGradation 8bpc Current-AEX Depth Control

Status: runnable depth-control probe. This package does not collect typed
values, coordinates, stage ownership, or algorithm proof. It verifies that AE
actually rendered the requested 8bpc case before interpreting callback hits.

The runner launches AE normally and uses the shared single-case renderer's
pause-before-render handshake. At the ready marker it locates the hash-pinned
`DistanceGradation.aex` module in that AE process, attaches CDB, and arms the
PF8 callback `+0x1170870` and PF32 callback `+0x1170c90` before allowing the
render to continue. It returns one run ID, PID, module base, SHA-256, the
AE-reported project depth, and both hit counts. The required control is PF8 > 0
and PF32 == 0. Do not infer algorithm behavior from it.

If AE does not reach the render-ready marker, the fail-closed return includes
the launcher exit code and stdout/stderr, AE log/result text, target desktop
session, and matching-process diagnostics. Do not resend an unmodified package
after such a failure; use those fields to repair the launch boundary first.

Run `artifacts/run_olmdistancegradation_8bpc_depth_control_20260713.ps1`.
Use `-ParseOnly -TracePath` for the included parser fixtures.
"""


RUNNER_TEMPLATE = r'''param(
  [string]$PackageRoot = (Split-Path -Parent $PSScriptRoot),
  [string]$WorkRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) 'work'),
  [switch]$ParseOnly,
  [string]$TracePath = '',
  [string]$AexPath = 'C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\Plug-ins\Effects\DistanceGradation.aex',
  [string]$AfterFxPath = 'C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe',
  [string]$CdbPath = 'C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe'
)

$ErrorActionPreference = 'Stop'
$requestId = 'olmdistancegradation_8bpc_current_aex_depth_control_20260713'
$rvas = @('1170870','1170c90')
$expectedHash = '__EXPECTED_HASH__'
$runId = 'dglive-' + ([guid]::NewGuid().ToString('N'))

function Failure([string]$reason, [object[]]$missing, [string]$last, [object]$diagnostics=$null) {
  $failure = [ordered]@{stage='depth_control';reason=$reason;missing_fields=@($missing);last_observation=$last}
  if ($null -ne $diagnostics) { $failure['diagnostics'] = $diagnostics }
  [ordered]@{ status='exact_bind_failure'; kind='depth_control'; request_id=$requestId; failure=$failure }
}

function Parse([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) { return Failure 'missing CDB trace' @('trace') '' }
  $rows = @{}
  $last = ''
  foreach ($line in Get-Content -LiteralPath $path) {
    $last = $line
    if ($line -notmatch '^DG8_DEPTH_SUMMARY\s+') { continue }
    $m = @{}
    foreach ($pair in [regex]::Matches($line, '(?<key>[a-z0-9_]+)=(?<value>[^\s]+)')) { $m[$pair.Groups['key'].Value] = $pair.Groups['value'].Value }
    if ($m.ContainsKey('rva')) { $rows[$m['rva']] = $m }
  }
  $missing = @()
  foreach ($rva in $rvas) {
    if (-not $rows.ContainsKey($rva)) { $missing += "missing:rva_$rva"; continue }
    foreach ($field in @('run_id','ae_pid','module_base','aex_sha256','hit_count')) {
      if (-not $rows[$rva].ContainsKey($field) -or [string]::IsNullOrWhiteSpace([string]$rows[$rva][$field])) { $missing += "rva_$rva:$field" }
    }
    if ($rows[$rva]['hit_count'] -notmatch '^\d+$') { $missing += "rva_$rva:hit_count_integer" }
  }
  $runIds = @($rows.Values | ForEach-Object { $_['run_id'] } | Select-Object -Unique)
  $pids = @($rows.Values | ForEach-Object { $_['ae_pid'] } | Select-Object -Unique)
  $bases = @($rows.Values | ForEach-Object { $_['module_base'] } | Select-Object -Unique)
  $hashes = @($rows.Values | ForEach-Object { ([string]$_['aex_sha256']).ToLowerInvariant() } | Select-Object -Unique)
  if ($runIds.Count -ne 1) { $missing += 'shared_run_id' }
  if ($pids.Count -ne 1 -or $pids[0] -notmatch '^\d+$') { $missing += 'shared_ae_pid' }
  if ($bases.Count -ne 1 -or $bases[0] -notmatch '^0x[0-9a-fA-F]+$') { $missing += 'shared_module_base' }
  if ($hashes.Count -ne 1 -or $hashes[0] -notmatch '^[0-9a-fA-F]{64}$') { $missing += 'shared_aex_sha256' }
  if ($hashes.Count -ne 1 -or $hashes[0] -ne $expectedHash) { $missing += 'shared_expected_aex_sha256' }
  if ($rows.ContainsKey('1170870') -and $rows['1170870']['hit_count'] -match '^\d+$' -and [int]$rows['1170870']['hit_count'] -le 0) { $missing += 'PF8_hit_count_gt_0' }
  if ($rows.ContainsKey('1170c90') -and $rows['1170c90']['hit_count'] -match '^\d+$' -and [int]$rows['1170c90']['hit_count'] -ne 0) { $missing += 'PF32_hit_count_eq_0' }
  if ($missing.Count) { return Failure 'PF8/PF32 summaries are not hash/run complete' $missing $last }
  [ordered]@{status='answered';kind='depth_control';request_id=$requestId;run_id=$runIds[0];ae_pid=[int]$pids[0];module_base=$bases[0];aex_sha256=$hashes[0].ToLowerInvariant();rvas=@($rvas | ForEach-Object { [ordered]@{rva=$_;hit_count=[int]$rows[$_]['hit_count']} })}
}

if ($ParseOnly) { if (-not $TracePath) { throw '-ParseOnly requires -TracePath' }; (Parse $TracePath) | ConvertTo-Json -Depth 8; exit 0 }

$work = Join-Path $WorkRoot "olmdg_depth_control_$runId"; New-Item -ItemType Directory -Force -Path $work | Out-Null; $work = (Get-Item -LiteralPath $work).FullName
$returnPath = Join-Path $work 'RETURN_RUNTIME_TRACE.json'
$trace = Join-Path $work 'cdb_trace.txt'; $stdout = Join-Path $work 'cdb_stdout.txt'; $stderr = Join-Path $work 'cdb_stderr.txt'; $cdbScript = Join-Path $work 'depth_control.cdb'
$launchStdout = Join-Path $work 'afterfx_launcher_stdout.txt'; $launchStderr = Join-Path $work 'afterfx_launcher_stderr.txt'
$readyMarker = Join-Path $work 'ae_ready.marker'; $continueMarker = Join-Path $work 'ae_continue.marker'
$aeLogPath = Join-Path $work 'AE_SINGLE_CASE.log'; $aeResultPath = Join-Path $work 'AE_SINGLE_CASE_RESULT.json'
$cdb = $null; $ae = $null; $launch = $null; $launchStarted = $false
$sessionId = (Get-Process -Id $PID -ErrorAction Stop).SessionId
function ReadOrNull([string]$path) { if (Test-Path -LiteralPath $path -PathType Leaf) { return Get-Content -LiteralPath $path -Raw }; return $null }
function Get-AfterFxState {
  @(Get-CimInstance Win32_Process -Filter "Name='AfterFX.exe'" -ErrorAction SilentlyContinue | Where-Object {
    $_.SessionId -eq $sessionId -and $_.ExecutablePath -and [IO.Path]::GetFullPath($_.ExecutablePath) -ieq $AfterFxPath
  } | ForEach-Object { [ordered]@{pid=[int]$_.ProcessId;parent_pid=[int]$_.ParentProcessId;session_id=[int]$_.SessionId;path=$_.ExecutablePath;command_line=$_.CommandLine} })
}
function MatchingAfterFX {
  @(Get-AfterFxState | ForEach-Object { Get-Process -Id $_.pid -ErrorAction SilentlyContinue })
}
function Get-LauncherState {
  if ($null -eq $launch) { return $null }; try { $launch.Refresh() } catch {}
  $exitCode = $null; if ($launch.HasExited) { try { $exitCode = $launch.ExitCode } catch {} }
  [ordered]@{pid=$launch.Id;launcher_exited=$launch.HasExited;launcher_exit_code=$exitCode}
}
function Get-ProcessDiagnostics { [ordered]@{executable_path=$AfterFxPath;session_id=$sessionId;launcher=(Get-LauncherState);candidate_afterfx=@(Get-AfterFxState)} }
function Get-RuntimeDiagnostics {
  [ordered]@{launcher=(Get-LauncherState);launcher_stderr=(ReadOrNull $launchStderr);launcher_stdout=(ReadOrNull $launchStdout);cdb_exit_code=$(if($cdb -and $cdb.HasExited){$cdb.ExitCode}else{$null});cdb_stderr=(ReadOrNull $stderr);cdb_stdout=(ReadOrNull $stdout);ae_log=(ReadOrNull $aeLogPath);ae_result=(ReadOrNull $aeResultPath);process_diagnostics=(Get-ProcessDiagnostics)}
}
function Finish([object]$body, [int]$code) {
  if ($code -ne 0) {
    if ($continueMarker -and (Test-Path -LiteralPath $readyMarker) -and -not (Test-Path -LiteralPath $continueMarker)) {
      Set-Content -LiteralPath $continueMarker -Value 'abort' -Encoding ASCII -ErrorAction SilentlyContinue
    }
    if ($cdb -and -not $cdb.HasExited) { Stop-Process -Id $cdb.Id -Force -ErrorAction SilentlyContinue }
    if ($ae -and -not $ae.HasExited) { Stop-Process -Id $ae.Id -Force -ErrorAction SilentlyContinue }
    if ($launch -and (-not $ae -or $launch.Id -ne $ae.Id) -and -not $launch.HasExited) { Stop-Process -Id $launch.Id -Force -ErrorAction SilentlyContinue }
    if ($launchStarted) { foreach ($candidate in @(MatchingAfterFX)) { Stop-Process -Id $candidate.Id -Force -ErrorAction SilentlyContinue } }
  }
  if ($body.status -eq 'exact_bind_failure') { $body.failure['runtime_diagnostics'] = Get-RuntimeDiagnostics }
  $json = $body | ConvertTo-Json -Depth 10
  $json | Set-Content -LiteralPath $returnPath -Encoding UTF8
  $json
  exit $code
}
$queue = Join-Path $PackageRoot 'scripts\ae_render_olmdistancegradation_8bpc_depth_control_queue.jsx'
foreach ($requiredPath in @($AexPath,$AfterFxPath,$CdbPath,$queue)) {
  if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) { Finish (Failure "required file missing: $requiredPath" @('preflight_file') '') 2 }
}
if (Get-Process -Name AfterFX -ErrorAction SilentlyContinue) { Finish (Failure 'After Effects must be fully closed before this run' @('fresh_AfterFX_process') '') 2 }
$AexPath = (Get-Item -LiteralPath $AexPath).FullName; $AfterFxPath = (Get-Item -LiteralPath $AfterFxPath).FullName; $CdbPath = (Get-Item -LiteralPath $CdbPath).FullName
$aexSha256 = (Get-FileHash -LiteralPath $AexPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($aexSha256 -notmatch '^[0-9a-f]{64}$') { Finish (Failure 'DistanceGradation.aex SHA-256 unavailable' @('aex_sha256') $AexPath) 2 }
if ($aexSha256 -ne $expectedHash) { Finish (Failure 'DistanceGradation.aex is not the accepted current binary' @('expected_aex_sha256') "expected=$expectedHash actual=$aexSha256 path=$AexPath") 2 }
$env:OLM_DG_LIVE_REQUEST_DIR = Join-Path $PackageRoot 'request'
$env:OLM_DG_LIVE_WORK_ROOT = $work
$env:OLM_DG_LIVE_RUN_ID = $runId
$env:OLM_AE_PAUSE_BEFORE_RENDER = '1'
$env:OLM_AE_READY_MARKER = $readyMarker
$env:OLM_AE_CONTINUE_MARKER = $continueMarker
$env:OLM_AE_PAUSE_TIMEOUT_SECONDS = '300'
$launch = Start-Process -FilePath $AfterFxPath -ArgumentList @('-m','-r',$queue) -RedirectStandardOutput $launchStdout -RedirectStandardError $launchStderr -PassThru; $launchStarted = $true
$deadline = (Get-Date).AddSeconds(180)
while ((Get-Date) -lt $deadline -and -not (Test-Path -LiteralPath $readyMarker)) { Start-Sleep -Milliseconds 250 }
if (-not (Test-Path -LiteralPath $readyMarker -PathType Leaf)) {
  $last = [ordered]@{launch_pid=$launch.Id;launcher_exited=$launch.HasExited;launcher_exit_code=$(if($launch.HasExited){$launch.ExitCode}else{$null});candidate_afterfx=@(Get-AfterFxState);ae_log=(ReadOrNull $aeLogPath);ae_result=(ReadOrNull $aeResultPath);launcher_stderr=(ReadOrNull $launchStderr);process_diagnostics=(Get-ProcessDiagnostics)} | ConvertTo-Json -Depth 8 -Compress
  Finish (Failure 'AE pause ready marker missing' @('ae_ready.marker') $last (Get-ProcessDiagnostics)) 2
}
$readyText = Get-Content -LiteralPath $readyMarker -Raw
if ($readyText -notmatch 'effect_loaded=1' -or $readyText -notmatch 'parameters_applied=1') { Finish (Failure 'AE ready marker is not render-ready' @('effect_loaded=1','parameters_applied=1') $readyText) 2 }
$loaded = @()
$deadline = (Get-Date).AddSeconds(30)
while ((Get-Date) -lt $deadline -and $loaded.Count -ne 1) {
  $loaded = @(Get-AfterFxState | ForEach-Object {
    $process = Get-Process -Id $_.pid -ErrorAction SilentlyContinue
    try {
      $module = $process.Modules | Where-Object { $_.FileName -ieq $AexPath } | Select-Object -First 1
      if ($module) { [pscustomobject]@{ Process=$process; Module=$module } }
    } catch {}
  })
  if ($loaded.Count -ne 1) { Start-Sleep -Milliseconds 250 }
}
if ($loaded.Count -ne 1) { Finish (Failure 'exactly one AE process with hash-pinned DistanceGradation.aex was not found' @('actual_ae_process_module') "matches=$($loaded.Count)") 2 }
$ae = $loaded[0].Process; $module = $loaded[0].Module
$loadedSha256 = (Get-FileHash -LiteralPath $module.FileName -Algorithm SHA256).Hash.ToLowerInvariant()
if ($loadedSha256 -ne $expectedHash) { Finish (Failure 'loaded module hash does not match the accepted current binary' @('loaded_aex_sha256') "expected=$expectedHash actual=$loadedSha256") 2 }
$baseValue = $module.BaseAddress.ToInt64(); $base = ('0x{0:x}' -f $baseValue); $pf8 = ('0x{0:x}' -f ($baseValue + 0x1170870)); $pf32 = ('0x{0:x}' -f ($baseValue + 0x1170c90)); $aePid = $ae.Id
$cdbText = @"
.effmach amd64
.expr /s masm
sxi 80000003
.logopen "$trace"
r @`$t0 = 0
r @`$t1 = 0
bp $pf8 ".printf \"DG8_DEPTH_HIT run_id=$runId ae_pid=$aePid module_base=$base rva=1170870 aex_sha256=$aexSha256 hit_count=%u\n\", @`$t0; r @`$t0 = @`$t0 + 1; gc"
bp $pf32 ".printf \"DG8_DEPTH_HIT run_id=$runId ae_pid=$aePid module_base=$base rva=1170c90 aex_sha256=$aexSha256 hit_count=%u\n\", @`$t1; r @`$t1 = @`$t1 + 1; gc"
.echo DG8_DEPTH_BREAKPOINTS_ARMED
g
.printf "DG8_DEPTH_SUMMARY run_id=$runId ae_pid=$aePid module_base=$base rva=1170870 aex_sha256=$aexSha256 hit_count=%u\n", @`$t0
.printf "DG8_DEPTH_SUMMARY run_id=$runId ae_pid=$aePid module_base=$base rva=1170c90 aex_sha256=$aexSha256 hit_count=%u\n", @`$t1
.logclose
q
"@
$cdbText | Set-Content -LiteralPath $cdbScript -Encoding ASCII
$cdb = Start-Process -FilePath $CdbPath -ArgumentList ('-cf "' + $cdbScript + '" -p ' + $aePid) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -NoNewWindow -PassThru
$deadline = (Get-Date).AddSeconds(60)
while ((Get-Date) -lt $deadline) {
  if ((Test-Path -LiteralPath $trace) -and ((Get-Content -LiteralPath $trace -Raw) -match 'DG8_DEPTH_BREAKPOINTS_ARMED')) { break }
  if ($cdb.HasExited) { break }
  Start-Sleep -Milliseconds 250; $cdb.Refresh()
}
if (-not (Test-Path -LiteralPath $trace) -or -not ((Get-Content -LiteralPath $trace -Raw) -match 'DG8_DEPTH_BREAKPOINTS_ARMED')) { Finish (Failure 'CDB did not arm PF8/PF32 breakpoints' @('DG8_DEPTH_BREAKPOINTS_ARMED') "pid=$aePid base=$base") 2 }
Set-Content -LiteralPath $continueMarker -Value 'continue' -Encoding ASCII
$deadline = (Get-Date).AddSeconds(240)
while ((Get-Date) -lt $deadline -and -not $cdb.HasExited) { Start-Sleep -Milliseconds 250; $cdb.Refresh() }
if (-not $cdb.HasExited) { Finish (Failure 'CDB/AE render did not complete after continue marker' @('cdb_exit') "pid=$aePid") 2 }
$aeResultPath = Join-Path $work 'AE_SINGLE_CASE_RESULT.json'
if (!(Test-Path -LiteralPath $aeResultPath -PathType Leaf)) { Finish (Failure 'AE result JSON missing after debugger completed' @('AE_SINGLE_CASE_RESULT.json') '') 2 }
$aeResult = Get-Content -LiteralPath $aeResultPath -Raw | ConvertFrom-Json
if ($aeResult.status -ne 'ok' -or [int]$aeResult.project_bits_per_channel -ne 8) { $parsed = Failure 'AE did not render the requested 8bpc case' @('status=ok','project_bits_per_channel=8') ($aeResult | ConvertTo-Json -Compress); $parsed['project_bits_per_channel'] = [int]$aeResult.project_bits_per_channel; Finish $parsed 2 }
$parsed = Parse $trace
$parsed['project_bits_per_channel'] = 8
if ($parsed.status -eq 'answered' -and ($parsed.aex_sha256 -ne $aexSha256 -or $parsed.ae_pid -ne $aePid -or $parsed.module_base -ne $base)) { $parsed = Failure 'CDB summaries do not bind to the located AE module' @('summary_process_module_identity') ($parsed | ConvertTo-Json -Compress); $parsed['project_bits_per_channel'] = 8 }
Finish $parsed $(if ($parsed.status -eq 'answered') { 0 } else { 2 })
'''

RUNNER = RUNNER_TEMPLATE.replace("__EXPECTED_HASH__", EXPECTED_CURRENT_AEX_SHA256)


QUEUE = r'''(function () {
    function env(name) { try { return $.getenv(name) || ""; } catch (e) { return ""; } }
    var root = File($.fileName).parent.parent.fsName;
    var requestDir = env("OLM_DG_LIVE_REQUEST_DIR");
    var workRoot = env("OLM_DG_LIVE_WORK_ROOT");
    if (!requestDir || !workRoot) { throw new Error("liveness request/work root is required"); }
    $.setenv("OLM_AE_REQUEST_DIR", requestDir);
    $.setenv("OLM_AE_CASE_ID", "case_0001");
    $.setenv("OLM_AE_OUTPUT_DIR", workRoot + "/single_case_output");
    $.setenv("OLM_AE_LOG_PATH", workRoot + "/AE_SINGLE_CASE.log");
    $.setenv("OLM_AE_RESULT_JSON", workRoot + "/AE_SINGLE_CASE_RESULT.json");
    $.setenv("OLM_AE_KEEP_OPEN", "0");
    $.setenv("OLM_AE_FORCE_NEW_PROJECT", "1");
    $.evalFile(new File(root + "/scripts/ae_render_single_case.jsx"));
})();
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--skip-support-sync", action="store_true")
    args = parser.parse_args()
    if not TYPED.is_dir() or not CURRENT_RENDERER.is_file():
        raise FileNotFoundError(TYPED)
    if PACKAGE.exists():
        shutil.rmtree(PACKAGE)
    if not args.skip_support_sync and SUPPORT.exists():
        shutil.rmtree(SUPPORT)
    (PACKAGE / "artifacts").mkdir(parents=True)
    (PACKAGE / "scripts").mkdir(parents=True)
    (PACKAGE / "request").mkdir(parents=True)
    (PACKAGE / "fixtures").mkdir(parents=True)
    (PACKAGE / "artifacts/run_olmdistancegradation_8bpc_depth_control_20260713.ps1").write_text(RUNNER, encoding="utf-8")
    (PACKAGE / "scripts/ae_render_olmdistancegradation_8bpc_depth_control_queue.jsx").write_text(QUEUE, encoding="utf-8")
    shutil.copy2(CURRENT_RENDERER, PACKAGE / "scripts/ae_render_single_case.jsx")
    shutil.copytree(TYPED / "request", PACKAGE / "request", dirs_exist_ok=True)
    (PACKAGE / "README_RUNTIME_TRACE.md").write_text(README, encoding="utf-8")
    (PACKAGE / "runtime_trace_package_manifest.json").write_text(json.dumps({
        "schema": 1, "kind": "olm_runtime_trace_request_package", "profile": "distancegradation-8bpc-current-aex-depth-control",
        "request_id": REQUEST_ID, "submission_status": "ready", "sendable": True,
        "accepted_current_aex": {
            "module": "DistanceGradation.aex",
            "path": r"C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\Plug-ins\Effects\DistanceGradation.aex",
            "sha256": EXPECTED_CURRENT_AEX_SHA256,
        },
        "runtime_actions": [{"request_id": REQUEST_ID, "status": "ready", "mode": "external-trace",
            "plugin_area": "OLMDistanceGradation PF8/PF32 callback depth control", "rvas": list(RVA),
            "stop_condition": "Require AE result project_bits_per_channel=8, then return one shared run_id/AEX hash and PF8/PF32 hit counts. Expected PF8>0 and PF32=0. No algorithm proof."}]
    }, indent=2) + "\n", encoding="utf-8")
    (PACKAGE / "RETURN_RUNTIME_TRACE_TEMPLATE.json").write_text(json.dumps({
        "schema": "olmdg_8bpc_depth_control_v1", "kind": "olm_runtime_trace_result", "status": "answered | exact_bind_failure",
        "request_id": REQUEST_ID, "run_id": None, "ae_pid": None, "module_base": None,
        "expected_current_aex_sha256": EXPECTED_CURRENT_AEX_SHA256,
        "aex_sha256": None, "project_bits_per_channel": 8,
        "rvas": [{"rva": rva, "hit_count": None} for rva in RVA]
    }, indent=2) + "\n", encoding="utf-8")
    counts = {"1170870": 3, "1170c90": 0}
    wrong_hash = ("0" if EXPECTED_CURRENT_AEX_SHA256[0] != "0" else "1") + EXPECTED_CURRENT_AEX_SHA256[1:]
    complete = "\n".join(f"DG8_DEPTH_SUMMARY run_id=dglive-fixture ae_pid=4242 module_base=0x7ff600000000 rva={rva} aex_sha256={EXPECTED_CURRENT_AEX_SHA256} hit_count={counts[rva]}" for rva in RVA) + "\n"
    missing = "\n".join(f"DG8_DEPTH_SUMMARY run_id=dglive-fixture ae_pid=4242 module_base=0x7ff600000000 rva={rva} aex_sha256={EXPECTED_CURRENT_AEX_SHA256} hit_count=0" for rva in RVA[:-1]) + "\n"
    adversarial = "\n".join(f"DG8_DEPTH_SUMMARY run_id=dglive-fixture ae_pid=4242 module_base=0x7ff600000000 rva={rva} aex_sha256={wrong_hash} hit_count={counts[rva]}" for rva in RVA) + "\n"
    (PACKAGE / "fixtures/complete_cdb_stdout.txt").write_text(complete, encoding="utf-8")
    (PACKAGE / "fixtures/missing_rva_cdb_stdout.txt").write_text(missing, encoding="utf-8")
    (PACKAGE / "fixtures/adversarial_wrong_hash_cdb_stdout.txt").write_text(adversarial, encoding="utf-8")
    (PACKAGE / "fixtures/latest_ae_ready_missing_failure.json").write_text(json.dumps({
        "status": "exact_bind_failure", "kind": "depth_control", "request_id": REQUEST_ID,
        "failure": {"stage": "depth_control", "reason": "AE pause ready marker missing",
            "missing_fields": ["ae_ready.marker"],
            "last_observation": {"launch_pid": 12708, "launcher_exited": True,
                "launcher_exit_code": None, "candidate_afterfx": [], "ae_log": None},
            "runtime_diagnostics": {"launcher": {"pid": 12708, "launcher_exited": True,
                "launcher_exit_code": None}, "launcher_stderr": None, "ae_log": None,
                "ae_result": None, "process_diagnostics": {"candidate_afterfx": []}}}},
        indent=2) + "\n", encoding="utf-8")
    if not args.skip_support_sync:
        shutil.copytree(PACKAGE, SUPPORT)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in PACKAGE.rglob("*") if p.is_file()):
            archive.write(path, path.relative_to(PACKAGE).as_posix())
    print(f"[OK] built depth-control package: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
