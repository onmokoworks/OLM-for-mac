#!/usr/bin/env python3
"""Build the DG current-AEX hook-liveness request package."""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TYPED = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712"
PACKAGE = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_hook_liveness_20260713"
OUTPUT = PACKAGE.with_suffix(".zip")
REQUEST_ID = "olmdistancegradation_8bpc_current_aex_hook_liveness_20260713"
RVA = ("1170870", "117057d", "11705f1", "1170808", "1170814")


README = f"""# OLMDistanceGradation 8bpc Current-AEX Hook Liveness

Status: runnable liveness probe. This package does not collect typed values,
coordinates, stage ownership, or algorithm proof. It only answers whether the
five existing RVA hooks execute in one fresh Windows AE/CDB run.

The runner arms all five ordinary breakpoints only after `DistanceGradation.aex`
has loaded. It returns one run ID, one SHA-256, and a hit count for each RVA.
Zero is a valid liveness result. Do not infer algorithm behavior from it.

Run `artifacts/run_olmdistancegradation_8bpc_hook_liveness_20260713.ps1`.
Use `-ParseOnly -TracePath` for the included parser fixtures.
"""


RUNNER = r'''param(
  [string]$PackageRoot = (Split-Path -Parent $PSScriptRoot),
  [string]$WorkRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) 'work'),
  [switch]$ParseOnly,
  [string]$TracePath = '',
  [string]$AexPath = 'C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\Plug-ins\Effects\DistanceGradation.aex'
)

$ErrorActionPreference = 'Stop'
$requestId = 'olmdistancegradation_8bpc_current_aex_hook_liveness_20260713'
$rvas = @('1170870','117057d','11705f1','1170808','1170814')
$runId = 'dglive-' + ([guid]::NewGuid().ToString('N'))

function Failure([string]$reason, [object[]]$missing, [string]$last) {
  [ordered]@{ status='exact_bind_failure'; kind='hook_liveness'; failure=[ordered]@{stage='hook_liveness';reason=$reason;missing_fields=@($missing);last_observation=$last} }
}

function Parse([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) { return Failure 'missing CDB stdout' @('stdout') '' }
  $rows = @{}
  $last = ''
  foreach ($line in Get-Content -LiteralPath $path) {
    $last = $line
    if ($line -notmatch '^DG8_LIVE_SUMMARY\s+') { continue }
    $m = @{}
    foreach ($pair in [regex]::Matches($line, '(?<key>[a-z0-9_]+)=(?<value>[^\s]+)')) { $m[$pair.Groups['key'].Value] = $pair.Groups['value'].Value }
    if ($m.ContainsKey('rva')) { $rows[$m['rva']] = $m }
  }
  $missing = @()
  foreach ($rva in $rvas) {
    if (-not $rows.ContainsKey($rva)) { $missing += "missing:rva_$rva"; continue }
    foreach ($field in @('run_id','aex_sha256','hit_count')) {
      if (-not $rows[$rva].ContainsKey($field) -or [string]::IsNullOrWhiteSpace([string]$rows[$rva][$field])) { $missing += "rva_$rva:$field" }
    }
    if ($rows[$rva]['hit_count'] -notmatch '^\d+$') { $missing += "rva_$rva:hit_count_integer" }
  }
  $runIds = @($rows.Values | ForEach-Object { $_['run_id'] } | Select-Object -Unique)
  $hashes = @($rows.Values | ForEach-Object { $_['aex_sha256'] } | Select-Object -Unique)
  if ($runIds.Count -ne 1) { $missing += 'shared_run_id' }
  if ($hashes.Count -ne 1 -or $hashes[0] -notmatch '^[0-9a-fA-F]{64}$') { $missing += 'shared_aex_sha256' }
  if ($missing.Count) { return Failure 'five RVA summaries are not hash/run complete' $missing $last }
  [ordered]@{status='answered';kind='hook_liveness';request_id=$requestId;run_id=$runIds[0];aex_sha256=$hashes[0];rvas=@($rvas | ForEach-Object { [ordered]@{rva=$_;hit_count=[int]$rows[$_]['hit_count']} })}
}

if ($ParseOnly) { if (-not $TracePath) { throw '-ParseOnly requires -TracePath' }; (Parse $TracePath) | ConvertTo-Json -Depth 8; exit 0 }

$work = Join-Path $WorkRoot "olmdg_hook_liveness_$runId"; New-Item -ItemType Directory -Force -Path $work | Out-Null
$trace = Join-Path $work 'cdb_stdout.txt'; $cdbScript = Join-Path $work 'hook_liveness.cdb'
$queue = Join-Path $PackageRoot 'scripts\ae_render_olmdistancegradation_8bpc_hook_liveness_queue.jsx'
$cdb = 'C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe'
$afterFx = 'C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe'
$aexSha256 = if (Test-Path -LiteralPath $AexPath) { (Get-FileHash -LiteralPath $AexPath -Algorithm SHA256).Hash.ToLowerInvariant() } else { '' }
if ($aexSha256 -notmatch '^[0-9a-f]{64}$') { throw "DistanceGradation.aex SHA-256 unavailable: $AexPath" }
$cdbText = @"
.effmach amd64
.expr /s masm
sxi 80000003
sxe ld:DistanceGradation.aex
sxe ld:DistanceGradation
.logopen /t $trace
g
.echo DG8_LIVE_MODULE_LOADED
lm m DistanceGradation
r `@$t0 = 0
r `@$t1 = 0
r `@$t2 = 0
r `@$t3 = 0
r `@$t4 = 0
bp DistanceGradation+0x1170870 ".printf \"DG8_LIVE_HIT run_id=$runId rva=1170870 aex_sha256=$aexSha256 hit_count=%u\n\", `@$t0; r `@$t0 = `@$t0 + 1; gc"
bp DistanceGradation+0x117057d ".printf \"DG8_LIVE_HIT run_id=$runId rva=117057d aex_sha256=$aexSha256 hit_count=%u\n\", `@$t1; r `@$t1 = `@$t1 + 1; gc"
bp DistanceGradation+0x11705f1 ".printf \"DG8_LIVE_HIT run_id=$runId rva=11705f1 aex_sha256=$aexSha256 hit_count=%u\n\", `@$t2; r `@$t2 = `@$t2 + 1; gc"
bp DistanceGradation+0x1170808 ".printf \"DG8_LIVE_HIT run_id=$runId rva=1170808 aex_sha256=$aexSha256 hit_count=%u\n\", `@$t3; r `@$t3 = `@$t3 + 1; gc"
bp DistanceGradation+0x1170814 ".printf \"DG8_LIVE_HIT run_id=$runId rva=1170814 aex_sha256=$aexSha256 hit_count=%u\n\", `@$t4; r `@$t4 = `@$t4 + 1; gc"
g
.printf "DG8_LIVE_SUMMARY run_id=$runId rva=1170870 aex_sha256=$aexSha256 hit_count=%u\n", `@$t0
.printf "DG8_LIVE_SUMMARY run_id=$runId rva=117057d aex_sha256=$aexSha256 hit_count=%u\n", `@$t1
.printf "DG8_LIVE_SUMMARY run_id=$runId rva=11705f1 aex_sha256=$aexSha256 hit_count=%u\n", `@$t2
.printf "DG8_LIVE_SUMMARY run_id=$runId rva=1170808 aex_sha256=$aexSha256 hit_count=%u\n", `@$t3
.printf "DG8_LIVE_SUMMARY run_id=$runId rva=1170814 aex_sha256=$aexSha256 hit_count=%u\n", `@$t4
.logclose
q
"@
$cdbText | Set-Content -LiteralPath $cdbScript -Encoding ASCII
$env:OLM_DG_LIVE_REQUEST_DIR = Join-Path $PackageRoot 'request'
$env:OLM_DG_LIVE_WORK_ROOT = $work
$env:OLM_DG_LIVE_RUN_ID = $runId
Start-Process -FilePath $cdb -ArgumentList @('-cf',$cdbScript,$afterFx,'-r',$queue) -RedirectStandardOutput $trace -RedirectStandardError ($trace+'.err') -NoNewWindow -PassThru -Wait | Out-Null
$parsed = Parse $trace
$parsed | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $work 'RETURN_RUNTIME_TRACE.json') -Encoding UTF8
$parsed | ConvertTo-Json -Depth 8
if ($parsed.status -ne 'answered') { exit 2 }
'''


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
    args = parser.parse_args()
    if not TYPED.is_dir():
        raise FileNotFoundError(TYPED)
    if PACKAGE.exists():
        shutil.rmtree(PACKAGE)
    (PACKAGE / "artifacts").mkdir(parents=True)
    (PACKAGE / "scripts").mkdir(parents=True)
    (PACKAGE / "request").mkdir(parents=True)
    (PACKAGE / "fixtures").mkdir(parents=True)
    (PACKAGE / "artifacts/run_olmdistancegradation_8bpc_hook_liveness_20260713.ps1").write_text(RUNNER, encoding="utf-8")
    (PACKAGE / "scripts/ae_render_olmdistancegradation_8bpc_hook_liveness_queue.jsx").write_text(QUEUE, encoding="utf-8")
    shutil.copy2(TYPED / "scripts/ae_render_single_case.jsx", PACKAGE / "scripts/ae_render_single_case.jsx")
    shutil.copytree(TYPED / "request", PACKAGE / "request", dirs_exist_ok=True)
    (PACKAGE / "README_RUNTIME_TRACE.md").write_text(README, encoding="utf-8")
    (PACKAGE / "runtime_trace_package_manifest.json").write_text(json.dumps({
        "schema": 1, "kind": "olm_runtime_trace_request_package", "profile": "distancegradation-8bpc-current-aex-hook-liveness",
        "request_id": REQUEST_ID, "submission_status": "ready", "sendable": True,
        "runtime_actions": [{"request_id": REQUEST_ID, "status": "ready", "mode": "external-trace",
            "plugin_area": "OLMDistanceGradation current-AEX hook liveness only", "rvas": list(RVA),
            "stop_condition": "Return one shared run_id and aex_sha256 plus one nonnegative hit_count for each RVA; zero hits is valid. No algorithm proof."}]
    }, indent=2) + "\n", encoding="utf-8")
    (PACKAGE / "RETURN_RUNTIME_TRACE_TEMPLATE.json").write_text(json.dumps({
        "schema": "olmdg_8bpc_hook_liveness_v1", "kind": "olm_runtime_trace_result", "status": "answered | exact_bind_failure",
        "request_id": REQUEST_ID, "run_id": None, "aex_sha256": None,
        "rvas": [{"rva": rva, "hit_count": None} for rva in RVA]
    }, indent=2) + "\n", encoding="utf-8")
    complete = "\n".join(f"DG8_LIVE_SUMMARY run_id=dglive-fixture rva={rva} aex_sha256={'a'*64} hit_count={i}" for i, rva in enumerate(RVA)) + "\n"
    missing = "\n".join(f"DG8_LIVE_SUMMARY run_id=dglive-fixture rva={rva} aex_sha256={'a'*64} hit_count=0" for rva in RVA[:-1]) + "\n"
    (PACKAGE / "fixtures/complete_cdb_stdout.txt").write_text(complete, encoding="utf-8")
    (PACKAGE / "fixtures/missing_rva_cdb_stdout.txt").write_text(missing, encoding="utf-8")
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in PACKAGE.rglob("*") if p.is_file()):
            archive.write(path, path.relative_to(PACKAGE).as_posix())
    print(f"[OK] built hook-liveness package: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
