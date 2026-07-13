#!/usr/bin/env python3
"""Materialize the executable AE 26.3 ColorKey 32bpc entry-identity request."""

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
STEM = "olm_ae26_3_32bpc_input_identity_request_20260713"
DEFAULT_OUTPUT = ROOT / "refs" / "runtime_trace_packages" / f"{STEM}.zip"
FIXTURE_JSX = ROOT / "scripts" / "ae_generate_32bpc_typed_procedural_fixture.jsx"
CASE_ID = "olmcolorkey__case_0002"
EFFECT = "OLM Color Key"
WINDOWS_AEX_SHA256 = "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"
WINDOWS_FLOAT_RENDER_RVA = "0x9960"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def contract() -> dict[str, Any]:
    return {
        "kind": "ae26_3_32bpc_pf_pixel_float_input_identity_contract",
        "schema": 3,
        "acceptance_basis": "ae26_3_float_exr_acceptance",
        "ae": {"major_minor": "26.3", "bit_depth": "32bpc", "bits_per_channel": 32, "linear_light": False},
        "host": {"renderer": "SOFTWARE", "required": ["windows", "macos"]},
        "capture_target": {"case": CASE_ID, "plugin": "OLMColorKey", "effect_name": EFFECT},
        "entry_buffer": {
            "pixel_type": "PF_PixelFloat",
            "channel_order": ["alpha", "red", "green", "blue"],
            "scalar": "float32",
            "endianness": "little",
            "pixel_stride_bytes": 16,
            "rowbytes_required": True,
            "identity": "raw-float32-bits, rowbytes-aware, no premultiply/unpremultiply or normalization",
        },
        "capture_paths": {
            "macos": {
                "method": "env-gated-plugin-instrumentation",
                "capture_point": "SmartRender.after_checkout_layer_pixels.before_checkout_output",
                "plugin_identity": "runner-hashes-required-executable; plugin records dladdr-loaded executable; validator rehashes and compares both",
            },
            "windows": {
                "method": "hash-pinned-cdb-rva-hook",
                "aex_sha256": WINDOWS_AEX_SHA256,
                "float_render_entry_rva": WINDOWS_FLOAT_RENDER_RVA,
                "input_world_register": "r8",
                "world_offsets": {"data": "0x08", "rowbytes": "0x10", "width": "0x24", "height": "0x28"},
            },
        },
        "exr": {"encoding": "uncompressed scanline", "channels": ["A", "B", "G", "R"], "sample_type": "FLOAT", "dimensions": [64, 64]},
        "case_outputs": {"source_input": "source_input_00000.exr", "no_effect": "effect_no_effect_00000.exr", "effect_on": "effect_effect_on_00000.exr"},
        "fail_closed": [
            "reject a raw dump without same-run capture provenance and nonce",
            "reject external-command, contract-only, synthetic, or unknown capture methods",
            "reject capture metadata not bound to the ColorKey case and AE process",
            "reject Windows capture unless the loaded AEX hash and RVA are exact",
            "reject Windows trace fields that differ from runner provenance or launch binding",
            "reject macOS capture unless the dladdr-loaded executable matches the run-pinned path and SHA-256",
            "reject missing source, no-effect, or effect-on EXR",
            "reject non-raw-float identity comparison or epsilon",
        ],
    }


def request_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    case = {
        "id": CASE_ID,
        "plugin": "OLMColorKey",
        "effect_name": EFFECT,
        "dimensions": [64, 64],
        "linear_light": False,
        "case_contract_sha256": sha256_bytes(json.dumps({"id": CASE_ID, "contract": payload}, sort_keys=True).encode()),
        "entry_buffer_identity": {"type": "PF_PixelFloat", "channel_order": ["alpha", "red", "green", "blue"], "compare": "raw-float32-bits"},
        "artifacts": {
            "source_input": {"path": f"cases/{CASE_ID}/source_input_00000.exr", "sha256": ""},
            "no_effect": {"path": f"cases/{CASE_ID}/effect_no_effect_00000.exr", "sha256": "", "effect_enabled": False},
            "effect_on": {"path": f"cases/{CASE_ID}/effect_effect_on_00000.exr", "sha256": "", "effect_enabled": True},
        },
    }
    return {"kind": "ae26_3_32bpc_input_identity_request", "schema": 3, "package": STEM, "contract": payload, "cases": [case]}


