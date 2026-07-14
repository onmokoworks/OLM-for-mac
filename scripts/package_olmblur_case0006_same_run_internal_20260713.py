#!/usr/bin/env python3
"""Build the narrow OLMBlur case_0006 same-run RGB16 witness package."""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625"
RENDERER = ROOT / "scripts/ae_render_single_case.jsx"
PACKAGE = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmblur_case0006_same_run_internal_20260713"
OUTPUT = PACKAGE.with_suffix(".zip")
REQUEST_ID = "olmblur_case0006_same_run_internal_20260713"
CASE_ID = "olmblur__case_0006"
SOURCE_CASE_ID = CASE_ID
AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
POINTS = ((29, 71, "capture"), (314, 14, "control"))
IDENTITY = "run_id=blur16-fixture ae_pid=6106 module_base=0x7ff800000000 aex_sha256=" + AEX_SHA256 + " project_bpc=16 renderer=Software case_id=olmblur__case_0006"


README = f"""# OLMBlur case_0006 same-run Windows internal witness

Status: ready and sendable.

This request performs one fresh desktop After Effects run with the current
hash-pinned `OLMBlur.aex`, a 16bpc Software project, and only `case_0006`.
It captures the Non-Legacy worker entry (RVA `0x2280`) and the standard RGB16
writer's final pre-store and post-store values at capture `(29,71)` and control
`(314,14)`. The PNG is exported by that same renderer invocation and retained
with its SHA-256, byte size, 16-bit pixel samples, run ID, AE PID, module base,
and AEX hash.

Run from the interactive Windows desktop session:

`artifacts/run_olmblur_case0006_same_run_internal_20260713.ps1`

The defaults target the verified Windows installation: AE 2025 and the
common MediaCore OLM folder. Override `-AexPath` or `-AfterFxPath` only when
the same hash-pinned plug-in is installed elsewhere.

The runner expects exactly one AE 2025 process to already be open in the
interactive Windows desktop session, then dispatches the queue JSX into that
process. Before the OLMBlur queue, it dispatches a tiny JSX probe and requires
the probe marker; probe failure is a dispatch failure, not an algorithm result.
Use -LaunchAfterFx only for an explicit launch experiment. It waits
for effect_loaded=1 and parameters_applied=1, discovers exactly one matching
process with the pinned module loaded, and only then attaches CDB.
Any missing/duplicate typed record, address mismatch, identity drift, wrong
depth/renderer/hash, stale or non-16-bit PNG, failed render, or missing raw log
returns `exact_bind_failure`. No partial answer is accepted.
"""


QUEUE = r'''/* One desktop AE process, one 16bpc case, one exported PNG. */
(function () {
    function env(name) { try { return $.getenv(name) || ""; } catch (_) { return ""; } }
    function write(path, text, append) { var f = new File(path); f.encoding = "UTF-8"; if (!f.open(append ? "a" : "w")) { throw new Error("could not write " + path); } f.write(text); f.close(); }
    var root = File($.fileName).parent.parent.fsName;
    var requestDir = env("OLM_BLUR16_REQUEST_DIR");
    var workRoot = env("OLM_BLUR16_WORK_ROOT");
    var runId = env("OLM_BLUR16_RUN_ID");
    if (!requestDir || !workRoot || !runId) { throw new Error("request/work/run binding is required"); }
    var queueLog = workRoot + "/AE_BLUR16_QUEUE.log";
    write(queueLog, "BLUR16_QUEUE_START run_id=" + runId + " case_id=olmblur__case_0006\n", false);
    $.setenv("OLM_AE_REQUEST_DIR", requestDir);
    $.setenv("OLM_AE_CASE_ID", "olmblur__case_0006");
    $.setenv("OLM_AE_OUTPUT_DIR", workRoot + "/export");
    $.setenv("OLM_AE_LOG_PATH", workRoot + "/AE_SINGLE_CASE.log");
    $.setenv("OLM_AE_RESULT_JSON", workRoot + "/AE_SINGLE_CASE.json");
    $.setenv("OLM_AE_READY_MARKER", workRoot + "/ae_ready.marker");
    $.setenv("OLM_AE_CONTINUE_MARKER", workRoot + "/ae_continue.marker");
    $.setenv("OLM_AE_KEEP_OPEN", "0");
    $.setenv("OLM_AE_FORCE_NEW_PROJECT", "1");
    $.evalFile(new File(root + "/scripts/ae_render_single_case.jsx"));
    write(queueLog, "BLUR16_QUEUE_END run_id=" + runId + " case_id=olmblur__case_0006\n", true);
}());
'''


DISPATCH_PROBE = r'''/* Prove that JSX reaches the pre-opened interactive AE process. */
(function () {
    function env(name) { try { return $.getenv(name) || ""; } catch (_) { return ""; } }
    function write(path, text) {
        var f = new File(path); f.encoding = "UTF-8";
        if (!f.open("w")) { throw new Error("could not write " + path); }
        f.write(text); f.close();
    }
    var marker = env("OLM_AE_DISPATCH_PROBE_MARKER");
    var log = env("OLM_AE_DISPATCH_PROBE_LOG");
    if (!marker || !log) { throw new Error("probe marker/log binding is required"); }
    var version = ""; var project = "";
    try { version = String(app.version); } catch (_) { version = "unknown"; }
    try { project = app.project ? String(app.project.file ? app.project.file.fsName : "") : ""; } catch (_) { project = "unavailable"; }
    var line = "OLM_AE_DISPATCH_PROBE version=" + version + " project=" + project + " timestamp=" + (new Date()).toISOString();
    write(log, line); write(marker, line);
}());
'''


