#!/usr/bin/env python3
"""Build the sendable DG 8bpc same-run typed-boundary v4 package."""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712"
OUTPUT = PACKAGE.with_suffix(".zip")
CURRENT_RENDERER = ROOT / "scripts/ae_render_single_case.jsx"
REQUEST_SOURCE = PACKAGE / "request"
REQUEST_ID = "olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712"
AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
CASES = ("case_0001", "case_0015", "case_0029")
STAGES = ("FIELD_IN", "FIELD_OUT", "COMPOSE_IN", "COMPOSE_OUT", "HOST_STORE")


README = f"""# OLMDistanceGradation 8bpc Current-AEX Typed Boundary v4

Status: ready and sendable.

This request extends the accepted desktop depth-control launch contract into a
three-case typed capture. The accepted control used run prefix `dglive-983b`,
AE PID `5936`, module base `0x7fffcd660000`, AEX SHA-256 `{AEX_SHA256}`, an
8bpc project, PF8 `+0x1170870` hit count `24377`, and PF32 `+0x1170c90` hit
count `0`. Those PID/base values identify the accepted prior run; the v4
runner discovers and returns the fresh run's actual PID/base and requires one
identity across all three captures.

The runner launches After Effects normally in the caller's desktop session.
For each of `case_0001`, `case_0015`, and `case_0029`, the included renderer
pauses only after `effect_loaded=1` and `parameters_applied=1`. The runner then
finds exactly one matching AfterFX process, pins the loaded module to the
expected hash, and attaches CDB. Initially only PF8 and PF32 depth-control
breakpoints are armed. The PF8 exact-coordinate hit at `(397,281)` emits
`DG8_DEPTH_CONTROL_CONFIRMED` and only then arms the typed PF8 sites.

The five required records are `FIELD_IN`, `FIELD_OUT`, `COMPOSE_IN`,
`COMPOSE_OUT`, and `HOST_STORE`. Every record binds the same run ID, AE PID,
module base, AEX hash, project depth, case, coordinate, and live output address.
Field/source base, rowbytes, pixel size, exact address formulas, byte values,
normalized field scalars, pre-store floats, and final host bytes are retained.

Run:

`artifacts/run_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712.ps1`

`-ParseOnly -TracePath <combined_cdb_trace.txt>` runs the same fail-closed
trace classifier. The return embeds raw launcher, CDB, AE, readiness, and queue
logs on both success and failure; the work directory also retains each file.
No partial status is accepted.
"""