def readme() -> str:
    return f"""# AE 26.3 32bpc ColorKey input identity request

This package performs one bounded real capture for `{CASE_ID}`. It does not
accept a caller-provided capture command.

On macOS, pass the exact instrumented `OLMColorKey.plugin` executable built from this workspace.
The runner enables its one-shot environment gate; immediately after SmartRender
checks out the input layer pixels, the plugin writes the complete rowbytes-aware
`PF_PixelFloat` A/R/G/B buffer and an atomic provenance record. The runner pins
the executable SHA-256 before launch, the plugin records its `dladdr` loaded-image
path, and the validator independently hashes that loaded file and compares both.

On Windows, provide CDB and the hash-pinned 2025 `OLMColorKey.aex`. The runner
requires SHA-256 `{WINDOWS_AEX_SHA256}`, pauses AE after the effect is loaded,
finds that exact module in the AE process, and hooks RVA `{WINDOWS_FLOAT_RENDER_RVA}`.
At that entry R8 is the input `PF_EffectWorld*`; CDB dumps `[R8+0x08]` for
`dwo(R8+0x10) * dwo(R8+0x28)` bytes before the float worker executes.

The validator requires same-run nonce, case, actual AE PID, capture point/method, dimensions,
rowbytes, and platform binding. A raw file by itself, old external-command
metadata, or contract-only metadata fails closed. The no-effect render is also
copied as `source_input_00000.exr`; all three EXRs and their hashes are recorded.
"""


def instrumented_fixture() -> str:
    source = FIXTURE_JSX.read_text(encoding="utf-8")
    anchor = "        if (!effect) fail(\"AE could not add \" + effectName);\n"
    insertion = anchor + """        var readyPath = getenv("OLM_PF_ENTRY_READY_MARKER");
        var continuePath = getenv("OLM_PF_ENTRY_CONTINUE_MARKER");
        if (readyPath || continuePath) {
            if (!readyPath || !continuePath) fail("both capture pause markers are required");
            var readyNonce = getenv("OLM_PF_ENTRY_NONCE");
            var readyCase = getenv("OLM_PF_ENTRY_CASE");
            if (!readyNonce || !readyCase) fail("capture marker identity is required");
            var readyPid = "";
            if ($.os.toLowerCase().indexOf("windows") >= 0) {
                var pidCommand = "powershell.exe -NoProfile -NonInteractive -Command \"$id=$PID; for($i=0;$i -lt 8;$i++){$p=Get-CimInstance Win32_Process -Filter ('ProcessId='+$id);if(-not $p){break};if($p.Name -ieq 'AfterFX.exe'){[Console]::Write($p.ProcessId);break};$id=$p.ParentProcessId}\"";
                readyPid = system.callSystem(pidCommand).replace(/[^0-9]/g, "");
                if (!readyPid) fail("could not bind capture marker to AfterFX PID");
            }
            writeText(readyPath, "nonce=" + readyNonce + "\\ncase=" + readyCase + "\\npid=" + readyPid + "\\nfixture=__FIXTURE_NAME__\\neffect_loaded=1\\nparameters_applied=1\\n");
            var pauseDeadline = (new Date()).getTime() + 300000;
            while (!(new File(continuePath)).exists && (new Date()).getTime() < pauseDeadline) $.sleep(100);
            if (!(new File(continuePath)).exists) fail("capture pause timed out");
        }
"""
    if source.count(anchor) != 1:
        raise RuntimeError("fixture pause anchor drifted")
    return source.replace(anchor, insertion.replace("__FIXTURE_NAME__", FIXTURE_JSX.name))


