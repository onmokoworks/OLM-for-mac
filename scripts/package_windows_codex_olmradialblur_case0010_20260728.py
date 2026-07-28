#!/usr/bin/env python3
"""Build the immutable OLMRadialBlur case_0010 Windows Codex child job."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.windows_witness.compiler import compile_witness
from tools.windows_witness.core import deterministic_zip


REQUEST_ID = "olmradialblur_case0010_same_run_upstream_sampler_20260728_r4"
JOB_ID = "olmradialblur_case0010_upstream_sampler_20260728_r4"
TARGET = (
    ROOT
    / "refs"
    / "handoffs"
    / "windows_codex_batch_jobs_20260728"
    / JOB_ID
)
SOURCE_REQUEST = (
    ROOT
    / "handoff"
    / "ae_pixel_validation_20260618"
    / "requests"
    / "ae_single_radialblur_case_0010_probe_20260701"
)
SOURCE_RENDERER = (
    ROOT
    / "refs"
    / "windows_witness_specs"
    / "olmradialblur_case0009_fullframe_postnorm_typed_common_core_20260713"
    / "renderer.jsx"
)
AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
INPUT_SHA256 = "7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4"
LEGACY_REFERENCE_SHA256 = "6d54dcfcd073b0cd1d90be2a9dcf020fb5d852a6a963e0246e521cc882d9960c"
CLAIM_BOUNDARY = "upstream_cells_and_direct_sampler_raw_only"
FINAL_WRITEBACK_BOUNDARY = "unresolved_later_job_required"
EFFECT_ARTIFACT_ROLE = "presence_only_not_output_exact"
WITNESS_ID = "olmradialblur-case0010-upstream-direct-sampler-v4"
PROJECT_ID = "case_0010_1920x1080_8bpc_frame0_software"
PLUGIN_ID = "OLMRadialBlur_2025"
RUNTIME_ID = "AfterFX_2025_desktop_CDB_x64"
DEFAULT_AEX_PATH = (
    "C:\\Program Files\\Adobe\\Common\\Plug-ins\\7.0\\MediaCore"
    "\\OLM\\OLMRadialBlur.aex"
)


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


IDENTITY_FIELDS = [
    "run_id",
    "ae_pid",
    "module_base",
    "aex_sha256",
    "project_bpc",
    "renderer",
    "case_id",
    "witness_id",
    "request_id",
    "project_id",
    "plugin_id",
    "runtime_id",
    "input_sha256",
    "claim_boundary",
    "final_writeback_boundary",
    "effect_artifact_role",
    "normalized_base",
    "accumulated_base",
    "validity_base",
]


EVENT_IDENTITY = (
    "run_id={{RUN_ID}} ae_pid={{AE_PID}} module_base={{MODULE_BASE}} "
    "aex_sha256={{AEX_SHA256}} project_bpc={{PROJECT_BPC}} "
    "renderer={{RENDERER}} case_id={{CASE_ID}} "
    "witness_id={{CASE_VALUE:witness_id}} "
    "request_id={{CASE_VALUE:request_id}} "
    "project_id={{CASE_VALUE:project_id}} "
    "plugin_id={{CASE_VALUE:plugin_id}} "
    "runtime_id={{CASE_VALUE:runtime_id}} "
    "input_sha256={{CASE_VALUE:input_sha256}} "
    "claim_boundary={{CASE_VALUE:claim_boundary}} "
    "final_writeback_boundary={{CASE_VALUE:final_writeback_boundary}} "
    "effect_artifact_role={{CASE_VALUE:effect_artifact_role}}"
)


CELL_EXPR = {
    "00": "(0n844*0n1800+0n1603)",
    "10": "(0n844*0n1800+0n1604)",
    "01": "(0n845*0n1800+0n1603)",
    "11": "(0n845*0n1800+0n1604)",
}


def rgba_reads(base: str, cell: str) -> str:
    index = CELL_EXPR[cell]
    return ",".join(
        f"dwo({base}+{index}*0n16+0n{offset})" for offset in (0, 4, 8, 12)
    )


def scalar_read(base: str, cell: str) -> str:
    return f"dwo({base}+{CELL_EXPR[cell]}*0n4)"


NORMALIZED_FIELDS = (
    "hook=0x4df0 polar_width=1800 "
    "cell00_id=1603,844 cell10_id=1604,844 "
    "cell01_id=1603,845 cell11_id=1604,845 "
    "row_origin=0 column_origin=0 stride=1800 "
    "cell00_row=844 cell00_column=1603 "
    "cell10_row=844 cell10_column=1604 "
    "cell01_row=845 cell01_column=1603 "
    "cell11_row=845 cell11_column=1604 "
    "normalized_base=%p accumulated_base=%p validity_base=%p "
    "cell00_normalized_address=%p cell10_normalized_address=%p "
    "cell01_normalized_address=%p cell11_normalized_address=%p "
    "cell00_accumulated_address=%p cell10_accumulated_address=%p "
    "cell01_accumulated_address=%p cell11_accumulated_address=%p "
    "cell00_validity_address=%p cell10_validity_address=%p "
    "cell01_validity_address=%p cell11_validity_address=%p "
    "cell00_f250_rgba=%08x,%08x,%08x,%08x "
    "cell10_f250_rgba=%08x,%08x,%08x,%08x "
    "cell01_f250_rgba=%08x,%08x,%08x,%08x "
    "cell11_f250_rgba=%08x,%08x,%08x,%08x "
    "cell00_f252=%08x cell10_f252=%08x cell01_f252=%08x cell11_f252=%08x "
    "cell00_normalized_rgba=%08x,%08x,%08x,%08x "
    "cell10_normalized_rgba=%08x,%08x,%08x,%08x "
    "cell01_normalized_rgba=%08x,%08x,%08x,%08x "
    "cell11_normalized_rgba=%08x,%08x,%08x,%08x "
    "same_run=1"
)


NORMALIZED_ARGS = ",".join(
    [
        "poi(@rsi+38)",
        "poi(@rsi+3c940)",
        "poi(@rsi+3c948)",
        *(
            f"poi(@rsi+38)+{CELL_EXPR[cell]}*0n16"
            for cell in CELL_EXPR
        ),
        *(
            f"poi(@rsi+3c940)+{CELL_EXPR[cell]}*0n16"
            for cell in CELL_EXPR
        ),
        *(
            f"poi(@rsi+3c948)+{CELL_EXPR[cell]}*0n4"
            for cell in CELL_EXPR
        ),
        *(rgba_reads("poi(@rsi+3c940)", cell) for cell in CELL_EXPR),
        *(scalar_read("poi(@rsi+3c948)", cell) for cell in CELL_EXPR),
        *(rgba_reads("poi(@rsi+38)", cell) for cell in CELL_EXPR),
    ]
)


SAMPLER_FIELDS = (
    "hook=0x4eb9/0x4ec8 witness_x=1614 witness_y=6 "
    "sample_x_f32=%08x sample_y_f32=%08x polar_width=1800 "
    "cell00_id=1603,844 cell10_id=1604,844 "
    "cell01_id=1603,845 cell11_id=1604,845 "
    "normalized_base=%p accumulated_base=%p validity_base=%p "
    "sampler_result_rgba_f32=%08x,%08x,%08x,%08x "
    "cell00_f250_rgba=%08x,%08x,%08x,%08x "
    "cell10_f250_rgba=%08x,%08x,%08x,%08x "
    "cell01_f250_rgba=%08x,%08x,%08x,%08x "
    "cell11_f250_rgba=%08x,%08x,%08x,%08x "
    "cell00_f252=%08x cell10_f252=%08x cell01_f252=%08x cell11_f252=%08x "
    "cell00_normalized_rgba=%08x,%08x,%08x,%08x "
    "cell10_normalized_rgba=%08x,%08x,%08x,%08x "
    "cell01_normalized_rgba=%08x,%08x,%08x,%08x "
    "cell11_normalized_rgba=%08x,%08x,%08x,%08x "
    "sampler_result_address=%p same_run=1"
)


SAMPLER_ARGS = ",".join(
    [
        "@$t2",
        "@$t3",
        "@$t4",
        "@$t5",
        "@$t6",
        "dwo(@$t0)",
        "dwo(@$t0+4)",
        "dwo(@$t0+8)",
        "dwo(@$t0+c)",
        *(rgba_reads("@$t5", cell) for cell in CELL_EXPR),
        *(scalar_read("@$t6", cell) for cell in CELL_EXPR),
        *(rgba_reads("@$t4", cell) for cell in CELL_EXPR),
        "@$t0",
    ]
)


CDB_TEMPLATE = f""".effmach amd64
.expr /s masm
sxi 80000003
.logopen /t "{{{{TRACE_PATH}}}}"
bp {{{{ADDRESS:normalization_done}}}} ".printf \\"RB10_NORMALIZED {EVENT_IDENTITY} {NORMALIZED_FIELDS}\\\\n\\",{NORMALIZED_ARGS};bc @$bpnum;gc"
bp {{{{ADDRESS:sampler_call}}}} ".if (@ebx==0n1614 && @r15d==0n6) {{r @$t0=@rdi;r @$t1=@rsi;r @$t2=dwo(@rsp+20);r @$t3=dwo(@rsp+28);r @$t4=poi(@rsi+38);r @$t5=poi(@rsi+3c940);r @$t6=poi(@rsi+3c948)}};gc"
bp {{{{ADDRESS:sampler_return}}}} ".if (@ebx==0n1614 && @r15d==0n6) {{.printf \\"RB10_SAMPLER_OUTPUT {EVENT_IDENTITY} {SAMPLER_FIELDS}\\\\n\\",{SAMPLER_ARGS};bc @$bpnum}};gc"
.echo RB10_CASE0010_BREAKPOINTS_ARMED
g
"""


CONTROL_COPY_ANCHOR = (
    '        var footage = importFootage(inputPath);\n'
)
CONTROL_COPY_INSERT = """        var footage = importFootage(inputPath);
        var noEffectControlPath = outputDir + "/case_0010_no_effect_control.png";
        var noEffectControl = new File(noEffectControlPath);
        if (noEffectControl.exists) {
            noEffectControl.remove();
        }
        if (!(new File(inputPath)).copy(noEffectControlPath)) {
            throw new Error("could not retain raw before-effects no-effect fixture control");
        }
        appendText(logPath, "raw_no_effect_fixture_control=" + noEffectControlPath + "\\n");