PNG_INSPECTOR = r'''#!/usr/bin/env python3
"""Read selected pixels from a non-interlaced 16-bit RGB/RGBA PNG."""
import argparse, json, struct, zlib
from pathlib import Path

def paeth(a, b, c):
    p = a + b - c; pa = abs(p-a); pb = abs(p-b); pc = abs(p-c)
    return a if pa <= pb and pa <= pc else b if pb <= pc else c

def inspect(path, points):
    data = Path(path).read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n': raise ValueError('not a PNG')
    pos=8; chunks=[]; width=height=depth=color=interlace=None
    while pos < len(data):
        n=struct.unpack('>I',data[pos:pos+4])[0]; kind=data[pos+4:pos+8]; body=data[pos+8:pos+8+n]; pos += 12+n
        if kind==b'IHDR': width,height,depth,color,_,_,interlace=struct.unpack('>IIBBBBB',body)
        elif kind==b'IDAT': chunks.append(body)
        elif kind==b'IEND': break
    if depth != 16 or color not in (2,6) or interlace != 0: raise ValueError('requires non-interlaced RGB/RGBA 16-bit PNG')
    channels=3 if color==2 else 4; bpp=channels*2; stride=width*bpp; raw=zlib.decompress(b''.join(chunks)); rows=[]; prior=bytearray(stride); off=0
    for _ in range(height):
        f=raw[off]; off+=1; src=raw[off:off+stride]; off+=stride; row=bytearray(stride)
        for i,v in enumerate(src):
            a=row[i-bpp] if i>=bpp else 0; b=prior[i]; c=prior[i-bpp] if i>=bpp else 0
            row[i]=(v + (0 if f==0 else a if f==1 else b if f==2 else (a+b)//2 if f==3 else paeth(a,b,c))) & 255
        rows.append(row); prior=row
    out=[]
    for x,y,role in points:
        if not (0<=x<width and 0<=y<height): raise ValueError('point outside PNG')
        vals=list(struct.unpack('>'+('H'*channels), rows[y][x*bpp:(x+1)*bpp]));
        if channels==3: vals.append(65535)
        out.append({'x':x,'y':y,'role':role,'rgba16':vals})
    return {'width':width,'height':height,'bit_depth':depth,'color_type':color,'interlace':interlace,'points':out}

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--input',required=True); ap.add_argument('--point',action='append',required=True)
    a=ap.parse_args(); pts=[]
    for item in a.point:
        x,y,role=item.split(',',2); pts.append((int(x),int(y),role))
    print(json.dumps(inspect(a.input,pts),separators=(',',':')))
'''


