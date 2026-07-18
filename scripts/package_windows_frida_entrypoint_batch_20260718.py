#!/usr/bin/env python3
"""Build the deterministic six-lane Windows Frida entrypoint batch package."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.windows_witness.compiler import compile_witness
from tools.windows_witness.core import SpecError, deterministic_zip


SPECS_ROOT = ROOT / "refs" / "windows_witness_specs"
PROFILE_PATH = ROOT / "tools" / "windows_witness" / "frida_profiles" / "olm_entrypoints_20260718.json"
DEFAULT_OUTPUT = ROOT / "refs" / "runtime_trace_packages" / "windows_frida_entrypoint_batch_20260718"
DEFAULT_ZIP = DEFAULT_OUTPUT.with_suffix(".zip")

# These are deliberately one representative request per lane.  The batch is an
# entrypoint/dispatch survey, not a replacement for the narrower pixel-witness
# requests already queued in the repository.
LANES: tuple[tuple[str, str], ...] = (
    ("OLMBlur", "olmblur_case0006_same_run_20260713"),
    ("OLMDirectionalBlur", "olmdirectionalblur_writer_entry_20260716"),
    ("OLMDistanceGradation", "olmdistancegradation_case0026_16bpc_livefield_20260713"),
    ("OLMKiraKira", "olmkirakira_mode3_live_gaussian_20260713"),
    ("OLMRadialBlur", "olmradialblur_case0009_fullframe_postnorm_typed_common_core_20260713"),
    ("OLMSmoother2AE", "olmsmoother2_case0004_writer_frame_20260718"),
)

IDENTITY_FIELDS = [
    "run_id",
    "ae_pid",
    "module_base",
    "aex_sha256",
    "project_bpc",
    "renderer",
    "case_id",
]


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _profile_by_name(profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    plugins = profile.get("plugins")
    if not isinstance(plugins, list):
        raise SpecError("Frida profile plugins must be an array")
    result: dict[str, dict[str, Any]] = {}
    for item in plugins:
        if not isinstance(item, dict) or not isinstance(item.get("plugin"), str):
            raise SpecError("Frida profile contains an invalid plugin entry")
        result[item["plugin"]] = item
    return result


def _rva_int(value: Any, where: str) -> int:
    if not isinstance(value, str) or not value.lower().startswith("0x"):
        raise SpecError(f"{where} must be a hexadecimal RVA")
    try:
        return int(value, 16)
    except ValueError as exc:
        raise SpecError(f"{where} is not a hexadecimal RVA") from exc


def _hook_name_for_rva(profile: dict[str, Any], rva: int) -> str:
    for item in profile.get("render_or_core", []):
        if not isinstance(item, dict):
            continue
        if _rva_int(item.get("rva"), "render_or_core.rva") == rva:
            name = item.get("name")
            if isinstance(name, str) and name:
                return name
    return f"rva_{rva:x}"


def _entry_config(profile: dict[str, Any]) -> tuple[dict[str, Any], int]:
    exports = profile.get("exports")
    if not isinstance(exports, list) or len(exports) != 1 or not isinstance(exports[0], dict):
        raise SpecError(f"{profile.get('plugin')}: expected exactly one profile export")
    exported = exports[0]
    export_name = exported.get("name")
    export_rva = _rva_int(exported.get("rva"), "profile.exports.rva")
    if not isinstance(export_name, str) or not export_name:
        raise SpecError(f"{profile.get('plugin')}: profile export name is missing")
    entry = {
        # The PF entrypoint receives setup/params/render commands, so one hit is
        # not sufficient.  The runner caps the bounded survey at 64 calls.
        "export": export_name,
        "name": export_name,
        "required": True,
        "hit_limit": 64,
        "argument_count": 5,
        "reads": [
            {"name": "pf_cmd", "source": "arg(0)", "type": "i32", "direct": True},
        ],
    }
    return entry, export_rva


def _frida_agent_config(profile: dict[str, Any], module_filename: str) -> dict[str, Any]:
    entry, entry_rva = _entry_config(profile)
    initial = profile.get("initial_frida_hooks")
    if not isinstance(initial, list) or not initial:
        raise SpecError(f"{profile.get('plugin')}: initial_frida_hooks is empty")
    internal: list[dict[str, Any]] = []
    seen: set[int] = {entry_rva}
    for index, raw_rva in enumerate(initial):
        rva = _rva_int(raw_rva, f"initial_frida_hooks[{index}]")
        if rva in seen:
            continue
        seen.add(rva)
        internal.append({
            "name": _hook_name_for_rva(profile, rva),
            "rva": rva,
            "hit_limit": 1,
            # The agent keeps these hooks bounded; cardinality 0..1 below
            # records that a path may legitimately not reach a deeper stage.
            "optional": True,
        })
    return {
        "module_name": module_filename,
        "exports": [entry],
        "internal_rvas": internal,
        "poll_interval_ms": 100,
    }


def _generic_events(agent_config: dict[str, Any], entry_rva: int) -> list[dict[str, Any]]:
    common = list(IDENTITY_FIELDS)
    events: list[dict[str, Any]] = [{
        "name": "module_loaded",
        "prefix": "FRIDA_MODULE_LOADED",
        "cardinality": {"scope": "global", "min": 1, "max": 1},
        "required_fields": common,
    }]
    entry = agent_config["exports"][0]
    events.append({
        "name": entry["name"],
        "prefix": "FRIDA_PF_ENTRY",
        "cardinality": {"scope": "per_case", "min": 1, "max": 64},
        "required_fields": common + ["hook", "rva", "reads", "pf_cmd_type", "pf_cmd_value"],
        "field_constraints": {
            "hook": {"equals": entry["name"]},
            "rva": {"equals": entry_rva},
            "pf_cmd_type": {"equals": "i32"},
            "pf_cmd_value": {"pattern": "^-?[0-9]+$"},
        },
    })
    for hook in agent_config["internal_rvas"]:
        events.append({
            "name": hook["name"],
            "prefix": "FRIDA_HOOK_" + hook["name"].upper().replace("-", "_").replace(".", "_"),
            "cardinality": {"scope": "per_case", "min": 0, "max": 1},
            "required_fields": common + ["hook", "rva"],
            "field_constraints": {"hook": {"equals": hook["name"]}, "rva": {"equals": int(hook["rva"])}},
        })
    return events


def _temporary_frida_spec(source: Path, profile: dict[str, Any], destination: Path, lane: str) -> Path:
    original = json.loads((source / "witness-spec.json").read_text(encoding="utf-8"))
    spec = deepcopy(original)
    spec["request_id"] = f"olm_frida_entrypoint_{lane.lower()}_20260718"
    spec["run_id_prefix"] = f"olm-frida-entry-{lane.lower()}"
    spec.pop("cdb", None)
    for case in spec["cases"]:
        case.pop("cdb_template", None)
        case.pop("addresses", None)
    agent_config = _frida_agent_config(profile, spec["plugin"]["module_filename"])
    if spec["plugin"]["aex_sha256"] != profile["aex_sha256"]:
        raise SpecError(f"{lane}: representative spec AEX SHA-256 does not match the entrypoint profile")
    entry_rva = _rva_int(profile["exports"][0]["rva"], "profile.exports.rva")
    spec["transport"] = {
        "kind": "frida",
        "agent_config": agent_config,
        "arm_timeout_seconds": 45,
        "capture_timeout_seconds": 180,
    }
    spec["validation"] = {
        "identity_fields": IDENTITY_FIELDS,
        "events": _generic_events(agent_config, entry_rva),
    }
    spec["return_bundle"] = {
        "json_name": f"RETURN_{lane.upper()}_FRIDA_ENTRYPOINT.json",
        "zip_name": f"RETURN_{lane.upper()}_FRIDA_ENTRYPOINT.zip",
        "include_logs": [],
    }

    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "renderer.jsx", destination / "renderer.jsx")
    shutil.copytree(source / "request", destination / "request")
    manifest_path = destination / "request" / "request_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    manifest["request_id"] = spec["request_id"]
    manifest_path.write_bytes(_json_bytes(manifest))
    spec_path = destination / "witness-spec.json"
    spec_path.write_bytes(_json_bytes(spec))
    return spec_path


OUTER_ZIP_HELPER = r'''import sys, zipfile
from pathlib import Path

FIXED = (2026, 1, 1, 0, 0, 0)
root = Path(sys.argv[1]).resolve()
archive = Path(sys.argv[2]).resolve()
files = sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix())
archive.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as out:
    for path in files:
        info = zipfile.ZipInfo(path.relative_to(root).as_posix(), FIXED)
        info.create_system = 3
        info.external_attr = 0o100644 << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        out.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
'''


OUTER_PS1 = r'''param(
  [string]$OutputDir = (Join-Path $PSScriptRoot 'returns'),
  [string]$ReturnZip = (Join-Path $PSScriptRoot 'RETURN_OLM_FRIDA_ENTRYPOINT_BATCH_20260718.zip'),
  [string]$AexRoot = '',
  [string]$AfterFxPath = ''
)
$ErrorActionPreference = 'Stop'
$root = (Get-Item -LiteralPath $PSScriptRoot).FullName
$manifestPath = Join-Path $root 'batch-manifest.json'
if (!(Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw 'batch-manifest.json is missing' }
$manifestSha256 = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.kind -ne 'olm_frida_entrypoint_batch_request' -or @($manifest.jobs).Count -ne 6) { throw 'batch manifest is invalid' }
& py -3 -c "import frida" 2>$null
if ($LASTEXITCODE -ne 0) { throw 'Python Frida API is unavailable: install frida in the Windows Python used by py -3' }
$packages = @(Get-ChildItem -LiteralPath (Join-Path $root 'packages') -Filter '*.zip' | Sort-Object Name)
if ($packages.Count -ne @($manifest.jobs).Count) { throw 'inner package set does not match the batch manifest' }
$output = New-Item -ItemType Directory -Force -Path $OutputDir
$output = (Get-Item -LiteralPath $output.FullName).FullName
Copy-Item -LiteralPath $manifestPath -Destination (Join-Path $output 'batch-manifest.json') -Force
$runs = Join-Path $output 'runs'
if (Test-Path -LiteralPath $runs) { Remove-Item -LiteralPath $runs -Recurse -Force }
New-Item -ItemType Directory -Force -Path $runs | Out-Null
$rows = @()
foreach ($package in $packages) {
  $name = [IO.Path]::GetFileNameWithoutExtension($package.Name)
  $run = Join-Path $runs $name
  New-Item -ItemType Directory -Force -Path $run | Out-Null
  Expand-Archive -LiteralPath $package.FullName -DestinationPath $run -Force
  $args = @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $run 'artifacts/run_witness.ps1'),'-WorkRoot',(Join-Path $run 'work'))
  if ($AexRoot) {
    $contract = Get-Content -LiteralPath (Join-Path $run 'witness-contract.json') -Raw | ConvertFrom-Json
    $candidate = Join-Path $AexRoot ([string]$contract.plugin.module_filename)
    if (Test-Path -LiteralPath $candidate) { $args += @('-AexPath',$candidate) }
  }
  if ($AfterFxPath) { $args += @('-AfterFxPath',$AfterFxPath) }
  $started = Get-Date
  $packageSha256 = (Get-FileHash -LiteralPath $package.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  $manifestJobs = @($manifest.jobs | Where-Object { [string]$_.package -ceq $package.Name })
  if ($manifestJobs.Count -ne 1 -or [string]$manifestJobs[0].package_sha256 -cne $packageSha256) { throw "inner package identity mismatch: $($package.Name)" }
  & powershell.exe @args *> (Join-Path $run 'batch_inner_stdout_stderr.txt')
  $code = $LASTEXITCODE
  $rows += [ordered]@{ package=$package.Name; package_sha256=$packageSha256; status=$(if ($code -eq 0) {'answered'} else {'failed'}); exit_code=$code; started_utc=$started.ToUniversalTime().ToString('o'); run_dir=$name }
}
$status = [ordered]@{ schema_version=1; kind='olm_frida_entrypoint_batch_return'; request_manifest_sha256=$manifestSha256; status=$(if (@($rows | Where-Object {$_.status -ne 'answered'}).Count -eq 0) {'answered'} else {'partial'}); packages=$rows }
$status | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $output 'batch_status.json') -Encoding UTF8
$helper = Join-Path $root 'scripts/deterministic_zip.py'
& py -3 $helper $output $ReturnZip
if ($LASTEXITCODE -ne 0) { throw 'deterministic return ZIP creation failed' }
if ($status.status -ne 'answered') { exit 2 }
'''


OUTER_CMD = r'''@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_FRIDA_ENTRYPOINT_BATCH.ps1" %*
exit /b %ERRORLEVEL%
'''


def _build_outer(output_dir: Path, archives: list[tuple[str, Path]]) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    (output_dir / "packages").mkdir(parents=True)
    (output_dir / "scripts").mkdir()
    jobs: list[dict[str, Any]] = []
    for lane, archive in archives:
        filename = f"{lane.lower()}_frida_entrypoint_20260718.zip"
        target = output_dir / "packages" / filename
        shutil.copy2(archive, target)
        with zipfile.ZipFile(target) as package:
            contract = json.loads(package.read("witness-contract.json"))
        jobs.append({
            "lane": lane,
            "package": filename,
            "package_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "request_id": contract["request_id"],
        })
    (output_dir / "batch-manifest.json").write_bytes(_json_bytes({
        "schema_version": 1,
        "kind": "olm_frida_entrypoint_batch_request",
        "jobs": jobs,
    }))
    (output_dir / "RUN_FRIDA_ENTRYPOINT_BATCH.ps1").write_text(OUTER_PS1, encoding="utf-8", newline="\n")
    (output_dir / "RUN_FRIDA_ENTRYPOINT_BATCH.cmd").write_text(OUTER_CMD, encoding="ascii", newline="\r\n")
    (output_dir / "scripts" / "deterministic_zip.py").write_text(OUTER_ZIP_HELPER, encoding="ascii", newline="\n")
    readme = """# OLM Frida Entrypoint Batch 20260718

