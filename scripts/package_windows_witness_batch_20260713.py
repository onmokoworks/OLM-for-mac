#!/usr/bin/env python3
"""Build a deterministic, one-click outer Windows witness batch."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "windows_witness_batch_20260713"
DEFAULT_OUTPUT_DIR = ROOT / "refs/runtime_trace_packages" / PACKAGE_NAME
DEFAULT_ZIP = DEFAULT_OUTPUT_DIR.with_suffix(".zip")
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)
DEFAULT_PRESET_ROOT_ENV = "OLM_WINDOWS_WITNESS_BATCH_DEFAULT_ROOT"
DEFAULT_PER_JOB_TIMEOUT_SECONDS = 3600
MIN_PER_JOB_TIMEOUT_SECONDS = 1
MAX_PER_JOB_TIMEOUT_SECONDS = 86400
DEFAULT_JOBS: tuple[dict[str, Any], ...] = (
    {
        "id": "olmblur_case0006_same_run_20260713",
        "script": ROOT / "scripts/package_windows_witness_olmblur_case0006_20260713.py",
        "archive": ROOT / "refs/runtime_trace_packages/windows_witness_olmblur_case0006_20260713.zip",
        "satisfies_request_ids": (
            "olmblur_case0006_same_run_internal_20260713",
        ),
    },
    {
        "id": "windows_witness_olmdistancegradation_8bpc_typed_boundary_20260713",
        "script": ROOT / "scripts/package_windows_witness_olmdistancegradation_8bpc_20260713.py",
        "archive": ROOT / "refs/runtime_trace_packages/windows_witness_olmdistancegradation_8bpc_20260713.zip",
        "satisfies_request_ids": (
            "olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712",
            "olmdistancegradation_8bpc_current_aex_depth_control_20260713",
        ),
    },
    {
        "id": "olmsmoother2_case0012_current_aex_20260713",
        "script": ROOT / "scripts/package_windows_witness_olmsmoother2_case0012_20260713.py",
        "archive": ROOT / "refs/runtime_trace_packages/windows_witness_olmsmoother2_case0012_20260713.zip",
        "satisfies_request_ids": (
            "olmsmoother2_case0012_live_config_binding_20260713",
            "olmsmoother2_current_aex_0012_typed_bind_read_20260710",
        ),
    },
    {
        "id": "windows_witness_olmdistancegradation_case0026_16bpc_livefield_20260713",
        "script": ROOT / "scripts/package_windows_witness_olmdistancegradation_case0026_20260713.py",
        "archive": ROOT / "refs/runtime_trace_packages/windows_witness_olmdistancegradation_case0026_20260713.zip",
        "satisfies_request_ids": (
            "olmdistancegradation_case0026_16bpc_livefield_source_witness_20260713",
        ),
    },
    {
        "id": "olmdirectionalblur_row755_20260713",
        "script": ROOT / "scripts/package_windows_witness_olmdirectionalblur_row755_20260713.py",
        "archive": ROOT / "refs/runtime_trace_packages/windows_witness_olmdirectionalblur_row755_20260713.zip",
        "satisfies_request_ids": (
            "olmdirectionalblur_alpha_fade_fullrender_row755_20260712",
        ),
    },
    {
        "id": "olmkirakira_mode3_live_gaussian_20260713",
        "script": ROOT / "scripts/package_windows_witness_olmkirakira_mode3_20260713.py",
        "archive": ROOT / "refs/runtime_trace_packages/windows_witness_olmkirakira_mode3_20260713.zip",
        "satisfies_request_ids": (),
    },
)

DEFAULT_SATISFIES_BY_ID = {
    str(job["id"]): tuple(str(value) for value in job.get("satisfies_request_ids", ()))
    for job in DEFAULT_JOBS
}


LAUNCHER = r'''param(
  [string]$WorkRoot = (Join-Path $PSScriptRoot 'batch_work'),
  [int]$PerJobTimeoutSeconds = 0,
  [switch]$PreflightOnly
)

$ErrorActionPreference = 'Stop'
$MinPerJobTimeoutSeconds = 1
$MaxPerJobTimeoutSeconds = 86400
$SessionId = (Get-Process -Id $PID).SessionId
$ManifestPath = Join-Path $PSScriptRoot 'batch-manifest.json'
$ReturnJson = Join-Path $PSScriptRoot 'windows_witness_batch_return.json'
$ReturnZip = Join-Path $PSScriptRoot 'windows_witness_batch_return.zip'
$Transcript = Join-Path $PSScriptRoot 'windows_witness_batch_launcher.log'

function Write-CanonicalJson([string]$Path, [object]$Value) {
  $Value | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Get-SessionProcessIds([string]$ProcessName) {
  @((Get-Process -Name $ProcessName -ErrorAction SilentlyContinue |
    Where-Object { $_.SessionId -eq $SessionId } |
    ForEach-Object { [int]$_.Id }) | Sort-Object)
}

function Append-Failure([string]$Current, [string]$Message) {
  if ($Current) { return $Current + '; ' + $Message }
  return $Message
}

function ConvertTo-NativeArgumentLiteral([string]$Value) {
  if ($null -eq $Value) { throw 'native argument value cannot be null' }
  if ($Value.Length -eq 0) { return '""' }
  if ($Value -notmatch '[\s"]') { return $Value }
  $builder = New-Object System.Text.StringBuilder
  [void]$builder.Append('"')
  $pendingBackslashes = 0
  foreach ($charValue in $Value.ToCharArray()) {
    if ($charValue -eq '\') {
      $pendingBackslashes += 1
      continue
    }
    if ($charValue -eq '"') {
      [void]$builder.Append('\', ($pendingBackslashes * 2) + 1)
      [void]$builder.Append('"')
      $pendingBackslashes = 0
      continue
    }
    if ($pendingBackslashes -gt 0) {
      [void]$builder.Append('\', $pendingBackslashes)
      $pendingBackslashes = 0
    }
    [void]$builder.Append($charValue)
  }
  if ($pendingBackslashes -gt 0) {
    [void]$builder.Append('\', $pendingBackslashes * 2)
  }
  [void]$builder.Append('"')
  return $builder.ToString()
}

function Get-ValidatedTimeoutSeconds([object]$Value, [string]$Label) {
  if ($null -eq $Value) { throw "$Label is missing" }
  try {
    $timeoutSeconds = [int]$Value
  } catch {
    throw "$Label must be an integer"
  }
  if ($timeoutSeconds -lt $MinPerJobTimeoutSeconds -or $timeoutSeconds -gt $MaxPerJobTimeoutSeconds) {
    throw "$Label must be between $MinPerJobTimeoutSeconds and $MaxPerJobTimeoutSeconds seconds"
  }
  return $timeoutSeconds
}

function Test-JobPreflight([object]$Job) {
  foreach ($label in @('default_aex_path', 'afterfx_path', 'cdb_path')) {
    $path = [string]$Job.$label
    if (!(Test-Path -LiteralPath $path -PathType Leaf)) {
      return "preflight missing $label for request_id $([string]$Job.request_id): $path"
    }
  }
  $actualHash = (Get-FileHash -LiteralPath ([string]$Job.default_aex_path) -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($actualHash -cne [string]$Job.aex_sha256) {
    return "preflight AEX SHA-256 mismatch for request_id $([string]$Job.request_id): actual=$actualHash"
  }
  return $null
}

function Assert-SafeZip([string]$ArchivePath) {
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $archive = [IO.Compression.ZipFile]::OpenRead($ArchivePath)
  try {
    $seen = @{}
    foreach ($entry in $archive.Entries) {
      $name = $entry.FullName
      if (!$name -or $name.Contains('\') -or $name.StartsWith('/') -or
          $name -match '^[A-Za-z]:' -or $name.Split('/') -contains '..') {
        throw "unsafe ZIP member: $name"
      }
      $folded = $name.ToLowerInvariant()
      if ($seen.ContainsKey($folded)) { throw "duplicate ZIP member on Windows: $name" }
      $seen[$folded] = $true
    }
  } finally {
    $archive.Dispose()
  }
}

function Try-FileSha256([string]$Path) {
  for ($attempt = 0; $attempt -lt 40; $attempt++) {
    try { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
    catch {
      if ($attempt -eq 39) { return $null }
      Start-Sleep -Milliseconds 250
    }
  }
  return $null
}

function File-Records([string]$Root, [string[]]$Patterns) {
  $records = @()
  foreach ($file in @(Get-ChildItem -LiteralPath $Root -Recurse -File -ErrorAction SilentlyContinue)) {
    $matches = $false
    foreach ($pattern in $Patterns) { if ($file.Name -like $pattern) { $matches = $true; break } }
    if (!$matches) { continue }
    $hash = Try-FileSha256 $file.FullName
    if (!$hash) { Write-Warning ("Skipping locked evidence file: " + $file.FullName); continue }
    $relative = $file.FullName.Substring($Root.Length).TrimStart([char[]]@('\','/')).Replace('\', '/')
    $records += [ordered]@{
      path = $relative
      size_bytes = [int64]$file.Length
      sha256 = $hash
    }
  }
  @($records | Sort-Object path)
}

if (!(Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { throw "missing batch manifest: $ManifestPath" }
$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$EffectivePerJobTimeoutSeconds = if ($PSBoundParameters.ContainsKey('PerJobTimeoutSeconds')) {
  Get-ValidatedTimeoutSeconds $PerJobTimeoutSeconds 'PerJobTimeoutSeconds'
} else {
  Get-ValidatedTimeoutSeconds $Manifest.per_job_timeout_seconds 'batch manifest per_job_timeout_seconds'
}
$PerJobTimeoutMilliseconds = [int]([int64]$EffectivePerJobTimeoutSeconds * 1000)
$BatchStarted = (Get-Date).ToUniversalTime().ToString('o')
$Results = @()
$Jobs = @($Manifest.jobs | Sort-Object order)
$PreflightById = @{}
foreach ($job in $Jobs) {
  $PreflightById[[string]$job.id] = Test-JobPreflight $job
}
$preflightFailures = @($Jobs | Where-Object { $PreflightById[[string]$_.id] })
if ($PreflightOnly) {
  foreach ($job in $Jobs) {
    $failure = [string]$PreflightById[[string]$job.id]
    if ($failure) {
      Write-Host ("PREFLIGHT_FAIL id=" + [string]$job.id + " reason=" + $failure)
    } else {
      Write-Host ("PREFLIGHT_OK id=" + [string]$job.id)
    }
  }
  if ($preflightFailures.Count -ne 0) { exit 2 }
  Write-Host ("PREFLIGHT_ALL_OK jobs=" + $Jobs.Count)
  exit 0
}

if (Test-Path -LiteralPath $WorkRoot) { Remove-Item -LiteralPath $WorkRoot -Recurse -Force }
New-Item -ItemType Directory -Path $WorkRoot -Force | Out-Null
if (Test-Path -LiteralPath $ReturnJson) { Remove-Item -LiteralPath $ReturnJson -Force }
if (Test-Path -LiteralPath $ReturnZip) { Remove-Item -LiteralPath $ReturnZip -Force }
if (Test-Path -LiteralPath $Transcript) { Remove-Item -LiteralPath $Transcript -Force }

Start-Transcript -LiteralPath $Transcript -Force | Out-Null
try {
  if ($preflightFailures.Count -ne 0) {
    foreach ($job in $Jobs) {
      $failure = [string]$PreflightById[[string]$job.id]
      if (!$failure) { $failure = 'batch preflight failed before any AE launch due to another job configuration' }
      $Results += [ordered]@{
        order = [int]$job.order
        id = [string]$job.id
        request_id = [string]$job.request_id
        required = [bool]$job.required
        status = 'failed'
        package_sha256 = [string]$job.package_sha256
        observed_package_sha256 = $null
        entrypoint = [string]$job.entrypoint
        return_json_name = [string]$job.return_json_name
        return_zip_name = [string]$job.return_zip_name
        exit_code = $null
        afterfx_before = @()
        afterfx_after = @()
        cdb_before = @()
        cdb_after = @()
        failure = $failure
        returned_statuses = @()
        evidence = @()
      }
    }
  } else {
    foreach ($job in $Jobs) {
      $jobRoot = Join-Path $WorkRoot ('{0:d3}_{1}' -f [int]$job.order, [string]$job.id)
      $extractRoot = Join-Path $jobRoot 'package'
      $stdoutPath = Join-Path $jobRoot 'entrypoint_stdout.log'
      $stderrPath = Join-Path $jobRoot 'entrypoint_stderr.log'
      New-Item -ItemType Directory -Path $extractRoot -Force | Out-Null
      $archivePath = Join-Path $PSScriptRoot ([string]$job.archive_path).Replace('/', '\')
      $afterFxBefore = @(Get-SessionProcessIds 'AfterFX')
      $afterFxAfter = @()
      $cdbBefore = @(Get-SessionProcessIds 'cdb')
      $cdbAfter = @()
      $actualHash = $null
      $exitCode = $null
      $failure = $null
      $childProcess = $null
      $entrypointPath = $null
      $initialFiles = @{}
      try {
        if (!(Test-Path -LiteralPath $archivePath -PathType Leaf)) { throw "bundled package is missing" }
        $actualHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -cne [string]$job.package_sha256) { throw "package SHA-256 drift" }
        if ($afterFxBefore.Count -ne 0) { throw "AfterFX.exe was running before the job" }
        if ($cdbBefore.Count -ne 0) { throw "cdb.exe was running before the job" }
        Assert-SafeZip $archivePath
        Expand-Archive -LiteralPath $archivePath -DestinationPath $extractRoot -Force
        $entrypointPath = Join-Path $extractRoot ([string]$job.entrypoint).Replace('/', '\')
        $resolvedRoot = (Get-Item -LiteralPath $extractRoot).FullName.TrimEnd([char[]]@('\')) + '\'
        $resolvedEntrypoint = (Get-Item -LiteralPath $entrypointPath -ErrorAction Stop).FullName
        if (!$resolvedEntrypoint.StartsWith($resolvedRoot, [StringComparison]::OrdinalIgnoreCase)) { throw "entrypoint escaped job root" }
        if ([IO.Path]::GetExtension($resolvedEntrypoint) -ine '.ps1') { throw "entrypoint is not PowerShell" }
        foreach ($file in @(Get-ChildItem -LiteralPath $extractRoot -Recurse -File -ErrorAction SilentlyContinue)) {
          $initialFiles[$file.FullName.ToLowerInvariant()] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
        $powerShellExe = (Get-Process -Id $PID).Path
        $processArguments = "-NoProfile -ExecutionPolicy Bypass -File $(ConvertTo-NativeArgumentLiteral $resolvedEntrypoint)"
        $childProcess = Start-Process -FilePath $powerShellExe `
          -ArgumentList $processArguments `
          -RedirectStandardOutput $stdoutPath `
          -RedirectStandardError $stderrPath `
          -PassThru
        $finished = $childProcess.WaitForExit($PerJobTimeoutMilliseconds)
        if ($finished) {
          $childProcess.WaitForExit()
          $exitCode = [int]$childProcess.ExitCode
        } else {
          $failure = Append-Failure $failure ("entrypoint timed out after {0} seconds" -f $EffectivePerJobTimeoutSeconds)
          if (!$childProcess.HasExited) {
            Stop-Process -Id $childProcess.Id -Force -ErrorAction SilentlyContinue
            $childProcess.WaitForExit()
          }
          Write-Warning ("Launcher timeout: entrypoint exceeded {0} seconds." -f $EffectivePerJobTimeoutSeconds)
          $exitCode = 124
        }
      } catch {
        $failure = $_.Exception.Message
        if ($null -eq $exitCode) { $exitCode = 2 }
        Write-Warning ("Witness launcher exception: " + ($_ | Out-String))
      } finally {
        if ($childProcess -and !$childProcess.HasExited) {
          Stop-Process -Id $childProcess.Id -Force -ErrorAction SilentlyContinue
          $childProcess.WaitForExit()
        }
        $afterFxAfter = @(Get-SessionProcessIds 'AfterFX')
        $cdbAfter = @(Get-SessionProcessIds 'cdb')
        if ($afterFxBefore.Count -eq 0 -and $afterFxAfter.Count -ne 0) {
          foreach ($pidValue in $afterFxAfter) {
            Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
            Wait-Process -Id $pidValue -Timeout 10 -ErrorAction SilentlyContinue
          }
          $failure = Append-Failure $failure 'AfterFX.exe remained after the job'
        }
        if ($cdbBefore.Count -eq 0 -and $cdbAfter.Count -ne 0) {
          foreach ($pidValue in $cdbAfter) {
            Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
            Wait-Process -Id $pidValue -Timeout 10 -ErrorAction SilentlyContinue
          }
          $failure = Append-Failure $failure 'cdb.exe remained after the job'
        }
      }

      $statusRecords = @()
      $authoritativeReturns = @()
      $authoritativeReturnZips = @()
      $authoritativeJsonProblem = $null
      foreach ($file in @(Get-ChildItem -LiteralPath $extractRoot -Recurse -File -ErrorAction SilentlyContinue)) {
        $hash = Try-FileSha256 $file.FullName
        if (!$hash) {
          $failure = Append-Failure $failure ("evidence file remained locked: " + $file.FullName)
          continue
        }
        $key = $file.FullName.ToLowerInvariant()
        if ($initialFiles.ContainsKey($key) -and $initialFiles[$key] -ceq $hash) { continue }
        $relative = $file.FullName.Substring($jobRoot.Length).TrimStart([char[]]@('\','/')).Replace('\', '/')
        if ($file.Name -ceq [string]$job.return_zip_name) {
          try {
            $returnArchive = [IO.Compression.ZipFile]::OpenRead($file.FullName)
            $returnArchive.Dispose()
            $authoritativeReturnZips += [ordered]@{path=$relative; sha256=$hash}
          } catch {
            $failure = Append-Failure $failure "authoritative return ZIP is not readable"
          }
        }
        if ($file.Extension -ine '.json') { continue }
        try {
          $body = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
        } catch {
          if ($file.Name -ceq [string]$job.return_json_name) {
            $authoritativeJsonProblem = "authoritative return JSON is invalid for request_id $([string]$job.request_id)"
          }
          continue
        }
        if ($body.PSObject.Properties.Name -contains 'status') {
          $statusRecords += [ordered]@{
            path = $relative
            request_id = [string]$body.request_id
            status = [string]$body.status
            sha256 = $hash
          }
        }
        if ($file.Name -ceq [string]$job.return_json_name) {
          $authoritativeReturns += [ordered]@{
            path = $relative
            request_id = [string]$body.request_id
            status = [string]$body.status
            sha256 = $hash
          }
        }
      }
      $authoritativeAnswered = (
        $authoritativeReturns.Count -eq 1 -and
        $authoritativeReturns[0].request_id -ceq [string]$job.request_id -and
        $authoritativeReturns[0].status -ceq 'answered'
      )
      $jobAnswered = (
        $exitCode -eq 0 -and
        !$failure -and
        $afterFxBefore.Count -eq 0 -and
        $afterFxAfter.Count -eq 0 -and
        $cdbBefore.Count -eq 0 -and
        $cdbAfter.Count -eq 0 -and
        $authoritativeAnswered -and
        $authoritativeReturnZips.Count -eq 1
      )
      if (!$jobAnswered -and !$failure) {
        if ($authoritativeJsonProblem) {
          $failure = $authoritativeJsonProblem
        } elseif ($authoritativeReturns.Count -eq 0) {
          $failure = "missing newly created authoritative return JSON $([string]$job.return_json_name) for request_id $([string]$job.request_id)"
        } elseif ($authoritativeReturns.Count -ne 1) {
          $failure = "multiple newly created authoritative return JSON files detected for request_id $([string]$job.request_id)"
        } elseif (!$authoritativeAnswered) {
          $failure = "authoritative return JSON did not bind answered/request_id for request_id $([string]$job.request_id)"
        } elseif ($authoritativeReturnZips.Count -eq 0) {
          $failure = "missing newly created authoritative return ZIP $([string]$job.return_zip_name) for request_id $([string]$job.request_id)"
        } else {
          $failure = "multiple newly created authoritative return ZIP files detected for request_id $([string]$job.request_id)"
        }
      }
      $evidence = @(File-Records $jobRoot @('*.zip', '*.json', '*.log', '*.txt', '*.marker'))
      $Results += [ordered]@{
        order = [int]$job.order
        id = [string]$job.id
        request_id = [string]$job.request_id
        required = [bool]$job.required
        status = $(if ($jobAnswered) { 'answered' } else { 'failed' })
        package_sha256 = [string]$job.package_sha256
        observed_package_sha256 = $actualHash
        entrypoint = [string]$job.entrypoint
        return_json_name = [string]$job.return_json_name
        return_zip_name = [string]$job.return_zip_name
        exit_code = $exitCode
        afterfx_before = @($afterFxBefore)
        afterfx_after = @($afterFxAfter)
        cdb_before = @($cdbBefore)
        cdb_after = @($cdbAfter)
        failure = $failure
        returned_statuses = @($statusRecords)
        evidence = @($evidence)
      }
    }
  }
} finally {
  Stop-Transcript -ErrorAction SilentlyContinue | Out-Null
}

$RequiredFailures = @($Results | Where-Object { $_.required -and $_.status -cne 'answered' })
$Overall = if ($RequiredFailures.Count -eq 0) { 'answered' } else { 'partial_success' }
$Return = [ordered]@{
  schema_version = 1
  kind = 'windows_witness_batch_return'
  batch_id = [string]$Manifest.batch_id
  status = $Overall
  started_at = $BatchStarted
  completed_at = (Get-Date).ToUniversalTime().ToString('o')
  manifest_sha256 = (Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
  jobs = @($Results)
}
Write-CanonicalJson $ReturnJson $Return

$returnStage = Join-Path $PSScriptRoot '_windows_witness_batch_return_stage'
if (Test-Path -LiteralPath $returnStage) { Remove-Item -LiteralPath $returnStage -Recurse -Force }
New-Item -ItemType Directory -Path $returnStage -Force | Out-Null
Copy-Item -LiteralPath $ReturnJson -Destination (Join-Path $returnStage 'windows_witness_batch_return.json')
Copy-Item -LiteralPath $ManifestPath -Destination (Join-Path $returnStage 'batch-manifest.json')
Copy-Item -LiteralPath $Transcript -Destination (Join-Path $returnStage 'windows_witness_batch_launcher.log')
New-Item -ItemType Directory -Path (Join-Path $returnStage 'jobs') -Force | Out-Null
foreach ($result in @($Results)) {
  $jobName = ('{0:D3}_{1}' -f [int]$result.order, [string]$result.id)
  $jobSource = Join-Path $WorkRoot $jobName
  $jobDestination = Join-Path (Join-Path $returnStage 'jobs') $jobName
  foreach ($record in @($result.evidence)) {
    $relative = ([string]$record.path).Replace('/', '\')
    $source = Join-Path $jobSource $relative
    $destination = Join-Path $jobDestination $relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination -Force
  }
}
Compress-Archive -Path (Join-Path $returnStage '*') -DestinationPath $ReturnZip -CompressionLevel Optimal
Remove-Item -LiteralPath $returnStage -Recurse -Force
Write-Host "status=$Overall"
Write-Host "return_json=$ReturnJson"
Write-Host "return_zip=$ReturnZip"
if ($Overall -eq 'answered') { exit 0 }
exit 2
'''

CMD_LAUNCHER = r'''@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_windows_witness_batch.ps1"
set "OLM_EXIT=%ERRORLEVEL%"
echo.
if "%OLM_EXIT%"=="0" (
  echo OLM witness batch completed. Return ZIP is beside this file.
) else (
  echo OLM witness batch finished with incomplete evidence. Keep the return ZIP and log.
)
pause
exit /b %OLM_EXIT%
'''

BATCH_README = '''OLM Windows witness batch

1. Close After Effects and any CDB debugger window.
2. Double-click RUN_WINDOWS_WITNESS_BATCH.cmd.
3. Keep the window open until all jobs finish.
4. Return windows_witness_batch_return.zip from this folder.

The batch preflights every host path and AEX hash before the first render.
Each job uses a fresh After Effects process. Partial evidence is preserved,
but it is not accepted as a complete result.
'''


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("ascii")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_id(label: str, value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    if any(char not in allowed for char in value) or value in {".", ".."}:
        raise ValueError(f"unsafe {label}: {value!r}")
    return value


def validate_file_name(label: str, value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    if "/" in value or "\\" in value or value in {".", ".."}:
        raise ValueError(f"unsafe {label}: {value!r}")
    return value


def require_string(mapping: Any, *keys: str) -> str:
    current = mapping
    trail: list[str] = []
    for key in keys:
        trail.append(key)
        if not isinstance(current, dict) or key not in current:
            raise ValueError(f"missing {'.'.join(trail)}")
        current = current[key]
    if not isinstance(current, str) or not current:
        raise ValueError(f"{'.'.join(keys)} must be a non-empty string")
    return current


def validate_timeout_seconds(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("per-job timeout seconds must be an integer")
    if not MIN_PER_JOB_TIMEOUT_SECONDS <= value <= MAX_PER_JOB_TIMEOUT_SECONDS:
        raise ValueError(
            f"per-job timeout seconds must be between {MIN_PER_JOB_TIMEOUT_SECONDS} and {MAX_PER_JOB_TIMEOUT_SECONDS}"
        )
    return value


def resolve_default_jobs() -> list[tuple[str, Path]]:
    override_root_raw = os.environ.get(DEFAULT_PRESET_ROOT_ENV)
    override_root = None
    if override_root_raw:
        override_root = Path(override_root_raw)
        if not override_root.is_absolute():
            override_root = ROOT / override_root
        override_root = override_root.resolve()
        override_root.mkdir(parents=True, exist_ok=True)
    jobs: list[tuple[str, Path]] = []
    for spec in DEFAULT_JOBS:
        archive = Path(spec["archive"])
        if override_root is not None:
            archive = override_root / archive.name
        output_dir = archive.with_suffix("")
        command = [
            sys.executable,
            str(spec["script"]),
            "--output-dir",
            str(output_dir),
            "--zip",
            str(archive),
        ]
        try:
            subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
            raise ValueError(f"default preset build failed for {spec['id']!r}: {message}") from exc
        jobs.append((str(spec["id"]), archive.resolve()))
    return jobs


def safe_member(name: str) -> PurePosixPath:
    if not name or "\\" in name or name.startswith("/"):
        raise ValueError(f"unsafe ZIP member path: {name!r}")
    path = PurePosixPath(name)
    if any(part in ("", ".", "..") for part in path.parts) or (path.parts and ":" in path.parts[0]):
        raise ValueError(f"unsafe ZIP member path: {name!r}")
    return path


def inspect_job(job_id: str, source: Path, order: int) -> dict[str, Any]:
    if not source.is_file() or not zipfile.is_zipfile(source):
        raise ValueError(f"job {job_id!r} is not a readable ZIP: {source}")
    with zipfile.ZipFile(source) as archive:
        names: dict[str, str] = {}
        manifests: list[str] = []
        contracts: list[str] = []
        for info in archive.infolist():
            member = safe_member(info.filename.rstrip("/"))
            folded = member.as_posix().casefold()
            if folded in names:
                raise ValueError(f"job {job_id!r} has duplicate Windows path: {info.filename!r}")
            names[folded] = member.as_posix()
            mode = info.external_attr >> 16
            if mode and stat.S_ISLNK(mode):
                raise ValueError(f"job {job_id!r} contains a symbolic link: {info.filename!r}")
            if not info.is_dir() and member.name == "package-manifest.json":
                manifests.append(member.as_posix())
            if not info.is_dir() and member.name == "witness-contract.json":
                contracts.append(member.as_posix())
        if len(manifests) != 1:
            raise ValueError(f"job {job_id!r} must contain exactly one package-manifest.json")
        if len(contracts) != 1:
            raise ValueError(f"job {job_id!r} must contain exactly one witness-contract.json")
        manifest_name = manifests[0]
        contract_name = contracts[0]
        try:
            package_manifest = json.loads(archive.read(manifest_name).decode("utf-8-sig"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"job {job_id!r} has an invalid package manifest: {exc}") from exc
        try:
            contract = json.loads(archive.read(contract_name).decode("utf-8-sig"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"job {job_id!r} has an invalid witness contract: {exc}") from exc
        request_id = validate_id(f"job {job_id!r} request_id", package_manifest.get("request_id"))
        if request_id != job_id:
            raise ValueError(f"job {job_id!r} request_id mismatch: package has {request_id!r}")
        contract_request_id = validate_id(f"job {job_id!r} contract request_id", contract.get("request_id"))
        if contract_request_id != request_id:
            raise ValueError(f"job {job_id!r} contract request_id mismatch: contract has {contract_request_id!r}")
        entrypoint_value = package_manifest.get("entrypoint", "artifacts/run_witness.ps1")
        if not isinstance(entrypoint_value, str) or not entrypoint_value:
            raise ValueError(f"job {job_id!r} has an invalid entrypoint")
        relative_entrypoint = safe_member(entrypoint_value)
        contract_value = package_manifest.get("contract", "witness-contract.json")
        if not isinstance(contract_value, str) or not contract_value:
            raise ValueError(f"job {job_id!r} has an invalid contract path")
        relative_contract = safe_member(contract_value)
        if relative_entrypoint.suffix.lower() != ".ps1":
            raise ValueError(f"job {job_id!r} entrypoint is not a PowerShell script")
        package_root = PurePosixPath(manifest_name).parent
        entrypoint = (package_root / relative_entrypoint).as_posix()
        contract_path = (package_root / relative_contract).as_posix()
        if entrypoint.casefold() not in names:
            raise ValueError(f"job {job_id!r} is missing entrypoint {entrypoint!r}")
        if contract_path.casefold() not in names or names[contract_path.casefold()] != contract_name:
            raise ValueError(f"job {job_id!r} is missing contract {contract_path!r}")
        default_aex_path = require_string(contract, "plugin", "default_aex_path")
        aex_sha256 = require_string(contract, "plugin", "aex_sha256").lower()
        if len(aex_sha256) != 64 or any(char not in "0123456789abcdef" for char in aex_sha256):
            raise ValueError(f"job {job_id!r} has an invalid plugin.aex_sha256")
        afterfx_path = require_string(contract, "host", "afterfx_path")
        cdb_path = require_string(contract, "host", "cdb_path")
        return_json_name = validate_file_name(
            f"job {job_id!r} return_bundle.json_name",
            require_string(contract, "return_bundle", "json_name"),
        )
        return_zip_name = validate_file_name(
            f"job {job_id!r} return_bundle.zip_name",
            require_string(contract, "return_bundle", "zip_name"),
        )
        if not return_json_name.lower().endswith(".json"):
            raise ValueError(f"job {job_id!r} return_bundle.json_name must end in .json")
        if not return_zip_name.lower().endswith(".zip"):
            raise ValueError(f"job {job_id!r} return_bundle.zip_name must end in .zip")
        if return_json_name.casefold() == return_zip_name.casefold():
            raise ValueError(f"job {job_id!r} return JSON and ZIP names must be distinct")
    return {
        "archive_path": f"jobs/{order:03d}_{job_id}.zip",
        "aex_sha256": aex_sha256,
        "afterfx_path": afterfx_path,
        "cdb_path": cdb_path,
        "contract_path": contract_path,
        "default_aex_path": default_aex_path,
        "entrypoint": entrypoint,
        "id": job_id,
        "order": order,
        "package_sha256": sha256(source),
        "request_id": request_id,
        "required": True,
        "return_json_name": return_json_name,
        "return_zip_name": return_zip_name,
        "size_bytes": source.stat().st_size,
        "source": source,
    }


def parse_job(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise ValueError(f"--job must be ID=PATH.zip: {value!r}")
    job_id, raw_path = value.split("=", 1)
    job_id = validate_id("job id", job_id)
    if not raw_path:
        raise ValueError(f"invalid --job: {value!r}")
    path = Path(raw_path)
    if not path.is_absolute():
        path = ROOT / path
    return job_id, path.resolve()


def write_zip(source_dir: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, prefix=output.name + ".", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(source_dir.rglob("*"), key=lambda item: item.relative_to(source_dir).as_posix()):
                if not path.is_file():
                    continue
                name = f"{PACKAGE_NAME}/{path.relative_to(source_dir).as_posix()}"
                info = zipfile.ZipInfo(name, ZIP_EPOCH)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o100644 & 0xFFFF) << 16
                archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


def build(
    job_values: list[str],
    output_dir: Path,
    output_zip: Path,
    per_job_timeout_seconds: int,
) -> tuple[Path, Path]:
    parsed = [parse_job(value) for value in job_values] if job_values else resolve_default_jobs()
    per_job_timeout_seconds = validate_timeout_seconds(per_job_timeout_seconds)
    ids = [job_id.casefold() for job_id, _ in parsed]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate job IDs are not allowed (case-insensitive)")
    jobs = [inspect_job(job_id, source, order) for order, (job_id, source) in enumerate(parsed, start=1)]
    for job in jobs:
        aliases = DEFAULT_SATISFIES_BY_ID.get(job["id"], ())
        folded: set[str] = set()
        satisfied: list[str] = []
        for value in (job["request_id"], *aliases):
            request_id = validate_id(f"job {job['id']!r} satisfies_request_id", value)
            key = request_id.casefold()
            if key in folded:
                continue
            folded.add(key)
            satisfied.append(request_id)
        job["satisfies_request_ids"] = satisfied
    output_dir = output_dir.resolve()
    output_zip = output_zip.resolve()
    if output_zip == output_dir or output_dir in output_zip.parents:
        raise ValueError("output ZIP must be outside the output directory")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=PACKAGE_NAME + "_", dir=output_dir.parent))
    try:
        (temporary / "jobs").mkdir(parents=True)
        manifest_jobs = []
        for job in jobs:
            destination = temporary / job["archive_path"]
            shutil.copyfile(job["source"], destination)
            if sha256(destination) != job["package_sha256"]:
                raise ValueError(f"package SHA drift while copying job {job['id']!r}")
            manifest_jobs.append({key: value for key, value in job.items() if key != "source"})
        manifest = {
            "batch_id": PACKAGE_NAME,
            "jobs": manifest_jobs,
            "kind": "windows_witness_batch_request",
            "launcher": "run_windows_witness_batch.ps1",
            "one_click_launcher": "RUN_WINDOWS_WITNESS_BATCH.cmd",
            "per_job_timeout_seconds": per_job_timeout_seconds,
            "readme": "README.txt",
            "schema_version": 1,
            "success_status": "answered",
            "failure_status": "partial_success",
        }
        (temporary / "batch-manifest.json").write_bytes(canonical_json(manifest))
        (temporary / "README.txt").write_text(BATCH_README, encoding="ascii", newline="\r\n")
        (temporary / "run_windows_witness_batch.ps1").write_text(LAUNCHER, encoding="ascii", newline="\n")
        (temporary / "RUN_WINDOWS_WITNESS_BATCH.cmd").write_text(CMD_LAUNCHER, encoding="ascii", newline="\r\n")
        if output_dir.exists():
            shutil.rmtree(output_dir)
        temporary.replace(output_dir)
        write_zip(output_dir, output_zip)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return output_dir, output_zip


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", action="append", default=[], metavar="ID=PATH.zip")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--per-job-timeout-seconds",
        type=int,
        default=DEFAULT_PER_JOB_TIMEOUT_SECONDS,
        help=(
            f"per-job timeout in seconds "
            f"({MIN_PER_JOB_TIMEOUT_SECONDS}-{MAX_PER_JOB_TIMEOUT_SECONDS}, default: {DEFAULT_PER_JOB_TIMEOUT_SECONDS})"
        ),
    )
    parser.add_argument("--zip", dest="output_zip", type=Path, default=DEFAULT_ZIP)
    args = parser.parse_args(argv)
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    output_zip = args.output_zip if args.output_zip.is_absolute() else ROOT / args.output_zip
    try:
        directory, archive = build(args.job, output_dir, output_zip, args.per_job_timeout_seconds)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"directory": str(directory), "sha256": sha256(archive), "status": "ok", "zip": str(archive)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