RUNNER = rf'''param(
  [string]$PackageRoot = (Split-Path -Parent $PSScriptRoot),
  [string]$WorkRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) 'work'),
  [switch]$ParseOnly,
  [string]$TracePath = '',
  [string]$ExportPngPath = '',
  [switch]$LaunchAfterFx,
  [string]$AexPath = 'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\OLMBlur.aex',
  [string]$AfterFxPath = 'C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\AfterFX.exe',
  [string]$CdbPath = 'C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe'
)
$ErrorActionPreference='Stop'
$requestId='{REQUEST_ID}';$expectedHash='{AEX_SHA256}';$runId='blur16-'+([guid]::NewGuid().ToString('N'))
$points=@(@{{x=29;y=71;role='capture'}},@{{x=314;y=14;role='control'}})
function Failure([string]$stage,[string]$reason,[object[]]$missing,[string]$last){{[ordered]@{{schema='olmblur-case0006-same-run-internal-return-v1';status='exact_bind_failure';case_id='olmblur__case_0006';failure=[ordered]@{{stage=$stage;reason=$reason;missing_fields=@($missing);last_observation=$last}}}}}}
function Inspect-Png([string]$path){{
  if(!(Test-Path -LiteralPath $path -PathType Leaf)){{throw 'exported PNG missing'}}
  $tool=Join-Path $PackageRoot 'scripts\inspect_png16.py';$text=& py -3 $tool --input $path --point '29,71,capture' --point '314,14,control' 2>&1
  if($LASTEXITCODE-ne0){{throw "PNG16 inspection failed: $text"}};$text|ConvertFrom-Json
}}
function Parse-Trace([string]$path){{
  if(!(Test-Path -LiteralPath $path -PathType Leaf)){{return Failure 'trace' 'missing CDB trace' @('trace') ''}}
  $entries=@();$pre=@{{}};$stored=@{{}};$missing=@();$last=''
  foreach($line in Get-Content -LiteralPath $path){{
    $last=$line;if($line-notmatch'^BLUR16_(WORKER_ENTRY|FINAL_PRE_STORE|STORED_RGB16)\s+'){{continue}};$stage=$Matches[1];$m=@{{}};foreach($pair in [regex]::Matches($line,'(?<key>[a-z0-9_]+)=(?<value>[^\s]+)')){{$m[$pair.Groups['key'].Value]=$pair.Groups['value'].Value}}
    if($stage-eq'WORKER_ENTRY'){{$entries+=,$m;continue}};if(!$m.ContainsKey('x')-or!$m.ContainsKey('y')){{continue}};$key="$($m.x),$($m.y)";$bucket=if($stage-eq'FINAL_PRE_STORE'){{$pre}}else{{$stored}};if($bucket.ContainsKey($key)){{$bucket[$key]['duplicate']='1'}}else{{$bucket[$key]=$m}}
  }}
  if($entries.Count-ne1){{$missing+='WORKER_ENTRY:count'}}
  $all=@();if($entries.Count-eq1){{$all+=,$entries[0]}}
  $identity=@('run_id','ae_pid','module_base','aex_sha256','project_bpc','renderer','case_id')
  foreach($point in $points){{$key="$($point.x),$($point.y)";foreach($spec in @(@{{name='FINAL_PRE_STORE';map=$pre;fields=@('role','output_addr','expected_output_addr','plane_addr','rgb_f32_bits')}},@{{name='STORED_RGB16';map=$stored;fields=@('role','output_addr','expected_output_addr','rgb16')}})){{if(!$spec.map.ContainsKey($key)){{$missing+="${{key}}:$($spec.name)";continue}};$row=$spec.map[$key];$all+=,$row;foreach($f in $identity+$spec.fields){{if(!$row.ContainsKey($f)-or[string]::IsNullOrWhiteSpace([string]$row[$f])){{$missing+="${{key}}:$($spec.name):$f"}}}};if($row.ContainsKey('duplicate')){{$missing+="${{key}}:$($spec.name):duplicate"}};if($row.role-ne$point.role){{$missing+="${{key}}:$($spec.name):role"}};if($row.output_addr-ne$row.expected_output_addr){{$missing+="${{key}}:$($spec.name):address"}}}}
    if($pre.ContainsKey($key)-and$stored.ContainsKey($key)-and$pre[$key].output_addr-ne$stored[$key].output_addr){{$missing+="${{key}}:stage_output_addr"}}
  }}
  if($entries.Count-eq1){{$e=$entries[0];foreach($f in $identity+@('entry_rva','source_base','source_rowbytes','output_base','output_rowbytes','width','height','pixel_size')){{if(!$e.ContainsKey($f)-or[string]::IsNullOrWhiteSpace([string]$e[$f])){{$missing+="WORKER_ENTRY:$f"}}}};if($e.entry_rva-ne'2280'){{$missing+='WORKER_ENTRY:entry_rva'}};if($e.width-ne'1920'-or$e.height-ne'1080'-or$e.pixel_size-ne'8'){{$missing+='WORKER_ENTRY:geometry'}}}}
  foreach($f in $identity){{$vals=@($all|ForEach-Object{{[string]$_[$f]}}|Select-Object -Unique);if($vals.Count-ne1){{$missing+="shared:$f"}}}}
  if($all.Count){{if(([string]$all[0].aex_sha256).ToLowerInvariant()-ne$expectedHash){{$missing+='shared:expected_aex_sha256'}};if($all[0].project_bpc-ne'16'){{$missing+='shared:project_bpc_16'}};if($all[0].renderer-ne'Software'){{$missing+='shared:renderer_Software'}};if($all[0].case_id-ne'olmblur__case_0006'){{$missing+='shared:case_id'}}}}
  if($missing.Count){{return Failure 'typed_internal' 'typed records are incomplete, duplicated, or identity/address mismatched' $missing $last}}
  [ordered]@{{status='answered';run_id=$all[0].run_id;ae_pid=[int]$all[0].ae_pid;module_base=$all[0].module_base;aex_sha256=$all[0].aex_sha256;worker_entry=$entries[0];pre_store=$pre;stored=$stored}}
}}
function Add-Export([object]$parsed,[string]$path){{
  if($parsed.status-ne'answered'){{return $parsed}};try{{$png=Inspect-Png $path}}catch{{return Failure 'export_png' $_.Exception.Message @('fresh_16bpc_png') ''}}
  if($png.width-ne1920-or$png.height-ne1080-or$png.bit_depth-ne16-or@($png.points).Count-ne2){{return Failure 'export_png' 'PNG geometry/depth/points mismatch' @('1920x1080','bit_depth=16','two_points') ($png|ConvertTo-Json -Compress)}}
  $file=Get-Item -LiteralPath $path;$id=[ordered]@{{run_id=$parsed.run_id;ae_pid=[int]$parsed.ae_pid;module='OLMBlur.aex';module_base=$parsed.module_base;aex_sha256=$parsed.aex_sha256;project_depth=16}}
  $witnesses=@($points|ForEach-Object{{$key="$($_.x),$($_.y)";$bits=@($parsed.pre_store[$key].rgb_f32_bits.Split(','));$words=@($parsed.stored[$key].rgb16.Split(',')|ForEach-Object{{[int]$_}});[ordered]@{{run_id=$id.run_id;ae_pid=$id.ae_pid;module=$id.module;module_base=$id.module_base;aex_sha256=$id.aex_sha256;project_depth=16;xy=@([int]$_.x,[int]$_.y);pre_store_rgb_bits_hex=$bits;stored_rgb16=$words}}}})
  $exportWitnesses=@($png.points|ForEach-Object{{[ordered]@{{run_id=$id.run_id;ae_pid=$id.ae_pid;module=$id.module;module_base=$id.module_base;aex_sha256=$id.aex_sha256;project_depth=16;xy=@([int]$_.x,[int]$_.y);rgba16=@($_.rgba16|ForEach-Object{{[int]$_}})}}}})
  [ordered]@{{schema='olmblur-case0006-same-run-internal-return-v1';status='answered';case_id='olmblur__case_0006';run=$id;witnesses=$witnesses;exported_png=[ordered]@{{run_id=$id.run_id;ae_pid=$id.ae_pid;module=$id.module;module_base=$id.module_base;aex_sha256=$id.aex_sha256;project_depth=16;archive_path='return/exported_case_0006.png';png_sha256=(Get-FileHash $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant();png_size_bytes=[int64]$file.Length;witnesses=$exportWitnesses}};worker_entry=$parsed.worker_entry}}
}}
if($ParseOnly){{if(!$TracePath-or!$ExportPngPath){{throw '-ParseOnly requires -TracePath and -ExportPngPath'}};(Add-Export (Parse-Trace $TracePath) $ExportPngPath)|ConvertTo-Json -Depth 14;exit 0}}
$work=Join-Path $WorkRoot "olmblur_$runId";New-Item -ItemType Directory -Force -Path $work|Out-Null;$work=(Get-Item $work).FullName
$returnPath=Join-Path $work 'RETURN_OLMBLUR_CASE0006.json';$returnZip=Join-Path $work 'RETURN_OLMBLUR_CASE0006.zip';$archivePng=Join-Path $work 'return\exported_case_0006.png';$trace=Join-Path $work 'cdb_trace.txt';$stdout=Join-Path $work 'cdb_stdout.txt';$stderr=Join-Path $work 'cdb_stderr.txt';$launchOut=Join-Path $work 'afterfx_launcher_stdout.txt';$launchErr=Join-Path $work 'afterfx_launcher_stderr.txt';$queueLog=Join-Path $work 'AE_BLUR16_QUEUE.log';$probeLog=Join-Path $work 'AE_DISPATCH_PROBE.log';$probeMarker=Join-Path $work 'ae_dispatch_probe.marker';$result=Join-Path $work 'AE_SINGLE_CASE.json';$ready=Join-Path $work 'ae_ready.marker';$continue=Join-Path $work 'ae_continue.marker';$export=Join-Path $work 'export\case_0006.png'
$sessionId=(Get-Process -Id $PID).SessionId;$launch=$null;$cdb=$null;$launchStarted=$false;$boundPid=$null;$boundBase=$null;$scheduledTaskName=$null;$dispatchTaskName=$null
function ReadOrNull([string]$p){{if(Test-Path -LiteralPath $p -PathType Leaf){{Get-Content -LiteralPath $p -Raw}}else{{$null}}}}
function Get-AE {{@(Get-CimInstance Win32_Process -Filter "Name='AfterFX.exe'" -ErrorAction SilentlyContinue|Where-Object{{$_.SessionId-eq$sessionId-and$_.ExecutablePath-and[IO.Path]::GetFullPath($_.ExecutablePath)-ieq$AfterFxPath}}|ForEach-Object{{[ordered]@{{pid=[int]$_.ProcessId;parent_pid=[int]$_.ParentProcessId;session_id=[int]$_.SessionId;path=$_.ExecutablePath;command_line=$_.CommandLine}}}})}}
function RawLogs {{[ordered]@{{work_directory=$work;launcher_stdout=(ReadOrNull $launchOut);launcher_stderr=(ReadOrNull $launchErr);probe_log=(ReadOrNull $probeLog);probe_marker=(ReadOrNull $probeMarker);queue_log=(ReadOrNull $queueLog);ready_marker=(ReadOrNull $ready);cdb_trace=(ReadOrNull $trace);cdb_stdout=(ReadOrNull $stdout);cdb_stderr=(ReadOrNull $stderr);ae_log=(ReadOrNull (Join-Path $work 'AE_SINGLE_CASE.log'));ae_result=(ReadOrNull $result);process_diagnostics=[ordered]@{{executable_path=$AfterFxPath;session_id=$sessionId;bound_pid=$boundPid;bound_base=$boundBase;candidates=@(Get-AE)}}}}}}
function Finish([object]$body,[int]$code){{if($code-ne0){{if((Test-Path $ready)-and!(Test-Path $continue)){{Set-Content $continue 'abort' -Encoding ASCII -ErrorAction SilentlyContinue}};if($cdb-and!$cdb.HasExited){{Stop-Process $cdb.Id -Force -ErrorAction SilentlyContinue}};if($launchStarted){{foreach($p in @(Get-AE)){{Stop-Process $p.pid -Force -ErrorAction SilentlyContinue}}}}}};foreach($task in @($dispatchTaskName,$scheduledTaskName)){{if($task){{schtasks.exe /Delete /TN $task /F 2>$null|Out-Null}}}};$body['raw_logs']=RawLogs;$json=$body|ConvertTo-Json -Depth 16;$json|Set-Content $returnPath -Encoding UTF8;if($code-eq0){{if(!(Test-Path -LiteralPath $archivePng -PathType Leaf)){{throw 'archive PNG missing before return ZIP creation'}};Add-Type -AssemblyName System.IO.Compression.FileSystem;if(Test-Path $returnZip){{Remove-Item $returnZip -Force}};$zip=[IO.Compression.ZipFile]::Open($returnZip,[IO.Compression.ZipArchiveMode]::Create);try{{[IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip,$returnPath,'RETURN_OLMBLUR_CASE0006.json',[IO.Compression.CompressionLevel]::Optimal)|Out-Null;[IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip,$archivePng,'return/exported_case_0006.png',[IO.Compression.CompressionLevel]::Optimal)|Out-Null}}finally{{$zip.Dispose()}}}};$json;if($code-eq0){{Write-Host "return_zip=$returnZip"}};exit $code}}
$queue=Join-Path $PackageRoot 'scripts\ae_render_olmblur_case0006_queue.jsx';$probe=Join-Path $PackageRoot 'scripts\ae_dispatch_probe.jsx';foreach($p in @($AexPath,$AfterFxPath,$CdbPath,$queue,$probe,(Join-Path $PackageRoot 'request\request_manifest.json'))){{if(!(Test-Path -LiteralPath $p -PathType Leaf)){{Finish (Failure 'preflight' "required file missing: $p" @('preflight_file') '') 2}}}}
if($LaunchAfterFx -and (Get-Process -Name AfterFX -ErrorAction SilentlyContinue)){{Finish (Failure 'desktop_launch' 'After Effects must be fully closed before LaunchAfterFx mode' @('fresh_AfterFX_process') '') 2}}
$AexPath=(Get-Item $AexPath).FullName;$AfterFxPath=(Get-Item $AfterFxPath).FullName;$CdbPath=(Get-Item $CdbPath).FullName;$hash=(Get-FileHash $AexPath -Algorithm SHA256).Hash.ToLowerInvariant();if($hash-ne$expectedHash){{Finish (Failure 'module_hash' 'OLMBlur.aex hash mismatch' @('expected_aex_sha256') "actual=$hash") 2}}
$env:OLM_BLUR16_REQUEST_DIR=(Join-Path $PackageRoot 'request');$env:OLM_BLUR16_WORK_ROOT=$work;$env:OLM_BLUR16_RUN_ID=$runId;$env:OLM_AE_PAUSE_BEFORE_RENDER='1';$env:OLM_AE_PAUSE_TIMEOUT_SECONDS='300';$env:OLM_AE_FORCE_SOFTWARE='1';$env:OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT='1'
$launchDir=Join-Path $env:PUBLIC ('OLMWitness\\blur16_'+([guid]::NewGuid().ToString('N')));New-Item -ItemType Directory -Force -Path $launchDir|Out-Null
$launchWrapper=Join-Path $launchDir 'launch.cmd';$dispatchWrapper=Join-Path $launchDir 'dispatch.cmd';$probeWrapper=Join-Path $launchDir 'probe.cmd';$requestDir=Join-Path $PackageRoot 'request'
$envLines=@(('set "OLM_BLUR16_REQUEST_DIR='+$requestDir+'"'),('set "OLM_BLUR16_WORK_ROOT='+$work+'"'),('set "OLM_BLUR16_RUN_ID='+$runId+'"'),('set "OLM_AE_DISPATCH_PROBE_MARKER='+$probeMarker+'"'),('set "OLM_AE_DISPATCH_PROBE_LOG='+$probeLog+'"'),'set "OLM_AE_PAUSE_BEFORE_RENDER=1"','set "OLM_AE_PAUSE_TIMEOUT_SECONDS=300"','set "OLM_AE_FORCE_SOFTWARE=1"','set "OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT=1"')
$launchLines=@('@echo off')+$envLines+@(('"' + $AfterFxPath + '" -m >"' + $launchOut + '" 2>"' + $launchErr + '"'),'exit /b %ERRORLEVEL%');$launchLines|Set-Content $launchWrapper -Encoding ASCII
$dispatchLines=@('@echo off')+$envLines+@(('"' + $AfterFxPath + '" -r "' + $queue + '"'),'exit /b %ERRORLEVEL%');$dispatchLines|Set-Content $dispatchWrapper -Encoding ASCII
$probeLines=@('@echo off')+$envLines+@(('"' + $AfterFxPath + '" -r "' + $probe + '"'),'exit /b %ERRORLEVEL%');$probeLines|Set-Content $probeWrapper -Encoding ASCII
$scheduledTaskName='OLM_Blur16_'+$runId;$probeTaskName='OLM_Blur16_Probe_'+$runId;$dispatchTaskName='OLM_Blur16_Dispatch_'+$runId;$taskStart=(Get-Date).AddMinutes(1);$taskDate=$taskStart.ToString('yyyy/MM/dd',[Globalization.CultureInfo]::InvariantCulture);$taskTime=$taskStart.ToString('HH:mm',[Globalization.CultureInfo]::InvariantCulture);$loaded=@(Get-AE)
if(!$LaunchAfterFx-and$loaded.Count-ne1){{Finish (Failure 'desktop_process_discovery' 'Exactly one pre-opened After Effects process is required' @('one_desktop_AfterFX_process') ($loaded|ConvertTo-Json -Compress)) 2}}
if($LaunchAfterFx){{$taskOutput=& schtasks.exe /Create /TN $scheduledTaskName /TR $launchWrapper /SC ONCE /SD $taskDate /ST $taskTime /IT /F 2>&1;if($LASTEXITCODE-ne0){{Finish (Failure 'interactive_task' 'Could not create the interactive After Effects task' @('interactive_task_created') ([string]$taskOutput)) 2}};$taskOutput=& schtasks.exe /Run /TN $scheduledTaskName 2>&1;if($LASTEXITCODE-ne0){{Finish (Failure 'interactive_task' 'Could not run the interactive After Effects task' @('interactive_task_started') ([string]$taskOutput)) 2}};$launchStarted=$true;$deadline=(Get-Date).AddSeconds(180);while((Get-Date)-lt$deadline-and$loaded.Count-ne1){{$loaded=@(Get-AE);if($loaded.Count-ne1){{Start-Sleep -Milliseconds 250}}}};if($loaded.Count-ne1){{Finish (Failure 'desktop_process_discovery' 'After Effects interactive task did not produce exactly one process' @('one_desktop_AfterFX_process') '') 2}}}}
$probeOutput=& schtasks.exe /Create /TN $probeTaskName /TR $probeWrapper /SC ONCE /SD $taskDate /ST $taskTime /IT /F 2>&1;if($LASTEXITCODE-ne0){{Finish (Failure 'interactive_task' 'Could not create the JSX probe task' @('jsx_probe_task_created') ([string]$probeOutput)) 2}};$probeOutput=& schtasks.exe /Run /TN $probeTaskName 2>&1;if($LASTEXITCODE-ne0){{Finish (Failure 'interactive_task' 'Could not run the JSX probe task' @('jsx_probe_task_started') ([string]$probeOutput)) 2}}
$deadline=(Get-Date).AddSeconds(60);while((Get-Date)-lt$deadline-and!(Test-Path $probeMarker)){{Start-Sleep -Milliseconds 250}};if(!(Test-Path $probeMarker -PathType Leaf)){{Finish (Failure 'jsx_probe' 'Diagnostic JSX did not write its marker' @('ae_dispatch_probe.marker') '') 2}}
cmd.exe /c schtasks.exe /Delete /TN $probeTaskName /F 1>nul 2>nul
$dispatchOutput=& schtasks.exe /Create /TN $dispatchTaskName /TR $dispatchWrapper /SC ONCE /SD $taskDate /ST $taskTime /IT /F 2>&1;if($LASTEXITCODE-ne0){{Finish (Failure 'interactive_task' 'Could not create the interactive queue dispatch task' @('queue_dispatch_task_created') ([string]$dispatchOutput)) 2}};$dispatchOutput=& schtasks.exe /Run /TN $dispatchTaskName 2>&1;if($LASTEXITCODE-ne0){{Finish (Failure 'interactive_task' 'Could not run the interactive queue dispatch task' @('queue_dispatch_task_started') ([string]$dispatchOutput)) 2}}
$deadline=(Get-Date).AddSeconds(180);while((Get-Date)-lt$deadline-and!(Test-Path $ready)){{Start-Sleep -Milliseconds 250}};if(!(Test-Path $ready -PathType Leaf)){{Finish (Failure 'readiness' 'AE ready marker missing after interactive queue dispatch' @('ae_ready.marker') '') 2}};$readyText=Get-Content $ready -Raw;if($readyText-notmatch'case_id=olmblur__case_0006'-or$readyText-notmatch'effect_loaded=1'-or$readyText-notmatch'parameters_applied=1'){{Finish (Failure 'readiness' 'AE marker is not render-ready' @('case_id','effect_loaded=1','parameters_applied=1') $readyText) 2}}
$loaded=@();$deadline=(Get-Date).AddSeconds(30);while((Get-Date)-lt$deadline-and$loaded.Count-ne1){{$loaded=@(Get-AE|ForEach-Object{{$p=Get-Process -Id $_.pid -ErrorAction SilentlyContinue;try{{$m=$p.Modules|Where-Object{{$_.FileName-ieq$AexPath}}|Select-Object -First 1;if($m){{[pscustomobject]@{{Process=$p;Module=$m}}}}}}catch{{}}}});if($loaded.Count-ne1){{Start-Sleep -Milliseconds 250}}}};if($loaded.Count-ne1){{Finish (Failure 'desktop_process_discovery' 'exactly one loaded OLMBlur module was not found' @('actual_ae_process_module') "matches=$($loaded.Count)") 2}}
$ae=$loaded[0].Process;$module=$loaded[0].Module;$boundPid=$ae.Id;$boundBase=('0x{{0:x}}'-f$module.BaseAddress.ToInt64());$loadedHash=(Get-FileHash $module.FileName -Algorithm SHA256).Hash.ToLowerInvariant();if($loadedHash-ne$expectedHash){{Finish (Failure 'module_hash' 'loaded module hash mismatch' @('loaded_aex_sha256') "actual=$loadedHash") 2}}
$base=$module.BaseAddress.ToInt64();$entry=('0x{{0:x}}'-f($base+0x2280));$pre=('0x{{0:x}}'-f($base+0x2ff1));$stored=('0x{{0:x}}'-f($base+0x3032));$script=Join-Path $work 'olmblur16.cdb'
$cdbText=@"
.effmach amd64
.expr /s masm
sxi 80000003
.logopen /t "$trace"
r @`$t0=0;r @`$t1=0;r @`$t2=0
bp $entry ".if (@`$t0==0 && dwo(@r9+18)==8 && dwo(@r8+24)==1920 && dwo(@r8+28)==1080) {{r @`$t0=1;r @`$t3=poi(@r8+18);r @`$t4=dwo(@r8+20);.printf \"BLUR16_WORKER_ENTRY run_id=$runId ae_pid=$boundPid module_base=$boundBase aex_sha256=$hash project_bpc=16 renderer=Software case_id=olmblur__case_0006 entry_rva=2280 source_base=%p source_rowbytes=%u output_base=%p output_rowbytes=%u width=%u height=%u pixel_size=8\\n\",poi(@rdx+18),dwo(@rdx+20),@`$t3,@`$t4,dwo(@r8+24),dwo(@r8+28);bp $pre \".if (@esi==314 && @r12d==14) {{.printf \\\"BLUR16_FINAL_PRE_STORE run_id=$runId ae_pid=$boundPid module_base=$boundBase aex_sha256=$hash project_bpc=16 renderer=Software case_id=olmblur__case_0006 x=314 y=14 role=control output_addr=%p expected_output_addr=%p plane_addr=%p rgb_f32_bits=0x%08x,0x%08x,0x%08x\\\\n\\\",@rbx,@`$t3+(14*@`$t4)+(314*8),@rdi-8,dwo(@rdi-8),dwo(@rdi-4),dwo(@rdi)}} .else {{.if (@esi==29 && @r12d==71) {{.printf \\\"BLUR16_FINAL_PRE_STORE run_id=$runId ae_pid=$boundPid module_base=$boundBase aex_sha256=$hash project_bpc=16 renderer=Software case_id=olmblur__case_0006 x=29 y=71 role=capture output_addr=%p expected_output_addr=%p plane_addr=%p rgb_f32_bits=0x%08x,0x%08x,0x%08x\\\\n\\\",@rbx,@`$t3+(71*@`$t4)+(29*8),@rdi-8,dwo(@rdi-8),dwo(@rdi-4),dwo(@rdi)}}}};gc\";bp $stored \".if (@esi==314 && @r12d==14) {{r @`$t1=@`$t1+1;.printf \\\"BLUR16_STORED_RGB16 run_id=$runId ae_pid=$boundPid module_base=$boundBase aex_sha256=$hash project_bpc=16 renderer=Software case_id=olmblur__case_0006 x=314 y=14 role=control output_addr=%p expected_output_addr=%p rgb16=%hu,%hu,%hu\\\\n\\\",@rbx,@`$t3+(14*@`$t4)+(314*8),wo(@rbx+2),wo(@rbx+4),wo(@rbx+6)}} .else {{.if (@esi==29 && @r12d==71) {{r @`$t2=@`$t2+1;.printf \\\"BLUR16_STORED_RGB16 run_id=$runId ae_pid=$boundPid module_base=$boundBase aex_sha256=$hash project_bpc=16 renderer=Software case_id=olmblur__case_0006 x=29 y=71 role=capture output_addr=%p expected_output_addr=%p rgb16=%hu,%hu,%hu\\\\n\\\",@rbx,@`$t3+(71*@`$t4)+(29*8),wo(@rbx+2),wo(@rbx+4),wo(@rbx+6);.if (@`$t1==1 && @`$t2==1) {{.detach;q}}}}}};gc\";.echo BLUR16_TYPED_BREAKPOINTS_ARMED_AFTER_WORKER_ENTRY;gc}} .else {{gc}}"
.echo BLUR16_WORKER_ENTRY_BREAKPOINT_ARMED
g
"@
$cdbText|Set-Content $script -Encoding ASCII;$cdb=Start-Process -FilePath $CdbPath -ArgumentList ('-cf "'+$script+'" -p '+$boundPid) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -NoNewWindow -PassThru
$deadline=(Get-Date).AddSeconds(60);while((Get-Date)-lt$deadline){{if((Test-Path $trace)-and((Get-Content $trace -Raw)-match'BLUR16_WORKER_ENTRY_BREAKPOINT_ARMED')){{break}};if($cdb.HasExited){{break}};Start-Sleep -Milliseconds 250;$cdb.Refresh()}};if(!(Test-Path $trace)-or!((Get-Content $trace -Raw)-match'BLUR16_WORKER_ENTRY_BREAKPOINT_ARMED')){{Finish (Failure 'worker_entry' 'CDB did not arm worker entry' @('BLUR16_WORKER_ENTRY_BREAKPOINT_ARMED') '') 2}}
Set-Content $continue 'continue' -Encoding ASCII;$deadline=(Get-Date).AddSeconds(300);while((Get-Date)-lt$deadline-and!$cdb.HasExited){{Start-Sleep -Milliseconds 250;$cdb.Refresh()}};if(!$cdb.HasExited){{Finish (Failure 'typed_internal' 'CDB did not complete both point captures' @('cdb_exit') '') 2}}
$deadline=(Get-Date).AddSeconds(180);while((Get-Date)-lt$deadline-and!(Test-Path $result)){{Start-Sleep -Milliseconds 250}};if(!(Test-Path $result)){{Finish (Failure 'render_result' 'AE result missing' @('AE_SINGLE_CASE.json') '') 2}};$aeResult=Get-Content $result -Raw|ConvertFrom-Json;$aeLog=ReadOrNull (Join-Path $work 'AE_SINGLE_CASE.log');$resultOutput=if([string]$aeResult.output_png){{[IO.Path]::GetFullPath([string]$aeResult.output_png)}}else{{''}};if($aeResult.status-ne'ok'-or$aeResult.case_id-ne'olmblur__case_0006'-or[int]$aeResult.project_bits_per_channel-ne16-or$resultOutput-ine[IO.Path]::GetFullPath($export)-or$aeLog-notmatch'gpuAccelType=SOFTWARE'-or$aeLog-notmatch'bitsPerChannel=16 source=project.bits_per_channel'){{Finish (Failure 'render_result' 'AE did not complete canonical case_0006 as 16bpc Software to the exact export path' @('status=ok','case_id=olmblur__case_0006','project_bits_per_channel=16','gpuAccelType=SOFTWARE','exact_output_png') ($aeResult|ConvertTo-Json -Compress)) 2}}
$parsed=Parse-Trace $trace;if($parsed.status-eq'answered'-and($parsed.run_id-ne$runId-or$parsed.ae_pid-ne$boundPid-or$parsed.module_base-ne$boundBase-or$parsed.aex_sha256-ne$hash)){{$parsed=Failure 'same_run_identity' 'trace differs from launched process/module' @('run_id','ae_pid','module_base','aex_sha256') ($parsed|ConvertTo-Json -Compress)}};if($parsed.status-eq'answered'){{$parsed=Add-Export $parsed $export}};if($parsed.status-eq'answered'){{New-Item -ItemType Directory -Force -Path (Split-Path -Parent $archivePng)|Out-Null;Copy-Item -LiteralPath $export -Destination $archivePng -Force}};Finish $parsed $(if($parsed.status-eq'answered'){{0}}else{{2}})
'''


