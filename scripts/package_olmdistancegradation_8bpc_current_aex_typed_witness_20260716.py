#!/usr/bin/env python3
"""Build the direct three-case DG 8bpc typed residual witness package."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712"
PACKAGE = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_three_case_residuals_20260716"
OUTPUT = PACKAGE.with_suffix(".zip")
REQUEST_ID = "olmdistancegradation_8bpc_current_aex_typed_witness_three_case_residuals_20260716"
AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
CASES = ("case_0001", "case_0015", "case_0029")
STAGES = ("ENTRY_FIELD_ADDR_SNAPSHOT", "FIELD_READ_INPUT", "SOURCE_READ", "COMPOSE_PRE_U8_SCALE", "U8_PRE_STORE", "POST_STORE")
RUNNER_NAME = "run_olmdistancegradation_8bpc_three_case_residuals_20260716.ps1"
QUEUE_NAME = "ae_render_olmdistancegradation_8bpc_three_case_residual_queue.jsx"
FIXED_ZIP_TIME = (2026, 7, 16, 0, 0, 0)
TARGETS = {
    "case_0001": {"chain": (0, 0), "residual": (17, 0), "mode": "derived", "optional": (0, 90), "mac": (57, 0, 0, 57), "windows": (56, 0, 0, 56)},
    "case_0015": {"chain": (780, 495), "residual": (780, 495), "mode": "direct", "optional": (1107, 315), "mac": (0, 0, 0, 10), "windows": (10, 0, 0, 10)},
    "case_0029": {"chain": (987, 496), "residual": (987, 496), "mode": "direct", "optional": None, "mac": (7, 0, 60, 64), "windows": (7, 0, 63, 67)},
}


README = f"""# OLMDistanceGradation 8bpc Three-Case Residual Witness

Status: ready and sendable as a bounded observation request. This package
makes no AE exactness claim.

The required cases are: `case_0001`, with the truthful six-stage chain at
live anchor `(0,0)` plus a data-store witness at exactly
`anchor_output_addr + 68` for residual `(17,0)`; `case_0015`, with the full
chain directly at live residual `(780,495)`; and `case_0029`, with the full
chain directly at live residual `(987,496)`. Optional diagnostics `(0,90)`
and `(1107,315)` never satisfy success.

The audited chain is `ENTRY_FIELD_ADDR_SNAPSHOT -> FIELD_READ_INPUT ->
SOURCE_READ -> COMPOSE_PRE_U8_SCALE -> U8_PRE_STORE -> POST_STORE`. PF8 uses
`RCX=refcon`, `EDX=x`, `R8D=y`, and output pointer `poi([rsp+0xe0])`.
Downstream stops use saved x/y pseudo-registers. Stage RVAs are `1170870`,
`117098f`, `1170a09`, `1170c11`, `1170c20`, byte stores `1170c29/30/37/3e`,
and post-store `1170c40`.

Each case runs in a fresh AE process while sharing one request run ID. Success
requires the pinned AEX SHA-256 `{AEX_SHA256}`, AE-log evidence of Software
rendering, project 8bpc, PF8 > 0, PF32 = 0, complete target evidence, and all
retained launcher/CDB/AE/queue logs. Any missing or inconsistent observation
is `exact_bind_failure`.

Mac comparison metadata is carried in the manifest only: case_0001 `(17,0)`
Mac `[57,0,0,57]`, Windows `[56,0,0,56]`; case_0015 `(780,495)` Mac
`[0,0,0,10]`, Windows `[10,0,0,10]`; case_0029 `(987,496)` Mac
`[7,0,60,64]`, Windows `[7,0,63,67]`. These do not claim AE exactness.