def capture_helper() -> str:
    return r'''#!/usr/bin/env python3
"""Validate a same-run, instrument-produced PF_PixelFloat entry dump."""
import argparse, hashlib, json, re, struct
from pathlib import Path

def fail(message): raise SystemExit("[FAIL] entry_capture: " + message)
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def hex_address(value):
    try: return int(value, 16)
    except (TypeError, ValueError): fail("invalid trace address")

p=argparse.ArgumentParser()
p.add_argument("--dump",type=Path,required=True); p.add_argument("--provenance",type=Path,required=True)
p.add_argument("--manifest",type=Path,required=True); p.add_argument("--nonce",required=True)
p.add_argument("--platform",choices=("macos","windows"),required=True); p.add_argument("--pid",type=int,required=True)
p.add_argument("--trace",type=Path); p.add_argument("--expected-plugin-sha256"); p.add_argument("--plugin-executable",type=Path)
a=p.parse_args()
a.manifest.unlink(missing_ok=True)
if not re.fullmatch(r"[0-9a-f]{32,64}",a.nonce): fail("invalid nonce")
if not a.dump.is_file(): fail("missing raw entry dump")
if not a.provenance.is_file(): fail("missing instrument provenance; raw/contract-only dump rejected")
try: prov=json.loads(a.provenance.read_text(encoding="utf-8-sig"))
except Exception as exc: fail("invalid provenance JSON: " + str(exc))
required={"kind":"olm_pf_pixel_float_entry_capture_provenance","schema":3,"case":"olmcolorkey__case_0002","nonce":a.nonce,"pid":a.pid,"bitdepth":32,"pixel_type":"PF_PixelFloat","channel_order":["alpha","red","green","blue"],"endianness":"little","pixel_stride_bytes":16}
for key,value in required.items():
    if prov.get(key) != value: fail(f"provenance {key} mismatch")
if a.platform == "macos":
    exact={"producer":"OLMColorKey.plugin","capture_method":"macos-env-gated-plugin-instrumentation","capture_point":"SmartRender.after_checkout_layer_pixels.before_checkout_output"}
    if not a.expected_plugin_sha256 or not re.fullmatch(r"[0-9a-f]{64}",a.expected_plugin_sha256): fail("required expected plugin SHA-256 missing")
    if not a.plugin_executable or not a.plugin_executable.is_file(): fail("required plugin executable missing")
    loaded=prov.get("loaded_plugin_executable")
    if not isinstance(loaded,str) or not Path(loaded).is_file(): fail("loaded plugin executable missing")
    if Path(loaded).resolve() != a.plugin_executable.resolve(): fail("loaded plugin executable path mismatch")
    if prov.get("launch_expected_plugin_sha256") != a.expected_plugin_sha256: fail("launch expected plugin SHA-256 mismatch")
    actual_plugin_sha256=digest(Path(loaded))
    if actual_plugin_sha256 != a.expected_plugin_sha256 or digest(a.plugin_executable) != a.expected_plugin_sha256: fail("loaded plugin executable SHA-256 mismatch")
else:
    exact={"producer":"cdb.exe","capture_method":"windows-hash-pinned-cdb-rva-hook","capture_point":"OLMColorKey.aex+0x9960","aex_sha256":"9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c","float_render_entry_rva":"0x9960","input_world_register":"r8"}
for key,value in exact.items():
    if prov.get(key) != value: fail(f"provenance {key} mismatch")
if a.platform == "windows":
    if not a.trace or not a.trace.is_file(): fail("missing CDB trace")
    trace=a.trace.read_text(encoding="utf-8-sig",errors="replace")
    matches=re.findall(r"OLM_CK_ENTRY nonce=([0-9a-f]+) case=(\S+) pid=(\d+) aex_sha256=([0-9a-f]+) rva=(0x[0-9a-fA-F]+) input_world=(?:0x)?([0-9a-fA-F`]+) data=(?:0x)?([0-9a-fA-F`]+) rowbytes=(\d+) width=(\d+) height=(\d+)",trace)
    if len(matches) != 1: fail("CDB trace must contain exactly one complete entry record")
    nonce,case,pid,aex_sha,rva,input_world,data,rowbytes,width,height=matches[0]
    input_world=input_world.replace("`",""); data=data.replace("`","")
    parsed={"nonce":nonce,"case":case,"pid":int(pid),"aex_sha256":aex_sha,"float_render_entry_rva":rva.lower(),"input_world_address":"0x"+input_world.lower(),"data_address":"0x"+data.lower(),"rowbytes":int(rowbytes),"width":int(width),"height":int(height)}
    for key in ("nonce","case","pid","aex_sha256","float_render_entry_rva","rowbytes","width","height"):
        if parsed[key] != ({"nonce":a.nonce,"case":required["case"],"pid":a.pid,"aex_sha256":exact["aex_sha256"],"float_render_entry_rva":exact["float_render_entry_rva"]}.get(key,prov.get(key))): fail(f"CDB trace {key} mismatch")
    for key in ("input_world_address","data_address"):
        if hex_address(parsed[key]) == 0 or hex_address(parsed[key]) != hex_address(prov.get(key)): fail(f"CDB trace {key} mismatch")
    if prov.get("cdb_trace_sha256") != digest(a.trace): fail("CDB trace SHA-256 mismatch")
    binding=prov.get("launch_binding")
    binding_required={"nonce":a.nonce,"case":required["case"],"actual_afterfx_pid":a.pid,"fresh_process":True,"fixture_commandline_bound":True}
    if not isinstance(binding,dict): fail("missing Windows launch binding")
    for key,value in binding_required.items():
        if binding.get(key) != value: fail(f"Windows launch binding {key} mismatch")
    if binding.get("relation") not in ("launcher-pid","descendant-of-launcher") or not isinstance(binding.get("launcher_pid"),int) or not isinstance(binding.get("session_id"),int): fail("wrong-process Windows launch binding")
width=prov.get("width"); height=prov.get("height"); rowbytes=prov.get("rowbytes")
if width != 64 or height != 64 or not isinstance(rowbytes,int) or rowbytes < width*16 or rowbytes % 16: fail("invalid dimensions/rowbytes")
raw=a.dump.read_bytes(); expected=rowbytes*height
if len(raw) != expected or prov.get("bytes") != expected: fail(f"entry dump size {len(raw)} != {expected}")
for y in range(height):
    for offset in range(0,width*16,16): struct.unpack_from("<4f",raw,y*rowbytes+offset)
raw_digest=hashlib.sha256(raw).hexdigest()
record={"kind":"pf_pixel_float_entry_buffer_capture","schema":3,"case":required["case"],"platform":a.platform,"source":prov["capture_method"],"capture_point":prov["capture_point"],"nonce":a.nonce,"pid":a.pid,"pixel_type":"PF_PixelFloat","channel_order":required["channel_order"],"scalar":"float32","endianness":"little","width":width,"height":height,"rowbytes":rowbytes,"bytes":len(raw),"sha256":raw_digest,"raw_float_bits":True,"provenance_sha256":digest(a.provenance)}
if a.platform == "macos": record["plugin_executable_sha256"]=actual_plugin_sha256
else: record["cdb_trace_sha256"]=digest(a.trace)
a.manifest.parent.mkdir(parents=True,exist_ok=True); a.manifest.write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps({"sha256":raw_digest,"bytes":len(raw),"manifest":str(a.manifest)}))
'''