def fixture(role_drift: bool = False, missing: str | None = None, pid_drift: bool = False) -> str:
    lines = [
        f"BLUR16_WORKER_ENTRY {IDENTITY} entry_rva=2280 source_base=0x1000 source_rowbytes=15360 output_base=0x2000 output_rowbytes=15360 width=1920 height=1080 pixel_size=8"
    ]
    for x, y, role in POINTS:
        expected = 0x2000 + y * 15360 + x * 8
        actual_role = "control" if role_drift and role == "capture" else role
        pre = f"BLUR16_FINAL_PRE_STORE {IDENTITY} x={x} y={y} role={actual_role} output_addr=0x{expected:x} expected_output_addr=0x{expected:x} plane_addr=0x3000 rgb_f32_bits=0x3f800000,0x3f800000,0x3f800000"
        stored_pid = 9999 if pid_drift and role == "capture" else 6106
        stored_identity = IDENTITY.replace("ae_pid=6106", f"ae_pid={stored_pid}")
        words = "727,727,727" if role == "capture" else "2201,2201,2201"
        stored = f"BLUR16_STORED_RGB16 {stored_identity} x={x} y={y} role={role} output_addr=0x{expected:x} expected_output_addr=0x{expected:x} rgb16={words}"
        if missing != f"pre:{x},{y}": lines.append(pre)
        if missing != f"stored:{x},{y}": lines.append(stored)
    return "\n".join(lines) + "\n"