QUEUE = r'''/* One desktop AE process, serial readiness handshakes, three typed cases. */
(function () {
    function env(name) { try { return $.getenv(name) || ""; } catch (e) { return ""; } }
    function write(path, text, append) { var f = new File(path); f.encoding = "UTF-8"; if (f.open(append ? "a" : "w")) { f.write(text); f.close(); } }
    var root = File($.fileName).parent.parent.fsName;
    var requestDir = env("OLM_DG_LIVE_REQUEST_DIR");
    var workRoot = env("OLM_DG_LIVE_WORK_ROOT");
    var runId = env("OLM_DG_LIVE_RUN_ID");
    if (!requestDir || !workRoot || !runId) { throw new Error("typed request/work/run binding is required"); }
    var cases = ["case_0001", "case_0015", "case_0029"];
    var queueLog = workRoot + "/AE_TYPED_QUEUE.log";
    write(queueLog, "OLMDG8_QUEUE_START run_id=" + runId + "\n", false);
    for (var i = 0; i < cases.length; i++) {
        var caseId = cases[i];
        $.setenv("OLM_AE_REQUEST_DIR", requestDir);
        $.setenv("OLM_AE_CASE_ID", caseId);
        $.setenv("OLM_AE_OUTPUT_DIR", workRoot + "/single_case_output/" + caseId);
        $.setenv("OLM_AE_LOG_PATH", workRoot + "/AE_SINGLE_CASE_" + caseId + ".log");
        $.setenv("OLM_AE_RESULT_JSON", workRoot + "/AE_SINGLE_CASE_" + caseId + ".json");
        $.setenv("OLM_AE_READY_MARKER", workRoot + "/ae_ready_" + caseId + ".marker");
        $.setenv("OLM_AE_CONTINUE_MARKER", workRoot + "/ae_continue_" + caseId + ".marker");
        $.setenv("OLM_AE_KEEP_OPEN", i === cases.length - 1 ? "0" : "1");
        $.setenv("OLM_AE_FORCE_NEW_PROJECT", i === 0 ? "1" : "0");
        write(queueLog, "OLMDG8_CASE_START run_id=" + runId + " case_id=" + caseId + "\n", true);
        $.evalFile(new File(root + "/scripts/ae_render_single_case.jsx"));
        write(queueLog, "OLMDG8_CASE_END run_id=" + runId + " case_id=" + caseId + "\n", true);
    }
    write(queueLog, "OLMDG8_QUEUE_END run_id=" + runId + "\n", true);
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
$requestId = 'olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712'
$expectedHash = 'a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae'
$cases = @('case_0001','case_0015','case_0029')
$requiredStages = @('FIELD_IN','FIELD_OUT','COMPOSE_IN','COMPOSE_OUT','HOST_STORE')
$runId = 'dg8typed-' + ([guid]::NewGuid().ToString('N'))

function Failure([string]$stage, [string]$reason, [object[]]$missing, [string]$last) {
  [ordered]@{status='exact_bind_failure';kind='typed_boundary';request_id=$requestId;failure=[ordered]@{stage=$stage;reason=$reason;missing_fields=@($missing);last_observation=$last}}
}
function Parse([string]$path) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return Failure 'typed_boundary' 'missing combined CDB trace' @('trace') '' }
  $rows = @{}; $depth = @{}; $last = ''
  foreach ($line in Get-Content -LiteralPath $path) {
    $last = $line
    if ($line -match '^DG8_DEPTH_SUMMARY\s+') {
      $m = @{}; foreach ($pair in [regex]::Matches($line,'(?<key>[a-z0-9_]+)=(?<value>[^\s]+)')) {$m[$pair.Groups['key'].Value]=$pair.Groups['value'].Value}
      if ($m.ContainsKey('case_id') -and $m.ContainsKey('rva')) {$depth["$($m.case_id)|$($m.rva)"]=$m}; continue
    }
    if ($line -notmatch '^DG8_(FIELD_IN|FIELD_OUT|COMPOSE_IN|COMPOSE_OUT|HOST_STORE)\s+') {continue}
    $stage = $Matches[1]; $m = @{}; foreach ($pair in [regex]::Matches($line,'(?<key>[a-z0-9_]+)=(?<value>[^\s]+)')) {$m[$pair.Groups['key'].Value]=$pair.Groups['value'].Value}
    if (-not ($m.ContainsKey('case_id') -and $m.ContainsKey('x') -and $m.ContainsKey('y'))) {continue}
    $key = "$($m.case_id)|$($m.x)|$($m.y)"; if (-not $rows.ContainsKey($key)) {$rows[$key]=[ordered]@{case_id=$m.case_id;x=$m.x;y=$m.y;stages=[ordered]@{}}}
    if ($rows[$key].stages.ContainsKey($stage)) {$rows[$key].stages[$stage]['duplicate']='1'} else {$rows[$key].stages[$stage]=$m}
  }
  $missing=@(); $identityFields=@('run_id','ae_pid','module_base','aex_sha256','project_bpc','case_id','x','y','output_addr')
  foreach ($case in $cases) {
    $key="$case|397|281"; if (-not $rows.ContainsKey($key)) {$missing+="missing:$key";continue}; $row=$rows[$key]
    foreach ($stage in $requiredStages) {
      if (-not $row.stages.ContainsKey($stage)) {$missing+="$key:$stage";continue}; $s=$row.stages[$stage]
      foreach ($field in $identityFields + @('typed_rgba')) {if (-not $s.ContainsKey($field)-or [string]::IsNullOrWhiteSpace([string]$s[$field])) {$missing+="$key:$stage:$field"}}
      if ($s.ContainsKey('duplicate')) {$missing+="$key:$stage:duplicate"}
      if ($s.typed_rgba -notmatch '^[^,]+,[^,]+,[^,]+,[^,]+$') {$missing+="$key:$stage:typed_rgba4"}
    }
    foreach ($stage in @('FIELD_IN','FIELD_OUT')) {foreach($field in @('field_base','field_rowbytes','field_addr','pixel_size','address_formula')) {if(-not $row.stages[$stage].ContainsKey($field)){$missing+="$key:$stage:$field"}}}
    foreach ($field in @('source_base','source_rowbytes','source_addr','field_green','x_before_invert','x_after_invert')) {if(-not $row.stages.COMPOSE_IN.ContainsKey($field)){$missing+="$key:COMPOSE_IN:$field"}}
    if (-not $row.stages.COMPOSE_OUT.ContainsKey('pre_store_rgba_float')) {$missing+="$key:COMPOSE_OUT:pre_store_rgba_float"}
    $ids=@($row.stages.Values|ForEach-Object{"$($_.run_id)|$($_.ae_pid)|$($_.module_base)|$($_.aex_sha256)|$($_.project_bpc)|$($_.output_addr)"}|Select-Object -Unique); if($ids.Count-ne 1){$missing+="$key:stage_identity"}
    foreach($rva in @('1170870','1170c90')) {$dk="$case|$rva";if(-not $depth.ContainsKey($dk)){$missing+="$key:depth_rva_$rva";continue};$d=$depth[$dk];foreach($field in @('run_id','ae_pid','module_base','aex_sha256','project_bpc','case_id','rva','hit_count')){if(-not$d.ContainsKey($field)-or[string]::IsNullOrWhiteSpace([string]$d[$field])){$missing+="$key:depth_rva_$rva:$field"}};if($d.run_id-ne$row.stages.FIELD_IN.run_id-or$d.ae_pid-ne$row.stages.FIELD_IN.ae_pid-or$d.module_base-ne$row.stages.FIELD_IN.module_base-or$d.aex_sha256-ne$row.stages.FIELD_IN.aex_sha256-or$d.project_bpc-ne'8'){$missing+="$key:depth_rva_$rva:identity"}}
    if($depth.ContainsKey("$case|1170870") -and [int]$depth["$case|1170870"].hit_count -le 0){$missing+="$key:PF8_hit_count_gt_0"}
    if($depth.ContainsKey("$case|1170c90") -and [int]$depth["$case|1170c90"].hit_count -ne 0){$missing+="$key:PF32_hit_count_eq_0"}
  }
  $selected=@($cases|ForEach-Object{$rows["$_|397|281"]}|Where-Object{$_}); $allStages=@($selected|ForEach-Object{$_.stages.Values})
  $runIds=@($allStages|ForEach-Object{$_.run_id}|Select-Object -Unique); $pids=@($allStages|ForEach-Object{$_.ae_pid}|Select-Object -Unique); $bases=@($allStages|ForEach-Object{$_.module_base}|Select-Object -Unique); $hashes=@($allStages|ForEach-Object{([string]$_.aex_sha256).ToLowerInvariant()}|Select-Object -Unique); $depths=@($allStages|ForEach-Object{$_.project_bpc}|Select-Object -Unique)
  if($runIds.Count-ne 1){$missing+='shared_run_id'};if($pids.Count-ne 1-or$pids[0]-notmatch'^\d+$'){$missing+='shared_ae_pid'};if($bases.Count-ne 1-or$bases[0]-notmatch'^0x[0-9a-fA-F]+$'){$missing+='shared_module_base'};if($hashes.Count-ne 1-or$hashes[0]-ne$expectedHash){$missing+='shared_expected_aex_sha256'};if($depths.Count-ne 1-or$depths[0]-ne'8'){$missing+='shared_project_bpc_8'}
  if($missing.Count){return Failure 'typed_boundary' 'typed stages or depth/module identity are incomplete or mismatched' $missing $last}
  [ordered]@{status='answered';kind='typed_boundary';request_id=$requestId;run_id=$runIds[0];ae_pid=[int]$pids[0];module_base=$bases[0];aex_sha256=$hashes[0];project_bits_per_channel=8;rvas=@([ordered]@{rva='1170870';hit_count=($cases|ForEach-Object{[int]$depth["$_|1170870"].hit_count}|Measure-Object -Sum).Sum},[ordered]@{rva='1170c90';hit_count=0});cases=$selected}
}
if($ParseOnly){if(-not$TracePath){throw '-ParseOnly requires -TracePath'};(Parse $TracePath)|ConvertTo-Json -Depth 14;exit 0}

$work=Join-Path $WorkRoot "olmdg_typed_$runId";New-Item -ItemType Directory -Force -Path $work|Out-Null;$work=(Get-Item -LiteralPath $work).FullName
$returnPath=Join-Path $work 'RETURN_RUNTIME_TRACE.json';$combinedTrace=Join-Path $work 'combined_cdb_trace.txt';$launchStdout=Join-Path $work 'afterfx_launcher_stdout.txt';$launchStderr=Join-Path $work 'afterfx_launcher_stderr.txt';$queueLog=Join-Path $work 'AE_TYPED_QUEUE.log'
$sessionId=(Get-Process -Id $PID).SessionId;$launch=$null;$ae=$null;$cdb=$null;$launchStarted=$false
function ReadOrNull([string]$path){if(Test-Path -LiteralPath $path -PathType Leaf){Get-Content -LiteralPath $path -Raw}else{$null}}
function Get-AfterFxState {@(Get-CimInstance Win32_Process -Filter "Name='AfterFX.exe'" -ErrorAction SilentlyContinue|Where-Object{$_.SessionId-eq$sessionId-and$_.ExecutablePath-and[IO.Path]::GetFullPath($_.ExecutablePath)-ieq$AfterFxPath}|ForEach-Object{[ordered]@{pid=[int]$_.ProcessId;parent_pid=[int]$_.ParentProcessId;session_id=[int]$_.SessionId;path=$_.ExecutablePath;command_line=$_.CommandLine}})}
function LauncherState {if($null-eq$launch){return $null};try{$launch.Refresh()}catch{};$exit=$null;if($launch.HasExited){try{$exit=$launch.ExitCode}catch{}};[ordered]@{pid=$launch.Id;launcher_exited=$launch.HasExited;launcher_exit_code=$exit}}
function RawLogs {[ordered]@{work_directory=$work;launcher_stdout=(ReadOrNull $launchStdout);launcher_stderr=(ReadOrNull $launchStderr);queue_log=(ReadOrNull $queueLog);combined_cdb_trace=(ReadOrNull $combinedTrace);cases=@($cases|ForEach-Object{[ordered]@{case_id=$_;ready_marker=(ReadOrNull (Join-Path $work "ae_ready_$_.marker"));cdb_trace=(ReadOrNull (Join-Path $work "cdb_trace_$_.txt"));cdb_stdout=(ReadOrNull (Join-Path $work "cdb_stdout_$_.txt"));cdb_stderr=(ReadOrNull (Join-Path $work "cdb_stderr_$_.txt"));ae_log=(ReadOrNull (Join-Path $work "AE_SINGLE_CASE_$_.log"));ae_result=(ReadOrNull (Join-Path $work "AE_SINGLE_CASE_$_.json"))}});process_diagnostics=[ordered]@{executable_path=$AfterFxPath;session_id=$sessionId;launcher=(LauncherState);candidate_afterfx=@(Get-AfterFxState)}}}
function Finish([object]$body,[int]$code){
  if($code-ne0){foreach($case in $cases){$ready=Join-Path $work "ae_ready_$case.marker";$continue=Join-Path $work "ae_continue_$case.marker";if((Test-Path $ready)-and-not(Test-Path $continue)){Set-Content $continue 'abort' -Encoding ASCII -ErrorAction SilentlyContinue}};if($cdb-and-not$cdb.HasExited){Stop-Process $cdb.Id -Force -ErrorAction SilentlyContinue};if($launchStarted){foreach($state in @(Get-AfterFxState)){Stop-Process $state.pid -Force -ErrorAction SilentlyContinue}}}
  $body['raw_logs']=RawLogs;$json=$body|ConvertTo-Json -Depth 16;$json|Set-Content $returnPath -Encoding UTF8;$json;exit $code
}
$queue=Join-Path $PackageRoot 'scripts\ae_render_olmdistancegradation_8bpc_queue.jsx'
foreach($path in @($AexPath,$AfterFxPath,$CdbPath,$queue)){if(-not(Test-Path -LiteralPath $path -PathType Leaf)){Finish (Failure 'preflight' "required file missing: $path" @('preflight_file') '') 2}}
if(Get-Process -Name AfterFX -ErrorAction SilentlyContinue){Finish (Failure 'desktop_launch' 'After Effects must be fully closed before this run' @('fresh_AfterFX_process') '') 2}
$AexPath=(Get-Item $AexPath).FullName;$AfterFxPath=(Get-Item $AfterFxPath).FullName;$CdbPath=(Get-Item $CdbPath).FullName;$aexSha256=(Get-FileHash $AexPath -Algorithm SHA256).Hash.ToLowerInvariant();if($aexSha256-ne$expectedHash){Finish (Failure 'module_hash' 'DistanceGradation.aex is not the accepted current binary' @('expected_aex_sha256') "actual=$aexSha256") 2}
$env:OLM_DG_LIVE_REQUEST_DIR=Join-Path $PackageRoot 'request';$env:OLM_DG_LIVE_WORK_ROOT=$work;$env:OLM_DG_LIVE_RUN_ID=$runId;$env:OLM_AE_PAUSE_BEFORE_RENDER='1';$env:OLM_AE_PAUSE_TIMEOUT_SECONDS='300';$env:OLM_AE_FORCE_SOFTWARE='1'
$launch=Start-Process -FilePath $AfterFxPath -ArgumentList @('-m','-r',$queue) -RedirectStandardOutput $launchStdout -RedirectStandardError $launchStderr -PassThru;$launchStarted=$true
$boundPid=$null;$boundBase=$null
foreach($case in $cases){
  $ready=Join-Path $work "ae_ready_$case.marker";$continue=Join-Path $work "ae_continue_$case.marker";$result=Join-Path $work "AE_SINGLE_CASE_$case.json";$deadline=(Get-Date).AddSeconds(180);while((Get-Date)-lt$deadline-and-not(Test-Path $ready)){Start-Sleep -Milliseconds 250}
  if(-not(Test-Path $ready -PathType Leaf)){Finish (Failure 'readiness' "AE ready marker missing for $case" @("ae_ready_$case.marker") '') 2};$readyText=Get-Content $ready -Raw;if($readyText-notmatch"case_id=$case"-or$readyText-notmatch'effect_loaded=1'-or$readyText-notmatch'parameters_applied=1'){Finish (Failure 'readiness' "AE marker is not render-ready for $case" @('case_id','effect_loaded=1','parameters_applied=1') $readyText) 2}
  $loaded=@();$deadline=(Get-Date).AddSeconds(30);while((Get-Date)-lt$deadline-and$loaded.Count-ne1){$loaded=@(Get-AfterFxState|ForEach-Object{$p=Get-Process -Id $_.pid -ErrorAction SilentlyContinue;try{$m=$p.Modules|Where-Object{$_.FileName-ieq$AexPath}|Select-Object -First 1;if($m){[pscustomobject]@{Process=$p;Module=$m}}}catch{}});if($loaded.Count-ne1){Start-Sleep -Milliseconds 250}}
  if($loaded.Count-ne1){Finish (Failure 'desktop_process_discovery' "exactly one loaded module was not found for $case" @('actual_ae_process_module') "matches=$($loaded.Count)") 2};$ae=$loaded[0].Process;$module=$loaded[0].Module;$loadedHash=(Get-FileHash $module.FileName -Algorithm SHA256).Hash.ToLowerInvariant();$base=('0x{0:x}'-f$module.BaseAddress.ToInt64())
  if($loadedHash-ne$expectedHash){Finish (Failure 'module_hash' 'loaded module hash mismatch' @('loaded_aex_sha256') "actual=$loadedHash") 2};if($null-eq$boundPid){$boundPid=$ae.Id;$boundBase=$base}elseif($ae.Id-ne$boundPid-or$base-ne$boundBase){Finish (Failure 'same_run_identity' 'AE PID or module base changed between cases' @('shared_ae_pid','shared_module_base') "pid=$($ae.Id) base=$base") 2}
  $baseValue=$module.BaseAddress.ToInt64();$pf8=('0x{0:x}'-f($baseValue+0x1170870));$pf32=('0x{0:x}'-f($baseValue+0x1170c90));$fieldOut=('0x{0:x}'-f($baseValue+0x117098f));$composeIn=('0x{0:x}'-f($baseValue+0x1170a09));$composeOut=('0x{0:x}'-f($baseValue+0x1170c11));$hostStore=('0x{0:x}'-f($baseValue+0x1170c40));$trace=Join-Path $work "cdb_trace_$case.txt";$stdout=Join-Path $work "cdb_stdout_$case.txt";$stderr=Join-Path $work "cdb_stderr_$case.txt";$script=Join-Path $work "typed_$case.cdb"
  $cdbText=@"
.effmach amd64
.expr /s masm
sxi 80000003
.logopen "$trace"
r @`$t0=0
r @`$t1=0
bp $pf32 ".printf \"DG8_DEPTH_HIT run_id=$runId ae_pid=$boundPid module_base=$boundBase aex_sha256=$aexSha256 project_bpc=8 case_id=$case rva=1170c90 hit_count=1\\n\";r @`$t1=@`$t1+1;gc"
bp $pf8 ".if (@edx==397 && @r8d==281) {r @`$t0=@`$t0+1;r @`$t2=poi(@rcx+8);r @`$t3=poi(@rcx);r @`$t4=poi(@rsp+28);r @`$t5=poi(@`$t2+18);r @`$t6=dwo(@`$t2+20);r @`$t7=@`$t5+(281*@`$t6)+(397*4);r @`$t8=poi(@`$t3+18)+(281*dwo(@`$t3+20))+(397*4);.printf \"DG8_DEPTH_CONTROL_CONFIRMED run_id=$runId ae_pid=$boundPid module_base=$boundBase aex_sha256=$aexSha256 project_bpc=8 case_id=$case x=397 y=281 output_addr=%p\\n\",@`$t4;.printf \"DG8_FIELD_IN run_id=$runId ae_pid=$boundPid module_base=$boundBase aex_sha256=$aexSha256 project_bpc=8 case_id=$case x=397 y=281 output_addr=%p field_base=%p field_rowbytes=%x field_addr=%p pixel_size=4 address_formula=base+y*rowbytes+x*4 typed_rgba=%02x,%02x,%02x,%02x\\n\",@`$t4,@`$t5,@`$t6,@`$t7,by(@`$t7+1),by(@`$t7+2),by(@`$t7+3),by(@`$t7);bp $fieldOut \".if (@rcx==@`$t7) {.printf \\\"DG8_FIELD_OUT run_id=$runId ae_pid=$boundPid module_base=$boundBase aex_sha256=$aexSha256 project_bpc=8 case_id=$case x=397 y=281 output_addr=%p field_base=%p field_rowbytes=%x field_addr=%p pixel_size=4 address_formula=base+y*rowbytes+x*4 typed_rgba=%02x,%02x,%02x,%02x\\\\n\\\",@`$t4,@`$t5,@`$t6,@rcx,by(@rcx+1),by(@rcx+2),by(@rcx+3),by(@rcx)};gc\";bp $composeIn \".if (@r10==@`$t8) {.printf \\\"DG8_COMPOSE_IN run_id=$runId ae_pid=$boundPid module_base=$boundBase aex_sha256=$aexSha256 project_bpc=8 case_id=$case x=397 y=281 output_addr=%p source_base=%p source_rowbytes=%x source_addr=%p pixel_size=4 address_formula=base+y*rowbytes+x*4 field_green=%02x x_before_invert=%f x_after_invert=%f typed_rgba=%02x,%02x,%02x,%02x\\\\n\\\",@`$t4,poi(@`$t3+18),dwo(@`$t3+20),@r10,by(@`$t7+1),@xmm1,@xmm2,by(@r10+1),by(@r10+2),by(@r10+3),by(@r10)};gc\";bp $composeOut \".if (@rdi==@`$t4) {.printf \\\"DG8_COMPOSE_OUT run_id=$runId ae_pid=$boundPid module_base=$boundBase aex_sha256=$aexSha256 project_bpc=8 case_id=$case x=397 y=281 output_addr=%p pre_store_rgba_float=%f,%f,%f,%f typed_rgba=%f,%f,%f,%f\\\\n\\\",@`$t4,@xmm1,@xmm5,@xmm3,@xmm6,@xmm1,@xmm5,@xmm3,@xmm6};gc\";bp $hostStore \".if (@rdi==@`$t4) {.printf \\\"DG8_HOST_STORE run_id=$runId ae_pid=$boundPid module_base=$boundBase aex_sha256=$aexSha256 project_bpc=8 case_id=$case x=397 y=281 output_addr=%p typed_rgba=%02x,%02x,%02x,%02x\\\\n\\\",@`$t4,by(@rdi+1),by(@rdi+2),by(@rdi+3),by(@rdi);.printf \\\"DG8_DEPTH_SUMMARY run_id=$runId ae_pid=$boundPid module_base=$boundBase aex_sha256=$aexSha256 project_bpc=8 case_id=$case rva=1170870 hit_count=%u\\\\n\\\",@`$t0;.printf \\\"DG8_DEPTH_SUMMARY run_id=$runId ae_pid=$boundPid module_base=$boundBase aex_sha256=$aexSha256 project_bpc=8 case_id=$case rva=1170c90 hit_count=%u\\\\n\\\",@`$t1;.detach;q};gc\";.echo DG8_TYPED_BREAKPOINTS_ARMED_AFTER_DEPTH_CONTROL;gc} .else {gc}"
.echo DG8_DEPTH_BREAKPOINTS_ARMED
g
"@
  $cdbText|Set-Content $script -Encoding ASCII;$cdb=Start-Process -FilePath $CdbPath -ArgumentList ('-cf "'+$script+'" -p '+$boundPid) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -NoNewWindow -PassThru;$deadline=(Get-Date).AddSeconds(60);while((Get-Date)-lt$deadline){if((Test-Path $trace)-and((Get-Content $trace -Raw)-match'DG8_DEPTH_BREAKPOINTS_ARMED')){break};if($cdb.HasExited){break};Start-Sleep -Milliseconds 250;$cdb.Refresh()};if(-not(Test-Path $trace)-or-not((Get-Content $trace -Raw)-match'DG8_DEPTH_BREAKPOINTS_ARMED')){Finish (Failure 'depth_control' "CDB did not arm depth controls for $case" @('DG8_DEPTH_BREAKPOINTS_ARMED') '') 2}
  Set-Content $continue 'continue' -Encoding ASCII;$deadline=(Get-Date).AddSeconds(240);while((Get-Date)-lt$deadline-and-not$cdb.HasExited){Start-Sleep -Milliseconds 250;$cdb.Refresh()};if(-not$cdb.HasExited){Finish (Failure 'typed_boundary' "CDB did not complete exact typed capture for $case" @('cdb_exit') '') 2};if(Test-Path $trace){Get-Content $trace|Add-Content $combinedTrace}
  $deadline=(Get-Date).AddSeconds(180);while((Get-Date)-lt$deadline-and-not(Test-Path $result)){Start-Sleep -Milliseconds 250};if(-not(Test-Path $result)){Finish (Failure 'render_result' "AE result missing for $case" @("AE_SINGLE_CASE_$case.json") '') 2};$aeResult=Get-Content $result -Raw|ConvertFrom-Json;if($aeResult.status-ne'ok'-or[int]$aeResult.project_bits_per_channel-ne8){Finish (Failure 'depth_control' "AE did not complete $case at 8bpc" @('status=ok','project_bits_per_channel=8') ($aeResult|ConvertTo-Json -Compress)) 2}
}
$parsed=Parse $combinedTrace;if($parsed.status-eq'answered'-and($parsed.ae_pid-ne$boundPid-or$parsed.module_base-ne$boundBase-or$parsed.aex_sha256-ne$aexSha256)){$parsed=Failure 'same_run_identity' 'parsed trace differs from located process/module' @('summary_process_module_identity') ($parsed|ConvertTo-Json -Compress)};Finish $parsed $(if($parsed.status-eq'answered'){0}else{2})
'''


