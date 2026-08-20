#!/usr/bin/env python3
"""Package the first generic-beta Windows AEX oracle campaign."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "handoffs/generic_beta_windows_oracle_20260820"
REQUEST_ID = "generic_beta_windows_oracle_20260820"
AEX = {
    "OLMToonDilate": ROOT / "plugins_2025/OLMToonDilate.aex",
    "ColorKeep": ROOT / "plugins_2025/ColorKeep.aex",
    "OLMColorKey": ROOT / "plugins_2025/OLMColorKey.aex",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_inputs(directory: Path) -> list[dict]:
    directory.mkdir(parents=True)
    rows = []
    definitions = [("odd_alpha", 17, 11, 1), ("sd_gradient", 640, 360, 2), ("hd_random", 1920, 1080, 3)]
    for name, width, height, seed in definitions:
        yy, xx = np.indices((height, width), dtype=np.uint32)
        rng = np.random.default_rng(seed)
        if name == "hd_random":
            rgba = rng.integers(0, 256, (height, width, 4), dtype=np.uint8)
            rgba[..., 3] = ((xx * 7 + yy * 11) % 256).astype(np.uint8)
        else:
            rgba = np.empty((height, width, 4), dtype=np.uint8)
            rgba[..., 0] = ((xx * 255) // max(1, width - 1)).astype(np.uint8)
            rgba[..., 1] = ((yy * 255) // max(1, height - 1)).astype(np.uint8)
            rgba[..., 2] = ((xx * 13 + yy * 29 + seed * 17) % 256).astype(np.uint8)
            rgba[..., 3] = ((xx * 19 + yy * 31 + seed * 23) % 256).astype(np.uint8)
        # Deterministic opaque/key-color islands exercise all three effects.
        rgba[0, 0] = (0, 0, 0, 255)
        rgba[height // 2, width // 2] = (0, 255, 0, 255)
        rgba[-1, -1] = (255, 0, 0, 0)
        path = directory / f"{name}_{width}x{height}.png"
        Image.fromarray(rgba, "RGBA").save(path, optimize=False)
        rows.append({"id": name, "file": f"inputs/{path.name}", "width": width, "height": height, "sha256": sha(path)})
    return rows


def parameter_sets() -> dict[str, list[dict]]:
    palette = [(255, 0, 0, 0), (255, 0, 255, 0), (255, 255, 0, 0)]
    colorkeep = []
    for count in (1, 3):
        args = [f"Enabled Color Num={count}"]
        for index in range(100):
            color = palette[index % len(palette)] if index < count else (255, 0, 0, 0)
            args.append(f"Color@{index + 2}={','.join(map(str, color))}")
        colorkeep.append({"id": f"count_{count}", "arguments": args})
    return {
        "OLMToonDilate": [
            {"id": "radius_0", "arguments": ["Search Radius=0"]},
            {"id": "radius_2_01", "arguments": ["Search Radius=2.01"]},
            {"id": "radius_5", "arguments": ["Search Radius=5"]},
        ],
        "ColorKeep": colorkeep,
        "OLMColorKey": [
            {"id": "two_keys", "arguments": [
                "Color Keep=0", "Threshold=0.085", "Premultiplied Color=0", "Color Space=3",
                "Number of Colors=2", "Use Color 1=1", "Color 1=255,0,0,0",
                "Use Color 2=1", "Color 2=255,0,255,0", "Enable Replace=0",
                "Amount@18=0", "Distance Type@19=1", "Direction@20=1",
            ]},
            {"id": "edge_blur", "arguments": [
                "Color Keep=0", "Threshold=0.085", "Premultiplied Color=0", "Color Space=3",
                "Number of Colors=2", "Use Color 1=1", "Color 1=255,0,0,0",
                "Use Color 2=1", "Color 2=255,0,255,0", "Enable Replace=0",
                "Amount@18=4", "Distance Type@19=1", "Direction@20=2",
            ]},
        ],
    }


RUNNER = r'''param([Parameter(Mandatory=$true)][string]$Worker,[string]$OutputRoot="")
$ErrorActionPreference="Stop"
$root=Split-Path -Parent $MyInvocation.MyCommand.Path
$manifest=Get-Content (Join-Path $root "campaign-manifest.json") -Raw | ConvertFrom-Json
if(-not [IO.Path]::IsPathFullyQualified($Worker)){throw "-Worker must be an explicit absolute path"}
if(-not (Test-Path -LiteralPath $Worker -PathType Leaf)){throw "worker not found: $Worker"}
if(-not $OutputRoot){$OutputRoot=Join-Path $env:TEMP ("olm_generic_beta_oracle_"+[guid]::NewGuid().ToString("N"))}
New-Item -ItemType Directory -Path $OutputRoot -ErrorAction Stop | Out-Null
$workerHash=(Get-FileHash -Algorithm SHA256 -LiteralPath $Worker).Hash.ToLowerInvariant()
$aexHashes=@{}
foreach($plugin in $manifest.plugins){$path=Join-Path $root $plugin.aex_file;$actual=(Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant();if($actual -ne $plugin.aex_sha256){throw "AEX hash mismatch: $($plugin.id)"};$aexHashes[$plugin.id]=$actual}
$rows=@()
foreach($case in $manifest.cases){
  $plugin=$manifest.plugins|Where-Object id -eq $case.plugin
  $input=$manifest.inputs|Where-Object id -eq $case.input
  $inputPath=Join-Path $root $input.file
  if((Get-FileHash -Algorithm SHA256 -LiteralPath $inputPath).Hash.ToLowerInvariant() -ne $input.sha256){throw "input hash mismatch: $($input.id)"}
  $output=Join-Path $OutputRoot ($case.id+".png");$stderr=Join-Path $OutputRoot ($case.id+".stderr.txt")
  $argv=@("render-png",(Join-Path $root $plugin.aex_file),$inputPath,$output)+@($case.arguments)
  $stdout=& $Worker @argv 2> $stderr;$rc=$LASTEXITCODE
  $payload=$null;try{$payload=$stdout|ConvertFrom-Json}catch{}
  $ok=($rc -eq 0 -and $payload -and $payload.render_error -eq 0 -and (Test-Path $output))
  $rows+=@{id=$case.id;plugin=$case.plugin;input=$case.input;parameters=$case.parameter_set;status=$(if($ok){"ok"}else{"error"});exit_code=$rc;render_error=$(if($payload){$payload.render_error}else{$null});input_sha256=$input.sha256;output_sha256=$(if($ok){(Get-FileHash -Algorithm SHA256 -LiteralPath $output).Hash.ToLowerInvariant()}else{$null});output_file=$(if($ok){[IO.Path]::GetFileName($output)}else{$null});stderr_file=[IO.Path]::GetFileName($stderr)}
}
$report=@{schema_version=1;request_id=$manifest.request_id;status=$(if(($rows|Where-Object status -ne "ok").Count){"failed"}else{"complete"});worker=@{path=$Worker;sha256=$workerHash};aex_sha256=$aexHashes;cases=$rows}
$reportPath=Join-Path $OutputRoot "GENERIC_BETA_WINDOWS_ORACLE_RETURN.json";$report|ConvertTo-Json -Depth 20|Set-Content -Encoding UTF8 $reportPath
Write-Host $reportPath
if($report.status -ne "complete"){exit 2}
'''

PREFLIGHT = r'''param([string]$Worker="")
$ErrorActionPreference="Stop";$root=Split-Path -Parent $MyInvocation.MyCommand.Path;$m=Get-Content (Join-Path $root "campaign-manifest.json") -Raw|ConvertFrom-Json
foreach($p in $m.plugins){$f=Join-Path $root $p.aex_file;$h=(Get-FileHash -Algorithm SHA256 $f).Hash.ToLowerInvariant();if($h-ne$p.aex_sha256){throw "AEX hash mismatch: $($p.id)"}}
if($Worker){if(-not[IO.Path]::IsPathFullyQualified($Worker)){throw "Worker must be absolute"};if(-not(Test-Path $Worker)){throw "Worker missing"};Write-Host "WORKER_EXPLICIT $Worker $((Get-FileHash -Algorithm SHA256 $Worker).Hash.ToLowerInvariant())"}
else{Write-Host "WORKER_REQUIRED: pass -Worker with an absolute path";Get-ChildItem C:\Users\optim -Filter aex-guest-worker.exe -File -Recurse -ErrorAction SilentlyContinue|Select-Object -First 20 FullName,@{N='SHA256';E={(Get-FileHash -Algorithm SHA256 $_.FullName).Hash.ToLowerInvariant()}}|Format-Table -AutoSize;exit 3}
Write-Host "PREFLIGHT_OK"
'''


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "aex").mkdir(parents=True)
    inputs = save_inputs(OUT / "inputs")
    plugins = []
    for name, source in AEX.items():
        target = OUT / "aex" / source.name
        shutil.copy2(source, target)
        plugins.append({"id": name, "aex_file": f"aex/{target.name}", "aex_sha256": sha(target)})
    sets = parameter_sets()
    cases = []
    for plugin, rows in sets.items():
        for input_row in inputs:
            for row in rows:
                cases.append({"id": f"{plugin}_{input_row['id']}_{row['id']}", "plugin": plugin, "input": input_row["id"], "parameter_set": row["id"], "arguments": row["arguments"]})
    manifest = {"schema_version": 1, "request_id": REQUEST_ID, "pixel_contract": "RGBA8 PNG input; tightly packed worker-owned output", "plugins": plugins, "inputs": inputs, "parameter_sets": sets, "cases": cases}
    (OUT / "campaign-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (OUT / "RUN_ORACLE.ps1").write_text(RUNNER, encoding="utf-8-sig", newline="\r\n")
    (OUT / "PREFLIGHT.ps1").write_text(PREFLIGHT, encoding="utf-8-sig", newline="\r\n")
    shutil.copy2(ROOT / "scripts/verify_generic_beta_windows_oracle_return.py", OUT / "VERIFY_RETURN.py")
    shutil.copy2(ROOT / "scripts/run_generic_beta_oracle_bundle.py", OUT / "RUN_ORACLE.py")
    report_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object",
        "required": ["schema_version", "request_id", "status", "worker", "aex_sha256", "cases"],
        "properties": {
            "schema_version": {"const": 1}, "request_id": {"const": REQUEST_ID},
            "status": {"enum": ["complete", "failed"]},
            "worker": {"type": "object", "required": ["path", "sha256"]},
            "aex_sha256": {"type": "object"},
            "cases": {"type": "array", "minItems": len(cases), "maxItems": len(cases)},
        },
    }
    output_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object",
        "required": ["id", "plugin", "input", "parameters", "status", "exit_code", "input_sha256", "output_sha256", "output_file"],
        "properties": {"status": {"const": "ok"}, "output_file": {"pattern": "^[A-Za-z0-9_.-]+\\.png$"}, "output_sha256": {"pattern": "^[0-9a-f]{64}$"}},
    }
    (OUT / "return-report.schema.json").write_text(json.dumps(report_schema, indent=2, sort_keys=True) + "\n")
    (OUT / "output-row.schema.json").write_text(json.dumps(output_schema, indent=2, sort_keys=True) + "\n")
    (OUT / "README.md").write_text("# Generic beta Windows oracle\n\nRun `PREFLIGHT.ps1 -Worker C:\\\\absolute\\\\aex-guest-worker.exe`, then `RUN_ORACLE.ps1 -Worker ...`. The worker is never selected automatically. `RUN_ORACLE.py --bundle . --worker <absolute-path>` provides the same explicit-worker contract for headless smoke runs. Copy the output directory back and run `python VERIFY_RETURN.py <output-dir>`.\n")
    files = sorted(path for path in OUT.rglob("*") if path.is_file())
    (OUT / "CHECKSUMS.sha256").write_text("".join(f"{sha(path)}  {path.relative_to(OUT).as_posix()}\n" for path in files))
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