def make_request(target: Path) -> None:
    request = json.loads((SOURCE / "request_manifest.json").read_text(encoding="utf-8"))
    reference = json.loads((SOURCE / "reference_manifest.json").read_text(encoding="utf-8"))
    source_case = next(c for c in reference["cases"] if c["id"] == SOURCE_CASE_ID)
    source_request_case = next(c for c in request["cases"] if c["id"] == SOURCE_CASE_ID)
    input_name = "case_0006_before_effects.png"
    request["request_id"] = REQUEST_ID
    request["cases"] = [{"id": CASE_ID, "before_effects_frame": input_name, "frame": "case_0006.png"}]
    selected_case = {**source_case, "id": CASE_ID, "before_effects_frame": input_name, "frame": "case_0006.png"}
    selected_case["instrumentation_notes"] = ["Rendered in a 16bpc AE project; PNG export is AE saveFrameToPng output."]
    reference.pop("request_package", None)
    reference["cases"] = [selected_case]
    reference["project"] = {**reference.get("project", {}), "bits_per_channel": 16}
    reference["current_reference_capture"] = {"renderer": "Software", "purpose": "same-run internal/export witness; expected image is not an acceptance oracle"}
    (target / "input").mkdir(parents=True)
    (target / "request_manifest.json").write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
    (target / "reference_manifest.json").write_text(json.dumps(reference, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(SOURCE / "input" / source_request_case["before_effects_frame"], target / "input" / input_name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if not SOURCE.is_dir() or not RENDERER.is_file():
        raise FileNotFoundError("16bpc OLMBlur request or current renderer is missing")
    if PACKAGE.exists(): shutil.rmtree(PACKAGE)
    for name in ("artifacts", "scripts", "fixtures", "request"):
        (PACKAGE / name).mkdir(parents=True, exist_ok=True)
    make_request(PACKAGE / "request")
    (PACKAGE / "README_RUNTIME_TRACE.md").write_text(README, encoding="utf-8")
    (PACKAGE / "artifacts/run_olmblur_case0006_same_run_internal_20260713.ps1").write_text(RUNNER, encoding="utf-8")
    (PACKAGE / "scripts/ae_render_olmblur_case0006_queue.jsx").write_text(QUEUE, encoding="utf-8")
    (PACKAGE / "scripts/ae_dispatch_probe.jsx").write_text(DISPATCH_PROBE, encoding="utf-8")
    (PACKAGE / "scripts/inspect_png16.py").write_text(PNG_INSPECTOR, encoding="utf-8")
    shutil.copy2(RENDERER, PACKAGE / "scripts/ae_render_single_case.jsx")
    (PACKAGE / "fixtures/complete_cdb_trace.txt").write_text(fixture(), encoding="utf-8")
    (PACKAGE / "fixtures/missing_stage_cdb_trace.txt").write_text(fixture(missing="pre:29,71"), encoding="utf-8")
    (PACKAGE / "fixtures/identity_drift_cdb_trace.txt").write_text(fixture(pid_drift=True), encoding="utf-8")
    (PACKAGE / "fixtures/role_drift_cdb_trace.txt").write_text(fixture(role_drift=True), encoding="utf-8")
    manifest = {"schema": 1, "kind": "olm_runtime_trace_request_package", "profile": "olmblur-case0006-same-run-internal-rgb16", "request_id": REQUEST_ID, "submission_status": "ready", "sendable": True, "entrypoint": "README_RUNTIME_TRACE.md", "platform": "windows", "plugin": {"name": "OLMBlur.aex", "required_sha256": AEX_SHA256}, "render": {"case_id": CASE_ID, "bits_per_channel": 16, "renderer": "Software", "output": "PNG16"}, "capture": {"worker_entry_rva": "0x2280", "pre_store_rva": "0x2ff1", "stored_rva": "0x3032", "points": [{"xy": [x, y], "role": role} for x, y, role in POINTS]}, "stop_condition": "One entry and one pre-store/stored RGB16 record per point, one run/PID/base/hash/depth/renderer identity, exact output addresses, and one fresh inspected PNG from the same renderer invocation; otherwise exact_bind_failure.", "runtime_actions": [{"request_id": REQUEST_ID, "status": "ready", "mode": "external-trace", "plugin_area": "OLMBlur case_0006 same-run internal pre-store/store/export witness", "cases": [CASE_ID], "xy": [[29, 71], [314, 14]], "stages": ["worker_entry", "final_pre_store", "stored_rgb16", "exported_png"], "stop_condition": "Return one same-run entry, pre-store, stored RGB16, and inspected PNG record for both points with stable PID/module/hash/depth/renderer identity; otherwise exact_bind_failure with raw logs."}]}
    (PACKAGE / "runtime_trace_package_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    identity = {"run_id": None, "ae_pid": None, "module": "OLMBlur.aex", "module_base": None, "aex_sha256": AEX_SHA256, "project_depth": 16}
    template = {
        "schema": "olmblur-case0006-same-run-internal-return-v1", "status": "answered", "case_id": CASE_ID,
        "run": identity,
        "witnesses": [{**identity, "xy": [x, y], "pre_store_rgb_bits_hex": [None, None, None], "stored_rgb16": [None, None, None]} for x, y, _ in POINTS],
        "exported_png": {**identity, "archive_path": "return/exported_case_0006.png", "png_sha256": None, "png_size_bytes": None,
                         "witnesses": [{**identity, "xy": [x, y], "rgba16": [None, None, None, None]} for x, y, _ in POINTS]},
    }
    (PACKAGE / "RETURN_RUNTIME_TRACE_TEMPLATE.json").write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
    leaked = []
    for path in PACKAGE.rglob("*"):
        if not path.is_file():
            continue
        data = path.read_bytes()
        if b"/Users/" in data or b"C:\\Users\\" in data or path.suffix == ".pyc" or "__pycache__" in path.parts:
            leaked.append(path.relative_to(PACKAGE).as_posix())
    if leaked:
        raise RuntimeError(f"workstation path or bytecode leaked into package: {leaked}")
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in PACKAGE.rglob("*") if p.is_file()):
            info = zipfile.ZipInfo(path.relative_to(PACKAGE).as_posix(), (2026, 7, 13, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    print(f"[OK] built OLMBlur case_0006 same-run package: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