def fixture_line(stage: str, case: str, *, pid: int = 5936, hash_value: str = AEX_SHA256) -> str:
    common = (
        f"run_id=dg8typed-fixture ae_pid={pid} module_base=0x7fffcd660000 "
        f"aex_sha256={hash_value} project_bpc=8 case_id={case} x=397 y=281 output_addr=0x1000"
    )
    details = {
        "FIELD_IN": "field_base=0x2000 field_rowbytes=1e00 field_addr=0x3000 pixel_size=4 address_formula=base+y*rowbytes+x*4 typed_rgba=01,02,03,ff",
        "FIELD_OUT": "field_base=0x2000 field_rowbytes=1e00 field_addr=0x3000 pixel_size=4 address_formula=base+y*rowbytes+x*4 typed_rgba=01,02,03,ff",
        "COMPOSE_IN": "source_base=0x4000 source_rowbytes=1e00 source_addr=0x5000 pixel_size=4 address_formula=base+y*rowbytes+x*4 field_green=02 x_before_invert=0.007843 x_after_invert=0.992157 typed_rgba=10,20,30,ff",
        "COMPOSE_OUT": "pre_store_rgba_float=1.0,2.0,3.0,255.0 typed_rgba=1.0,2.0,3.0,255.0",
        "HOST_STORE": "typed_rgba=01,02,03,ff",
    }[stage]
    return f"DG8_{stage} {common} {details}"