"""


FAIL_CLOSED_RUNNER = r"""param(
  [string]$PackageRoot = $PSScriptRoot,
  [string]$AexPath = 'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\OLMRadialBlur.aex',
  [string]$AfterFxPath = '',
  [string]$CdbPath = ''
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$requestId = 'olmradialblur_case0010_same_run_upstream_sampler_20260728_r4'
$claimBoundary = 'upstream_cells_and_direct_sampler_raw_only'
$finalWritebackBoundary = 'unresolved_later_job_required'
$effectArtifactRole = 'presence_only_not_output_exact'
$evidenceRoot = Join-Path $PackageRoot 'evidence'
$workRoot = Join-Path $PackageRoot 'work_r4'
$innerRunner = Join-Path $PackageRoot 'artifacts\run_witness.ps1'
$contractPath = Join-Path $PackageRoot 'witness-contract.json'
$stdoutPath = Join-Path $evidenceRoot 'INNER_RUNNER_STDOUT.txt'
$stderrPath = Join-Path $evidenceRoot 'INNER_RUNNER_STDERR.txt'
$statusPath = Join-Path $evidenceRoot 'CHILD_STATUS.json'
$innerStatusEvidence = Join-Path $evidenceRoot 'INNER_VALIDATION_STATUS.json'
$ownedRegistryPath = Join-Path $evidenceRoot 'OWNED_PROCESS_REGISTRY.json'
$cleanupPath = Join-Path $evidenceRoot 'OWNERSHIP_CLEANUP.json'
$runner = $null
$owned = @{}
$cleanupUnresolved = $false
$cleanupDetails = @()
$exitCode = 2
$startedAt = Get-Date

function Write-JsonSafely([string]$Path, [object]$Value) {
  try {
    $Value | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $Path -Encoding UTF8 -ErrorAction Stop
    return $true
  } catch {
    return $false
  }
}

function New-Failure([string]$Stage, [string]$Reason) {
  [ordered]@{
    schema_version = 1
    status = 'exact_bind_failure'
    request_id = $requestId
    claim_boundary = $claimBoundary
    final_writeback_boundary = $finalWritebackBoundary
    effect_artifact_role = $effectArtifactRole
    failure = [ordered]@{
      stage = $Stage
      reason = $Reason
      missing_fields = @('narrow_upstream_sampler_witness')
    }
  }
}

function Get-ProcessRows {
  try {
    return @(Get-CimInstance Win32_Process -ErrorAction Stop)
  } catch {
    return @()
  }
}

function Register-OwnedDescendants {
  if ($null -eq $runner) { return }
  $rows = @(Get-ProcessRows)
  $descendants = @([int]$runner.Id)
  $changed = $true
  while ($changed) {
    $changed = $false
    foreach ($row in $rows) {
      $pidValue = [int]$row.ProcessId
      if ($descendants -contains $pidValue) { continue }
      if ($descendants -contains [int]$row.ParentProcessId) {
        $descendants += $pidValue
        $changed = $true
      }
    }
  }
  foreach ($row in $rows) {
    $pidValue = [int]$row.ProcessId
    if (!($descendants -contains $pidValue)) { continue }
    $name = [string]$row.Name
    if ($name -ine 'cdb.exe') { continue }
    $path = [string]$row.ExecutablePath
    if ([string]::IsNullOrWhiteSpace($path)) { continue }
    $key = [string]$pidValue
    if (!$owned.ContainsKey($key)) {
      $owned[$key] = [ordered]@{
        pid = $pidValue
        parent_pid = [int]$row.ParentProcessId
        name = $name
        executable_path = $path
        creation_date = [string]$row.CreationDate
        ownership = 'descendant_of_package_runner'
      }
    }
  }
}

function Stop-RegisteredProcesses {
  foreach ($entry in @($owned.Values)) {
    try {
      $row = Get-CimInstance Win32_Process -Filter ("ProcessId=" + [int]$entry.pid) -ErrorAction Stop
      if ($null -eq $row) { continue }
      if ([string]$row.ExecutablePath -cne [string]$entry.executable_path) { continue }
      if ([string]$row.CreationDate -cne [string]$entry.creation_date) { continue }
      Stop-Process -Id ([int]$entry.pid) -Force -ErrorAction SilentlyContinue
      Wait-Process -Id ([int]$entry.pid) -Timeout 10 -ErrorAction SilentlyContinue
    } catch {
      # Cleanup is best effort and is restricted to the exact recorded PID,
      # executable path, and creation timestamp.
    }
  }
}

function Latest-OwnershipFile([string]$Name) {
  if (!(Test-Path -LiteralPath $workRoot -PathType Container)) { return $null }
  return Get-ChildItem -LiteralPath $workRoot -Recurse -File -Filter $Name -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTimeUtc -Descending |
    Select-Object -First 1
}

function Stop-ExactOwnedAfterFx {
  $contextFile = Latest-OwnershipFile 'launch_ownership_context.json'
  $sidecarFile = $null
  $context = $null
  if ($contextFile) {
    try {
      $context = Get-Content -LiteralPath $contextFile.FullName -Raw -ErrorAction Stop | ConvertFrom-Json
      Copy-Item -LiteralPath $contextFile.FullName -Destination (Join-Path $evidenceRoot 'LAUNCH_OWNERSHIP_CONTEXT.json') -Force -ErrorAction SilentlyContinue
      $candidateSidecar = Join-Path $contextFile.Directory.FullName 'owned_afterfx_process.json'
      if (Test-Path -LiteralPath $candidateSidecar -PathType Leaf) {
        $sidecarFile = Get-Item -LiteralPath $candidateSidecar -ErrorAction Stop
        Copy-Item -LiteralPath $sidecarFile.FullName -Destination (Join-Path $evidenceRoot 'OWNED_AFTERFX_PROCESS.json') -Force -ErrorAction SilentlyContinue
      }
      $expectedPrefix = '\OLM_Witness_' + ($requestId -replace '[^A-Za-z0-9_-]', '_') + '_'
      $taskName = [string]$context.scheduled_task_name
      $expectedTaskName = $expectedPrefix + ([string]$context.run_id -replace '[^A-Za-z0-9_-]', '_')
      $taskValid = (
        [string]$context.request_id -ceq $requestId -and
        ![string]::IsNullOrWhiteSpace([string]$context.run_id) -and
        $taskName -ceq $expectedTaskName
      )
      if ($taskValid) {
        & schtasks.exe /End /TN $taskName *> $null
        & schtasks.exe /Delete /TN $taskName /F *> $null
        $script:cleanupDetails += "exact_task_end_delete_attempted:$taskName"
      } else {
        $script:cleanupUnresolved = $true
        $script:cleanupDetails += 'task_name_mismatch_not_touched'
      }
      if (!$sidecarFile -and [bool]$context.task_run_requested) {
        $script:cleanupUnresolved = $true
        $script:cleanupDetails += 'missing_owned_pid_sidecar_no_process_touched'
      }
    } catch {
      $script:cleanupUnresolved = $true
      $script:cleanupDetails += ('context_validation_failed:' + $_.Exception.Message)
    }
  }
  if (!$sidecarFile) { return }
  if ($null -eq $context) {
    $script:cleanupUnresolved = $true
    $script:cleanupDetails += 'owned_pid_sidecar_without_context_no_process_touched'
    return
  }
  try {
    $ownedAe = Get-Content -LiteralPath $sidecarFile.FullName -Raw -ErrorAction Stop | ConvertFrom-Json
    if ([string]$ownedAe.request_id -cne $requestId) { throw 'request identity mismatch' }
    if ([string]$ownedAe.run_id -cne [string]$context.run_id) { throw 'run identity mismatch' }
    if ([string]$ownedAe.project_id -cne [string]$context.project_id) { throw 'project identity mismatch' }
    if ([string]$ownedAe.ownership -cne 'exact_fresh_scheduled_task_launch') { throw 'ownership kind mismatch' }
    if ([string]$ownedAe.scheduled_task_name -cne [string]$context.scheduled_task_name) { throw 'task identity mismatch' }
    if (@($context.prelaunch_afterfx | Where-Object { [int]$_.pid -eq [int]$ownedAe.pid }).Count -ne 0) { throw 'PID existed in prelaunch snapshot' }
    if ([DateTime]::Parse([string]$ownedAe.creation_time_utc).ToUniversalTime() -lt [DateTime]::Parse([string]$context.launch_window_start_utc).ToUniversalTime()) { throw 'creation time predates launch window' }
    $row = Get-CimInstance Win32_Process -Filter ("ProcessId=" + [int]$ownedAe.pid) -ErrorAction SilentlyContinue
    if ($null -eq $row) {
      $script:cleanupDetails += 'owned_afterfx_already_exited'
      return
    }
    $creation = ([DateTime]$row.CreationDate).ToUniversalTime().ToString('o')
    if ([string]$row.ExecutablePath -cne [string]$ownedAe.executable_path) { throw 'executable path mismatch' }
    if ($creation -cne [string]$ownedAe.creation_time_utc) { throw 'creation time mismatch (possible recycled PID)' }
    $currentHash = (Get-FileHash -LiteralPath ([string]$row.ExecutablePath) -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
    if ($currentHash -cne [string]$ownedAe.executable_sha256) { throw 'executable hash mismatch' }
    Stop-Process -Id ([int]$ownedAe.pid) -Force -ErrorAction Stop
    Wait-Process -Id ([int]$ownedAe.pid) -Timeout 10 -ErrorAction SilentlyContinue
    $script:cleanupDetails += ('exact_owned_afterfx_stopped:' + [string]$ownedAe.pid)
  } catch {
    $script:cleanupUnresolved = $true
    $script:cleanupDetails += ('owned_pid_revalidation_failed_no_process_touched:' + $_.Exception.Message)
  }
}

function Latest-RunDirectory {
  if (!(Test-Path -LiteralPath $workRoot -PathType Container)) { return $null }
  return @(
    Get-ChildItem -LiteralPath $workRoot -Directory -ErrorAction Stop |
      Sort-Object LastWriteTimeUtc -Descending
  ) | Select-Object -First 1
}

try {
  New-Item -ItemType Directory -Force -Path $evidenceRoot -ErrorAction Stop | Out-Null
  New-Item -ItemType Directory -Force -Path $workRoot -ErrorAction Stop | Out-Null
  if (!(Test-Path -LiteralPath $innerRunner -PathType Leaf)) {
    throw "missing package-owned inner runner: $innerRunner"
  }
  if (!(Test-Path -LiteralPath $contractPath -PathType Leaf)) {
    throw "missing witness contract: $contractPath"
  }
  $arguments = @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-File', ('"' + $innerRunner + '"'),
    '-PackageRoot', ('"' + $PackageRoot + '"'),
    '-WorkRoot', ('"' + $workRoot + '"')
  )
  if ($AexPath) { $arguments += @('-AexPath', ('"' + $AexPath + '"')) }
  if ($AfterFxPath) { $arguments += @('-AfterFxPath', ('"' + $AfterFxPath + '"')) }
  if ($CdbPath) { $arguments += @('-CdbPath', ('"' + $CdbPath + '"')) }
  $env:WINDOWS_WITNESS_DIRECT_R = '1'
  $runner = Start-Process -FilePath 'powershell.exe' -ArgumentList $arguments `
    -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath `
    -PassThru -WindowStyle Hidden -ErrorAction Stop
  while (!$runner.HasExited) {
    Register-OwnedDescendants
    Start-Sleep -Milliseconds 250
    $runner.Refresh()
  }
  Register-OwnedDescendants
  $runDirectory = Latest-RunDirectory
  if ($null -eq $runDirectory) {
    throw "inner runner emitted no package-owned run directory; exit=$($runner.ExitCode)"
  }
  $innerStatus = Join-Path $runDirectory.FullName 'validation_status.json'
  if (!(Test-Path -LiteralPath $innerStatus -PathType Leaf)) {
    throw "inner runner emitted no validation_status.json; exit=$($runner.ExitCode)"
  }
  Copy-Item -LiteralPath $innerStatus -Destination $innerStatusEvidence -Force -ErrorAction Stop
  $parsed = Get-Content -LiteralPath $innerStatus -Raw -ErrorAction Stop | ConvertFrom-Json
  if ($runner.ExitCode -ne 0 -or [string]$parsed.status -cne 'answered') {
    $reason = "inner runner terminal status=$([string]$parsed.status) exit=$($runner.ExitCode)"
    Write-JsonSafely $statusPath (New-Failure 'inner_runner' $reason) | Out-Null
    $exitCode = 2
  } else {
    $answered = [ordered]@{
      schema_version = 1
      status = 'answered'
      request_id = $requestId
      claim_boundary = $claimBoundary
      answered_meaning = 'upstream_cells_and_direct_sampler_raw_witness_only'
      final_writeback_boundary = $finalWritebackBoundary
      effect_artifact_role = $effectArtifactRole
      output_world_exact = $false
      export_pixel_classified = $false
      ae_exact = $false
      later_job_required = $true
      inner_validation_status = $innerStatusEvidence
    }
    if (!(Write-JsonSafely $statusPath $answered)) {
      throw "could not publish direct CHILD_STATUS.json evidence"
    }
    $exitCode = 0
  }
} catch {
  try {
    if (!(Test-Path -LiteralPath $evidenceRoot -PathType Container)) {
      New-Item -ItemType Directory -Force -Path $evidenceRoot -ErrorAction Stop | Out-Null
    }
  } catch {}
  Write-JsonSafely $statusPath (New-Failure 'top_level_exception' $_.Exception.Message) | Out-Null
  try {
    Add-Content -LiteralPath $stderrPath -Value ("top_level_exception=" + $_.Exception.Message) -Encoding UTF8 -ErrorAction SilentlyContinue
  } catch {}
  $exitCode = 2
} finally {
  Register-OwnedDescendants
  if ($runner -and !$runner.HasExited) {
    try { Stop-Process -Id $runner.Id -Force -ErrorAction SilentlyContinue } catch {}
    try { Wait-Process -Id $runner.Id -Timeout 10 -ErrorAction SilentlyContinue } catch {}
  }
  Stop-RegisteredProcesses
  Stop-ExactOwnedAfterFx
  Write-JsonSafely $cleanupPath ([ordered]@{
    request_id = $requestId
    cleanup_unresolved = [bool]$cleanupUnresolved
    details = @($cleanupDetails)
    process_policy = 'stop only exact sidecar PID after request/task/path/hash/creation-time revalidation'
    missing_sidecar_policy = 'remove exact request task only; touch no AfterFX PID'
  }) | Out-Null
  if ($cleanupUnresolved) {
    $cleanupFailure = New-Failure 'ownership_cleanup' 'cleanup_unresolved; no ambiguous or user AfterFX PID was touched'
    $cleanupFailure['cleanup_unresolved'] = $true
    Write-JsonSafely $statusPath $cleanupFailure | Out-Null
    $exitCode = 2
  }
  Write-JsonSafely $ownedRegistryPath ([ordered]@{
    request_id = $requestId
    recorded_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    package_owned_processes = @($owned.Values)
    cleanup_scope = 'CDB descendants only; scheduled-task AfterFX requires the exact ownership sidecar'
  }) | Out-Null
  if (!(Test-Path -LiteralPath $statusPath -PathType Leaf)) {
    Write-JsonSafely $statusPath (New-Failure 'finalization' 'status evidence was not published') | Out-Null
    $exitCode = 2
  }
}

if (Test-Path -LiteralPath $statusPath -PathType Leaf) {
  Get-Content -LiteralPath $statusPath -Raw
}
exit $exitCode
"""


INNER_OWNERSHIP_STATE = r"""
$ownershipContextPath = Join-Path $work 'launch_ownership_context.json'
$ownershipSidecarPath = Join-Path $work 'owned_afterfx_process.json'
$ownershipCleanupPath = Join-Path $work 'ownership_cleanup.json'
$prelaunchAeSnapshot = @()
$launchWindowStartUtc = $null
$ownedAfterFx = $null
$ownedCdb = $null
$cleanupUnresolved = $false
$cleanupDetails = @()
$afterFxSha256 = $null
$projectIdentity = [string]$contract.cases[0].template_values.project_id
"""


INNER_GET_AE_STATE_OLD = r"""function Get-AfterFxState {
  @(Get-CimInstance Win32_Process -Filter "Name='AfterFX.exe'" -ErrorAction SilentlyContinue |
    Where-Object {
      $_.ExecutablePath -and
      [IO.Path]::GetFullPath($_.ExecutablePath) -ieq $AfterFxPath
    } |
    ForEach-Object {
      [ordered]@{pid=[int]$_.ProcessId; parent_pid=[int]$_.ParentProcessId; session_id=[int]$_.SessionId; path=$_.ExecutablePath; command_line=$_.CommandLine}
    })
}
"""


INNER_GET_AE_STATE_NEW = r"""function Get-AfterFxState {
  @(Get-CimInstance Win32_Process -Filter "Name='AfterFX.exe'" -ErrorAction SilentlyContinue |
    Where-Object {
      $_.ExecutablePath -and
      [IO.Path]::GetFullPath($_.ExecutablePath) -ieq $AfterFxPath
    } |
    ForEach-Object {
      [ordered]@{
        pid = [int]$_.ProcessId
        parent_pid = [int]$_.ParentProcessId
        session_id = [int]$_.SessionId
        path = [string]$_.ExecutablePath
        command_line = [string]$_.CommandLine
        creation_time_utc = ([DateTime]$_.CreationDate).ToUniversalTime().ToString('o')
      }
    })
}
"""


INNER_OWNERSHIP_FUNCTIONS = r"""
function Write-OwnershipJson([string]$path, [object]$value) {
  $value | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $path -Encoding UTF8 -ErrorAction Stop
}

function Publish-LaunchOwnershipContext([bool]$taskRunRequested) {
  Write-OwnershipJson $ownershipContextPath ([ordered]@{
    schema_version = 1
    request_id = [string]$contract.request_id
    run_id = $runId
    project_id = $projectIdentity
    scheduled_task_name = $scheduledTaskName
    scheduled_task_name_prefix = ('\OLM_Witness_' + ([string]$contract.request_id -replace '[^A-Za-z0-9_-]', '_') + '_')
    task_run_requested = $taskRunRequested
    launch_window_start_utc = $launchWindowStartUtc
    afterfx_path = $AfterFxPath
    afterfx_sha256 = $afterFxSha256
    queue_sha256 = $queueHash
    queue_path = $normalizedQueuePath
    prelaunch_afterfx = @($prelaunchAeSnapshot)
    cleanup_contract = 'exact_task_and_exact_sidecar_pid_only'
  })
}

function Publish-OwnedAfterFx([object]$state) {
  $script:ownedAfterFx = [ordered]@{
    schema_version = 1
    ownership = 'exact_fresh_scheduled_task_launch'
    request_id = [string]$contract.request_id
    run_id = $runId
    project_id = $projectIdentity
    scheduled_task_name = $scheduledTaskName
    launch_window_start_utc = $launchWindowStartUtc
    pid = [int]$state.pid
    creation_time_utc = [string]$state.creation_time_utc
    executable_path = [string]$state.path
    executable_sha256 = $afterFxSha256
    queue_sha256 = $queueHash
    queue_path = $normalizedQueuePath
  }
  Write-OwnershipJson $ownershipSidecarPath $ownedAfterFx
}

function Remove-ExactWitnessTask {
  if (!$scheduledTaskCreated -or !$scheduledTaskName) { return }
  $expected = '\OLM_Witness_' + ([string]$contract.request_id -replace '[^A-Za-z0-9_-]', '_') + '_' + ($runId -replace '[^A-Za-z0-9_-]', '_')
  if ($scheduledTaskName -cne $expected) {
    $script:cleanupUnresolved = $true
    $script:cleanupDetails += 'task_name_mismatch_not_touched'
    return
  }
  & schtasks.exe /End /TN $scheduledTaskName *> $null
  & schtasks.exe /Delete /TN $scheduledTaskName /F *> $null
  $script:cleanupDetails += ('exact_task_end_delete_attempted:' + $scheduledTaskName)
}

function Stop-ExactOwnedAfterFx {
  if ($null -eq $ownedAfterFx) {
    if ($launchStarted) {
      $script:cleanupUnresolved = $true
      $script:cleanupDetails += 'missing_owned_pid_sidecar_no_afterfx_process_touched'
    }
    return
  }
  try {
    $sidecar = Get-Content -LiteralPath $ownershipSidecarPath -Raw -ErrorAction Stop | ConvertFrom-Json
    if ([string]$sidecar.request_id -cne [string]$contract.request_id) { throw 'request identity mismatch' }
    if ([string]$sidecar.run_id -cne $runId) { throw 'run identity mismatch' }
    if ([string]$sidecar.project_id -cne $projectIdentity) { throw 'project identity mismatch' }
    if ([string]$sidecar.scheduled_task_name -cne $scheduledTaskName) { throw 'task identity mismatch' }
    if ([string]$sidecar.ownership -cne 'exact_fresh_scheduled_task_launch') { throw 'ownership kind mismatch' }
    if (@($prelaunchAeSnapshot | Where-Object { [int]$_.pid -eq [int]$sidecar.pid }).Count -ne 0) { throw 'PID existed in prelaunch snapshot' }
    if ([DateTime]::Parse([string]$sidecar.creation_time_utc).ToUniversalTime() -lt [DateTime]::Parse($launchWindowStartUtc).ToUniversalTime()) { throw 'creation time predates launch window' }
    $row = Get-CimInstance Win32_Process -Filter ("ProcessId=" + [int]$sidecar.pid) -ErrorAction SilentlyContinue
    if ($null -eq $row) {
      $script:cleanupDetails += 'owned_afterfx_already_exited'
      return
    }
    $creation = ([DateTime]$row.CreationDate).ToUniversalTime().ToString('o')
    if ([string]$row.ExecutablePath -cne [string]$sidecar.executable_path) { throw 'executable path mismatch' }
    if ($creation -cne [string]$sidecar.creation_time_utc) { throw 'creation time mismatch (possible recycled PID)' }
    $currentHash = (Get-FileHash -LiteralPath ([string]$row.ExecutablePath) -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
    if ($currentHash -cne [string]$sidecar.executable_sha256) { throw 'executable hash mismatch' }
    Stop-Process -Id ([int]$sidecar.pid) -Force -ErrorAction Stop
    Wait-Process -Id ([int]$sidecar.pid) -Timeout 10 -ErrorAction SilentlyContinue
    $script:cleanupDetails += ('exact_owned_afterfx_stopped:' + [string]$sidecar.pid)
  } catch {
    $script:cleanupUnresolved = $true
    $script:cleanupDetails += ('owned_pid_revalidation_failed_no_process_touched:' + $_.Exception.Message)
  }
}

function Publish-OwnedCdb {
  $row = Get-CimInstance Win32_Process -Filter ("ProcessId=" + [int]$cdb.Id) -ErrorAction SilentlyContinue
  if ($null -eq $row -or [string]::IsNullOrWhiteSpace([string]$row.ExecutablePath)) {
    $script:cleanupUnresolved = $true
    $script:cleanupDetails += 'cdb_ownership_sidecar_unavailable'
    return
  }
  $script:ownedCdb = [ordered]@{
    ownership = 'direct_child_start_process'
    request_id = [string]$contract.request_id
    run_id = $runId
    pid = [int]$row.ProcessId
    creation_time_utc = ([DateTime]$row.CreationDate).ToUniversalTime().ToString('o')
    executable_path = [string]$row.ExecutablePath
    executable_sha256 = (Get-FileHash -LiteralPath ([string]$row.ExecutablePath) -Algorithm SHA256).Hash.ToLowerInvariant()
  }
  Write-OwnershipJson (Join-Path $work 'owned_cdb_process.json') $ownedCdb
}
"""


INNER_STOP_OLD = r"""  if ($launch -and !$launch.HasExited) { Stop-Process -Id $launch.Id -Force -ErrorAction SilentlyContinue }
  foreach ($retry in @($queueRetryProcesses)) {
    if ($retry -and !$retry.HasExited) { Stop-Process -Id $retry.Id -Force -ErrorAction SilentlyContinue }
  }
  if ($launchStarted) {
    foreach ($state in @(Get-AfterFxState)) {
      Stop-Process -Id $state.pid -Force -ErrorAction SilentlyContinue
      Wait-Process -Id $state.pid -Timeout 10 -ErrorAction SilentlyContinue
    }
  }
  if ($scheduledTaskCreated -and $scheduledTaskName) {
    & schtasks.exe /Delete /TN $scheduledTaskName /F *> $null
  }
  if ($dispatchScheduledTaskCreated -and $dispatchScheduledTaskName) {
    & schtasks.exe /Delete /TN $dispatchScheduledTaskName /F *> $null
  }
"""


INNER_STOP_NEW = r"""  Remove-ExactWitnessTask
  Stop-ExactOwnedAfterFx
  Write-OwnershipJson $ownershipCleanupPath ([ordered]@{
    request_id = [string]$contract.request_id
    run_id = $runId
    cleanup_unresolved = [bool]$cleanupUnresolved
    details = @($cleanupDetails)
    policy = 'no AfterFX process is stopped without exact sidecar revalidation'
  })
"""


INNER_STOP_CDB_OLD = r"""function Stop-CdbCapture {
  if ($cdb -and !$cdb.HasExited) {
    Stop-Process -Id $cdb.Id -Force -ErrorAction SilentlyContinue
  }
  if ($cdb) { Wait-Process -Id $cdb.Id -Timeout 10 -ErrorAction SilentlyContinue }
}
"""


INNER_STOP_CDB_NEW = r"""function Stop-CdbCapture {
  if (!$cdb -or $cdb.HasExited) { return }
  if ($null -eq $ownedCdb) {
    $script:cleanupUnresolved = $true
    $script:cleanupDetails += 'missing_cdb_ownership_sidecar_no_process_touched'
    return
  }
  try {
    $row = Get-CimInstance Win32_Process -Filter ("ProcessId=" + [int]$ownedCdb.pid) -ErrorAction SilentlyContinue
    if ($null -eq $row) { return }
    $creation = ([DateTime]$row.CreationDate).ToUniversalTime().ToString('o')
    if ([string]$row.ExecutablePath -cne [string]$ownedCdb.executable_path) { throw 'CDB executable path mismatch' }
    if ($creation -cne [string]$ownedCdb.creation_time_utc) { throw 'CDB creation mismatch (possible recycled PID)' }
    $currentHash = (Get-FileHash -LiteralPath ([string]$row.ExecutablePath) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($currentHash -cne [string]$ownedCdb.executable_sha256) { throw 'CDB executable hash mismatch' }
    Stop-Process -Id ([int]$ownedCdb.pid) -Force -ErrorAction Stop
    Wait-Process -Id ([int]$ownedCdb.pid) -Timeout 10 -ErrorAction SilentlyContinue
  } catch {
    $script:cleanupUnresolved = $true
    $script:cleanupDetails += ('owned_cdb_revalidation_failed_no_process_touched:' + $_.Exception.Message)
  }
}
"""


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label} anchor count is {count}, expected 1")
    return text.replace(old, new, 1)


def patch_inner_runner(package_dir: Path) -> None:
    path = package_dir / "artifacts" / "run_witness.ps1"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "  [string]$AexPath = '',\n",
        "  [string]$AexPath = '"
        + DEFAULT_AEX_PATH
        + "',\n",
        "inner default AEX path",
    )
    text = replace_once(
        text,
        "$fridaAnsweredCases = @()\n",
        "$fridaAnsweredCases = @()\n" + INNER_OWNERSHIP_STATE,
        "ownership state",
    )
    text = replace_once(
        text,
        INNER_GET_AE_STATE_OLD,
        INNER_GET_AE_STATE_NEW,
        "Get-AfterFxState",
    )
    text = replace_once(
        text,
        "function Stop-WitnessProcesses {\n",
        INNER_OWNERSHIP_FUNCTIONS + "\nfunction Stop-WitnessProcesses {\n",
        "ownership functions",
    )
    text = replace_once(
        text, INNER_STOP_OLD, INNER_STOP_NEW, "broad AE cleanup"
    )
    text = replace_once(
        text, INNER_STOP_CDB_OLD, INNER_STOP_CDB_NEW, "exact CDB cleanup"
    )
    text = replace_once(
        text,
        "  Stop-WitnessProcesses\n"
        "  $captureDiagnostics | ConvertTo-Json",
        "  Stop-WitnessProcesses\n"
        "  if ($cleanupUnresolved) {\n"
        "    if ([string]$body.status -ceq 'answered') {\n"
        "      $body = Failure 'ownership_cleanup' 'cleanup_unresolved; no "
        "ambiguous or user AfterFX PID was touched' "
        "@('exact_owned_afterfx_cleanup') ''\n"
        "    } else {\n"
        "      $body.failure | Add-Member -NotePropertyName cleanup_unresolved "
        "-NotePropertyValue $true -Force\n"
        "    }\n"
        "    $body['cleanup_unresolved'] = $true\n"
        "  }\n"
        "  $captureDiagnostics | ConvertTo-Json",
        "Finish cleanup status",
    )
    text = replace_once(
        text,
        "if (Get-Process -Name AfterFX -ErrorAction SilentlyContinue) {\n"
        "  Finish (Failure 'desktop_launch' 'After Effects must be fully "
        "closed before this run' @('fresh_AfterFX_process') '') 2\n"
        "}\n",
        "",
        "global AE preflight",
    )
    text = replace_once(
        text,
        "$PackageRoot = (Get-Item -LiteralPath $PackageRoot).FullName\n"
        "$hash = (Get-FileHash -LiteralPath $AexPath -Algorithm SHA256).Hash.ToLowerInvariant()\n",
        "$PackageRoot = (Get-Item -LiteralPath $PackageRoot).FullName\n"
        "$afterFxSha256 = (Get-FileHash -LiteralPath $AfterFxPath -Algorithm SHA256).Hash.ToLowerInvariant()\n"
        "$prelaunchAeSnapshot = @(Get-AfterFxState)\n"
        "$hash = (Get-FileHash -LiteralPath $AexPath -Algorithm SHA256).Hash.ToLowerInvariant()\n",
        "prelaunch snapshot",
    )
    text = replace_once(
        text,
        "$directQueueLaunch = ([string]$env:WINDOWS_WITNESS_DIRECT_R -eq '1') "
        "-or ($transportKind -eq 'in_process_collector') -or "
        "($transportKind -eq 'frida')\n",
        "$directQueueLaunch = $true # package r4: one request-bound scheduled "
        "task, one ownership sidecar PID\n",
        "direct launch policy",
    )
    text = replace_once(
        text,
        "$scheduledTaskName = '\\OLM_Witness_' + ($runId -replace "
        "'[^A-Za-z0-9_-]', '_')\n",
        "$scheduledTaskName = '\\OLM_Witness_' + ([string]$contract.request_id "
        "-replace '[^A-Za-z0-9_-]', '_') + '_' + ($runId -replace "
        "'[^A-Za-z0-9_-]', '_')\n",
        "request-bound task name",
    )
    text = replace_once(
        text,
        "$scheduledTaskCreated = $true\n"
        "$taskOutput = & schtasks.exe /Run /TN $scheduledTaskName 2>&1\n",
        "$scheduledTaskCreated = $true\n"
        "$launchWindowStartUtc = (Get-Date).ToUniversalTime().ToString('o')\n"
        "Publish-LaunchOwnershipContext $false\n"
        "$taskOutput = & schtasks.exe /Run /TN $scheduledTaskName 2>&1\n",
        "launch context before task run",
    )
    text = replace_once(
        text,
        "$launchStarted = $true\n"
        "$deadline = (Get-Date).AddSeconds(180)\n"
        "$launchStates = @()\n"
        "while ((Get-Date) -lt $deadline) {\n"
        "  $launchStates = @(Get-AfterFxState)\n"
        "  if ($launchStates.Count -eq 1) { break }\n"
        "  if ($launchStates.Count -gt 1) {\n"
        "    Finish (Failure 'desktop_process_discovery' 'After Effects launch "
        "produced more than one candidate process before queue dispatch' "
        "@('one_desktop_AfterFX_process') ($launchStates | ConvertTo-Json "
        "-Compress)) 2\n"
        "  }\n"
        "  Start-Sleep -Milliseconds 250\n"
        "}\n",
        "$launchStarted = $true\n"
        "Publish-LaunchOwnershipContext $true\n"
        "$deadline = (Get-Date).AddSeconds(180)\n"
        "$launchStates = @()\n"
        "$prelaunchPids = @($prelaunchAeSnapshot | ForEach-Object { [int]$_.pid })\n"
        "while ((Get-Date) -lt $deadline) {\n"
        "  $launchStates = @(Get-AfterFxState | Where-Object {\n"
        "    $prelaunchPids -notcontains [int]$_.pid -and\n"
        "    [DateTime]::Parse([string]$_.creation_time_utc).ToUniversalTime() "
        "-ge [DateTime]::Parse($launchWindowStartUtc).ToUniversalTime() -and\n"
        "    ![string]::IsNullOrWhiteSpace([string]$_.command_line) -and\n"
        "    ([string]$_.command_line).IndexOf($normalizedQueuePath, "
        "[StringComparison]::OrdinalIgnoreCase) -ge 0\n"
        "  })\n"
        "  if ($launchStates.Count -eq 1) { break }\n"
        "  if ($launchStates.Count -gt 1) {\n"
        "    Finish (Failure 'desktop_process_discovery' 'More than one fresh "
        "After Effects candidate matched the request launch window; no PID is "
        "owned or stopped' @('one_exact_fresh_AfterFX_process') "
        "($launchStates | ConvertTo-Json -Compress)) 2\n"
        "  }\n"
        "  Start-Sleep -Milliseconds 250\n"
        "}\n",
        "fresh launch discovery",
    )
    text = replace_once(
        text,
        "$launch = Get-Process -Id ([int]$launchStates[0].pid) -ErrorAction SilentlyContinue\n",
        "Publish-OwnedAfterFx $launchStates[0]\n"
        "$launch = Get-Process -Id ([int]$launchStates[0].pid) -ErrorAction SilentlyContinue\n",
        "immediate ownership sidecar",
    )
    dispatch_start = text.index("$dispatchTaskOutput = @()\n")
    dispatch_end = text.index("$postDispatchStates = @(Get-AfterFxState)\n")
    dispatch_block = text[dispatch_start:dispatch_end]
    if dispatch_block.count("schtasks.exe /Create") != 1:
        raise RuntimeError("legacy dispatch scheduled-task block drifted")
    text = (
        text[:dispatch_start]
        + "$dispatchTaskOutput = @() # r4 has no secondary dispatch task\n"
        + text[dispatch_end:]
    )
    text = replace_once(
        text,
        "$renderAePid = $mainAePid\n"
        "if (!$directQueueLaunch) {\n"
        "  $queueStates = @(Get-AfterFxState | Where-Object { [int]$_.pid "
        "-ne $mainAePid })\n"
        "  if ($queueStates.Count -gt 1) {\n"
        "    Finish (Failure 'queue_process_binding' 'More than one AE process "
        "remained after the JSX dispatch' @('zero_or_one_queue_AfterFX_process') "
        "($queueStates | ConvertTo-Json -Compress)) 2\n"
        "  }\n"
        "  if ($queueStates.Count -eq 1) {\n"
        "    $renderAePid = [int]$queueStates[0].pid\n"
        "  }\n"
        "}\n",
        "$renderAePid = $mainAePid # exact sidecar-owned direct queue process\n",
        "secondary render process selection",
    )
    text = replace_once(
        text,
        "  $cdb = Start-Process -FilePath $CdbPath -ArgumentList "
        "$cdbArguments -RedirectStandardOutput $stdout "
        "-RedirectStandardError $stderr -NoNewWindow -PassThru\n",
        "  $cdb = Start-Process -FilePath $CdbPath -ArgumentList "
        "$cdbArguments -RedirectStandardOutput $stdout "
        "-RedirectStandardError $stderr -NoNewWindow -PassThru\n"
        "  Publish-OwnedCdb\n",
        "immediate CDB ownership sidecar",
    )
    text = replace_once(
        text,
        'Finish (Failure \'cdb_capture\' "CDB did not complete for $caseId; '
        'CDB was terminated and AfterFX was stopped"',
        'Finish (Failure \'cdb_capture\' "CDB did not complete for $caseId; '
        'CDB was terminated and exact-owned AfterFX cleanup was attempted"',
        "timeout wording",
    )
    if "foreach ($state in @(Get-AfterFxState))" in text:
        raise RuntimeError("global AfterFX cleanup survived ownership patch")
    path.write_text(text, encoding="utf-8", newline="\n")


HEX_RGBA_PATTERN = r"^(?:[0-9a-fA-F]{8},){3}[0-9a-fA-F]{8}$"
HEX_SCALAR_PATTERN = r"^[0-9a-fA-F]{8}$"
POINTER_PATTERN = (
    r"^(?!(?:0x)?(?i:0+|deadbeef|baadf00d|cccccccc|cdcdcdcd|"
    r"feeefeee|ffffffff)$)(?:0x)?(?=[0-9a-fA-F`]*[1-9a-fA-F])"
    r"[0-9a-fA-F`]+$"
)


def identity_constraints() -> dict[str, dict[str, str]]:
    return {
        "witness_id": {"equals": WITNESS_ID},
        "request_id": {"equals": REQUEST_ID},
        "project_id": {"equals": PROJECT_ID},
        "plugin_id": {"equals": PLUGIN_ID},
        "runtime_id": {"equals": RUNTIME_ID},
        "input_sha256": {"equals": INPUT_SHA256},
        "claim_boundary": {"equals": CLAIM_BOUNDARY},
        "final_writeback_boundary": {"equals": FINAL_WRITEBACK_BOUNDARY},
        "effect_artifact_role": {"equals": EFFECT_ARTIFACT_ROLE},
    }


def event(
    name: str,
    prefix: str,
    required: list[str],
    constraints: dict[str, dict[str, str]],
    relations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    row = {
        "name": name,
        "prefix": prefix,
        "cardinality": {"scope": "per_case", "min": 1, "max": 1},
        "required_fields": [*IDENTITY_FIELDS, *required],
        "field_constraints": {**identity_constraints(), **constraints},
    }
    if relations:
        row["field_relations"] = relations
    return row


def cell_address_relations() -> list[dict[str, Any]]:
    relations: list[dict[str, Any]] = []
    for cell in CELL_EXPR:
        for plane, base, element_size in (
            ("normalized", "normalized_base", 16),
            ("accumulated", "accumulated_base", 16),
            ("validity", "validity_base", 4),
        ):
            relations.append(
                {
                    "type": "address_arithmetic",
                    "address_field": f"cell{cell}_{plane}_address",
                    "base_field": base,
                    "row_field": f"cell{cell}_row",
                    "row_origin_field": "row_origin",
                    "column_field": f"cell{cell}_column",
                    "column_origin_field": "column_origin",
                    "stride_field": "stride",
                    "element_size": element_size,
                    "channel_offset": 0,
                }
            )
    return relations


def spec() -> dict[str, Any]:
    normalized_fields = [
        "hook",
        "polar_width",
        "cell00_id",
        "cell10_id",
        "cell01_id",
        "cell11_id",
        "row_origin",
        "column_origin",
        "stride",
        *(f"cell{cell}_row" for cell in CELL_EXPR),
        *(f"cell{cell}_column" for cell in CELL_EXPR),
        *(f"cell{cell}_normalized_address" for cell in CELL_EXPR),
        *(f"cell{cell}_accumulated_address" for cell in CELL_EXPR),
        *(f"cell{cell}_validity_address" for cell in CELL_EXPR),
        *(f"cell{cell}_f250_rgba" for cell in CELL_EXPR),
        *(f"cell{cell}_f252" for cell in CELL_EXPR),
        *(f"cell{cell}_normalized_rgba" for cell in CELL_EXPR),
        "same_run",
    ]
    normalized_constraints: dict[str, dict[str, str]] = {
        "hook": {"equals": "0x4df0"},
        "polar_width": {"equals": "1800"},
        "cell00_id": {"equals": "1603,844"},
        "cell10_id": {"equals": "1604,844"},
        "cell01_id": {"equals": "1603,845"},
        "cell11_id": {"equals": "1604,845"},
        "row_origin": {"equals": "0"},
        "column_origin": {"equals": "0"},
        "stride": {"equals": "1800"},
        "normalized_base": {"pattern": POINTER_PATTERN},
        "accumulated_base": {"pattern": POINTER_PATTERN},
        "validity_base": {"pattern": POINTER_PATTERN},
        "same_run": {"equals": "1"},
    }
    for cell in CELL_EXPR:
        row, column = (
            ("844", "1603")
            if cell == "00"
            else ("844", "1604")
            if cell == "10"
            else ("845", "1603")
            if cell == "01"
            else ("845", "1604")
        )
        normalized_constraints[f"cell{cell}_row"] = {"equals": row}
        normalized_constraints[f"cell{cell}_column"] = {"equals": column}
        for plane in ("normalized", "accumulated", "validity"):
            normalized_constraints[f"cell{cell}_{plane}_address"] = {
                "pattern": POINTER_PATTERN
            }
        normalized_constraints[f"cell{cell}_f250_rgba"] = {
            "pattern": HEX_RGBA_PATTERN
        }
        normalized_constraints[f"cell{cell}_f252"] = {
            "pattern": HEX_SCALAR_PATTERN
        }
        normalized_constraints[f"cell{cell}_normalized_rgba"] = {
            "pattern": HEX_RGBA_PATTERN
        }

    sampler_fields = [
        "hook",
        "witness_x",
        "witness_y",
        "sample_x_f32",
        "sample_y_f32",
        "polar_width",
        "cell00_id",
        "cell10_id",
        "cell01_id",
        "cell11_id",
        "sampler_result_rgba_f32",
        *(f"cell{cell}_f250_rgba" for cell in CELL_EXPR),
        *(f"cell{cell}_f252" for cell in CELL_EXPR),
        *(f"cell{cell}_normalized_rgba" for cell in CELL_EXPR),
        "sampler_result_address",
        "same_run",
    ]
    sampler_constraints: dict[str, dict[str, str]] = {
        "hook": {"equals": "0x4eb9/0x4ec8"},
        "witness_x": {"equals": "1614"},
        "witness_y": {"equals": "6"},
        "sample_x_f32": {"equals": "44c87ade"},
        "sample_y_f32": {"equals": "44531452"},
        "polar_width": {"equals": "1800"},
        "cell00_id": {"equals": "1603,844"},
        "cell10_id": {"equals": "1604,844"},
        "cell01_id": {"equals": "1603,845"},
        "cell11_id": {"equals": "1604,845"},
        "normalized_base": {"pattern": POINTER_PATTERN},
        "accumulated_base": {"pattern": POINTER_PATTERN},
        "validity_base": {"pattern": POINTER_PATTERN},
        "sampler_result_rgba_f32": {"pattern": HEX_RGBA_PATTERN},
        "sampler_result_address": {"pattern": POINTER_PATTERN},
        "same_run": {"equals": "1"},
    }
    for cell in CELL_EXPR:
        sampler_constraints[f"cell{cell}_f250_rgba"] = {
            "pattern": HEX_RGBA_PATTERN
        }
        sampler_constraints[f"cell{cell}_f252"] = {
            "pattern": HEX_SCALAR_PATTERN
        }
        sampler_constraints[f"cell{cell}_normalized_rgba"] = {
            "pattern": HEX_RGBA_PATTERN
        }
    return {
        "schema_version": 1,
        "description": (
            "Fresh immutable Windows 2025 OLMRadialBlur tiny Rotation case_0010 "
            "(1614,6) same-run normalized-plane and direct inverse-sampler raw "
            "witness with required artifact presence. The before-effects PNG is "
            "returned as a checksum-bound raw no-effect fixture control; it is "
            "not represented as a live AE no-effect render. Final output-world "
            "writeback, exported pixel classification, alternate-path ownership, "
            "CLI exactness, and AE exactness remain unresolved and require a "
            "later job. Process cleanup is fail-closed rather than guaranteed: "
            "ambiguous ownership reports cleanup_unresolved and touches no AE PID."
        ),
        "request_id": REQUEST_ID,
        "run_id_prefix": "rb10upstreamr4",
        "queue": {
            "profile": "radialblur-case0010-upstream-direct-sampler",
            "plugin_area": "OLMRadialBlur tiny Rotation case_0010",
            "command": (
                "Run one pinned-AEX 8bpc Software render and capture the exact "
                "(1614,6) upstream planes and direct sampler raw values; retain "
                "the required effect-on artifact without classifying its pixel."
            ),
            "stop_condition": (
                "answered only when all four +0xf250/+0xf252/normalized cells, "
                "exact direct-sampler coordinates/result, pointer relations, "
                "effect-on artifact presence, and raw no-effect fixture control "
                "bind to one request/run identity. Answered does not resolve "
                "final writeback, export-pixel provenance, or AE/output exactness. "
                "Cleanup ambiguity is exact_bind_failure with cleanup_unresolved."
            ),
            "supersedes": [],
        },
        "plugin": {
            "name": "OLM RadialBlur",
            "module_filename": "OLMRadialBlur.aex",
            "aex_sha256": AEX_SHA256,
            "default_aex_path": DEFAULT_AEX_PATH,
        },
        "host": {
            "afterfx_path": (
                "C:\\Program Files\\Adobe\\Adobe After Effects 2025"
                "\\Support Files\\AfterFX.exe"
            ),
            "cdb_path": (
                "C:\\Program Files (x86)\\Windows Kits\\10"
                "\\Debuggers\\x64\\cdb.exe"
            ),
        },
        "project": {
            "bits_per_channel": 8,
            "renderer": "Software",
            "environment": {
                "OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT": "1",
                "OLM_AE_FORCE_SOFTWARE": "1",
            },
        },
        "renderer": {"source": "renderer.jsx"},
        "request_assets": {"source": "request"},
        "cdb": {
            "armed_marker": "RB10_CASE0010_BREAKPOINTS_ARMED",
            "arm_timeout_seconds": 60,
            "capture_timeout_seconds": 600,
        },
        "cases": [
            {
                "id": "case_0010",
                "bits_per_channel": 8,
                "cdb_template": "probe.cdb.in",
                "template_values": {
                    "witness_id": WITNESS_ID,
                    "request_id": REQUEST_ID,
                    "project_id": PROJECT_ID,
                    "plugin_id": PLUGIN_ID,
                    "runtime_id": RUNTIME_ID,
                    "input_sha256": INPUT_SHA256,
                    "legacy_reference_sha256": LEGACY_REFERENCE_SHA256,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "final_writeback_boundary": FINAL_WRITEBACK_BOUNDARY,
                    "effect_artifact_role": EFFECT_ARTIFACT_ROLE,
                },
                "addresses": {
                    "normalization_done": "0x4df0",
                    "sampler_call": "0x4eb9",
                    "sampler_return": "0x4ec8",
                },
                "exports": [
                    {
                        "source": "exports/{case_id}/case_0010.png",
                        "archive_path": (
                            "return/effect_on_artifact_presence_case_0010.png"
                        ),
                        "required": True,
                    },
                    {
                        "source": (
                            "exports/{case_id}/case_0010_no_effect_control.png"
                        ),
                        "archive_path": (
                            "return/raw_no_effect_fixture_control_case_0010.png"
                        ),
                        "required": True,
                    },
                ],
            }
        ],
        "validation": {
            "identity_fields": IDENTITY_FIELDS,
            "events": [
                event(
                    "normalized_cells",
                    "RB10_NORMALIZED",
                    normalized_fields,
                    normalized_constraints,
                    cell_address_relations(),
                ),
                event(
                    "sampler_output",
                    "RB10_SAMPLER_OUTPUT",
                    sampler_fields,
                    sampler_constraints,
                ),
            ],
        },
        "return_bundle": {
            "json_name": "RETURN_OLMRADIALBLUR_CASE0010_UPSTREAM.json",
            "zip_name": "RETURN_OLMRADIALBLUR_CASE0010_UPSTREAM.zip",
            "include_logs": [],
        },
    }


def prepare_sources(root: Path) -> Path:
    spec_root = root / "spec"
    request = spec_root / "request"
    shutil.copytree(SOURCE_REQUEST, request)
    request_manifest_path = request / "request_manifest.json"
    request_manifest = json.loads(
        request_manifest_path.read_text(encoding="utf-8-sig")
    )
    request_manifest["request_id"] = REQUEST_ID
    request_manifest["gate_kind"] = "windows_live_raw_witness_only"
    request_manifest["notes"] = [
        (
            "Fresh same-run upstream normalized-plane and direct-sampler raw "
            "witness; final writeback and exported-pixel classification remain "
            "unresolved."
        ),
        (
            "expected/case_0010.png is retained only as a legacy provenance "
            "fixture and is not an AE-exact target."
        ),
        (
            "input/case_0010_before_effects.png is returned byte-for-byte as "
            "the raw no-effect fixture control, not as a live AE no-effect render."
        ),
    ]
    request_manifest_path.write_bytes(canonical_json(request_manifest))
    renderer = SOURCE_RENDERER.read_text(encoding="utf-8")
    if renderer.count(CONTROL_COPY_ANCHOR) != 1:
        raise RuntimeError("renderer control-copy anchor drifted")
    renderer = renderer.replace(
        CONTROL_COPY_ANCHOR, CONTROL_COPY_INSERT, 1
    )
    (spec_root / "renderer.jsx").write_text(
        renderer, encoding="utf-8", newline="\n"
    )
    (spec_root / "probe.cdb.in").write_text(
        CDB_TEMPLATE, encoding="ascii", newline="\n"
    )
    spec_path = spec_root / "witness-spec.json"
    spec_path.write_bytes(canonical_json(spec()))
    return spec_path


def finalize_compiled_package(package_dir: Path, package_zip: Path) -> None:
    patch_inner_runner(package_dir)
    (package_dir / "run.ps1").write_text(
        FAIL_CLOSED_RUNNER, encoding="ascii", newline="\n"
    )
    readme_path = package_dir / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    readme = replace_once(
        readme,
        "Run from an interactive Windows desktop PowerShell session:\n\n"
        "```powershell\n"
        ".\\artifacts\\run_witness.ps1\n"
        "```\n",
        "From an interactive Windows desktop PowerShell session, run only the "
        "package-root `run.ps1` entrypoint.\n",
        "README root entrypoint",
    )
    readme += (
        "\nThe default installed AEX binding used by both entrypoints is "
        f"`{DEFAULT_AEX_PATH}`. Pass `-AexPath` only to override that exact "
        "installed location.\n"
    )
    readme += f"""

## Claim boundary

An `answered` result means only that the checksum- and identity-bound upstream
`+0xf250`, `+0xf252`, normalized `+0xe`, and direct sampler raw observations
were captured and the required effect-on and raw fixture-control artifacts were
present.

It does not resolve the final output-world writeback, classify the exported
pixel at `(1614,6)`, establish an alternate output path, or prove CLI/AE/output
exactness. The final-writeback boundary is `{FINAL_WRITEBACK_BOUNDARY}` and
requires a later separately grounded job. The effect-on PNG role is
`{EFFECT_ARTIFACT_ROLE}`.

The root entrypoint catches unexpected top-level failures and emits direct
`evidence/CHILD_STATUS.json` plus `evidence/OWNERSHIP_CLEANUP.json` evidence.
The scheduled task is uniquely bound to request and run identity. After Effects
is stopped only when its ownership sidecar still matches request, run, project,
task, PID, creation time, executable path, and executable hash. Missing or
ambiguous ownership never authorizes stopping an After Effects process; the
result instead becomes `exact_bind_failure` with `cleanup_unresolved=true`.
Pre-existing and concurrent user After Effects processes are never swept.
Cleanup is therefore fail-closed, not guaranteed. The entrypoint does not
change preferences, caches, or modal state.
"""
    readme_path.write_text(readme, encoding="utf-8", newline="\n")
    package_manifest_path = package_dir / "package-manifest.json"
    existing = json.loads(package_manifest_path.read_text(encoding="utf-8"))
    inventory: list[dict[str, Any]] = []
    for path in sorted(
        (
            path
            for path in package_dir.rglob("*")
            if path.is_file() and path != package_manifest_path
        ),
        key=lambda item: item.relative_to(package_dir).as_posix(),
    ):
        inventory.append(
            {
                "path": path.relative_to(package_dir).as_posix(),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    final_manifest = {
        "schema_version": 1,
        "kind": "windows_witness_generated_package",
        "request_id": REQUEST_ID,
        "contract": "witness-contract.json",
        "entrypoint": "run.ps1",
        "files": inventory,
        "queue": existing["queue"],
        "claim_boundary": CLAIM_BOUNDARY,
        "final_writeback_boundary": FINAL_WRITEBACK_BOUNDARY,
        "effect_artifact_role": EFFECT_ARTIFACT_ROLE,
    }
    package_manifest_path.write_bytes(canonical_json(final_manifest))
    deterministic_zip(package_dir, package_zip)


def build_bytes(work: Path) -> tuple[bytes, bytes, bytes]:
    spec_path = prepare_sources(work)
    package_dir = work / "compiled"
    package_zip = work / "package.zip"
    compile_witness(spec_path, package_dir, package_zip)
    finalize_compiled_package(package_dir, package_zip)
    package_bytes = package_zip.read_bytes()
    package_sha = sha256_bytes(package_bytes)
    manifest = {
        "schema": "windows_codex_batch_job_v1",
        "job_id": JOB_ID,
        "package": "package.zip",
        "package_sha256": package_sha,
        "entrypoint": "run.ps1",
        "failure_policy": "independent",
        "success_status": "answered",
        "failure_status": "exact_bind_failure",
        "request_id": REQUEST_ID,
        "description": (
            "Pinned OLMRadialBlur 2025 case_0010 (1614,6) upstream-plane and "
            "direct-sampler raw witness with required artifact presence. "
            "Final writeback/export-pixel classification remains unresolved; "
            "no output-, CLI-, or AE-exact claim. Cleanup is fail-closed, not "
            "guaranteed when ownership is ambiguous."
        ),
    }
    checksum = f"{package_sha}  package.zip\n".encode("ascii")
    return package_bytes, canonical_json(manifest), checksum


def build_target() -> dict[str, Any]:
    if TARGET.exists():
        raise RuntimeError(
            f"immutable target already exists: {TARGET}; use --verify"
        )
    with tempfile.TemporaryDirectory(prefix="rb10_windows_child_") as tmp:
        package_bytes, manifest_bytes, checksum_bytes = build_bytes(Path(tmp))
    TARGET.mkdir(parents=True)
    (TARGET / "package.zip").write_bytes(package_bytes)
    (TARGET / "job_manifest.json").write_bytes(manifest_bytes)
    (TARGET / "package.zip.sha256").write_bytes(checksum_bytes)
    return result()


def verify_target() -> dict[str, Any]:
    required = [
        TARGET / "package.zip",
        TARGET / "job_manifest.json",
        TARGET / "package.zip.sha256",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing immutable target files: {missing}")
    with tempfile.TemporaryDirectory(prefix="rb10_windows_verify_") as tmp:
        expected_package, expected_manifest, expected_checksum = build_bytes(
            Path(tmp)
        )
    observed = [
        (TARGET / "package.zip").read_bytes(),
        (TARGET / "job_manifest.json").read_bytes(),
        (TARGET / "package.zip.sha256").read_bytes(),
    ]
    expected = [expected_package, expected_manifest, expected_checksum]
    if observed != expected:
        raise RuntimeError("immutable target bytes drifted from deterministic build")
    manifest = json.loads(observed[1])
    if sha256_bytes(observed[0]) != manifest["package_sha256"]:
        raise RuntimeError("job manifest package SHA-256 does not bind package.zip")
    return result()


def result() -> dict[str, Any]:
    package = TARGET / "package.zip"
    manifest = json.loads(
        (TARGET / "job_manifest.json").read_text(encoding="utf-8")
    )
    return {
        "job_id": JOB_ID,
        "request_id": REQUEST_ID,
        "target": str(TARGET),
        "package_sha256": sha256_file(package),
        "package_size_bytes": package.stat().st_size,
        "entrypoint": manifest["entrypoint"],
        "status": "verified_immutable",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="rebuild in a temporary directory and compare every target byte",
    )
    args = parser.parse_args()
    output = verify_target() if args.verify else build_target()
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