def windows_runner() -> str:
    return rf'''param(
  [Parameter(Mandatory=$true)][string]$AfterFX,
  [Parameter(Mandatory=$true)][string]$ColorKeyPlugin,
  [Parameter(Mandatory=$true)][string]$CdbPath,
  [string]$OutputDir="run", [int]$TimeoutSeconds=300
)
$ErrorActionPreference="Stop"; $Root=Split-Path -Parent $PSCommandPath; $CaseId="{CASE_ID}"; $Fixture=[IO.Path]::GetFullPath((Join-Path $Root "fixture\{FIXTURE_JSX.name}"))
function Fail([string]$m) {{ throw "[FAIL] $m" }}
function Get-CimProcess([int]$Id) {{ Get-CimInstance Win32_Process -Filter ("ProcessId="+$Id) -ErrorAction SilentlyContinue }}
function Get-LaunchRelation([int]$ActualPid,[int]$LauncherPid) {{
  if($ActualPid-eq$LauncherPid){{return "launcher-pid"}}
  $cursor=$ActualPid
  for($i=0;$i-lt 8;$i++){{$p=Get-CimProcess $cursor;if(-not$p){{break}};$parent=[int]$p.ParentProcessId;if($parent-eq$LauncherPid){{return "descendant-of-launcher"}};$cursor=$parent}}
  return $null
}}
foreach($p in @($AfterFX,$ColorKeyPlugin,$CdbPath,$Fixture,(Join-Path $Root "capture_pf_pixel_float_entry.py"))) {{ if(-not(Test-Path -LiteralPath $p -PathType Leaf)){{Fail "missing $p"}} }}
if(Get-Process -Name AfterFX -ErrorAction SilentlyContinue){{Fail "AfterFX must be closed"}}
$hash=(Get-FileHash -LiteralPath $ColorKeyPlugin -Algorithm SHA256).Hash.ToLowerInvariant(); if($hash -ne "{WINDOWS_AEX_SHA256}"){{Fail "unsupported AEX SHA-256 $hash"}}
$run=[IO.Path]::GetFullPath((Join-Path $Root $OutputDir)); $case=Join-Path $run "cases\{CASE_ID}"; New-Item -ItemType Directory -Force $case|Out-Null
$dump=Join-Path $case "entry_buffer_pf_pixel_float.bin"; $prov=Join-Path $case "entry_buffer_provenance.json"; $entry=Join-Path $case "entry_buffer_manifest.json"; $trace=Join-Path $case "cdb_entry_trace.log"; $ready=Join-Path $case "capture.ready"; $continue=Join-Path $case "capture.continue"; $result=Join-Path $case "fixture_result.json"; $project=Join-Path $case "fixture.aep"
foreach($p in @($dump,$prov,$entry,$trace,$ready,$continue,$result)){{Remove-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue}}
$nonce=[guid]::NewGuid().ToString("N")
$env:OLM_AE_TYPED_FIXTURE_OUTPUT_DIR=$case; $env:OLM_AE_TYPED_FIXTURE_TEMPLATE="OLM EXR 32 Float"; $env:OLM_AE_TYPED_FIXTURE_PROJECT_PATH=$project; $env:OLM_AE_TYPED_FIXTURE_EFFECT="{EFFECT}"; $env:OLM_AE_TYPED_FIXTURE_OVERWRITE="1"; $env:OLM_PF_ENTRY_READY_MARKER=$ready; $env:OLM_PF_ENTRY_CONTINUE_MARKER=$continue; $env:OLM_PF_ENTRY_NONCE=$nonce; $env:OLM_PF_ENTRY_CASE=$CaseId
$launchStarted=Get-Date; $callerSession=(Get-Process -Id $PID).SessionId
$launch=Start-Process -FilePath $AfterFX -ArgumentList ('-r "'+$Fixture+'"') -PassThru
$launchCim=$null; $deadline=(Get-Date).AddSeconds(10); while((Get-Date) -lt $deadline -and -not $launchCim){{$launchCim=Get-CimProcess $launch.Id;if(-not $launchCim){{Start-Sleep -Milliseconds 100}}}};if(-not $launchCim){{Fail "launcher process identity unavailable"}}
if([int]$launchCim.SessionId -ne $callerSession -or $launchCim.CommandLine -notlike ("*"+$Fixture+"*")){{Fail "launcher session/fixture command line mismatch"}}
$deadline=(Get-Date).AddSeconds($TimeoutSeconds); while((Get-Date)-lt $deadline -and -not(Test-Path $ready)){{Start-Sleep -Milliseconds 200}}; if(-not(Test-Path $ready)){{Stop-Process -Id $launch.Id -Force -ErrorAction SilentlyContinue; Fail "render-ready marker missing"}}
$readyData=ConvertFrom-StringData (Get-Content -LiteralPath $ready -Raw);if($readyData.nonce -ne $nonce -or $readyData.case -ne $CaseId -or $readyData.fixture -ne "{FIXTURE_JSX.name}" -or $readyData.pid -notmatch '^\d+$'){{Fail "render-ready marker identity mismatch"}}
$pidValue=[int]$readyData.pid; $aeCim=Get-CimProcess $pidValue; if(-not $aeCim -or $aeCim.Name -ine "AfterFX.exe"){{Fail "ready marker PID is not a live AfterFX process"}}
$relation=Get-LaunchRelation $pidValue $launch.Id;if(-not$relation){{Fail "ready marker AfterFX PID is unrelated to this launch"}}
if([int]$aeCim.SessionId -ne $callerSession -or $aeCim.CreationDate -lt $launchStarted.AddSeconds(-2)){{Fail "ready marker AfterFX process is not fresh/in-session"}}
$ae=Get-Process -Id $pidValue -ErrorAction Stop; $module=$ae.Modules|Where-Object{{$_.FileName-ieq([IO.Path]::GetFullPath($ColorKeyPlugin))}}|Select-Object -First 1;if(-not$module){{Fail "exact loaded ColorKey module absent from bound AfterFX PID"}};if((Get-FileHash $module.FileName -Algorithm SHA256).Hash.ToLowerInvariant()-ne$hash){{Fail "loaded AEX hash mismatch"}}
$base=$module.BaseAddress.ToInt64(); $hook=('0x{{0:x}}'-f($base+0x9960)); $script=Join-Path $case "capture_entry.cdb"; $pidValue=$ae.Id
@"
.effmach amd64
.expr /s masm
.logopen "$trace"
.echo OLM_CK_BREAKPOINT_ARMED
bp $hook ".printf \"OLM_CK_ENTRY nonce=$nonce case=$CaseId pid=$pidValue aex_sha256=$hash rva=0x9960 input_world=%p data=%p rowbytes=%u width=%u height=%u\\n\", @r8, poi(@r8+8), dwo(@r8+0x10), dwo(@r8+0x24), dwo(@r8+0x28); r @`$t0=poi(@r8+8); r @`$t1=dwo(@r8+0x10)*dwo(@r8+0x28); .writemem \"$dump\" @`$t0 (@`$t0+@`$t1-1); .detach; q"
g
"@|Set-Content -LiteralPath $script -Encoding ASCII
$cdb=Start-Process -FilePath $CdbPath -ArgumentList ('-cf "'+$script+'" -p '+$pidValue) -PassThru -NoNewWindow
$deadline=(Get-Date).AddSeconds(60);while((Get-Date)-lt $deadline -and (-not(Test-Path $trace)-or (Get-Content $trace -Raw)-notmatch 'OLM_CK_BREAKPOINT_ARMED')){{if($cdb.HasExited){{break}};Start-Sleep -Milliseconds 200;$cdb.Refresh()}};if(-not(Test-Path $trace)-or(Get-Content $trace -Raw)-notmatch 'OLM_CK_BREAKPOINT_ARMED'){{Fail "CDB breakpoint not armed"}}
Set-Content -LiteralPath $continue -Value continue -Encoding ASCII
$deadline=(Get-Date).AddSeconds($TimeoutSeconds);while((Get-Date)-lt $deadline -and -not $cdb.HasExited){{Start-Sleep -Milliseconds 200;$cdb.Refresh()}};if(-not $cdb.HasExited){{Fail "CDB capture timeout"}}
$lines=@(Get-Content $trace|Where-Object{{$_-match'OLM_CK_ENTRY'}});if($lines.Count-ne1){{Fail "CDB trace must contain exactly one entry record"}};$pattern='OLM_CK_ENTRY nonce=(?<nonce>[0-9a-f]+) case=(?<case>\S+) pid=(?<pid>\d+) aex_sha256=(?<hash>[0-9a-f]+) rva=(?<rva>0x[0-9a-fA-F]+) input_world=(?:0x)?(?<world>[0-9a-fA-F`]+) data=(?:0x)?(?<data>[0-9a-fA-F`]+) rowbytes=(?<rowbytes>\d+) width=(?<width>\d+) height=(?<height>\d+)';if($lines[0]-notmatch$pattern){{Fail "CDB entry record incomplete"}}
$tn=$Matches.nonce;$tc=$Matches.case;$tp=[int]$Matches.pid;$th=$Matches.hash;$tr=$Matches.rva.ToLowerInvariant();$worldHex=$Matches.world.Replace('`','').ToLowerInvariant();$dataHex=$Matches.data.Replace('`','').ToLowerInvariant();$tw='0x'+$worldHex;$td='0x'+$dataHex;$rb=[int]$Matches.rowbytes;$w=[int]$Matches.width;$h=[int]$Matches.height
if($tn -ne $nonce -or $tc -ne $CaseId -or $tp -ne $pidValue -or $th -ne $hash -or $tr -ne '0x9960' -or [convert]::ToUInt64($worldHex,16) -eq 0 -or [convert]::ToUInt64($dataHex,16) -eq 0){{Fail "CDB entry identity mismatch"}}
$traceHash=(Get-FileHash $trace -Algorithm SHA256).Hash.ToLowerInvariant();$binding=[ordered]@{{nonce=$nonce;case=$CaseId;actual_afterfx_pid=$pidValue;launcher_pid=$launch.Id;session_id=$callerSession;relation=$relation;fresh_process=$true;fixture_commandline_bound=$true}}
[ordered]@{{kind="olm_pf_pixel_float_entry_capture_provenance";schema=3;producer="cdb.exe";capture_method="windows-hash-pinned-cdb-rva-hook";capture_point="OLMColorKey.aex+0x9960";case=$tc;nonce=$tn;pid=$tp;bitdepth=32;pixel_type="PF_PixelFloat";channel_order=@("alpha","red","green","blue");endianness="little";pixel_stride_bytes=16;width=$w;height=$h;rowbytes=$rb;bytes=$rb*$h;aex_sha256=$th;float_render_entry_rva=$tr;module_base=('0x{{0:x}}'-f$base);input_world_register="r8";input_world_address=$tw;data_address=$td;cdb_trace_sha256=$traceHash;launch_binding=$binding}}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $prov -Encoding UTF8
python (Join-Path $Root "capture_pf_pixel_float_entry.py") --dump $dump --provenance $prov --manifest $entry --nonce $nonce --platform windows --pid $pidValue --trace $trace;if($LASTEXITCODE-ne 0){{Fail "capture validation failed"}}
$deadline=(Get-Date).AddSeconds($TimeoutSeconds);while((Get-Date)-lt $deadline -and -not(Test-Path $result)){{Start-Sleep -Milliseconds 200}};if(-not(Test-Path $result)){{Fail "render result timeout"}};$fr=Get-Content $result -Raw|ConvertFrom-Json;if($fr.status-ne "ok"){{Fail "render failed"}}
$no=Join-Path $case "effect_no_effect_00000.exr";$on=Join-Path $case "effect_effect_on_00000.exr";$src=Join-Path $case "source_input_00000.exr";foreach($p in @($no,$on)){{if(-not(Test-Path $p -PathType Leaf)){{Fail "missing EXR $p"}}}};Copy-Item -LiteralPath $no -Destination $src -Force
function H($p){{(Get-FileHash $p -Algorithm SHA256).Hash.ToLowerInvariant()}};$record=[ordered]@{{kind="ae26_3_32bpc_input_identity_return";schema=3;platform="windows";ae_version=$fr.ae_version;bit_depth="32bpc";renderer="SOFTWARE";case="{CASE_ID}";plugin_sha256=$hash;entry_buffer=[ordered]@{{path="cases/{CASE_ID}/entry_buffer_pf_pixel_float.bin";sha256=(H $dump);manifest="cases/{CASE_ID}/entry_buffer_manifest.json"}};outputs=[ordered]@{{source_input=[ordered]@{{path="cases/{CASE_ID}/source_input_00000.exr";sha256=(H $src)}};no_effect=[ordered]@{{path="cases/{CASE_ID}/effect_no_effect_00000.exr";sha256=(H $no);effect_enabled=$false}};effect_on=[ordered]@{{path="cases/{CASE_ID}/effect_effect_on_00000.exr";sha256=(H $on);effect_enabled=$true}}}}}};$record|ConvertTo-Json -Depth 20|Set-Content -Encoding UTF8 (Join-Path $run "return_manifest.json")
Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue; Write-Host "[OK] captured {CASE_ID}: $run"
'''


