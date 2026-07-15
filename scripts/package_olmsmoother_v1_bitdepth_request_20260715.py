#!/usr/bin/env python3
"""Build and verify the executable OLMSmoother v1 16/32bpc Windows request."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REQUEST_ID = "olmsmoother_v1_bitdepth_16_32bpc_software_20260715"
MANIFEST = ROOT / "refs/win_references/20260604_olm/OLMSmoother/reference_manifest.json"
PROJECT = ROOT / "refs/win_references/20260604_olm/aep/OLM test.aep"
AEX = ROOT / "plugins_2025/OLMSmoother.aex"
INPUT_DIR = ROOT / "refs/win_references/20260604_olm/OLMSmoother"
RUNNER_PATH = "run_windows.ps1"
JSX_PATH = "scripts/render_olmsmoother_v1.jsx"
COLOR_PATH = "contracts/color.json"
TEMPLATES_PATH = "contracts/output_templates.json"
SOURCE_MANIFEST_PATH = "source/reference_manifest.json"


class PackageError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def pretty_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=True) + "\n").encode()


def load_manifest() -> dict[str, Any]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("platform") != "windows" or data.get("comp", {}).get("bpc") != 8:
        raise PackageError("the fixed source manifest is no longer the expected Windows 8bpc source")
    return data


def color_contract() -> dict[str, Any]:
    return {
        "working_space": "",
        "working_space_label": "None",
        "linear_blending": False,
        "blend_colors_using_1_0_gamma": False,
    }


def output_template_contract() -> dict[str, Any]:
    return {
        "software_16bpc": {
            "name": "OLM PNG 16 RGBA",
            "container_format": "PNG",
            "sample_type": "unsigned_integer",
            "bits_per_channel": 16,
            "channel_order": "RGBA",
            "channel_count": 4,
        },
        "software_32bpc": {
            "name": "OLM EXR 32 Float RGBA No Compression",
            "container_format": "OpenEXR",
            "compression": "none",
            "sample_type": "float32",
            "pixel_type": 2,
            "channel_order": "RGBA",
            "channel_count": 4,
            "classification": "probe-only",
        },
    }


def renderer_jsx_asset() -> str:
    return r'''/* Deterministic OLMSmoother v1 dual-depth AE renderer. */
(function () {
    function env(name) { try { return $.getenv(name) || ""; } catch (_) { return ""; } }
    function fail(message) { throw new Error("OLMSmoother v1 request: " + message); }
    function readText(path) { var f = new File(path); f.encoding = "UTF-8"; if (!f.open("r")) fail("cannot read " + path); var t = f.read(); f.close(); return t; }
    function parse(path) { return eval("(" + readText(path) + ")"); }
    function writeText(path, text) { var f = new File(path); f.encoding = "UTF-8"; if (!f.open("w")) fail("cannot write " + path); f.write(text); f.close(); }
    function esc(value) { return String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\r/g, "\\r").replace(/\n/g, "\\n"); }
    function json(value) {
        if (value === null || value === undefined) return "null";
        if (typeof value === "string") return '"' + esc(value) + '"';
        if (typeof value === "number" || typeof value === "boolean") return String(value);
        if (Object.prototype.toString.call(value) === "[object Array]") { var a = []; for (var i = 0; i < value.length; i++) a.push(json(value[i])); return "[" + a.join(",") + "]"; }
        var rows = []; for (var key in value) if (value.hasOwnProperty(key)) rows.push(json(key) + ":" + json(value[key])); return "{" + rows.join(",") + "}";
    }
    function findById(rows, id) { for (var i = 0; i < rows.length; i++) if (rows[i].id === id) return rows[i]; return null; }
    function childByMatch(group, matchName) { for (var i = 1; i <= group.numProperties; i++) { var p = group.property(i); if (p && p.matchName === matchName) return p; } return null; }
    function equalValue(actual, expected) {
        if (Object.prototype.toString.call(expected) === "[object Array]") {
            if (!actual || actual.length !== expected.length) return false;
            for (var i = 0; i < expected.length; i++) if (Math.abs(Number(actual[i]) - Number(expected[i])) > 0.000001) return false;
            return true;
        }
        return Math.abs(Number(actual) - Number(expected)) <= 0.000001;
    }
    function hasTemplate(module, name) { var rows = module.templates; for (var i = 0; i < rows.length; i++) if (rows[i] === name) return true; return false; }
    function canonicalParams(params) {
        var rows = [];
        for (var i = 0; i < params.length; i++) {
            var p = params[i];
            rows.push({match_name:p.match_name, name:p.name, property_index:p.property_index, value:p.value});
        }
        return json(rows) + "\n";
    }

    var root = env("OLM_SMOOTHER_PACKAGE_ROOT");
    var runRoot = env("OLM_SMOOTHER_RUN_ROOT");
    var caseId = env("OLM_SMOOTHER_CASE_ID");
    var renderSetId = env("OLM_SMOOTHER_RENDER_SET_ID");
    var resultPath = env("OLM_SMOOTHER_RESULT_JSON");
    var result = {status:"error", error:"", ae_version:String(app.version), case_id:caseId, render_set_id:renderSetId, renderer:"", project_bits_per_channel:-1, working_space:"", linear_blending:null, effect:{}, params:[], params_canonical:"", output:"", output_template:"", output_settings:""};
    var suppress = false;
    try {
        if (!root || !runRoot || !caseId || !renderSetId || !resultPath) fail("required environment is missing");
        var request = parse(root + "/request.json");
        var colors = parse(root + "/contracts/color.json");
        var templates = parse(root + "/contracts/output_templates.json");
        if (request.effect.name !== "OLM Smoother" || request.effect.match_name !== "OLM Smoother" || request.effect.variant !== "v1") fail("request effect identity is not v1");
        var requestCase = findById(request.cases, caseId);
        var renderSet = findById(request.render_sets, renderSetId);
        if (!requestCase || !renderSet) fail("unknown case or render set");
        app.beginSuppressDialogs(); suppress = true;
        if (app.project) try { app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES); } catch (_) {}
        app.newProject();
        app.project.bitsPerChannel = Number(renderSet.bits_per_channel);
        app.project.workingSpace = colors.working_space;
        app.project.linearBlending = colors.linear_blending;
        try { app.project.gpuAccelType = GpuAccelType.SOFTWARE; } catch (gpuError) { fail("cannot set SOFTWARE renderer: " + gpuError.toString()); }
        result.renderer = String(app.project.gpuAccelType).toUpperCase();
        result.project_bits_per_channel = Number(app.project.bitsPerChannel);
        result.working_space = String(app.project.workingSpace);
        result.linear_blending = app.project.linearBlending ? true : false;
        if (result.renderer.indexOf("SOFTWARE") < 0) fail("renderer is not SOFTWARE: " + result.renderer);
        if (result.project_bits_per_channel !== Number(renderSet.bits_per_channel)) fail("project bpc mismatch");
        if (result.working_space !== colors.working_space || result.linear_blending !== colors.linear_blending) fail("color contract mismatch");

        var input = new File(root + "/" + requestCase.input.path);
        if (!input.exists) fail("input missing: " + input.fsName);
        var footage = app.project.importFile(new ImportOptions(input));
        if (Number(footage.width) !== Number(request.fixture.width) || Number(footage.height) !== Number(request.fixture.height)) fail("input dimensions do not match fixed render cell");
        var comp = app.project.items.addComp("OLMSmoother_v1_" + renderSetId + "_" + caseId, Number(request.fixture.width), Number(request.fixture.height), 1.0, 1.0 / Number(request.fixture.frame_rate), Number(request.fixture.frame_rate));
        var layer = comp.layers.add(footage);
        var parade = layer.property("ADBE Effect Parade");
        var effect = parade.addProperty("OLM Smoother");
        if (!effect || effect.name !== "OLM Smoother" || effect.matchName !== "OLM Smoother") fail("OLM Smoother v1 did not bind exactly");
        result.effect = {name:effect.name, match_name:effect.matchName, property_index:effect.propertyIndex, enabled:effect.enabled, active:effect.active};
        var expectedParams = requestCase.effect.params;
        for (var p = 0; p < expectedParams.length; p++) {
            var expected = expectedParams[p];
            var prop = childByMatch(effect, expected.match_name);
            if (!prop || prop.propertyIndex !== expected.property_index) fail("missing exact parameter " + expected.match_name);
            prop.setValue(expected.value);
            var actual = prop.value;
            if (!equalValue(actual, expected.value)) fail("parameter readback mismatch " + expected.match_name);
            result.params.push({name:prop.name, match_name:prop.matchName, property_index:prop.propertyIndex, value:actual});
        }
        if (result.params.length !== 3) fail("v1 parameter count is not three");
        result.params_canonical = canonicalParams(result.params);

        var template = templates[renderSetId];
        if (!template || !template.name) fail("output template contract missing");
        var rq = app.project.renderQueue.items.add(comp);
        rq.timeSpanStart = Number(requestCase.time || 0);
        rq.timeSpanDuration = 1.0 / Number(request.fixture.frame_rate);
        var module = rq.outputModule(1);
        if (!hasTemplate(module, template.name)) fail("missing Output Module template: " + template.name);
        module.applyTemplate(template.name);
        result.output_template = template.name;
        try { result.output_settings = module.getSettings(GetSettingsFormat.STRING_SETTABLE).toSource(); } catch (settingsError) { fail("cannot record output settings: " + settingsError.toString()); }
        var extension = renderSetId === "software_16bpc" ? ".png" : ".exr";
        var sequence = runRoot + "/outputs/" + renderSetId + "/" + caseId + "_[#####]" + extension;
        var expectedOutput = new File(sequence.replace("[#####]", "00000"));
        if (expectedOutput.exists && !expectedOutput.remove()) fail("cannot remove stale output");
        module.file = new File(sequence);
        app.project.renderQueue.render();
        if (!expectedOutput.exists) fail("output was not written: " + expectedOutput.fsName);
        result.output = expectedOutput.fsName;
        result.status = "ok";
    } catch (error) {
        result.error = error.toString();
    } finally {
        try { if (suppress) app.endSuppressDialogs(false); } catch (_) {}
        if (resultPath) writeText(resultPath, json(result) + "\n");
        try { if (app.project) app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES); } catch (_) {}
        try { app.quit(); } catch (_) {}
    }
    if (result.status !== "ok") fail(result.error || "unknown render failure");
}());
'''


def powershell_asset() -> str:
    return r'''param(
  [Parameter(Mandatory=$true)][string]$AfterFX,
  [string]$OutputDir = "",
  [int]$TimeoutSeconds = 600
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSCommandPath
$RunRoot = if ($OutputDir) { [IO.Path]::GetFullPath($OutputDir) } else { Join-Path $Root "run" }
$ReturnManifest = Join-Path $RunRoot "return_manifest.json"
$RequestPath = Join-Path $Root "request.json"
$BackupPath = $null
$InstalledAex = Join-Path $env:APPDATA "Adobe\Common\Plug-ins\7.0\MediaCore\OLMSmoother.aex"
$InstalledAexExisted = $false
$InstalledAexChanged = $false

function Write-Json([string]$Path, $Value) { $Value | ConvertTo-Json -Depth 50 | Set-Content -LiteralPath $Path -Encoding UTF8 }
function Fail-Closed([string]$Status, [string]$Message) {
  New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
  Write-Json $ReturnManifest ([ordered]@{kind="olmsmoother_v1_bitdepth_return";schema=1;request_id="olmsmoother_v1_bitdepth_16_32bpc_software_20260715";status=$Status;rendered=$false;error=$Message})
  throw "$Status`: $Message"
}
function Hash([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Resolve-PackagePath([string]$Relative) { Join-Path $Root ($Relative.Replace('/', '\')) }
function Require-File([string]$Path, [string]$Status) { if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { Fail-Closed $Status "missing file: $Path" } }
function Read-BigEndian32([byte[]]$Bytes, [int]$Offset) { ([int64]$Bytes[$Offset] -shl 24) -bor ([int64]$Bytes[$Offset+1] -shl 16) -bor ([int64]$Bytes[$Offset+2] -shl 8) -bor [int64]$Bytes[$Offset+3] }
function Get-PngMetadata([string]$Path) {
  $b=[IO.File]::ReadAllBytes($Path)
  if ($b.Length -lt 29 -or $b[0] -ne 137 -or $b[1] -ne 80 -or $b[2] -ne 78 -or $b[3] -ne 71) { Fail-Closed "output_metadata" "invalid PNG header: $Path" }
  [ordered]@{container_format="PNG";width=(Read-BigEndian32 $b 16);height=(Read-BigEndian32 $b 20);bits_per_channel=[int]$b[24];color_type=[int]$b[25];channel_order="RGBA";channel_count=4;sample_type="unsigned_integer"}
}
function Read-CString([byte[]]$Bytes, [ref]$Index) { $start=$Index.Value; while($Index.Value -lt $Bytes.Length -and $Bytes[$Index.Value] -ne 0){$Index.Value++}; if($Index.Value -ge $Bytes.Length){Fail-Closed "output_metadata" "unterminated EXR string"}; $s=[Text.Encoding]::ASCII.GetString($Bytes,$start,$Index.Value-$start);$Index.Value++;$s }
function Get-ExrMetadata([string]$Path) {
  $b=[IO.File]::ReadAllBytes($Path); if($b.Length -lt 32 -or [BitConverter]::ToUInt32($b,0) -ne 20000630){Fail-Closed "output_metadata" "invalid OpenEXR header: $Path"}
  $i=8;$channels=@();$compression=-1;$width=0;$height=0
  while($i -lt $b.Length){$ri=[ref]$i;$name=Read-CString $b $ri;$i=$ri.Value;if($name -eq ""){break};$ri=[ref]$i;$type=Read-CString $b $ri;$i=$ri.Value;if($i+4 -gt $b.Length){Fail-Closed "output_metadata" "truncated EXR attribute"};$size=[BitConverter]::ToInt32($b,$i);$i+=4;$end=$i+$size;if($size -lt 0 -or $end -gt $b.Length){Fail-Closed "output_metadata" "invalid EXR attribute size"}
    if($name -eq "compression"){$compression=[int]$b[$i]}
    elseif($name -eq "dataWindow" -and $size -eq 16){$minx=[BitConverter]::ToInt32($b,$i);$miny=[BitConverter]::ToInt32($b,$i+4);$maxx=[BitConverter]::ToInt32($b,$i+8);$maxy=[BitConverter]::ToInt32($b,$i+12);$width=$maxx-$minx+1;$height=$maxy-$miny+1}
    elseif($name -eq "channels"){$ci=$i;while($ci -lt $end){$cr=[ref]$ci;$cn=Read-CString $b $cr;$ci=$cr.Value;if($cn -eq ""){break};if($ci+16 -gt $end){Fail-Closed "output_metadata" "truncated EXR channel"};$pt=[BitConverter]::ToInt32($b,$ci);$ci+=16;$channels+=,[ordered]@{name=$cn;pixel_type=$pt;sample_type=$(if($pt -eq 2){"float32"}elseif($pt -eq 1){"float16"}else{"unsupported"})}}}
    $i=$end
  }
  $names=@($channels|ForEach-Object{$_.name}|Sort-Object);if(($names -join ',') -ne 'A,B,G,R'){Fail-Closed "output_metadata" "OpenEXR must contain exactly RGBA channels"};foreach($c in $channels){if($c.pixel_type -ne 2){Fail-Closed "output_metadata" "OpenEXR channel $($c.name) is not FLOAT"}}
  [ordered]@{container_format="OpenEXR";width=$width;height=$height;compression_code=$compression;channels=$channels;channel_order="RGBA";channel_count=4;sample_type="float32";typed_float=$true}
}

New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
Require-File $RequestPath "missing_request"
Require-File $AfterFX "missing_afterfx"
if(Get-Process -Name AfterFX -ErrorAction SilentlyContinue){Fail-Closed "afterfx_running" "close After Effects before running this package"}
$request=Get-Content -LiteralPath $RequestPath -Raw|ConvertFrom-Json
if($request.effect.name -cne "OLM Smoother" -or $request.effect.match_name -cne "OLM Smoother" -or $request.effect.variant -cne "v1" -or -not $request.effect.v2_is_out_of_scope){Fail-Closed "effect_identity" "request does not bind OLMSmoother v1 exactly"}
foreach($name in @("reference_manifest","project","windows_aex","runner","renderer_jsx","color_management","output_templates")){$record=$request.source_contract.$name;$path=Resolve-PackagePath ([string]$record.path);Require-File $path "missing_asset";if((Hash $path)-ne [string]$record.sha256){Fail-Closed "hash_mismatch" "$name SHA-256 mismatch"}}
foreach($case in $request.cases){$path=Resolve-PackagePath ([string]$case.input.path);Require-File $path "missing_input";if((Hash $path)-ne [string]$case.input.sha256){Fail-Closed "input_hash_mismatch" "$($case.id) input SHA-256 mismatch"}}
$color=Get-Content -LiteralPath (Resolve-PackagePath ([string]$request.source_contract.color_management.path)) -Raw|ConvertFrom-Json
$templates=Get-Content -LiteralPath (Resolve-PackagePath ([string]$request.source_contract.output_templates.path)) -Raw|ConvertFrom-Json
if($color.working_space -cne "" -or [bool]$color.linear_blending -or [bool]$color.blend_colors_using_1_0_gamma){Fail-Closed "color_contract" "fixed color settings changed"}
if($templates.software_16bpc.name -cne "OLM PNG 16 RGBA" -or $templates.software_32bpc.name -cne "OLM EXR 32 Float RGBA No Compression"){Fail-Closed "template_contract" "fixed output-template names changed"}

$AexPath=Resolve-PackagePath ([string]$request.source_contract.windows_aex.path)
$records=@()
try {
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $InstalledAex)|Out-Null
  $InstalledAexExisted=Test-Path -LiteralPath $InstalledAex
  if($InstalledAexExisted){if((Hash $InstalledAex) -ne (Hash $AexPath)){$BackupPath=Join-Path $RunRoot "preexisting_OLMSmoother.aex";Copy-Item -LiteralPath $InstalledAex -Destination $BackupPath -Force;Copy-Item -LiteralPath $AexPath -Destination $InstalledAex -Force;$InstalledAexChanged=$true}}else{Copy-Item -LiteralPath $AexPath -Destination $InstalledAex -Force;$InstalledAexChanged=$true}
  if((Hash $InstalledAex) -ne [string]$request.source_contract.windows_aex.sha256){Fail-Closed "aex_install" "installed v1 AEX hash mismatch"}
  foreach($set in $request.render_sets){foreach($case in $request.cases){
    $caseRoot=Join-Path $RunRoot ("results\"+$set.id+"\"+$case.id);New-Item -ItemType Directory -Force -Path $caseRoot|Out-Null
    $resultPath=Join-Path $caseRoot "ae_result.json";if(Test-Path $resultPath){Remove-Item $resultPath -Force}
    $env:OLM_SMOOTHER_PACKAGE_ROOT=$Root;$env:OLM_SMOOTHER_RUN_ROOT=$RunRoot;$env:OLM_SMOOTHER_CASE_ID=$case.id;$env:OLM_SMOOTHER_RENDER_SET_ID=$set.id;$env:OLM_SMOOTHER_RESULT_JSON=$resultPath
    $process=Start-Process -FilePath $AfterFX -ArgumentList ('-r "'+(Resolve-PackagePath ([string]$request.execution.renderer_jsx))+'"') -PassThru
    if(-not $process.WaitForExit($TimeoutSeconds*1000)){try{$process|Stop-Process -Force}catch{};Fail-Closed "render_timeout" "$($set.id)/$($case.id) timed out"}
    Require-File $resultPath "missing_result";$result=Get-Content -LiteralPath $resultPath -Raw|ConvertFrom-Json
    if($result.status -ne "ok" -or [int]$result.project_bits_per_channel -ne [int]$set.bits_per_channel -or ([string]$result.renderer).ToUpperInvariant() -notmatch "SOFTWARE"){Fail-Closed "render_contract" "$($set.id)/$($case.id) AE contract failed: $($result.error)"}
    if($result.effect.name -cne "OLM Smoother" -or $result.effect.match_name -cne "OLM Smoother" -or @($result.params).Count -ne 3 -or -not [string]$result.params_canonical){Fail-Closed "effect_metadata" "$($set.id)/$($case.id) effect/parameter metadata incomplete"}
    $output=[string]$result.output;Require-File $output "missing_output";$metadata=if($set.id -eq "software_16bpc"){Get-PngMetadata $output}else{Get-ExrMetadata $output}
    if($metadata.width -ne [int]$request.fixture.width -or $metadata.height -ne [int]$request.fixture.height){Fail-Closed "output_metadata" "$($set.id)/$($case.id) dimensions changed"}
    if($set.id -eq "software_16bpc" -and ($metadata.bits_per_channel -ne 16 -or $metadata.color_type -ne 6)){Fail-Closed "output_metadata" "$($case.id) is not 16-bit RGBA PNG"}
    if($set.id -eq "software_32bpc" -and $metadata.compression_code -ne 0){Fail-Closed "output_metadata" "$($case.id) OpenEXR is not uncompressed"}
    $templateRecord=$templates.PSObject.Properties[[string]$set.id].Value
    if([string]$result.output_template -cne [string]$templateRecord.name -or -not [string]$result.output_settings){Fail-Closed "template_metadata" "$($set.id)/$($case.id) template/settings missing"}
    $paramsPath=Join-Path $caseRoot "effect_params.json";[IO.File]::WriteAllText($paramsPath,[string]$result.params_canonical,(New-Object -TypeName System.Text.UTF8Encoding -ArgumentList $false));$actualParamsHash=Hash $paramsPath;if($actualParamsHash -cne [string]$case.effect.v1_params_sha256){Fail-Closed "parameter_hash_mismatch" "$($set.id)/$($case.id) v1 parameter readback hash mismatch"}
    $records+=,[ordered]@{ae_version=$result.ae_version;render_set_id=$set.id;bits_per_channel=[int]$set.bits_per_channel;classification=$set.acceptance;case_id=$case.id;input=[ordered]@{path=$case.input.path;sha256=$case.input.sha256};effect=$result.effect;params=$result.params;params_hashes=[ordered]@{expected_v1_params_sha256=$case.effect.v1_params_sha256;actual_readback_sha256=$actualParamsHash;matched=$true};renderer="SOFTWARE";color=[ordered]@{contract_sha256=$request.source_contract.color_management.sha256;working_space=$result.working_space;linear_blending=$result.linear_blending};output_template=[ordered]@{name=$result.output_template;contract_sha256=$request.source_contract.output_templates.sha256;settings=$result.output_settings};output=[ordered]@{path=$output;sha256=(Hash $output);metadata=$metadata};ae_result_sha256=(Hash $resultPath)}
  }}
  if($records.Count -ne 6){Fail-Closed "missing_records" "expected six render records"}
  $return=[ordered]@{kind="olmsmoother_v1_bitdepth_return";schema=1;request_id=$request.request_id;status="rendered";rendered=$true;ae_version=$records[0].ae_version;effect=$request.effect;source_contract=$request.source_contract;render_sets=$request.render_sets;records=$records;classification=[ordered]@{software_16bpc="exact-eligible only after cross-host comparison";software_32bpc="probe-only"}}
  Write-Json $ReturnManifest $return
  $returnHash=Hash $ReturnManifest;Set-Content -LiteralPath ($ReturnManifest+".sha256") -Encoding ASCII -Value ($returnHash+"  return_manifest.json")
  Compress-Archive -Path (Join-Path $RunRoot "*") -DestinationPath ($RunRoot+"_return.zip") -Force
  Write-Host "OK return_manifest=$ReturnManifest return_zip=$($RunRoot)_return.zip"
} finally {
  Get-Process -Name AfterFX -ErrorAction SilentlyContinue|Stop-Process -Force -ErrorAction SilentlyContinue
  if($InstalledAexChanged){if($InstalledAexExisted -and $BackupPath -and (Test-Path $BackupPath)){Copy-Item -LiteralPath $BackupPath -Destination $InstalledAex -Force}elseif(Test-Path $InstalledAex){Remove-Item -LiteralPath $InstalledAex -Force}}
}
'''


def build_request() -> dict[str, Any]:
    manifest = load_manifest()
    cases = []
    for source_case in manifest["cases"][:3]:
        effect = source_case["effects"][0]
        if effect.get("name") != "OLM Smoother" or effect.get("match_name") != "OLM Smoother":
            raise PackageError(f"unexpected v1 effect identity in {source_case['id']}")
        params = [{key: param.get(key) for key in ("name", "match_name", "property_index", "property_value_type", "value", "enabled", "active")} for param in effect["params"][:3]]
        before = INPUT_DIR / source_case["before_effects_frame"]
        readback = [{key: param[key] for key in ("match_name", "name", "property_index", "value")} for param in params]
        cases.append({"id": source_case["id"], "time": source_case["time"], "input": {"path": f"inputs/{before.name}", "sha256": sha256_file(before), "before_effects_scope": source_case["before_effects_scope"]}, "effect": {"name": effect["name"], "match_name": effect["match_name"], "property_index": effect["property_index"], "enabled": effect["enabled"], "active": effect["active"], "params": params, "v1_params_sha256": sha256_bytes(canonical_json(readback))}})
    color_data = canonical_json(color_contract())
    template_data = canonical_json(output_template_contract())
    runner_data = powershell_asset().encode()
    jsx_data = renderer_jsx_asset().encode()
    return {
        "schema": "olm.conformance.request/2", "request_id": REQUEST_ID, "created_at": "2026-07-15", "status": "sendable_fail_closed",
        "effect": {"name": "OLM Smoother", "match_name": "OLM Smoother", "variant": "v1", "v2_is_out_of_scope": True},
        "execution": {"runner": RUNNER_PATH, "renderer_jsx": JSX_PATH, "mode": "deterministic_comp_build_from_hashed_inputs", "command": '.\\run_windows.ps1 -AfterFX "C:\\Program Files\\Adobe\\Adobe After Effects 2026\\Support Files\\AfterFX.exe"'},
        "fixture": {"width": 960, "height": 540, "frame_rate": 24, "source_comp_width": 1920, "source_comp_height": 1080, "source_resolution_factor": [2, 2]},
        "source_contract": {
            "reference_manifest": {"path": SOURCE_MANIFEST_PATH, "sha256": sha256_file(MANIFEST)},
            "project": {"path": "project/OLM test.aep", "sha256": sha256_file(PROJECT), "role": "fixed source provenance; comps are rebuilt deterministically"},
            "windows_aex": {"path": "plugin/OLMSmoother.aex", "sha256": sha256_file(AEX)},
            "runner": {"path": RUNNER_PATH, "sha256": sha256_bytes(runner_data)},
            "renderer_jsx": {"path": JSX_PATH, "sha256": sha256_bytes(jsx_data)},
            "color_management": {"path": COLOR_PATH, "sha256": sha256_bytes(color_data)},
            "output_templates": {"path": TEMPLATES_PATH, "sha256": sha256_bytes(template_data)},
        },
        "render_sets": [
            {"id": "software_16bpc", "required": True, "renderer": "Software", "project_gpu_accel_type.current_name": "SOFTWARE", "bits_per_channel": 16, "output_format": "png", "output_template": output_template_contract()["software_16bpc"]["name"], "acceptance": "integer-exact-eligible-after-return-and-cross-host-hash-checks"},
            {"id": "software_32bpc", "required": True, "renderer": "Software", "project_gpu_accel_type.current_name": "SOFTWARE", "bits_per_channel": 32, "output_format": "exr", "output_template": output_template_contract()["software_32bpc"]["name"], "acceptance": "probe-only-until-independent-mac-boundary-proof"},
        ],
        "cases": cases,
        "parameter_contract": {"mapping": "Use Color Key, Color Key, Do Smooth Range -> v1 SM_USE_KEY, SM_KEY_COLOR, SM_TOLERANCE", "property_indices": [1, 2, 3], "do_not_use_v2_mapping": True},
        "return_requirements": ["Six successful AE render records", "exact v1 effect identity, three parameter readbacks, and parameter artifact hashes", "SOFTWARE renderer and fixed project/color/template metadata", "SHA-256 for inputs, outputs, AEX, AEP, runner, JSX, contracts, AE result files and return manifest", "16-bit RGBA PNG metadata for 16bpc", "typed uncompressed RGBA OpenEXR metadata for 32bpc; classification remains probe-only"],
        "stop_lines": ["missing_runner_or_jsx", "missing_renderer_or_template", "aex_or_input_hash_mismatch", "effect_identity_or_parameter_readback_mismatch", "parameter_hash_mismatch", "missing_output_or_metadata", "32bpc_non_typed_exr", "any_v2_substitution"],
    }


def package_entries(request: dict[str, Any]) -> dict[str, bytes]:
    entries = {
        "request.json": pretty_json(request),
        RUNNER_PATH: powershell_asset().encode(), JSX_PATH: renderer_jsx_asset().encode(),
        COLOR_PATH: canonical_json(color_contract()), TEMPLATES_PATH: canonical_json(output_template_contract()),
        SOURCE_MANIFEST_PATH: MANIFEST.read_bytes(), "project/OLM test.aep": PROJECT.read_bytes(), "plugin/OLMSmoother.aex": AEX.read_bytes(),
    }
    for case in request["cases"]:
        entries[case["input"]["path"]] = (INPUT_DIR / Path(case["input"]["path"]).name).read_bytes()
    entries["README.md"] = ("# OLMSmoother v1 16/32bpc Windows Software request\n\nRun the packaged `run_windows.ps1` with `-AfterFX`. The runner stages and hash-checks the packaged v1 AEX, deterministically builds all three cases at 16bpc and 32bpc under Software, requires the exact named Output Module templates, validates typed output headers, restores any prior AEX, and emits `run/return_manifest.json` plus a return ZIP. The 32bpc lane remains probe-only.\n").encode()
    return entries


def verify_request(request: dict[str, Any]) -> None:
    if request.get("status") != "sendable_fail_closed": raise PackageError("request is not marked sendable_fail_closed")
    if request.get("effect") != {"name": "OLM Smoother", "match_name": "OLM Smoother", "variant": "v1", "v2_is_out_of_scope": True}: raise PackageError("request effect identity is not exact v1")
    if request.get("execution", {}).get("runner") != RUNNER_PATH or request.get("execution", {}).get("renderer_jsx") != JSX_PATH: raise PackageError("request does not reference the packaged runner and JSX")
    if [row.get("bits_per_channel") for row in request.get("render_sets", [])] != [16, 32]: raise PackageError("request render sets are not fixed 16/32bpc")
    if any(len(case.get("effect", {}).get("params", [])) != 3 for case in request.get("cases", [])): raise PackageError("request must contain exactly three v1 parameters per case")
    if request.get("source_contract", {}).get("output_templates", {}).get("path") != TEMPLATES_PATH: raise PackageError("request does not bind the output-template contract")
    required_stops = {"missing_runner_or_jsx", "missing_renderer_or_template", "aex_or_input_hash_mismatch", "parameter_hash_mismatch", "missing_output_or_metadata", "any_v2_substitution"}
    if not required_stops <= set(request.get("stop_lines", [])): raise PackageError("request is missing negative stop conditions")


def verify_package(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        required = {"request.json", "README.md", RUNNER_PATH, JSX_PATH, COLOR_PATH, TEMPLATES_PATH, SOURCE_MANIFEST_PATH, "project/OLM test.aep", "plugin/OLMSmoother.aex"}
        missing = sorted(required - names)
        if missing: raise PackageError("missing package entries: " + ", ".join(missing))
        request = json.loads(archive.read("request.json"))
        verify_request(request)
        for name, record in request["source_contract"].items():
            asset = record["path"]
            if asset not in names: raise PackageError(f"missing source_contract asset {name}: {asset}")
            if sha256_bytes(archive.read(asset)) != record["sha256"]: raise PackageError(f"sha256 mismatch for {name}: {asset}")
        for case in request["cases"]:
            asset = case["input"]["path"]
            if asset not in names or sha256_bytes(archive.read(asset)) != case["input"]["sha256"]: raise PackageError(f"input hash mismatch for {case['id']}")
        runner = archive.read(RUNNER_PATH).decode()
        jsx = archive.read(JSX_PATH).decode()
        for token in ("missing_afterfx", "missing_input", "missing_output", "output_metadata", "template_metadata", "effect_metadata", "parameter_hash_mismatch", "Get-PngMetadata", "Get-ExrMetadata"):
            if token not in runner: raise PackageError(f"runner is missing fail-closed gate {token}")
        for token in ('GpuAccelType.SOFTWARE', 'bitsPerChannel', 'addProperty("OLM Smoother")', 'missing Output Module template', 'parameter readback mismatch'):
            if token not in jsx: raise PackageError(f"JSX is missing execution gate {token}")
        if "OLMSmoother2" in runner or "OLMSmoother2" in jsx: raise PackageError("runner/JSX must not reference OLMSmoother2")


def write_package(output: Path) -> None:
    request = build_request()
    verify_request(request)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(package_entries(request).items()): archive.writestr(name, data)
    verify_package(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-output", type=Path, default=ROOT / "refs/reference_requests" / f"{REQUEST_ID}.json")
    parser.add_argument("--package-output", type=Path, default=ROOT / "handoffs/windows_batch" / f"{REQUEST_ID}.zip")
    parser.add_argument("--verify-only", type=Path)
    args = parser.parse_args()
    try:
        if args.verify_only:
            verify_package(args.verify_only); print(f"[OK] verified {args.verify_only}"); return 0
        request = build_request(); args.request_output.parent.mkdir(parents=True, exist_ok=True); args.request_output.write_bytes(pretty_json(request)); write_package(args.package_output)
        print(f"wrote {args.request_output}"); print(f"wrote {args.package_output}"); return 0
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"[FAIL] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
