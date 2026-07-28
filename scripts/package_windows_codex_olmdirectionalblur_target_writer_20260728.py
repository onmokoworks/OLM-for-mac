#!/usr/bin/env python3
"""Build the immutable DirectionalBlur one-shot target-writer batch child."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "refs/runtime_trace_packages/windows_witness_olmdirectionalblur_writer_entry_20260716.zip"
TARGET = ROOT / "refs/handoffs/windows_codex_batch_jobs_20260728/olmdirectionalblur_target_writer_20260728_r3"
JOB_ID = "olmdirectionalblur_target_writer_20260728_r3"
REQUEST_ID = "olmdirectionalblur_writer_entry_20260716"

WRAPPER = r"""param(
  [string]$PackageRoot = $PSScriptRoot,
  [string]$AexPath = '',
  [string]$AfterFxPath = '',
  [string]$CdbPath = ''
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$requestId = 'olmdirectionalblur_writer_entry_20260716'
$evidence = Join-Path $PackageRoot 'evidence'
$work = Join-Path $PackageRoot 'work_target_writer'
$inner = Join-Path $PackageRoot 'artifacts\run_witness.ps1'
$status = Join-Path $evidence 'CHILD_STATUS.json'
$exitCode = 2
$cleanupFailed = $false

function Write-Status([string]$Terminal, [string]$Stage, [string]$Reason) {
  $directManifest = $null
  $directManifestPath = Join-Path $evidence 'DIRECT_EVIDENCE_MANIFEST.json'
  if (Test-Path -LiteralPath $directManifestPath -PathType Leaf) {
    try { $directManifest = Get-Content -LiteralPath $directManifestPath -Raw | ConvertFrom-Json } catch {}
  }
  $body = [ordered]@{
    schema_version = 1
    status = $Terminal
    request_id = $requestId
    claim_boundary = 'raw_target_writer_words_plus_rendered_output_presence_only'
    rendered_output_role = 'presence_only_not_exact'
    ae_exact = $false
    output_exact = $false
    production_change_authorized = $false
    direct_evidence = $(if ($directManifest) { $directManifest.direct_evidence } else { @() })
    runtime_provenance = $(if ($directManifest) {
      [ordered]@{run_id=$directManifest.run_id;ae_pid=$directManifest.ae_pid;module_base=$directManifest.module_base;aex_sha256=$directManifest.aex_sha256;renderer=$directManifest.renderer;case_id=$directManifest.case_id}
    } else { $null })
    failure = $(if ($Terminal -eq 'answered') { $null } else {
      [ordered]@{ stage = $Stage; reason = $Reason; missing_fields = @('direct_target_store_evidence') }
    })
  }
  $body | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $status -Encoding UTF8
}

try {
  New-Item -ItemType Directory -Force -Path $evidence,$work | Out-Null
  $args = @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $inner + '"'),
    '-PackageRoot',('"' + $PackageRoot + '"'),'-WorkRoot',('"' + $work + '"'))
  if ($AexPath) { $args += @('-AexPath',('"' + $AexPath + '"')) }
  if ($AfterFxPath) { $args += @('-AfterFxPath',('"' + $AfterFxPath + '"')) }
  if ($CdbPath) { $args += @('-CdbPath',('"' + $CdbPath + '"')) }
  $stdout = Join-Path $evidence 'INNER_RUNNER_STDOUT.txt'
  $stderr = Join-Path $evidence 'INNER_RUNNER_STDERR.txt'
  $proc = Start-Process powershell.exe -ArgumentList $args -PassThru -Wait `
    -RedirectStandardOutput $stdout -RedirectStandardError $stderr
  $run = Get-ChildItem -LiteralPath $work -Directory | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
  if ($null -eq $run) { throw 'inner runner emitted no run directory' }
  $validation = Get-ChildItem -LiteralPath $run.FullName -Filter validation_status.json -Recurse | Select-Object -First 1
  if ($null -eq $validation) { throw 'inner runner emitted no validation_status.json' }
  Copy-Item $validation.FullName (Join-Path $evidence 'INNER_VALIDATION_STATUS.json') -Force
  $parsed = Get-Content $validation.FullName -Raw | ConvertFrom-Json
  foreach ($pattern in @('cdb_trace_*.txt','cdb_stdout_*.txt','cdb_stderr_*.txt')) {
    $candidate = Get-ChildItem -LiteralPath $run.FullName -Filter $pattern -Recurse | Select-Object -First 1
    if ($candidate) { Copy-Item $candidate.FullName (Join-Path $evidence $candidate.Name) -Force }
  }
  $flatten = Join-Path $PackageRoot 'scripts\flatten_return.py'
  & py -3 $flatten --run-root $run.FullName --evidence-root $evidence
  if ($LASTEXITCODE -ne 0) { throw 'manifest-bound direct evidence extraction failed' }
  $argb = Test-Path -LiteralPath (Join-Path $evidence 'writer_pf_argb8.bin') -PathType Leaf
  $png = Test-Path -LiteralPath (Join-Path $evidence 'rendered_db_angle0_alpha_fade_hard_edges.png') -PathType Leaf
  if ($proc.ExitCode -ne 0 -or [string]$parsed.status -cne 'answered') {
    Write-Status 'exact_bind_failure' 'inner_runner' ("status=" + [string]$parsed.status + " exit=" + $proc.ExitCode)
  } elseif (!$argb -or !$png) {
    Write-Status 'exact_bind_failure' 'direct_evidence' 'required raw ARGB or rendered PNG evidence missing'
  } else {
    Write-Status 'answered' '' ''
    $exitCode = 0
  }
} catch {
  New-Item -ItemType Directory -Force -Path $evidence | Out-Null
  Write-Status 'exact_bind_failure' 'wrapper_exception' $_.Exception.Message
} finally {
  try {
    Get-ChildItem -LiteralPath $work -Filter 'RETURN*.zip' -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction Stop
    Get-ChildItem -LiteralPath $work -Filter '*.zip' -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction Stop
    Remove-Item -LiteralPath (Join-Path $work 'expanded_return') -Recurse -Force -ErrorAction SilentlyContinue
  } catch {
    $cleanupFailed = $true
    $exitCode = 2
    Remove-Item -LiteralPath $status -Force -ErrorAction SilentlyContinue
    try { Write-Status 'exact_bind_failure' 'cleanup_unresolved' $_.Exception.Message } catch {
      Remove-Item -LiteralPath $status -Force -ErrorAction SilentlyContinue
    }
  }
  if ($cleanupFailed -and !(Test-Path -LiteralPath $status -PathType Leaf)) {
    $exitCode = 2
    try { Write-Status 'exact_bind_failure' 'cleanup_unresolved' 'cleanup failed without direct status evidence' } catch {
      Remove-Item -LiteralPath $status -Force -ErrorAction SilentlyContinue
    }
  }
}
if (Test-Path -LiteralPath $status -PathType Leaf) { Get-Content -LiteralPath $status -Raw }
exit $exitCode
""".encode("utf-8")

FLATTENER = r"""#!/usr/bin/env python3
import argparse, hashlib, json, re, shutil, zipfile
from pathlib import Path, PurePosixPath

p = argparse.ArgumentParser()
p.add_argument("--run-root", type=Path, required=True)
p.add_argument("--evidence-root", type=Path, required=True)
a = p.parse_args()
manifests = sorted(a.run_root.rglob("RETURN_OLMDIRECTIONALBLUR_WRITER_ENTRY.json"))
archives = sorted(a.run_root.rglob("RETURN_OLMDIRECTIONALBLUR_WRITER_ENTRY.zip"))
if len(manifests) != 1 or len(archives) != 1:
    raise SystemExit("exactly one inner return manifest/archive required")
m = json.loads(manifests[0].read_text(encoding="utf-8-sig"))
if m.get("status") != "answered" or m.get("request_id") != "olmdirectionalblur_writer_entry_20260716":
    raise SystemExit("inner return is not the answered bound request")
records = {x["archive_path"]: x for x in m.get("artifacts", [])}
required = [
    "return/writer_pf_argb8.bin",
    "return/rendered_db_angle0_alpha_fade_hard_edges.png",
]
if any(name not in records for name in required):
    raise SystemExit("required manifest-bound artifacts missing")
a.evidence_root.mkdir(parents=True, exist_ok=True)
direct = []
with zipfile.ZipFile(archives[0]) as z:
    names = set(z.namelist())
    for name in required:
        if name not in names or PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts:
            raise SystemExit("unsafe or missing manifest-bound member")
        data = z.read(name)
        digest = hashlib.sha256(data).hexdigest()
        rec = records[name]
        if digest != rec.get("sha256") or len(data) != rec.get("size_bytes"):
            raise SystemExit("manifest-bound member checksum/size mismatch")
        out = a.evidence_root / PurePosixPath(name).name
        out.write_bytes(data)
        direct.append({"original_archive_path": name, "direct_filename": out.name,
                       "sha256": digest, "size_bytes": len(data),
                       "role": "raw_target_writer_words" if name.endswith(".bin")
                               else "rendered_output_presence_only_not_exact"})
    trace_records = [x for x in m.get("logs", []) if x.get("archive_path") == "logs/combined_cdb_trace.txt"]
    if len(trace_records) != 1 or "logs/combined_cdb_trace.txt" not in names:
        raise SystemExit("manifest-bound runtime trace missing")
    trace = z.read("logs/combined_cdb_trace.txt")
if hashlib.sha256(trace).hexdigest() != trace_records[0].get("sha256"):
    raise SystemExit("runtime trace checksum mismatch")
text = trace.decode("utf-8", "replace")
event = next((line for line in text.splitlines() if line.startswith("DBR_TARGET_STORE ")), "")
fields = dict(re.findall(r"([A-Za-z0-9_]+)=([^ ]+)", event))
if not event or fields.get("aex_sha256") != "d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e":
    raise SystemExit("target-store runtime provenance missing")
provenance = {
    "request_id": m["request_id"], "run_id": fields.get("run_id"),
    "ae_pid": fields.get("ae_pid"), "module_base": fields.get("module_base"),
    "aex_sha256": fields.get("aex_sha256"), "renderer": fields.get("renderer"),
    "case_id": fields.get("case_id"), "direct_evidence": direct,
    "claim": "raw target writer words plus rendered output presence only; no output exact or AE exact claim",
}
(a.evidence_root / "DIRECT_EVIDENCE_MANIFEST.json").write_text(
    json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
""".encode("utf-8")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def package_bytes() -> bytes:
    source = SOURCE.read_bytes()
    if sha(source) != "6482b4e2092688f699162a24fd9ee1338b44864bcc831a21bdaa2436ee1d62e6":
        raise RuntimeError("DirectionalBlur witness package is stale; regenerate and re-audit")
    members: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(source)) as zin:
        for info in zin.infolist():
            if not info.is_dir():
                members[info.filename] = zin.read(info)
    inner = members["artifacts/run_witness.ps1"].decode("utf-8")
    inner = inner.replace(
        "[ordered]@{pid=[int]$_.ProcessId; parent_pid=[int]$_.ParentProcessId; session_id=[int]$_.SessionId; path=$_.ExecutablePath; command_line=$_.CommandLine}",
        "[ordered]@{pid=[int]$_.ProcessId; parent_pid=[int]$_.ParentProcessId; session_id=[int]$_.SessionId; path=$_.ExecutablePath; creation_date=[string]$_.CreationDate; command_line=$_.CommandLine}",
    )
    cleanup_start = inner.index("function Stop-WitnessProcesses {")
    cleanup_end = inner.index("function Get-TypedHitCount")
    exact_cleanup = r"""function Stop-ExactOwnedProcess([string]$SidecarPath, [string]$Kind, [bool]$RequireQueueBinding) {
  $report = Join-Path $work ($Kind.ToUpperInvariant() + '_CLEANUP_STATUS.json')
  try {
    if (!(Test-Path -LiteralPath $SidecarPath -PathType Leaf)) { throw 'owned sidecar missing' }
    $owned = Get-Content -LiteralPath $SidecarPath -Raw | ConvertFrom-Json
    if ([string]$owned.run_id -cne $runId -or [string]$owned.request_id -cne [string]$contract.request_id) { throw 'owned sidecar request mismatch' }
    if ($RequireQueueBinding) {
      if (!(Test-Path -LiteralPath $queueBootstrap -PathType Leaf)) { throw 'request-bound queue marker missing' }
      $binding = Read-QueueBootstrapBinding $queueBootstrap
      if ([string]$binding.run_id -cne $runId -or [string]$binding.request_id -cne [string]$contract.request_id) { throw 'request-bound queue marker mismatch' }
      $baseline = @(Get-Content -LiteralPath (Join-Path $work 'PRELAUNCH_AFTERFX_BASELINE.json') -Raw | ConvertFrom-Json)
      if (@($baseline | Where-Object { [int]$_.pid -eq [int]$owned.pid }).Count -ne 0) { throw 'owned PID appears in prelaunch baseline' }
    }
    $rows = @(Get-CimInstance Win32_Process -Filter ('ProcessId=' + [int]$owned.pid) -ErrorAction Stop)
    if ($rows.Count -ne 1 -or [string]$rows[0].ExecutablePath -cne [string]$owned.path -or [string]$rows[0].CreationDate -cne [string]$owned.creation_date) { throw 'owned PID identity recycled or ambiguous' }
    Stop-Process -Id ([int]$owned.pid) -Force -ErrorAction Stop
    Wait-Process -Id ([int]$owned.pid) -Timeout 10 -ErrorAction SilentlyContinue
    [ordered]@{status='cleaned_exact_owned_identity';process=$Kind;pid=[int]$owned.pid} | ConvertTo-Json | Set-Content -LiteralPath $report -Encoding UTF8
  } catch {
    [ordered]@{status='cleanup_unresolved';process=$Kind;reason=$_.Exception.Message;user_pid_touched=$false} | ConvertTo-Json | Set-Content -LiteralPath $report -Encoding UTF8
  }
}

function Stop-CdbCapture {
  Stop-ExactOwnedProcess (Join-Path $work 'OWNED_CDB_IDENTITY.json') 'cdb' $false
}

function Stop-WitnessProcesses {
  foreach ($case in @($contract.cases)) {
    $ready = Join-Path $work ("ready_" + $case.id + '.marker')
    $continue = Join-Path $work ("continue_" + $case.id + '.marker')
    if ((Test-Path -LiteralPath $ready) -and !(Test-Path -LiteralPath $continue)) {
      Set-Content -LiteralPath $continue -Value 'abort' -Encoding ASCII -ErrorAction SilentlyContinue
    }
  }
  Stop-CdbCapture
  Stop-ExactOwnedProcess (Join-Path $work 'OWNED_AFTERFX_IDENTITY.json') 'afterfx' $true
  if ($scheduledTaskCreated -and $scheduledTaskName) { & schtasks.exe /Delete /TN $scheduledTaskName /F *> $null }
  if ($dispatchScheduledTaskCreated -and $dispatchScheduledTaskName) { & schtasks.exe /Delete /TN $dispatchScheduledTaskName /F *> $null }
}

"""
    inner = inner[:cleanup_start] + exact_cleanup + inner[cleanup_end:]
    anchor = "$mainAePid = [int]$launch.Id"
    sidecar = """$mainAePid = [int]$launch.Id
$ownedState = @(Get-AfterFxState | Where-Object { [int]$_.pid -eq $mainAePid })
if ($ownedState.Count -ne 1 -or [string]::IsNullOrWhiteSpace([string]$ownedState[0].creation_date)) {
  Finish (Failure 'owned_identity' 'launch identity is ambiguous' @('owned_afterfx_identity') '') 2
}
[ordered]@{pid=$mainAePid;path=[string]$ownedState[0].path;creation_date=[string]$ownedState[0].creation_date;run_id=$runId;request_id=[string]$contract.request_id} |
  ConvertTo-Json | Set-Content -LiteralPath (Join-Path $work 'OWNED_AFTERFX_IDENTITY.json') -Encoding UTF8"""
    if anchor not in inner:
        raise RuntimeError("inner ownership sidecar anchor missing")
    inner = inner.replace(anchor, sidecar)
    cdb_anchor = "$cdb = Start-Process -FilePath $CdbPath -ArgumentList $cdbArguments -RedirectStandardOutput $stdout -RedirectStandardError $stderr -NoNewWindow -PassThru"
    cdb_sidecar = cdb_anchor + """
  $cdbRows = @(Get-CimInstance Win32_Process -Filter ('ProcessId=' + [int]$cdb.Id) -ErrorAction Stop)
  if ($cdbRows.Count -ne 1 -or [string]::IsNullOrWhiteSpace([string]$cdbRows[0].CreationDate)) {
    Finish (Failure 'owned_identity' 'CDB launch identity is ambiguous' @('owned_cdb_identity') '') 2
  }
  [ordered]@{pid=[int]$cdb.Id;path=[string]$cdbRows[0].ExecutablePath;creation_date=[string]$cdbRows[0].CreationDate;run_id=$runId;request_id=[string]$contract.request_id} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $work 'OWNED_CDB_IDENTITY.json') -Encoding UTF8"""
    if cdb_anchor not in inner:
        raise RuntimeError("inner CDB sidecar anchor missing")
    inner = inner.replace(cdb_anchor, cdb_sidecar)
    baseline_anchor = """if (Get-Process -Name AfterFX -ErrorAction SilentlyContinue) {
  Finish (Failure 'desktop_launch' 'After Effects must be fully closed before this run' @('fresh_AfterFX_process') '') 2
}"""
    baseline_patch = """$prelaunchBaseline = @(Get-AfterFxState)
$prelaunchBaseline | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $work 'PRELAUNCH_AFTERFX_BASELINE.json') -Encoding UTF8
if ($prelaunchBaseline.Count -ne 0) {
  Finish (Failure 'desktop_launch' 'Preexisting After Effects identity detected; no user PID touched' @('empty_prelaunch_afterfx_baseline') ($prelaunchBaseline | ConvertTo-Json -Compress)) 2
}"""
    if baseline_anchor not in inner:
        raise RuntimeError("inner prelaunch baseline patch anchor missing")
    inner = inner.replace(baseline_anchor, baseline_patch)
    members["artifacts/run_witness.ps1"] = inner.encode("utf-8")
    members["README.md"] = (
        "# OLMDirectionalBlur batch child\n\nRun only `run.ps1` from the package root. "
        "`artifacts/run_witness.ps1` is `internal_not_entrypoint` and must never be "
        "invoked directly. This captures raw runtime writer words and rendered-output "
        "presence only; it makes no output-exact or AE-exact claim.\n"
    ).encode()
    manifest = json.loads(members["package-manifest.json"])
    manifest["entrypoint"] = "run.ps1"
    manifest["inner_runner_role"] = "internal_not_entrypoint"
    manifest["claim_boundary"] = "raw_target_writer_words_plus_rendered_output_presence_only"
    manifest["ae_exact"] = False
    manifest.pop("files", None)
    members["package-manifest.json"] = canonical(manifest)
    members["run.ps1"] = WRAPPER
    members["scripts/flatten_return.py"] = FLATTENER
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zout.writestr(info, members[name])
    return output.getvalue()


def expected() -> tuple[bytes, bytes, bytes]:
    package = package_bytes()
    digest = sha(package)
    manifest = canonical({
        "schema": "windows_codex_batch_job_v1",
        "job_id": JOB_ID,
        "package": "package.zip",
        "package_sha256": digest,
        "entrypoint": "run.ps1",
        "failure_policy": "independent",
        "success_status": "answered",
        "failure_status": "exact_bind_failure",
        "request_id": REQUEST_ID,
        "description": (
            "Pinned OLMDirectionalBlur 2025 one-shot (494,169) raw target writer "
            "words plus rendered output presence only. Direct non-ZIP evidence is flattened by the "
            "root wrapper; no production or AE-exact claim."
        ),
    })
    return package, manifest, f"{digest}  package.zip\n".encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    built = expected()
    paths = (TARGET / "package.zip", TARGET / "job_manifest.json", TARGET / "package.zip.sha256")
    if args.verify:
        if any(not path.is_file() for path in paths):
            raise RuntimeError("child target is incomplete")
        if tuple(path.read_bytes() for path in paths) != built:
            raise RuntimeError("child target drifted from deterministic build")
    else:
        if TARGET.exists():
            raise RuntimeError(f"immutable target already exists: {TARGET}")
        TARGET.mkdir(parents=True)
        for path, data in zip(paths, built):
            path.write_bytes(data)
    print(json.dumps({"job_id": JOB_ID, "package_sha256": sha(built[0]), "status": "verified"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