This outer package runs six hash-pinned Windows AE Software witness packages
serially. It requires desktop After Effects, Python 3, and `frida` installed
for `py -3`. A failed lane is retained under `returns/runs/`; the outer return
ZIP is created even when one or more lanes fail.

Run `RUN_FRIDA_ENTRYPOINT_BATCH.cmd` from an interactive Windows desktop.
The entrypoint hook records up to 64 PF command calls and a direct `i32`
`pf_cmd` read. Deeper hooks are bounded to one hit and are optional.
"""
    (output_dir / "README.md").write_text(readme, encoding="ascii", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--zip", dest="zip_path", type=Path, default=DEFAULT_ZIP)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    profiles = _profile_by_name(profile)
    with tempfile.TemporaryDirectory(prefix="olm_frida_entrypoint_batch_") as temp_name:
        temp = Path(temp_name)
        archives: list[tuple[str, Path]] = []
        for lane, spec_dir_name in LANES:
            source = SPECS_ROOT / spec_dir_name
            if lane not in profiles:
                raise SpecError(f"missing Frida profile for {lane}")
            if not (source / "witness-spec.json").is_file():
                raise SpecError(f"missing representative witness spec: {source}")
            spec_dir = temp / "specs" / lane
            spec_path = _temporary_frida_spec(source, profiles[lane], spec_dir, lane)
            package_dir = temp / "inner" / lane
            package_zip = temp / "inner" / f"{lane}.zip"
            compile_witness(spec_path, package_dir, package_zip)
            archives.append((lane, package_zip))
        _build_outer(args.output_dir, archives)
    deterministic_zip(args.output_dir, args.zip_path)
    print(json.dumps({"status": "ok", "output_dir": str(args.output_dir), "zip": str(args.zip_path), "lanes": [lane for lane, _ in LANES]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
