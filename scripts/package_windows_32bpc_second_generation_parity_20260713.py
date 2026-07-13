#!/usr/bin/env python3
"""Package focused Windows AE26.3 second-generation EXR parity probes."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMbit-depthconformancebatch"
PACKAGE = "olm_windows_32bpc_second_generation_parity_20260713"
TEMPLATE = "OLM EXR 32 Float"
CASES = (
    {
        "id": "olmcolorkey__case_0002",
        "spec": "refs/reference_requests/olm_bitdepth_32bpc_colorkey_float_20260710.json",
        "effect": "OLM Color Key",
        "plugin_name": "OLMColorKey.aex",
        "plugin_sha256": "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c",
    },
    {
        "id": "olmtoondilate__case_0001",
        "spec": "refs/reference_requests/olm_bitdepth_32bpc_toondilate_float_20260710.json",
        "effect": "ADBE OLMToonDilate",
        "plugin_name": "OLMToonDilate.aex",
        "plugin_sha256": "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3",
    },
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ps1() -> str:
    case_rows = json.dumps(CASES, separators=(",", ":"))
    return rf'''param(
  [Parameter(Mandatory=$true)][string]$AfterFX,
  [Parameter(Mandatory=$true)][string]$ColorKeyAex,
  [Parameter(Mandatory=$true)][string]$ToonDilateAex,
  [Parameter(Mandatory=$false)][string]$OutputDir=""
)
$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$RunDir=if($OutputDir){{$OutputDir}}else{{Join-Path $Root "run"}}
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
$Cases=ConvertFrom-Json @'
{case_rows}
'@
function WriteJson($Path,$Value){{$Value|ConvertTo-Json -Depth 30|Set-Content -Encoding UTF8 $Path}}
function Fail([string]$Status,[string]$Message){{WriteJson (Join-Path $RunDir "return_manifest.json") ([ordered]@{{kind="olm_32bpc_second_generation_return";status=$Status;error=$Message;rendered=$false}});throw "$Status`: $Message"}}
if(-not(Test-Path -LiteralPath $AfterFX -PathType Leaf)){{Fail "missing_afterfx" "AfterFX.exe missing"}}
if($env:OLM_EXR_TEMPLATE -and $env:OLM_EXR_TEMPLATE -cne "{TEMPLATE}"){{Fail "wrong_template" "OLM_EXR_TEMPLATE must be exactly {TEMPLATE}"}}
$Template="{TEMPLATE}"
$Plugins=@{{"OLMColorKey.aex"=$ColorKeyAex;"OLMToonDilate.aex"=$ToonDilateAex}}
$PluginRecords=@{{}}
foreach($c in $Cases){{$p=$Plugins[$c.plugin_name];if(-not(Test-Path -LiteralPath $p -PathType Leaf)){{Fail "missing_plugin" "$($c.plugin_name) missing"}};$h=(Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLowerInvariant();if($h -ne $c.plugin_sha256){{Fail "hash_mismatch" "$($c.plugin_name) $h != $($c.plugin_sha256)"}};$PluginRecords[$c.plugin_name]=[ordered]@{{path=(Resolve-Path $p).Path;sha256=$h}}}}
$Results=@()
foreach($c in $Cases){{
  $RequestDir=Join-Path $Root ("cases\"+$c.id)
  foreach($mode in @("effect_on","no_effect")){{
    $Out=Join-Path $RunDir ($c.id+"_"+$mode);New-Item -ItemType Directory -Force -Path $Out|Out-Null
    $env:OLM_AE_REQUEST_DIR=$RequestDir;$env:OLM_AE_CASE_ID=$c.id;$env:OLM_AE_OUTPUT_DIR=$Out
    $env:OLM_AE_LOG_PATH=Join-Path $Out "AE_SINGLE_CASE.log";$env:OLM_AE_RESULT_JSON=Join-Path $Out "AE_SINGLE_CASE_RESULT.json"
    $env:OLM_AE_OUTPUT_MODE="exr_render_queue";$env:OLM_AE_OUTPUT_TEMPLATE=$Template;$env:OLM_AE_FORCE_SOFTWARE="1"
    $env:OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT="1";$env:OLM_AE_FORCE_NEW_PROJECT="1";$env:OLM_AE_KEEP_OPEN=""
    $env:OLM_AE_DISABLE_EFFECT=if($mode -eq "no_effect"){{"1"}}else{{""}}
    & $AfterFX -r (Join-Path $Root "render_case.jsx")
    if($LASTEXITCODE -ne 0 -or -not(Test-Path $env:OLM_AE_RESULT_JSON)){{Fail "render_failed" "$($c.id) $mode did not return JSON"}}
    $r=Get-Content $env:OLM_AE_RESULT_JSON -Raw|ConvertFrom-Json
    if($r.status -ne "ok" -or $r.project_bits_per_channel -ne 32 -or $r.project_linear_blending -ne $false){{Fail "contract_mismatch" "$($c.id) $mode host contract mismatch"}}
    if(($mode -eq "no_effect") -ne [bool]$r.effect_disabled){{Fail "effect_state_mismatch" "$($c.id) $mode effect state mismatch"}}
    if(-not $r.output_exr -or -not(Test-Path -LiteralPath $r.output_exr)){{Fail "missing_exr" "$($c.id) $mode EXR missing"}}
    $Results += [ordered]@{{case_id=$c.id;mode=$mode;effect=$c.effect;plugin=$PluginRecords[$c.plugin_name];result=$r;exr_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $r.output_exr).Hash.ToLowerInvariant()}}
  }}
}}
if(-not $Results[0].result.ae_version.StartsWith("26.3")){{Fail "wrong_ae_version" "AE 26.3 required; got $($Results[0].result.ae_version)"}}
$Manifest=[ordered]@{{kind="olm_32bpc_second_generation_return";schema=1;status="rendered";rendered=$true;ae_version=$Results[0].result.ae_version;renderer="SOFTWARE";bits_per_channel=32;linear_light=$false;output_template=$Template;input_contract="same supplied Windows before-effect EXR re-imported for effect-on and no-effect";results=$Results}}
WriteJson (Join-Path $RunDir "return_manifest.json") $Manifest
$Zip=Join-Path (Split-Path $RunDir -Parent) "olm_windows_32bpc_second_generation_parity_return.zip"
if(Test-Path $Zip){{Remove-Item $Zip -Force}}
Compress-Archive -Path (Join-Path $RunDir "*") -DestinationPath $Zip
Write-Host "OK return=$Zip"
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "refs/reference_requests" / f"{PACKAGE}.zip")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    from materialize_32bpc_mac_request import materialize

    with tempfile.TemporaryDirectory(prefix=PACKAGE + "_") as td:
        stage = Path(td) / PACKAGE
        stage.mkdir()
        input_records = []
        for case in CASES:
            case_dir = stage / "cases" / case["id"]
            materialize(ROOT / case["spec"], SOURCE, case_dir, case["id"])
            source_exr = next((case_dir / "input").glob("*.exr"))
            input_records.append({"case_id": case["id"], "path": source_exr.relative_to(stage).as_posix(), "sha256": sha256(source_exr)})
        shutil.copy2(ROOT / "scripts/ae_render_single_case.jsx", stage / "render_case.jsx")
        (stage / "run.ps1").write_text(ps1(), encoding="utf-8")
        manifest = {"kind": "olm_32bpc_second_generation_request", "schema": 1, "created_at": "2026-07-13", "required_ae": "26.3", "renderer": "SOFTWARE", "bits_per_channel": 32, "linear_light": False, "output_template": TEMPLATE, "input_contract": "re-import supplied before-effect EXR identically for effect-on and no-effect", "cases": list(CASES), "inputs": input_records}
        (stage / "request_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (stage / "README.md").write_text("# 32bpc second-generation parity\n\nRun `run.ps1 -AfterFX <AfterFX.exe> -ColorKeyAex <2025 OLMColorKey.aex> -ToonDilateAex <2025 OLMToonDilate.aex>`. This deliberately re-imports the supplied before-effect EXR on Windows and renders both effect-on and no-effect, matching the Mac input generation. Return the generated zip. Any host, hash, effect-state, or artifact mismatch fails closed.\n", encoding="utf-8")
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    z.write(path, f"{PACKAGE}/{path.relative_to(stage).as_posix()}")
    print(f"[OK] {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