Entrypoint: `artifacts/{RUNNER_NAME}`
"""


QUEUE = r'''(function () {
    function env(name) { try { return $.getenv(name) || ""; } catch (e) { return ""; } }
    function write(path, text, append) {
        var file = new File(path);
        file.encoding = "UTF-8";
        if (!file.open(append ? "a" : "w")) { throw new Error("cannot open " + path); }
        file.write(text);
        file.close();
    }
    var root = File($.fileName).parent.parent.fsName;
    var caseId = env("OLM_AE_CASE_ID");
    var queueLog = env("OLM_DG_QUEUE_LOG");
    if (!caseId || !queueLog) { throw new Error("case and queue log bindings are required"); }
    write(queueLog, "DG8_QUEUE_START case_id=" + caseId + "\n", false);
    $.evalFile(new File(root + "/scripts/ae_render_single_case.jsx"));
    write(queueLog, "DG8_QUEUE_END case_id=" + caseId + "\n", true);
}());
'''


RUNNER = r'''param(
  [string]$PackageRoot = (Split-Path -Parent $PSScriptRoot),
  [string]$WorkRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) 'work'),
  [switch]$ParseOnly,
  [string]$TracePath = '',
  [string]$AexPath = 'C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\Plug-ins\Effects\DistanceGradation.aex',
  [string]$AfterFxPath = 'C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe',
  [string]$CdbPath = 'C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe'
)

$ErrorActionPreference = 'Stop'
$requestId = 'olmdistancegradation_8bpc_current_aex_typed_witness_three_case_residuals_20260716'
$expectedHash = 'a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae'
$cases = @('case_0001', 'case_0015', 'case_0029')
$requiredStages = @('ENTRY_FIELD_ADDR_SNAPSHOT', 'FIELD_READ_INPUT', 'SOURCE_READ', 'COMPOSE_PRE_U8_SCALE', 'U8_PRE_STORE', 'POST_STORE')
$obsoleteStages = @('FIELD_IN', 'FIELD_OUT', 'COMPOSE_IN', 'COMPOSE_OUT', 'HOST_STORE')
$targets = @{
  case_0001 = [ordered]@{chain_x=0;chain_y=0;residual_x=17;residual_y=0;mode='derived';mac='57,0,0,57';windows='56,0,0,56'}
  case_0015 = [ordered]@{chain_x=780;chain_y=495;residual_x=780;residual_y=495;mode='direct';mac='0,0,0,10';windows='10,0,0,10'}
  case_0029 = [ordered]@{chain_x=987;chain_y=496;residual_x=987;residual_y=496;mode='direct';mac='7,0,60,64';windows='7,0,63,67'}
}
$runId = 'dg8three-' + [guid]::NewGuid().ToString('N')

function New-Failure([string]$stage, [string]$reason, [object[]]$missing, [string]$last) {
  [ordered]@{status='exact_bind_failure';kind='typed_boundary_residual_witness';request_id=$requestId;failure=[ordered]@{stage=$stage;reason=$reason;missing_fields=@($missing);last_observation=$last}}
}

function Parse-Fields([string]$line) {
  $fields = @{}
  foreach ($match in [regex]::Matches($line, '(?<key>[a-z0-9_]+)=(?<value>[^\s]+)')) {
    $fields[$match.Groups['key'].Value] = $match.Groups['value'].Value
  }
  $fields
}

function Convert-HexAddress([string]$value, [string]$name) {
  if ($value -notmatch '^0x[0-9a-fA-F]+$') { throw "${name} is not a hex address: $value" }
  [Convert]::ToInt64($value.Substring(2), 16)
}

function Parse-Trace([string]$path) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return New-Failure 'parse' 'combined trace is missing' @('combined_cdb_trace') '' }
  $stageRows = @{}
  $boundRows = @{}
  $residualRows = @{}
  $depthRows = @{}
  $missing = @()
  $last = ''
  foreach ($line in Get-Content -LiteralPath $path) {
    $last = $line
    if ($line -match '^DG8_(FIELD_IN|FIELD_OUT|COMPOSE_IN|COMPOSE_OUT|HOST_STORE)\s+') {
      $missing += ('obsolete_stage:{0}' -f $Matches[1])
      continue
    }
    if ($line -match '^DG8_(ENTRY_FIELD_ADDR_SNAPSHOT|FIELD_READ_INPUT|SOURCE_READ|COMPOSE_PRE_U8_SCALE|U8_PRE_STORE|POST_STORE)\s+') {
      $stage = $Matches[1]
      $fields = Parse-Fields $line
      $key = "$($fields.case_id)|$($fields.x)|$($fields.y)|${stage}"
      if (-not $stageRows.ContainsKey($key)) { $stageRows[$key] = @() }
      $stageRows[$key] = @($stageRows[$key]) + @($fields)
      continue
    }
    if ($line -match '^DG8_OUTPUT_ADDR_BOUND\s+') {
      $fields = Parse-Fields $line
      if (-not $boundRows.ContainsKey($fields.case_id)) { $boundRows[$fields.case_id] = @() }
      $boundRows[$fields.case_id] = @($boundRows[$fields.case_id]) + @($fields)
      continue
    }
    if ($line -match '^DG8_RESIDUAL_DATA_STORE\s+') {
      $fields = Parse-Fields $line
      if (-not $residualRows.ContainsKey($fields.case_id)) { $residualRows[$fields.case_id] = @() }
      $residualRows[$fields.case_id] = @($residualRows[$fields.case_id]) + @($fields)
      continue
    }
    if ($line -match '^DG8_DEPTH_SUMMARY\s+') {
      $fields = Parse-Fields $line
      $key = "$($fields.case_id)|$($fields.rva)"
      if (-not $depthRows.ContainsKey($key)) { $depthRows[$key] = @() }
      $depthRows[$key] = @($depthRows[$key]) + @($fields)
    }
  }

  $caseResults = @()
  $allStageRows = @()
  foreach ($caseId in $cases) {
    $target = $targets[$caseId]
    $chainRows = @()
    foreach ($stage in $requiredStages) {
      $key = "${caseId}|$($target.chain_x)|$($target.chain_y)|${stage}"
      $matches = @($stageRows[$key])
      if ($matches.Count -ne 1) { $missing += "${key}:count=$($matches.Count)"; continue }
      $row = $matches[0]
      $chainRows += $row
      $allStageRows += $row
      foreach ($field in @('request_id','run_id','ae_pid','module_base','aex_sha256','renderer','project_bpc','case_id','x','y','output_addr','typed_rgba')) {
        if (-not $row.ContainsKey($field) -or [string]::IsNullOrWhiteSpace([string]$row[$field])) { $missing += ('{0}:{1}' -f $key,$field) }
      }
      if ($row.request_id -ne $requestId -or $row.aex_sha256 -ne $expectedHash -or $row.renderer -ne 'Software' -or $row.project_bpc -ne '8') { $missing += ('{0}:identity_contract' -f $key) }
    }
    if ($chainRows.Count -eq $requiredStages.Count) {
      $identities = @($chainRows | ForEach-Object { "$($_.request_id)|$($_.run_id)|$($_.ae_pid)|$($_.module_base)|$($_.aex_sha256)|$($_.renderer)|$($_.project_bpc)|$($_.case_id)|$($_.x)|$($_.y)|$($_.output_addr)" } | Select-Object -Unique)
      if ($identities.Count -ne 1) { $missing += "${caseId}:chain_identity" }
    }
    $bounds = @($boundRows[$caseId])
    if ($bounds.Count -ne 1) { $missing += "${caseId}:DG8_OUTPUT_ADDR_BOUND:count=$($bounds.Count)" }
    $residuals = @($residualRows[$caseId])
    if ($residuals.Count -ne 1) { $missing += "${caseId}:DG8_RESIDUAL_DATA_STORE:count=$($residuals.Count)" }
    if ($bounds.Count -eq 1 -and $residuals.Count -eq 1 -and $chainRows.Count -eq $requiredStages.Count) {
      $bound = $bounds[0]
      $residual = $residuals[0]
      foreach ($field in @('request_id','run_id','ae_pid','module_base','aex_sha256','renderer','project_bpc','case_id','mode','chain_x','chain_y','residual_x','residual_y','anchor_output_addr','residual_output_addr')) {
        if (-not $bound.ContainsKey($field)) { $missing += "${caseId}:bound:${field}" }
      }
      foreach ($field in @('request_id','run_id','ae_pid','module_base','aex_sha256','renderer','project_bpc','case_id','x','y','output_addr','store_addr','anchor_output_addr','residual_output_addr','expected_rgba_mac','expected_rgba_windows')) {
        if (-not $residual.ContainsKey($field) -or [string]::IsNullOrWhiteSpace([string]$residual[$field])) { $missing += ('{0}:residual:{1}' -f $caseId,$field) }
      }
      if ($bound.mode -ne $target.mode -or $bound.chain_x -ne [string]$target.chain_x -or $bound.chain_y -ne [string]$target.chain_y -or $bound.residual_x -ne [string]$target.residual_x -or $bound.residual_y -ne [string]$target.residual_y) { $missing += "${caseId}:bound_coordinates" }
      $chainIdentity = $chainRows[0]
      if ($residual.request_id -ne $requestId -or $residual.run_id -ne $chainIdentity.run_id -or $residual.ae_pid -ne $chainIdentity.ae_pid -or $residual.module_base -ne $chainIdentity.module_base -or $residual.aex_sha256 -ne $expectedHash -or $residual.renderer -ne 'Software' -or $residual.project_bpc -ne '8' -or $residual.case_id -ne $caseId) { $missing += "${caseId}:residual_identity_contract" }
      if ($residual.x -ne [string]$target.residual_x -or $residual.y -ne [string]$target.residual_y -or $residual.expected_rgba_mac -ne $target.mac -or $residual.expected_rgba_windows -ne $target.windows) { $missing += "${caseId}:residual_contract" }
      if ($residual.output_addr -ne $bound.residual_output_addr -or $residual.store_addr -ne $bound.residual_output_addr -or $residual.anchor_output_addr -ne $bound.anchor_output_addr -or $residual.residual_output_addr -ne $bound.residual_output_addr) { $missing += "${caseId}:residual_output_identity" }
      if ($target.mode -eq 'derived') {
        try {
          $anchorAddress = Convert-HexAddress $bound.anchor_output_addr "${caseId}:anchor_output_addr"
          $residualAddress = Convert-HexAddress $bound.residual_output_addr "${caseId}:residual_output_addr"
          if ($residualAddress -ne ($anchorAddress + 68)) { $missing += "${caseId}:residual_output_addr_not_anchor_plus_68" }
        } catch { $missing += "${caseId}:derived_address_parse" }
        if ($chainRows[0].output_addr -ne $bound.anchor_output_addr) { $missing += "${caseId}:anchor_chain_output_identity" }
      } elseif ($chainRows[0].output_addr -ne $bound.residual_output_addr) {
        $missing += "${caseId}:direct_chain_output_identity"
      }
    }
    foreach ($rva in @('1170870','1170c90')) {
      $key = "${caseId}|${rva}"
      $matches = @($depthRows[$key])
      if ($matches.Count -ne 1) { $missing += "${key}:count=$($matches.Count)"; continue }
      $depth = $matches[0]
      foreach ($field in @('request_id','run_id','ae_pid','module_base','aex_sha256','renderer','project_bpc','case_id','rva','hit_count')) {
        if (-not $depth.ContainsKey($field)) { $missing += ('{0}:{1}' -f $key,$field) }
      }
      $chainIdentity = $chainRows[0]
      if ($depth.request_id -ne $requestId -or $depth.run_id -ne $chainIdentity.run_id -or $depth.ae_pid -ne $chainIdentity.ae_pid -or $depth.module_base -ne $chainIdentity.module_base -or $depth.aex_sha256 -ne $expectedHash -or $depth.renderer -ne 'Software' -or $depth.project_bpc -ne '8' -or $depth.case_id -ne $caseId -or $depth.rva -ne $rva) { $missing += ('{0}:identity_contract' -f $key) }
      if ($depth.hit_count -notmatch '^\d+$') { $missing += ('{0}:hit_count_integer' -f $key) }
      elseif ($rva -eq '1170870' -and [int64]$depth.hit_count -le 0) { $missing += ('{0}:PF8_gt_0' -f $key) }
      elseif ($rva -eq '1170c90' -and [int64]$depth.hit_count -ne 0) { $missing += ('{0}:PF32_eq_0' -f $key) }
    }
    $caseResults += [ordered]@{case_id=$caseId;chain_xy=@($target.chain_x,$target.chain_y);residual_xy=@($target.residual_x,$target.residual_y);mode=$target.mode}
  }
  $runIds = @($allStageRows | ForEach-Object { $_.run_id } | Select-Object -Unique)
  $requestIds = @($allStageRows | ForEach-Object { $_.request_id } | Select-Object -Unique)
  $pids = @($allStageRows | ForEach-Object { $_.ae_pid } | Select-Object -Unique)
  if ($runIds.Count -ne 1) { $missing += 'shared_run_id' }
  if ($requestIds.Count -ne 1 -or $requestIds[0] -ne $requestId) { $missing += 'shared_request_id' }
  if ($pids.Count -ne 3) { $missing += 'fresh_process_per_case' }
  if ($missing.Count -gt 0) { return New-Failure 'parse' 'required typed residual evidence is incomplete or inconsistent' $missing $last }
  [ordered]@{status='answered';kind='typed_boundary_residual_witness';request_id=$requestId;run_id=$runIds[0];renderer='Software';project_bits_per_channel=8;aex_sha256=$expectedHash;cases=$caseResults}
}

if ($ParseOnly) {
  if (-not $TracePath) { throw '-ParseOnly requires -TracePath' }
  $parsed = Parse-Trace $TracePath
  $parsed | ConvertTo-Json -Depth 16
  exit $(if ($parsed.status -eq 'answered') { 0 } else { 2 })
}

$work = Join-Path $WorkRoot $runId
New-Item -ItemType Directory -Force -Path $work | Out-Null
$work = (Get-Item -LiteralPath $work).FullName
$returnPath = Join-Path $work 'RETURN_RUNTIME_TRACE.json'
$combinedTrace = Join-Path $work 'combined_cdb_trace.txt'
$sessionId = (Get-Process -Id $PID).SessionId
$currentLaunch = $null
$currentCdb = $null
$launchedPids = @()

function Read-OrNull([string]$path) {
  if (Test-Path -LiteralPath $path -PathType Leaf) { return Get-Content -LiteralPath $path -Raw }
  $null
}
function Get-AfterFxState {
  @(Get-CimInstance Win32_Process -Filter "Name='AfterFX.exe'" -ErrorAction SilentlyContinue | Where-Object {
    $_.SessionId -eq $sessionId -and $_.ExecutablePath -and [IO.Path]::GetFullPath($_.ExecutablePath) -ieq $AfterFxPath
  } | ForEach-Object { [ordered]@{pid=[int]$_.ProcessId;parent_pid=[int]$_.ParentProcessId;session_id=[int]$_.SessionId;path=$_.ExecutablePath;command_line=$_.CommandLine} })
}
function Raw-Logs {
  [ordered]@{work_directory=$work;combined_cdb_trace=(Read-OrNull $combinedTrace);cases=@($cases | ForEach-Object {
    $caseId = $_; $caseDir = Join-Path $work $caseId
    [ordered]@{case_id=$caseId;queue_log=(Read-OrNull (Join-Path $caseDir 'AE_QUEUE.log'));ready_marker=(Read-OrNull (Join-Path $caseDir 'ae_ready.marker'));launcher_stdout=(Read-OrNull (Join-Path $caseDir 'launcher_stdout.txt'));launcher_stderr=(Read-OrNull (Join-Path $caseDir 'launcher_stderr.txt'));cdb_trace=(Read-OrNull (Join-Path $caseDir 'cdb_trace.txt'));cdb_stdout=(Read-OrNull (Join-Path $caseDir 'cdb_stdout.txt'));cdb_stderr=(Read-OrNull (Join-Path $caseDir 'cdb_stderr.txt'));ae_log=(Read-OrNull (Join-Path $caseDir 'AE_SINGLE_CASE.log'));ae_result=(Read-OrNull (Join-Path $caseDir 'AE_SINGLE_CASE_RESULT.json'))}
  });process_diagnostics=[ordered]@{session_id=$sessionId;candidate_afterfx=@(Get-AfterFxState)}}
}
function Test-RawLogsComplete {
  if (-not (Test-Path -LiteralPath $combinedTrace -PathType Leaf) -or (Get-Item -LiteralPath $combinedTrace).Length -le 0) { return $false }
  foreach ($caseId in $cases) {
    $caseDir = Join-Path $work $caseId
    foreach ($name in @('AE_QUEUE.log','ae_ready.marker','launcher_stdout.txt','launcher_stderr.txt','cdb_trace.txt','cdb_stdout.txt','cdb_stderr.txt','AE_SINGLE_CASE.log','AE_SINGLE_CASE_RESULT.json')) {
      if (-not (Test-Path -LiteralPath (Join-Path $caseDir $name) -PathType Leaf)) { return $false }
    }
    foreach ($name in @('AE_QUEUE.log','ae_ready.marker','cdb_trace.txt','AE_SINGLE_CASE.log','AE_SINGLE_CASE_RESULT.json')) {
      if ((Get-Item -LiteralPath (Join-Path $caseDir $name)).Length -le 0) { return $false }
    }
  }
  $true
}
function Finish([object]$body, [int]$code) {
  if ($code -ne 0) {
    if ($currentCdb -and -not $currentCdb.HasExited) { Stop-Process -Id $currentCdb.Id -Force -ErrorAction SilentlyContinue }
    foreach ($state in @(Get-AfterFxState)) { Stop-Process -Id $state.pid -Force -ErrorAction SilentlyContinue }
  }
  $body['raw_logs'] = Raw-Logs
  $json = $body | ConvertTo-Json -Depth 18
  $json | Set-Content -LiteralPath $returnPath -Encoding UTF8
  $json
  exit $code
}

$queue = Join-Path $PackageRoot 'scripts\ae_render_olmdistancegradation_8bpc_three_case_residual_queue.jsx'
foreach ($requiredPath in @($AexPath,$AfterFxPath,$CdbPath,$queue)) {
  if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) { Finish (New-Failure 'preflight' "required file missing: $requiredPath" @('preflight_file') '') 2 }
}
$AexPath = (Get-Item -LiteralPath $AexPath).FullName
$AfterFxPath = (Get-Item -LiteralPath $AfterFxPath).FullName
$CdbPath = (Get-Item -LiteralPath $CdbPath).FullName
$actualHash = (Get-FileHash -LiteralPath $AexPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualHash -ne $expectedHash) { Finish (New-Failure 'module_hash' 'DistanceGradation.aex hash mismatch' @('expected_aex_sha256') "actual=$actualHash") 2 }
if (Get-Process -Name AfterFX -ErrorAction SilentlyContinue) { Finish (New-Failure 'fresh_process' 'After Effects must be fully closed before the request' @('no_existing_AfterFX') '') 2 }

foreach ($caseId in $cases) {
  if (Get-Process -Name AfterFX -ErrorAction SilentlyContinue) { Finish (New-Failure 'fresh_process' "After Effects remained open before $caseId" @("${caseId}:fresh_process") '') 2 }
  $caseDir = Join-Path $work $caseId
  New-Item -ItemType Directory -Force -Path $caseDir | Out-Null
  $ready = Join-Path $caseDir 'ae_ready.marker'; $continue = Join-Path $caseDir 'ae_continue.marker'; $queueLog = Join-Path $caseDir 'AE_QUEUE.log'
  $aeLog = Join-Path $caseDir 'AE_SINGLE_CASE.log'; $aeResultPath = Join-Path $caseDir 'AE_SINGLE_CASE_RESULT.json'
  $launchOut = Join-Path $caseDir 'launcher_stdout.txt'; $launchErr = Join-Path $caseDir 'launcher_stderr.txt'
  $trace = Join-Path $caseDir 'cdb_trace.txt'; $cdbOut = Join-Path $caseDir 'cdb_stdout.txt'; $cdbErr = Join-Path $caseDir 'cdb_stderr.txt'; $cdbScript = Join-Path $caseDir 'typed.cdb'
  $env:OLM_AE_REQUEST_DIR = Join-Path $PackageRoot 'request'; $env:OLM_AE_CASE_ID = $caseId; $env:OLM_AE_OUTPUT_DIR = Join-Path $caseDir 'output'
  $env:OLM_AE_LOG_PATH = $aeLog; $env:OLM_AE_RESULT_JSON = $aeResultPath; $env:OLM_AE_READY_MARKER = $ready; $env:OLM_AE_CONTINUE_MARKER = $continue
  $env:OLM_AE_PAUSE_BEFORE_RENDER = '1'; $env:OLM_AE_PAUSE_TIMEOUT_SECONDS = '300'; $env:OLM_AE_FORCE_SOFTWARE = '1'; $env:OLM_AE_FORCE_NEW_PROJECT = '1'; $env:OLM_AE_KEEP_OPEN = '0'; $env:OLM_DG_QUEUE_LOG = $queueLog
  $currentLaunch = Start-Process -FilePath $AfterFxPath -ArgumentList @('-m','-r',$queue) -RedirectStandardOutput $launchOut -RedirectStandardError $launchErr -PassThru
  $deadline = (Get-Date).AddSeconds(180)
  while ((Get-Date) -lt $deadline -and -not (Test-Path -LiteralPath $ready)) { Start-Sleep -Milliseconds 250 }
  if (-not (Test-Path -LiteralPath $ready -PathType Leaf)) { Finish (New-Failure 'readiness' "ready marker missing for $caseId" @("${caseId}:ae_ready.marker") '') 2 }
  $readyText = Get-Content -LiteralPath $ready -Raw
  if ($readyText -notmatch "case_id=$caseId" -or $readyText -notmatch 'effect_loaded=1' -or $readyText -notmatch 'parameters_applied=1') { Finish (New-Failure 'readiness' "invalid ready marker for $caseId" @("${caseId}:ready_contract") $readyText) 2 }
  $loaded = @(); $deadline = (Get-Date).AddSeconds(30)
  while ((Get-Date) -lt $deadline -and $loaded.Count -ne 1) {
    $loaded = @(Get-AfterFxState | ForEach-Object { $process = Get-Process -Id $_.pid -ErrorAction SilentlyContinue; try { $module = $process.Modules | Where-Object { $_.FileName -ieq $AexPath } | Select-Object -First 1; if ($module) { [pscustomobject]@{Process=$process;Module=$module} } } catch {} })
    if ($loaded.Count -ne 1) { Start-Sleep -Milliseconds 250 }
  }
  if ($loaded.Count -ne 1) { Finish (New-Failure 'process_discovery' "one loaded AEX process was not found for $caseId" @("${caseId}:loaded_module") "count=$($loaded.Count)") 2 }
  $ae = $loaded[0].Process; $module = $loaded[0].Module; $aePid = [int]$ae.Id; $moduleBase = ('0x{0:x}' -f $module.BaseAddress.ToInt64())
  if ($launchedPids -contains $aePid) { Finish (New-Failure 'fresh_process' "AE PID reused for $caseId" @("${caseId}:fresh_pid") "pid=$aePid") 2 }
  $launchedPids += $aePid
  $loadedHash = (Get-FileHash -LiteralPath $module.FileName -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($loadedHash -ne $expectedHash) { Finish (New-Failure 'module_hash' "loaded hash mismatch for $caseId" @("${caseId}:loaded_aex_sha256") "actual=$loadedHash") 2 }
  $target = $targets[$caseId]; $baseValue = $module.BaseAddress.ToInt64()
  $pf8 = ('0x{0:x}' -f ($baseValue + 0x1170870)); $pf32 = ('0x{0:x}' -f ($baseValue + 0x1170c90)); $fieldRead = ('0x{0:x}' -f ($baseValue + 0x117098f)); $sourceRead = ('0x{0:x}' -f ($baseValue + 0x1170a09)); $composeScale = ('0x{0:x}' -f ($baseValue + 0x1170c11)); $u8PreStore = ('0x{0:x}' -f ($baseValue + 0x1170c20)); $store0 = ('0x{0:x}' -f ($baseValue + 0x1170c29)); $store1 = ('0x{0:x}' -f ($baseValue + 0x1170c30)); $store2 = ('0x{0:x}' -f ($baseValue + 0x1170c37)); $store3 = ('0x{0:x}' -f ($baseValue + 0x1170c3e)); $postStore = ('0x{0:x}' -f ($baseValue + 0x1170c40))
  $residualOffset = if ($target.mode -eq 'derived') { 68 } else { 0 }
  # These fragments are inserted two CDB command-string levels deep. PowerShell
  # single quotes preserve @$tN literally; the doubled backslashes keep the
  # nested .printf quotes and newline escaped when CDB parses the outer bp.
  $depthSummary0 = '.printf \\\"DG8_DEPTH_SUMMARY request_id=' + $requestId + ' run_id=' + $runId + ' ae_pid=' + $aePid + ' module_base=' + $moduleBase + ' aex_sha256=' + $actualHash + ' renderer=Software project_bpc=8 case_id=' + $caseId + ' rva=1170870 hit_count=%I64u\\\\n\\\",@$t0'
  $depthSummary1 = '.printf \\\"DG8_DEPTH_SUMMARY request_id=' + $requestId + ' run_id=' + $runId + ' ae_pid=' + $aePid + ' module_base=' + $moduleBase + ' aex_sha256=' + $actualHash + ' renderer=Software project_bpc=8 case_id=' + $caseId + ' rva=1170c90 hit_count=%I64u\\\\n\\\",@$t1'
  $dataStop = if ($target.mode -eq 'derived') { $depthSummary0 + ';' + $depthSummary1 + ';.detach;q' } else { 'gc' }
  $postStop = if ($target.mode -eq 'direct') { $depthSummary0 + ';' + $depthSummary1 + ';.detach;q' } else { 'gc' }
  $cdbText = @"
.effmach amd64
.expr /s masm
sxi 80000003
.logopen "$trace"
r @`$t0=0
r @`$t1=0
r @`$t12=0
bp $pf32 "r @`$t1=@`$t1+1;gc"
bp $pf8 ".if (@edx==$($target.chain_x) && @r8d==$($target.chain_y)) {r @`$t0=@`$t0+1;r @`$t10=@edx;r @`$t11=@r8d;r @`$t2=poi(@rcx+8);r @`$t3=poi(@rcx);r @`$t4=poi(@rsp+0xe0);r @`$t5=poi(@`$t2+18);r @`$t6=dwo(@`$t2+20);r @`$t7=@`$t5+(@`$t11*@`$t6)+(@`$t10*4);r @`$t8=poi(@`$t3+18)+(@`$t11*dwo(@`$t3+20))+(@`$t10*4);r @`$t9=@`$t4+$residualOffset;.printf \"DG8_OUTPUT_ADDR_BOUND request_id=$requestId run_id=$runId ae_pid=$aePid module_base=$moduleBase aex_sha256=$actualHash renderer=Software project_bpc=8 case_id=$caseId mode=$($target.mode) chain_x=$($target.chain_x) chain_y=$($target.chain_y) residual_x=$($target.residual_x) residual_y=$($target.residual_y) anchor_output_addr=%p residual_output_addr=%p\\n\",@`$t4,@`$t9;.printf \"DG8_ENTRY_FIELD_ADDR_SNAPSHOT request_id=$requestId run_id=$runId ae_pid=$aePid module_base=$moduleBase aex_sha256=$actualHash renderer=Software project_bpc=8 case_id=$caseId x=%u y=%u output_addr=%p field_base=%p field_rowbytes=%x field_addr=%p pixel_size=4 address_formula=base+y*rowbytes+x*4 typed_rgba=%02x,%02x,%02x,%02x\\n\",@`$t10,@`$t11,@`$t4,@`$t5,@`$t6,@`$t7,by(@`$t7+1),by(@`$t7+2),by(@`$t7+3),by(@`$t7);ba w4 @`$t9 \".if (@`$t12==0) {r @`$t12=1;.printf \\\"DG8_RESIDUAL_DATA_STORE request_id=$requestId run_id=$runId ae_pid=$aePid module_base=$moduleBase aex_sha256=$actualHash renderer=Software project_bpc=8 case_id=$caseId x=$($target.residual_x) y=$($target.residual_y) output_addr=%p store_addr=%p anchor_output_addr=%p residual_output_addr=%p expected_rgba_mac=$($target.mac) expected_rgba_windows=$($target.windows)\\\\n\\\",@`$t9,@`$t9,@`$t4,@`$t9;$dataStop} .else {gc}\";bp $fieldRead \".if (@rcx==@`$t7) {.printf \\\"DG8_FIELD_READ_INPUT request_id=$requestId run_id=$runId ae_pid=$aePid module_base=$moduleBase aex_sha256=$actualHash renderer=Software project_bpc=8 case_id=$caseId x=%u y=%u output_addr=%p field_base=%p field_rowbytes=%x field_addr=%p pixel_size=4 address_formula=base+y*rowbytes+x*4 typed_rgba=%02x,%02x,%02x,%02x\\\\n\\\",@`$t10,@`$t11,@`$t4,@`$t5,@`$t6,@rcx,by(@rcx+1),by(@rcx+2),by(@rcx+3),by(@rcx)};gc\";bp $sourceRead \".if (@r10==@`$t8) {.printf \\\"DG8_SOURCE_READ request_id=$requestId run_id=$runId ae_pid=$aePid module_base=$moduleBase aex_sha256=$actualHash renderer=Software project_bpc=8 case_id=$caseId x=%u y=%u output_addr=%p source_addr=%p typed_rgba=%02x,%02x,%02x,%02x\\\\n\\\",@`$t10,@`$t11,@`$t4,@r10,by(@r10+1),by(@r10+2),by(@r10+3),by(@r10)};gc\";bp $composeScale \".if (@rdi==@`$t4) {.printf \\\"DG8_COMPOSE_PRE_U8_SCALE request_id=$requestId run_id=$runId ae_pid=$aePid module_base=$moduleBase aex_sha256=$actualHash renderer=Software project_bpc=8 case_id=$caseId x=%u y=%u output_addr=%p pre_u8_scale_rgba=%f,%f,%f,%f typed_rgba=%f,%f,%f,%f\\\\n\\\",@`$t10,@`$t11,@`$t4,@xmm1,@xmm5,@xmm3,@xmm6,@xmm1,@xmm5,@xmm3,@xmm6};gc\";bp $u8PreStore \".if (@rdi==@`$t4) {.printf \\\"DG8_U8_PRE_STORE request_id=$requestId run_id=$runId ae_pid=$aePid module_base=$moduleBase aex_sha256=$actualHash renderer=Software project_bpc=8 case_id=$caseId x=%u y=%u output_addr=%p pre_cvtt_lane_1_3_2_0=%f,%f,%f,%f lane_order=out+1,out+3,out+2,out+0 xmm5_scale_pending=1 typed_rgba=%f,%f,%f,%f\\\\n\\\",@`$t10,@`$t11,@`$t4,@xmm1,@xmm3,@xmm5,@xmm6,@xmm1,@xmm3,@xmm5,@xmm6};gc\";bp $store0 \"gc\";bp $store1 \"gc\";bp $store2 \"gc\";bp $store3 \"gc\";bp $postStore \".if (@rdi==@`$t4) {.printf \\\"DG8_POST_STORE request_id=$requestId run_id=$runId ae_pid=$aePid module_base=$moduleBase aex_sha256=$actualHash renderer=Software project_bpc=8 case_id=$caseId x=%u y=%u output_addr=%p typed_rgba=%02x,%02x,%02x,%02x\\\\n\\\",@`$t10,@`$t11,@`$t4,by(@rdi+1),by(@rdi+2),by(@rdi+3),by(@rdi);$postStop};gc\";gc} .else {gc}"
.echo DG8_BREAKPOINTS_ARMED
g
"@
  $cdbText | Set-Content -LiteralPath $cdbScript -Encoding ASCII
  $currentCdb = Start-Process -FilePath $CdbPath -ArgumentList ('-cf "' + $cdbScript + '" -p ' + $aePid) -RedirectStandardOutput $cdbOut -RedirectStandardError $cdbErr -NoNewWindow -PassThru
  $deadline = (Get-Date).AddSeconds(60)
  while ((Get-Date) -lt $deadline) { if ((Test-Path -LiteralPath $trace) -and (Get-Content -LiteralPath $trace -Raw) -match 'DG8_BREAKPOINTS_ARMED') { break }; if ($currentCdb.HasExited) { break }; Start-Sleep -Milliseconds 250; $currentCdb.Refresh() }
  if (-not (Test-Path -LiteralPath $trace) -or (Get-Content -LiteralPath $trace -Raw) -notmatch 'DG8_BREAKPOINTS_ARMED') { Finish (New-Failure 'cdb_arm' "CDB did not arm for $caseId" @("${caseId}:DG8_BREAKPOINTS_ARMED") '') 2 }
  Set-Content -LiteralPath $continue -Value 'continue' -Encoding ASCII
  $deadline = (Get-Date).AddSeconds(300)
  while ((Get-Date) -lt $deadline -and -not $currentCdb.HasExited) { Start-Sleep -Milliseconds 250; $currentCdb.Refresh() }
  if (-not $currentCdb.HasExited) { Finish (New-Failure 'trace_timeout' "CDB did not finish for $caseId" @("${caseId}:cdb_exit") '') 2 }
  Get-Content -LiteralPath $trace | Add-Content -LiteralPath $combinedTrace
  $deadline = (Get-Date).AddSeconds(180)
  while ((Get-Date) -lt $deadline -and -not (Test-Path -LiteralPath $aeResultPath)) { Start-Sleep -Milliseconds 250 }
  if (-not (Test-Path -LiteralPath $aeResultPath -PathType Leaf)) { Finish (New-Failure 'ae_result' "AE result missing for $caseId" @("${caseId}:AE_SINGLE_CASE_RESULT.json") '') 2 }
  $aeResult = Get-Content -LiteralPath $aeResultPath -Raw | ConvertFrom-Json
  if ($aeResult.status -ne 'ok' -or [int]$aeResult.project_bits_per_channel -ne 8) { Finish (New-Failure 'ae_result' "AE result is not successful 8bpc for $caseId" @("${caseId}:status=ok","${caseId}:project_bpc=8") ($aeResult | ConvertTo-Json -Compress)) 2 }
  if (-not (Test-Path -LiteralPath $aeLog -PathType Leaf) -or (Get-Content -LiteralPath $aeLog -Raw) -notmatch 'gpuAccelType=SOFTWARE') { Finish (New-Failure 'renderer' "Software evidence missing for $caseId" @("${caseId}:gpuAccelType=SOFTWARE") '') 2 }
  $deadline = (Get-Date).AddSeconds(60)
  while ((Get-Date) -lt $deadline -and (Get-Process -Id $aePid -ErrorAction SilentlyContinue)) { Start-Sleep -Milliseconds 250 }
  if (Get-Process -Id $aePid -ErrorAction SilentlyContinue) { Stop-Process -Id $aePid -Force -ErrorAction SilentlyContinue; Finish (New-Failure 'fresh_process' "AE did not exit after $caseId" @("${caseId}:process_exit") "pid=$aePid") 2 }
}

$parsed = Parse-Trace $combinedTrace
if ($parsed.status -eq 'answered' -and -not (Test-RawLogsComplete)) { $parsed = New-Failure 'raw_logs' 'retained raw logs are incomplete' @('raw_logs_complete') '' }
Finish $parsed $(if ($parsed.status -eq 'answered') { 0 } else { 2 })
'''


def filter_manifest(source: Path) -> dict:
    data = json.loads(source.read_text(encoding="utf-8"))
    if "cases" in data:
        data["cases"] = [row for row in data["cases"] if row.get("id") in CASES or row.get("case_id") in CASES]
    return data


def identity(case: str, pid: int, *, wrong_hash: bool = False, wrong_depth: bool = False) -> str:
    digest = "0" * 64 if wrong_hash else AEX_SHA256
    depth = 16 if wrong_depth else 8
    return f"request_id={REQUEST_ID} run_id=dg8fixture ae_pid={pid} module_base=0x7fffcd660000 aex_sha256={digest} renderer=Software project_bpc={depth} case_id={case}"


def fixture(*, missing_stage: bool = False, wrong_hash: bool = False, wrong_depth: bool = False, drift: bool = False, bad_derived: bool = False) -> str:
    lines: list[str] = []
    for index, case in enumerate(CASES):
        target = TARGETS[case]
        pid = 4101 + index
        common = identity(case, pid, wrong_hash=wrong_hash, wrong_depth=wrong_depth)
        chain_x, chain_y = target["chain"]
        anchor_addr = 0x1000 + CASES.index(case) * 0x10000
        residual_addr = anchor_addr + (68 if target["mode"] == "derived" else 0)
        if bad_derived and target["mode"] == "derived":
            residual_addr += 4
        anchor_text = f"0x{anchor_addr:x}"
        residual_text = f"0x{residual_addr:x}"
        lines.append(f"DG8_OUTPUT_ADDR_BOUND {common} mode={target['mode']} chain_x={chain_x} chain_y={chain_y} residual_x={target['residual'][0]} residual_y={target['residual'][1]} anchor_output_addr={anchor_text} residual_output_addr={residual_text}")
        for stage in STAGES:
            if missing_stage and case == "case_0015" and stage == "FIELD_READ_INPUT":
                continue
            stage_pid = 9999 if drift and case == "case_0029" and stage == "POST_STORE" else pid
            stage_common = identity(case, stage_pid, wrong_hash=wrong_hash, wrong_depth=wrong_depth)
            output = anchor_text if target["mode"] == "derived" else residual_text
            lines.append(f"DG8_{stage} {stage_common} x={chain_x} y={chain_y} output_addr={output} typed_rgba=01,02,03,ff")
        lines.append(f"DG8_RESIDUAL_DATA_STORE {common} x={target['residual'][0]} y={target['residual'][1]} output_addr={residual_text} store_addr={residual_text} anchor_output_addr={anchor_text} residual_output_addr={residual_text} expected_rgba_mac={','.join(map(str,target['mac']))} expected_rgba_windows={','.join(map(str,target['windows']))}")
        lines.append(f"DG8_DEPTH_SUMMARY {common} rva=1170870 hit_count=1")
        lines.append(f"DG8_DEPTH_SUMMARY {common} rva=1170c90 hit_count=0")
    return "\n".join(lines) + "\n"


def manifest() -> dict:
    return {
        "schema": 5,
        "kind": "olm_runtime_trace_request_package",
        "profile": "distancegradation-8bpc-three-case-residual-witness",
        "request_id": REQUEST_ID,
        "submission_status": "ready",
        "sendable": True,
        "exactness_claim": "forbidden",
        "aex_sha256": AEX_SHA256,
        "renderer": "Software",
        "project_bits_per_channel": 8,
        "process_contract": {"fresh_process_per_case": True, "shared_request_id": True, "shared_run_id": True},
        "stage_contract": {"stages": list(STAGES), "rvas": {"pf8_entry": "1170870", "field_read_input": "117098f", "source_read": "1170a09", "compose_pre_u8_scale": "1170c11", "u8_pre_store": "1170c20", "byte_stores": ["1170c29", "1170c30", "1170c37", "1170c3e"], "post_store": "1170c40"}},
        "cases": [
            {"case_id": case, "chain_xy": list(TARGETS[case]["chain"]), "required_residual_xy": list(TARGETS[case]["residual"]), "mode": TARGETS[case]["mode"], "optional_control_xy": list(TARGETS[case]["optional"]) if TARGETS[case]["optional"] else None, "optional_success_eligible": False, "mac_rgba": list(TARGETS[case]["mac"]), "windows_rgba": list(TARGETS[case]["windows"])}
            for case in CASES
        ],
        "runtime_actions": [{"request_id": REQUEST_ID, "status": "ready", "mode": "external-trace", "stop_condition": "Answered requires every primary chain/residual, case0001 anchor+68 exactly, three fresh PIDs, shared request/run ID, pinned hash, Software evidence, 8bpc, PF8>0, PF32=0, and complete raw logs. Optional controls never satisfy success."}],
    }


def write_zip(output: Path) -> str:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in PACKAGE.rglob("*") if p.is_file()):
            info = zipfile.ZipInfo(path.relative_to(PACKAGE).as_posix(), FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return hashlib.sha256(output.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if not SOURCE.is_dir():
        raise FileNotFoundError(SOURCE)
    if PACKAGE.exists():
        shutil.rmtree(PACKAGE)
    for directory in ("artifacts", "scripts", "request", "fixtures"):
        (PACKAGE / directory).mkdir(parents=True, exist_ok=True)
    (PACKAGE / "README_RUNTIME_TRACE.md").write_text(README, encoding="utf-8")
    (PACKAGE / "artifacts" / RUNNER_NAME).write_text(RUNNER, encoding="utf-8")
    (PACKAGE / "scripts" / QUEUE_NAME).write_text(QUEUE, encoding="utf-8")
    shutil.copy2(ROOT / "scripts/ae_render_single_case.jsx", PACKAGE / "scripts/ae_render_single_case.jsx")
    source_request = SOURCE / "request"
    (PACKAGE / "request/request_manifest.json").write_text(json.dumps(filter_manifest(source_request / "request_manifest.json"), indent=2) + "\n", encoding="utf-8")
    (PACKAGE / "request/reference_manifest.json").write_text(json.dumps(filter_manifest(source_request / "reference_manifest.json"), indent=2) + "\n", encoding="utf-8")
    for path in source_request.rglob("*"):
        if path.is_file() and path.name not in {"request_manifest.json", "reference_manifest.json"} and any(case in path.name for case in CASES):
            destination = PACKAGE / "request" / path.relative_to(source_request)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
    (PACKAGE / "runtime_trace_package_manifest.json").write_text(json.dumps(manifest(), indent=2) + "\n", encoding="utf-8")
    template = {"schema": "olmdg_8bpc_typed_residual_v4", "status": "answered | exact_bind_failure", "request_id": REQUEST_ID, "exactness_claim": False, "renderer": "Software", "project_bits_per_channel": 8, "cases": [{"case_id": case, "chain_xy": TARGETS[case]["chain"], "residual_xy": TARGETS[case]["residual"]} for case in CASES], "raw_logs": None}
    (PACKAGE / "RETURN_RUNTIME_TRACE_TEMPLATE.json").write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
    fixtures = {
        "complete_cdb_stdout.txt": fixture(),
        "missing_stage_cdb_stdout.txt": fixture(missing_stage=True),
        "identity_drift_cdb_stdout.txt": fixture(drift=True),
        "wrong_hash_cdb_stdout.txt": fixture(wrong_hash=True),
        "wrong_depth_cdb_stdout.txt": fixture(wrong_depth=True),
        "bad_derived_address_cdb_stdout.txt": fixture(bad_derived=True),
    }
    for name, text in fixtures.items():
        (PACKAGE / "fixtures" / name).write_text(text, encoding="utf-8")
    digest = write_zip(args.output)
    files = sorted(path.relative_to(PACKAGE).as_posix() for path in PACKAGE.rglob("*") if path.is_file())
    print(json.dumps({"status": "ok", "package": str(PACKAGE), "zip": str(args.output), "sha256": digest, "files": files}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