def mac_runner() -> str:
    return rf'''#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
: "${{AFTERFX:?set AFTERFX}}"; : "${{OLM_COLORKEY_PLUGIN:?set instrumented OLMColorKey binary path}}"
RUN_ROOT=${{OUTPUT_DIR:-"$ROOT/run"}}; mkdir -p "$RUN_ROOT"
python3 - "$ROOT" "$RUN_ROOT" "$AFTERFX" "$OLM_COLORKEY_PLUGIN" <<'PY'
import hashlib,json,os,secrets,shutil,subprocess,sys,time
from pathlib import Path
root,run,afterfx,plugin=map(Path,sys.argv[1:]); afterfx=afterfx.resolve(); plugin=plugin.resolve(); case=run/"cases"/"{CASE_ID}"; case.mkdir(parents=True,exist_ok=True)
if not afterfx.is_file() or not plugin.is_file(): raise SystemExit("[FAIL] missing AfterFX/plugin binary")
if subprocess.run(["pgrep","-x","AfterFX"],stdout=subprocess.DEVNULL).returncode==0: raise SystemExit("[FAIL] AfterFX must be closed")
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest(); expected_plugin_sha256=digest(plugin)
dump=case/"entry_buffer_pf_pixel_float.bin"; prov=case/"entry_buffer_provenance.json"; entry=case/"entry_buffer_manifest.json"; result=case/"fixture_result.json"; project=case/"fixture.aep"; nonce=secrets.token_hex(32)
for p in (dump,prov,entry,result,Path(str(prov)+".claim"),case/"effect_no_effect_00000.exr",case/"effect_effect_on_00000.exr",case/"source_input_00000.exr"): p.unlink(missing_ok=True)
env=os.environ|{{"OLM_AE_TYPED_FIXTURE_OUTPUT_DIR":str(case),"OLM_AE_TYPED_FIXTURE_TEMPLATE":"OLM EXR 32 Float","OLM_AE_TYPED_FIXTURE_PROJECT_PATH":str(project),"OLM_AE_TYPED_FIXTURE_EFFECT":"{EFFECT}","OLM_AE_TYPED_FIXTURE_OVERWRITE":"1","OLM_PF_PIXELFLOAT_ENTRY_CAPTURE":"1","OLM_PF_PIXELFLOAT_ENTRY_DUMP":str(dump),"OLM_PF_PIXELFLOAT_ENTRY_METADATA":str(prov),"OLM_PF_PIXELFLOAT_ENTRY_NONCE":nonce,"OLM_PF_PIXELFLOAT_ENTRY_CASE":"{CASE_ID}","OLM_PF_PIXELFLOAT_ENTRY_EXPECTED_PLUGIN_SHA256":expected_plugin_sha256}}
proc=subprocess.Popen([str(afterfx),"-r",str(root/"fixture"/"{FIXTURE_JSX.name}")],env=env); deadline=time.time()+int(os.environ.get("TIMEOUT_SECONDS","300"))
while time.time()<deadline and not (result.is_file() and dump.is_file() and prov.is_file()): time.sleep(.2)
if not (result.is_file() and dump.is_file() and prov.is_file()): proc.kill(); raise SystemExit("[FAIL] render/capture timeout")
fr=json.loads(result.read_text());
if fr.get("status")!="ok": proc.kill(); raise SystemExit("[FAIL] render failed: "+fr.get("error",""))
subprocess.run([sys.executable,str(root/"capture_pf_pixel_float_entry.py"),"--dump",str(dump),"--provenance",str(prov),"--manifest",str(entry),"--nonce",nonce,"--platform","macos","--pid",str(proc.pid),"--expected-plugin-sha256",expected_plugin_sha256,"--plugin-executable",str(plugin)],check=True)
no=case/"effect_no_effect_00000.exr"; on=case/"effect_effect_on_00000.exr"; src=case/"source_input_00000.exr"
if not no.is_file() or not on.is_file(): proc.kill(); raise SystemExit("[FAIL] missing EXR")
shutil.copy2(no,src)
if digest(plugin)!=expected_plugin_sha256: proc.kill(); raise SystemExit("[FAIL] plugin executable changed during capture")
record={{"kind":"ae26_3_32bpc_input_identity_return","schema":3,"platform":"macos","ae_version":fr["ae_version"],"bit_depth":"32bpc","renderer":"SOFTWARE","case":"{CASE_ID}","plugin_sha256":expected_plugin_sha256,"entry_buffer":{{"path":"cases/{CASE_ID}/entry_buffer_pf_pixel_float.bin","sha256":digest(dump),"manifest":"cases/{CASE_ID}/entry_buffer_manifest.json"}},"outputs":{{"source_input":{{"path":"cases/{CASE_ID}/source_input_00000.exr","sha256":digest(src)}},"no_effect":{{"path":"cases/{CASE_ID}/effect_no_effect_00000.exr","sha256":digest(no),"effect_enabled":False}},"effect_on":{{"path":"cases/{CASE_ID}/effect_effect_on_00000.exr","sha256":digest(on),"effect_enabled":True}}}}}}
(run/"return_manifest.json").write_text(json.dumps(record,indent=2)+"\n"); proc.kill(); proc.wait(); print(f"[OK] captured {CASE_ID}: {{run}}")
PY
'''


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def materialize(output: Path) -> Path:
    payload = contract(); manifest = request_manifest(payload)
    with tempfile.TemporaryDirectory(prefix="olm_input_identity_pkg_") as temp_name:
        root = Path(temp_name) / STEM; root.mkdir(parents=True)
        (root/"README.md").write_text(readme(),encoding="utf-8"); write_json(root/"CONTRACT.json",payload); write_json(root/"REQUEST_MANIFEST.json",manifest)
        write_json(root/"RETURN_MANIFEST_TEMPLATE.json",{"kind":"ae26_3_32bpc_input_identity_return","schema":3,"request":STEM,"case":manifest["cases"][0]})
        fixture=root/"fixture"/FIXTURE_JSX.name; fixture.parent.mkdir(); fixture.write_text(instrumented_fixture(),encoding="utf-8")
        (root/"capture_pf_pixel_float_entry.py").write_text(capture_helper(),encoding="utf-8")
        (root/"run_windows_ae26_3_32bpc_input_identity.ps1").write_text(windows_runner(),encoding="utf-8")
        mac=root/"run_macos_ae26_3_32bpc_input_identity.sh"; mac.write_text(mac_runner(),encoding="utf-8"); mac.chmod(0o755)
        output.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(p for p in root.rglob("*") if p.is_file()):
                name=(Path(STEM)/path.relative_to(root)).as_posix()
                info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0)); info.create_system=3
                info.external_attr=((0o755 if path==mac else 0o644)<<16); info.compress_type=zipfile.ZIP_DEFLATED
                archive.writestr(info,path.read_bytes())
    return output


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT); args=parser.parse_args(); print(f"[OK] wrote {materialize(args.output)}"); return 0


if __name__ == "__main__": raise SystemExit(main())