def build_fixture(*, omit: tuple[str, str] | None = None, drift_pid: bool = False, wrong_hash: bool = False, wrong_depth: bool = False) -> str:
    lines: list[str] = []
    for case in CASES:
        for stage in STAGES:
            if omit == (case, stage):
                continue
            pid = 6000 if drift_pid and case == "case_0029" and stage == "HOST_STORE" else 5936
            hash_value = "0" * 64 if wrong_hash and case == "case_0015" else AEX_SHA256
            lines.append(fixture_line(stage, case, pid=pid, hash_value=hash_value))
        depth = 16 if wrong_depth and case == "case_0029" else 8
        lines.append(f"DG8_DEPTH_SUMMARY run_id=dg8typed-fixture ae_pid=5936 module_base=0x7fffcd660000 aex_sha256={AEX_SHA256} project_bpc={depth} case_id={case} rva=1170870 hit_count=1")
        lines.append(f"DG8_DEPTH_SUMMARY run_id=dg8typed-fixture ae_pid=5936 module_base=0x7fffcd660000 aex_sha256={AEX_SHA256} project_bpc=8 case_id={case} rva=1170c90 hit_count=0")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if not CURRENT_RENDERER.is_file() or not REQUEST_SOURCE.is_dir():
        raise FileNotFoundError("current renderer or typed request assets are missing")

    request_tmp = ROOT / ".tmp_olmdg_typed_request"
    if request_tmp.exists():
        shutil.rmtree(request_tmp)
    shutil.copytree(REQUEST_SOURCE, request_tmp)
    if PACKAGE.exists():
        shutil.rmtree(PACKAGE)
    (PACKAGE / "artifacts").mkdir(parents=True)
    (PACKAGE / "scripts").mkdir()
    (PACKAGE / "fixtures").mkdir()
    shutil.copytree(request_tmp, PACKAGE / "request")
    shutil.rmtree(request_tmp)
    (PACKAGE / "artifacts/run_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712.ps1").write_text(RUNNER, encoding="utf-8")
    (PACKAGE / "scripts/ae_render_olmdistancegradation_8bpc_queue.jsx").write_text(QUEUE, encoding="utf-8")
    shutil.copy2(CURRENT_RENDERER, PACKAGE / "scripts/ae_render_single_case.jsx")
    (PACKAGE / "README_RUNTIME_TRACE.md").write_text(README, encoding="utf-8")
    manifest = {
        "schema": 4,
        "kind": "olm_runtime_trace_request_package",
        "profile": "distancegradation-8bpc-current-aex-same-run-typed-boundary-v4",
        "request_id": REQUEST_ID,
        "submission_status": "ready",
        "sendable": True,
        "entrypoint": "README_RUNTIME_TRACE.md",
        "accepted_depth_control": {"run_id_prefix": "dglive-983b", "ae_pid": 5936, "module_base": "0x7fffcd660000", "aex_sha256": AEX_SHA256, "project_bits_per_channel": 8, "rvas": [{"rva": "1170870", "hit_count": 24377}, {"rva": "1170c90", "hit_count": 0}]},
        "runtime_actions": [{"request_id": REQUEST_ID, "status": "ready", "mode": "external-trace", "plugin_area": "OLMDistanceGradation PF8 typed field/compose/host boundary", "cases": list(CASES), "xy": [397, 281], "stages": list(STAGES), "stop_condition": "Return answered only for 15 typed records plus PF8>0/PF32=0, one run/PID/base/hash/depth identity, and one output address within each case. Otherwise exact_bind_failure with raw logs."}],
    }
    (PACKAGE / "runtime_trace_package_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    template = {"schema": "olmdg_8bpc_current_aex_typed_boundary_v4", "kind": "typed_boundary", "status": "answered | exact_bind_failure", "request_id": REQUEST_ID, "run_id": None, "ae_pid": None, "module_base": None, "aex_sha256": AEX_SHA256, "project_bits_per_channel": 8, "rvas": [{"rva": "1170870", "hit_count": None}, {"rva": "1170c90", "hit_count": None}], "cases": [{"case_id": case, "xy": [397, 281], "output_addr": None, "stages": list(STAGES)} for case in CASES], "raw_logs": {"launcher_stdout": None, "launcher_stderr": None, "queue_log": None, "combined_cdb_trace": None, "cases": []}}
    (PACKAGE / "RETURN_RUNTIME_TRACE_TEMPLATE.json").write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
    (PACKAGE / "fixtures/complete_cdb_stdout.txt").write_text(build_fixture(), encoding="utf-8")
    (PACKAGE / "fixtures/missing_stage_cdb_stdout.txt").write_text(build_fixture(omit=("case_0015", "COMPOSE_OUT")), encoding="utf-8")
    (PACKAGE / "fixtures/identity_drift_cdb_stdout.txt").write_text(build_fixture(drift_pid=True), encoding="utf-8")
    (PACKAGE / "fixtures/wrong_hash_cdb_stdout.txt").write_text(build_fixture(wrong_hash=True), encoding="utf-8")
    (PACKAGE / "fixtures/wrong_depth_cdb_stdout.txt").write_text(build_fixture(wrong_depth=True), encoding="utf-8")

    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in PACKAGE.rglob("*") if p.is_file()):
            info = zipfile.ZipInfo(path.relative_to(PACKAGE).as_posix(), (2026, 7, 13, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    print(f"[OK] built sendable typed-boundary v4 package: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
