#!/usr/bin/env python3
"""Materialize the OLMSmoother2 case0012 live config-binding request package."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Any


PACKAGE_STEM = "olmsmoother2_case0012_live_config_binding_20260713"
REQUEST_ID = "olmsmoother2_case0012_live_config_binding_20260713"
SCHEMA = "olmsmoother2_case0012_live_config_binding_return_v1"
CASE_ID = "legacy_case_0012_gamma5_red_blue_current_aex"
PACKAGE_ZIP = "olm_runtime_trace_olmsmoother2_case0012_live_config_binding_20260713.zip"
SUPPORT_DIR = Path("refs/runtime_trace_support") / PACKAGE_STEM
OUTPUT_ZIP = Path("refs/runtime_trace_packages") / PACKAGE_ZIP
CONTRACT_PATH = Path("refs/conformance/olmsmoother2_case0012_live_config_contract_20260712.md")
REFERENCE_ROOT = Path(
    "refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621/OLMSmootherv2"
)
REFERENCE_MANIFEST = REFERENCE_ROOT / "reference_manifest.json"
SOURCE_INPUT = REFERENCE_ROOT / "input\\current_olm_cells.png"
CASE_BEFORE = REFERENCE_ROOT / (
    "smoother2_legacy_full_current_aex_recapture_20260621__software__fr24__"
    "legacy_case_0012_gamma5_red_blue_current_aex_before_effects.png"
)
TARGET_PIXEL = [91, 841]
TARGET_DESCRIPTOR = [91, 841, 1, 91, 843, 5]
TARGET_IDX = 105


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def package_manifest() -> dict[str, Any]:
    return {
        "kind": "olm_windows_live_config_binding_request",
        "package": PACKAGE_STEM,
        "request_id": REQUEST_ID,
        "schema": SCHEMA,
        "plugin": "OLMSmoother2",
        "variant": "current-AEX",
        "case_id": CASE_ID,
        "pixel": TARGET_PIXEL,
        "idx": TARGET_IDX,
        "descriptor": TARGET_DESCRIPTOR,
        "run_policy": "one_fresh_windows_run_for_bind_and_all_reads",
        "contract": str(CONTRACT_PATH.as_posix()),
        "required_fields": [
            "run.run_id",
            "run.case_id",
            "run.pixel",
            "run.module",
            "run.module_base",
            "bind.writer_hook",
            "bind.c280_hook",
            "bind.cce0_hook",
            "bind.binding_expression",
            "bind.pointer_context",
            "observations.c280.config_pointer",
            "observations.c280.config_pointer_arithmetic",
            "observations.c280.config_raw_bytes",
            "observations.c280.scale_fixed",
            "observations.cce0.config_pointer",
            "observations.cce0.config_pointer_arithmetic",
            "observations.cce0.config_raw_bytes",
            "observations.cce0.mode_byte",
            "observations.cce0.mode_name",
            "observations.final_writer.site",
            "observations.final_writer.rgba_u8",
            "observations.final_writer.rgba_float",
        ],
        "failure_status": "exact_bind_failure",
        "forbidden_statuses": ["answered_partial", "partial", "unknown"],
        "transport": "project_local_only",
        "runner": {
            "entrypoint": f"{PACKAGE_STEM}/run_olmsmoother2_case0012_live_config_binding_20260713.ps1",
            "cdb_template": f"{PACKAGE_STEM}/case0012_live_config_binding.cdb.in",
            "jsx": f"{PACKAGE_STEM}/case/ae_render_single_case.jsx",
        },
        "local_replay_not_truth": {
            "c280_scale_fixed": [65536, 65536],
            "cce0_mode_byte": 0,
            "claim": "schema evidence only; never Windows expected values",
        },
    }


def runtime_trace_package_manifest(root: Path) -> dict[str, Any]:
    return {
        "kind": "olm_runtime_trace_request_package",
        "schema": 1,
        "profile": PACKAGE_STEM,
        "repo_root_name": root.name,
        "entrypoint": CONTRACT_PATH.as_posix(),
        "effect": "OLMSmoother2",
        "runtime_actions": [
            {
                "request_id": REQUEST_ID,
                "request_schema": SCHEMA,
                "plugin_area": "OLMSmoother2 case0012 live c280/cce0 config binding",
                "mode": "external-trace",
                "command": (
                    "Run one fresh current-AEX Software render for case0012 and "
                    "capture the live c280 scale words plus cce0 gamma-context "
                    "bytes/mode from the same witness-local call chain."
                ),
                "stop_condition": (
                    "Return c280/cce0 raw config bytes, decoded fields, and final "
                    "writer corroboration for one run id; otherwise exact_bind_failure."
                ),
                "forbidden": [
                    "broad ungated +0xc280/+0xcce0 reruns",
                    "local replay scaffold promoted as Windows truth",
                    "partial status without exact failure context",
                ],
            }
        ],
    }


def return_template() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "request_id": REQUEST_ID,
        "status": "answered | exact_bind_failure",
        "run": {
            "run_id": None,
            "case_id": CASE_ID,
            "pixel": TARGET_PIXEL,
            "module": None,
            "module_base": None,
        },
        "bind": {
            "writer_hook": None,
            "c280_hook": None,
            "cce0_hook": None,
            "binding_expression": None,
            "pointer_context": None,
        },
        "observations": {
            "idx": TARGET_IDX,
            "descriptor": TARGET_DESCRIPTOR,
            "c280": {
                "config_pointer": None,
                "config_pointer_arithmetic": None,
                "config_raw_bytes": [None] * 8,
                "scale_fixed": [None, None],
            },
            "cce0": {
                "config_pointer": None,
                "config_pointer_arithmetic": None,
                "config_raw_bytes": [None] * 7,
                "mode_byte": None,
                "mode_name": None,
            },
            "final_writer": {
                "site": None,
                "rgba_u8": [None, None, None, None],
                "rgba_float": [None, None, None, None],
            },
        },
        "failure": {
            "stage": None,
            "reason": None,
            "module": None,
            "hook": None,
            "run_id": None,
            "case_id": CASE_ID,
            "pixel": TARGET_PIXEL,
            "pointer_context": None,
            "last_observation": None,
            "missing": [],
        },
    }


def request_manifest(reference: dict[str, Any]) -> dict[str, Any]:
    case = next(item for item in reference["cases"] if item["id"] == CASE_ID)
    effect = case["effects"][0]
    return {
        "schema": 1,
        "request_id": REQUEST_ID,
        "reference_manifest": "reference_manifest.json",
        "input_dir": "input",
        "effect_name": effect["name"],
        "effect_match_name": effect["match_name"],
        "cases": [
            {
                "id": CASE_ID,
                "before_effects_frame": "case_0012_before_effects.png",
                "frame": "case_0012.png",
            }
        ],
    }


def readme() -> str:
    return """# OLMSmoother2 case0012 live config binding package

This package is scoped to one fresh Windows current-AEX Software run of
`legacy_case_0012_gamma5_red_blue_current_aex` at `(91,841)`.

The contract is the existing live-config binding contract:

- capture c280 config raw bytes and decoded `scale_fixed`
- capture cce0 gamma-context raw bytes and decoded `mode_byte` / `mode_name`
- keep every observation on one run id
- fail closed as `exact_bind_failure` if any bind/read is missing

The local replay defaults (`scale_fixed=[65536,65536]`, `mode_byte=0`) are
schema-only evidence and must not be copied into a Windows answer.
"""


def cdb_template() -> str:
    return r""".logopen /t WORKDIR\cdb_trace.log
.symfix
.effmach amd64
.expr /s masm
sxi e06d7363
.echo S2_CFG_RUN_START request_id=olmsmoother2_case0012_live_config_binding_20260713 run_id=RUN_ID case_id=legacy_case_0012_gamma5_red_blue_current_aex x=91 y=841 idx=105 descriptor=91,841,1,91,843,5
bu OLMSmoother2+0x3370 ".if (dwo(@rsp+0x34)==91 && dwo(@rsp+0x38)==841) { r @$t0=1; .printf \"S2_CFG_BIND run_id=RUN_ID module=OLMSmoother2 module_base=%p writer_hook=OLMSmoother2+0x3370 c280_hook=OLMSmoother2+0xc280 cce0_hook=OLMSmoother2+0xcce0 binding_expression=writer_xy_anchor_then_config_reads pointer_context=rsp+0x34_x_rsp+0x38_y\n\", @$modbase(OLMSmoother2); } .else { gc }"
bu OLMSmoother2+0xc280 ".if (@$t0==1) { .printf \"S2_CFG_C280 run_id=RUN_ID config_pointer=%p config_pointer_arithmetic=rax+0x20_scale_fixed_words config_raw_bytes=%02x,%02x,%02x,%02x,%02x,%02x,%02x,%02x scale_fixed=%u,%u\n\", @rax, by(@rax+0x20), by(@rax+0x21), by(@rax+0x22), by(@rax+0x23), by(@rax+0x24), by(@rax+0x25), by(@rax+0x26), by(@rax+0x27), dwo(@rax+0x20), dwo(@rax+0x24); } .else { gc }"
bu OLMSmoother2+0xcce0 ".if (@$t0==1) { r @$t1=poi(@rsp+0x28); .printf \"S2_CFG_CCE0 run_id=RUN_ID config_pointer=%p config_pointer_arithmetic=poi(rsp+0x28)_gamma_context config_raw_bytes=%02x,%02x,%02x,%02x,%02x,%02x,%02x mode_byte=%u\n\", @$t1, by(@$t1+0x00), by(@$t1+0x01), by(@$t1+0x02), by(@$t1+0x03), by(@$t1+0x04), by(@$t1+0x05), by(@$t1+0x06), by(@$t1+0x06); } .else { gc }"
bu OLMSmoother2+0x3610 ".if (@$t0==1) { .printf \"S2_CFG_WRITER run_id=RUN_ID writer_site=OLMSmoother2+0x3610 writer_rgba_u8=%u,%u,%u,%u writer_rgba_float=%g,%g,%g,%g\n\", by(@rsi), by(@rsi+1), by(@rsi+2), by(@rsi+3), @xmm0, @xmm1, @xmm2, @xmm3; .echo S2_CFG_RUN_END; q } .else { gc }"
g
q
"""


def runner_ps1() -> str:
    return r"""param(
  [string]$PackageRoot = '',
  [string]$WorkRoot = "$env:TEMP\olmsmoother2_case0012_live_config_binding_20260713",
  [string]$AfterFx = 'C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe',
  [string]$Cdb = 'C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe'
)

$ErrorActionPreference = 'Stop'
if (-not $PackageRoot) { $PackageRoot = Split-Path -Parent $PSCommandPath }
$caseRoot = Join-Path $PackageRoot 'case'
$jsx = Join-Path $caseRoot 'ae_render_single_case.jsx'
$requestDir = $caseRoot
$work = Join-Path $WorkRoot 'single_fresh_run'
$returnJson = Join-Path $work 'RETURN.json'
$stdout = Join-Path $work 'cdb_stdout.txt'
$stderr = Join-Path $work 'cdb_stderr.txt'
$cdbTemplate = Join-Path $PackageRoot 'case0012_live_config_binding.cdb.in'
$cdbScript = Join-Path $work 'case0012_live_config_binding.cdb'
$expectedAexSha256 = '7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7'
$expectedAexSize = 192000L
$aexPath = 'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\OLMSmoother2.aex'
foreach ($path in @($AfterFx, $Cdb, $jsx, $cdbTemplate, (Join-Path $requestDir 'request_manifest.json'), (Join-Path $requestDir 'reference_manifest.json'), (Join-Path $requestDir 'input\case_0012_before_effects.png'))) {
  if (-not (Test-Path -LiteralPath $path)) { throw "Missing packaged runner asset or tool: $path" }
}
if (-not (Test-Path -LiteralPath $aexPath -PathType Leaf)) { throw "Pinned AEX missing: $aexPath" }
$aex = Get-Item -LiteralPath $aexPath
$aexSha256 = (Get-FileHash -LiteralPath $aexPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($aex.Length -ne $expectedAexSize -or $aexSha256 -ne $expectedAexSha256) {
  throw "Pinned AEX identity mismatch: size=$($aex.Length) sha256=$aexSha256"
}
New-Item -ItemType Directory -Force -Path $work | Out-Null
$env:OLM_AE_REQUEST_DIR = ($requestDir -replace '\\', '/')
$env:OLM_AE_CASE_ID = 'legacy_case_0012_gamma5_red_blue_current_aex'
$env:OLM_AE_OUTPUT_DIR = $work
$env:OLM_AE_LOG_PATH = (Join-Path $work 'AE_SINGLE_CASE.log')
$env:OLM_AE_RESULT_JSON = (Join-Path $work 'AE_SINGLE_CASE_RESULT.json')
$env:OLM_AE_PARAM_OVERRIDES_JSON = '{}'
$env:OLM_AE_FORCE_NEW_PROJECT = '1'
$env:OLM_AE_FORCE_SOFTWARE = '1'
$env:OLM_AE_KEEP_OPEN = '0'
$runId = 's2cfg_' + (Get-Date -Format 'yyyyMMddHHmmssfff')
$template = Get-Content -LiteralPath $cdbTemplate -Raw
$template = $template.Replace('WORKDIR', $work).Replace('RUN_ID', $runId)
$template | Set-Content -LiteralPath $cdbScript -Encoding ASCII
$cdbArgs = '-cf "' + $cdbScript + '" "' + $AfterFx + '" -r "' + $jsx + '"'
$proc = Start-Process -FilePath $Cdb -ArgumentList $cdbArgs -RedirectStandardOutput $stdout -RedirectStandardError $stderr -NoNewWindow -PassThru -Wait
$lines = @()
if (Test-Path $stdout) { $lines += Get-Content $stdout }
if (Test-Path $stderr) { $lines += Get-Content $stderr }
$lines = @($lines | ForEach-Object { [string]$_ })
$lines | Set-Content (Join-Path $work 'cdb_console.txt') -Encoding UTF8

function Field([string]$line, [string]$key) {
  $m = [regex]::Match($line, "(?:^|\s)$key=([^\s]+)")
  if ($m.Success) { return $m.Groups[1].Value }
  return $null
}

function Vec([string]$line, [string]$key) {
  $raw = Field $line $key
  if ($null -eq $raw) { return $null }
  return @($raw.Split(','))
}

function Marker([string]$prefix) {
  return ($lines | Where-Object { $_ -match "^$prefix\s" } | Select-Object -Last 1)
}

function DecodeModeName($modeByte) {
  switch ($modeByte) {
    '0' { return 'no_gamma' }
    '1' { return 'gamma_all_channels' }
    '3' { return 'gamma_colors' }
    default { return "mode_$modeByte" }
  }
}

$start = Marker 'S2_CFG_RUN_START'
$bind = Marker 'S2_CFG_BIND'
$c280 = Marker 'S2_CFG_C280'
$cce0 = Marker 'S2_CFG_CCE0'
$writer = Marker 'S2_CFG_WRITER'
$missing = @()
foreach ($pair in @(@('run_start',$start), @('bind',$bind), @('c280',$c280), @('cce0',$cce0), @('writer',$writer))) {
  if (-not $pair[1]) { $missing += $pair[0] }
}
if (-not ($start -and (Field $start 'case_id') -eq 'legacy_case_0012_gamma5_red_blue_current_aex' -and (Field $start 'x') -eq '91' -and (Field $start 'y') -eq '841' -and (Field $start 'idx') -eq '105' -and (Field $start 'descriptor') -eq '91,841,1,91,843,5')) {
  $missing += 'witness_identity'
}
$runIds = @($lines | ForEach-Object { if ($_ -match '^S2_CFG_\S+.*\brun_id=([^\s]+)') { $Matches[1] } } | Sort-Object -Unique)
if ($runIds.Count -ne 1) { $missing += 'same_run_identity' }
$requiredValues = @(
  @($bind, 'module'),
  @($bind, 'module_base'),
  @($bind, 'writer_hook'),
  @($bind, 'c280_hook'),
  @($bind, 'cce0_hook'),
  @($bind, 'binding_expression'),
  @($bind, 'pointer_context'),
  @($c280, 'config_pointer'),
  @($c280, 'config_pointer_arithmetic'),
  @($c280, 'config_raw_bytes'),
  @($c280, 'scale_fixed'),
  @($cce0, 'config_pointer'),
  @($cce0, 'config_pointer_arithmetic'),
  @($cce0, 'config_raw_bytes'),
  @($cce0, 'mode_byte'),
  @($writer, 'writer_site'),
  @($writer, 'writer_rgba_u8'),
  @($writer, 'writer_rgba_float')
)
foreach ($pair in $requiredValues) {
  if (-not (Field $pair[0] $pair[1])) { $missing += $pair[1] }
}
$c280Bytes = if ($c280) { Vec $c280 'config_raw_bytes' } else { $null }
$cce0Bytes = if ($cce0) { Vec $cce0 'config_raw_bytes' } else { $null }
if ($c280Bytes -and $c280Bytes.Count -ne 8) { $missing += 'c280_raw_span' }
if ($cce0Bytes -and $cce0Bytes.Count -ne 7) { $missing += 'cce0_raw_span' }
$status = if ($missing.Count -eq 0) { 'answered' } else { 'exact_bind_failure' }
$modeByte = if ($cce0) { Field $cce0 'mode_byte' } else { $null }
$modeName = if ($modeByte) { DecodeModeName $modeByte } else { $null }
$result = @{
  schema = 'olmsmoother2_case0012_live_config_binding_return_v1'
  request_id = 'olmsmoother2_case0012_live_config_binding_20260713'
  status = $status
  run = @{
    run_id = if ($runIds.Count -ge 1) { $runIds[0] } else { $null }
    case_id = 'legacy_case_0012_gamma5_red_blue_current_aex'
    pixel = @(91, 841)
    module = if ($bind) { Field $bind 'module' } else { $null }
    module_base = if ($bind) { Field $bind 'module_base' } else { $null }
  }
  bind = @{
    writer_hook = if ($bind) { Field $bind 'writer_hook' } else { $null }
    c280_hook = if ($bind) { Field $bind 'c280_hook' } else { $null }
    cce0_hook = if ($bind) { Field $bind 'cce0_hook' } else { $null }
    binding_expression = if ($bind) { Field $bind 'binding_expression' } else { $null }
    pointer_context = if ($bind) { Field $bind 'pointer_context' } else { $null }
  }
  observations = @{
    idx = 105
    descriptor = @(91, 841, 1, 91, 843, 5)
    c280 = @{
      config_pointer = if ($c280) { Field $c280 'config_pointer' } else { $null }
      config_pointer_arithmetic = if ($c280) { Field $c280 'config_pointer_arithmetic' } else { $null }
      config_raw_bytes = $c280Bytes
      scale_fixed = if ($c280) { Vec $c280 'scale_fixed' } else { $null }
    }
    cce0 = @{
      config_pointer = if ($cce0) { Field $cce0 'config_pointer' } else { $null }
      config_pointer_arithmetic = if ($cce0) { Field $cce0 'config_pointer_arithmetic' } else { $null }
      config_raw_bytes = $cce0Bytes
      mode_byte = $modeByte
      mode_name = $modeName
    }
    final_writer = @{
      site = if ($writer) { Field $writer 'writer_site' } else { $null }
      rgba_u8 = if ($writer) { Vec $writer 'writer_rgba_u8' } else { $null }
      rgba_float = if ($writer) { Vec $writer 'writer_rgba_float' } else { $null }
    }
  }
  failure = @{
    stage = if ($missing -contains 'run_start') { 'run_start' } elseif ($missing -contains 'bind') { 'bind' } else { 'typed_read' }
    reason = if ($missing.Count) { 'Missing decoded config-binding fields: ' + ($missing -join ', ') } else { $null }
    module = if ($bind) { Field $bind 'module' } else { $null }
    hook = if ($bind) { Field $bind 'c280_hook' } else { $null }
    run_id = if ($runIds.Count -ge 1) { $runIds[0] } else { $null }
    case_id = 'legacy_case_0012_gamma5_red_blue_current_aex'
    pixel = @(91, 841)
    pointer_context = if ($bind) { Field $bind 'pointer_context' } else { $null }
    last_observation = if ($writer) { 'final_writer' } elseif ($cce0) { 'cce0' } elseif ($c280) { 'c280' } elseif ($bind) { 'bind' } else { $null }
    missing = $missing
  }
}
$result | ConvertTo-Json -Depth 12 | Set-Content $returnJson -Encoding UTF8
if ($status -ne 'answered') { exit 2 }
exit 0
"""


def parse_trace_lines(lines: list[str]) -> dict[str, Any]:
    values: dict[str, str] = {}
    for line in lines:
        if not line.startswith("S2_CFG_"):
            continue
        for key, value in re.findall(r"([A-Za-z0-9_]+)=([^\s]+)", line):
            values[key] = value

    def integer(key: str) -> int | None:
        raw = values.get(key)
        if raw is None:
            return None
        try:
            return int(raw, 0)
        except ValueError:
            return None

    def vector(key: str, cast: type = int) -> list[Any] | None:
        raw = values.get(key)
        if raw is None:
            return None
        try:
            return [cast(item) for item in raw.split(",")]
        except ValueError:
            return None

    def mode_name(mode: int | None) -> str | None:
        if mode is None:
            return None
        mapping = {0: "no_gamma", 1: "gamma_all_channels", 3: "gamma_colors"}
        return mapping.get(mode, f"mode_{mode}")

    required = {
        "run_id": values.get("run_id"),
        "module": values.get("module"),
        "module_base": values.get("module_base"),
        "writer_hook": values.get("writer_hook"),
        "c280_hook": values.get("c280_hook"),
        "cce0_hook": values.get("cce0_hook"),
        "binding_expression": values.get("binding_expression"),
        "pointer_context": values.get("pointer_context"),
        "case_id": values.get("case_id"),
        "x": integer("x"),
        "y": integer("y"),
        "idx": integer("idx"),
        "descriptor": vector("descriptor"),
        "c280_config_pointer": values.get("config_pointer") if "scale_fixed" in values else None,
        "c280_pointer_arithmetic": values.get("config_pointer_arithmetic") if "scale_fixed" in values else None,
        "c280_raw": vector("config_raw_bytes", str) if "scale_fixed" in values else None,
        "scale_fixed": vector("scale_fixed"),
        "mode_byte": integer("mode_byte"),
        "writer_site": values.get("writer_site"),
        "writer_rgba_u8": vector("writer_rgba_u8"),
        "writer_rgba_float": vector("writer_rgba_float", float),
    }

    c280_line = next((line for line in lines if line.startswith("S2_CFG_C280 ")), None)
    cce0_line = next((line for line in lines if line.startswith("S2_CFG_CCE0 ")), None)
    if c280_line:
        required["c280_config_pointer"] = re.search(r"\bconfig_pointer=([^\s]+)", c280_line).group(1) if re.search(r"\bconfig_pointer=([^\s]+)", c280_line) else None
        required["c280_pointer_arithmetic"] = re.search(r"\bconfig_pointer_arithmetic=([^\s]+)", c280_line).group(1) if re.search(r"\bconfig_pointer_arithmetic=([^\s]+)", c280_line) else None
        required["c280_raw"] = vector_from_line(c280_line, "config_raw_bytes", str)
    if cce0_line:
        required["cce0_config_pointer"] = re.search(r"\bconfig_pointer=([^\s]+)", cce0_line).group(1) if re.search(r"\bconfig_pointer=([^\s]+)", cce0_line) else None
        required["cce0_pointer_arithmetic"] = re.search(r"\bconfig_pointer_arithmetic=([^\s]+)", cce0_line).group(1) if re.search(r"\bconfig_pointer_arithmetic=([^\s]+)", cce0_line) else None
        required["cce0_raw"] = vector_from_line(cce0_line, "config_raw_bytes", str)

    missing = [key for key, value in required.items() if value is None]
    if required["case_id"] != CASE_ID or required["x"] != TARGET_PIXEL[0] or required["y"] != TARGET_PIXEL[1] or required["idx"] != TARGET_IDX or required["descriptor"] != TARGET_DESCRIPTOR:
        missing.append("witness_identity")
    run_ids = {
        match.group(1)
        for line in lines
        if line.startswith("S2_CFG_") and (match := re.search(r"\brun_id=([^\s]+)", line))
    }
    if len(run_ids) != 1 or required["run_id"] not in run_ids:
        missing.append("same_run_identity")
    if required.get("c280_raw") is not None and len(required["c280_raw"]) != 8:
        missing.append("c280_raw_span")
    if required.get("cce0_raw") is not None and len(required["cce0_raw"]) != 7:
        missing.append("cce0_raw_span")

    if missing:
        return {
            "schema": SCHEMA,
            "request_id": REQUEST_ID,
            "status": "exact_bind_failure",
            "failure": {
                "stage": "typed_read" if "run_start" not in missing and "bind" not in missing else ("bind" if "bind" in missing else "run_start"),
                "reason": "Missing decoded config-binding fields: " + ", ".join(missing),
                "module": required["module"],
                "hook": required["c280_hook"],
                "run_id": required["run_id"],
                "case_id": CASE_ID,
                "pixel": TARGET_PIXEL,
                "pointer_context": required["pointer_context"],
                "last_observation": "cce0" if cce0_line else ("c280" if c280_line else None),
                "missing": missing,
            },
        }

    return {
        "schema": SCHEMA,
        "request_id": REQUEST_ID,
        "status": "answered",
        "run": {
            "run_id": required["run_id"],
            "case_id": CASE_ID,
            "pixel": TARGET_PIXEL,
            "module": required["module"],
            "module_base": required["module_base"],
        },
        "bind": {
            "writer_hook": required["writer_hook"],
            "c280_hook": required["c280_hook"],
            "cce0_hook": required["cce0_hook"],
            "binding_expression": required["binding_expression"],
            "pointer_context": required["pointer_context"],
        },
        "observations": {
            "idx": TARGET_IDX,
            "descriptor": TARGET_DESCRIPTOR,
            "c280": {
                "config_pointer": required["c280_config_pointer"],
                "config_pointer_arithmetic": required["c280_pointer_arithmetic"],
                "config_raw_bytes": required["c280_raw"],
                "scale_fixed": required["scale_fixed"],
            },
            "cce0": {
                "config_pointer": required["cce0_config_pointer"],
                "config_pointer_arithmetic": required["cce0_pointer_arithmetic"],
                "config_raw_bytes": required["cce0_raw"],
                "mode_byte": required["mode_byte"],
                "mode_name": mode_name(required["mode_byte"]),
            },
            "final_writer": {
                "site": required["writer_site"],
                "rgba_u8": required["writer_rgba_u8"],
                "rgba_float": required["writer_rgba_float"],
            },
        },
    }


def vector_from_line(line: str, key: str, cast: type) -> list[Any] | None:
    match = re.search(rf"\b{re.escape(key)}=([^\s]+)", line)
    if not match:
        return None
    try:
        return [cast(item) for item in match.group(1).split(",")]
    except ValueError:
        return None


def materialize_support(root: Path, support_dir: Path, zip_path: Path) -> None:
    support_dir.mkdir(parents=True, exist_ok=True)
    case_dir = support_dir / "case" / "input"
    case_dir.mkdir(parents=True, exist_ok=True)
    reference = json.loads((root / REFERENCE_MANIFEST).read_text(encoding="utf-8"))
    request = request_manifest(reference)

    files: dict[Path, bytes] = {
        support_dir / "CONTRACT.md": (root / CONTRACT_PATH).read_bytes(),
        support_dir / "README.md": readme().encode("utf-8"),
        support_dir / "manifest.json": (json.dumps(package_manifest(), indent=2) + "\n").encode("utf-8"),
        support_dir / "runtime_trace_package_manifest.json": (json.dumps(runtime_trace_package_manifest(root), indent=2) + "\n").encode("utf-8"),
        support_dir / "RETURN_RUNTIME_TRACE_TEMPLATE.json": (json.dumps(return_template(), indent=2) + "\n").encode("utf-8"),
        support_dir / "case0012_live_config_binding.cdb.in": cdb_template().encode("utf-8"),
        support_dir / "run_olmsmoother2_case0012_live_config_binding_20260713.ps1": runner_ps1().encode("utf-8"),
        support_dir / "case" / "request_manifest.json": (json.dumps(request, indent=2) + "\n").encode("utf-8"),
        support_dir / "case" / "reference_manifest.json": (json.dumps(reference, indent=2) + "\n").encode("utf-8"),
        support_dir / "case" / "ae_render_single_case.jsx": (root / "scripts/ae_render_single_case.jsx").read_bytes(),
        support_dir / "case" / "input" / "case_0012_before_effects.png": (root / CASE_BEFORE).read_bytes(),
        support_dir / "case" / "input" / "current_olm_cells.png": (root / SOURCE_INPUT).read_bytes(),
    }
    for path, data in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(support_dir.rglob("*")):
            if path.is_dir():
                continue
            archive.write(path, f"{PACKAGE_STEM}/{path.relative_to(support_dir).as_posix()}")
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        if any(name.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:[\\/]", name) for name in names):
            raise SystemExit("package contains an absolute archive path")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--support-dir", type=Path, default=SUPPORT_DIR)
    parser.add_argument("--output", type=Path, default=OUTPUT_ZIP)
    args = parser.parse_args()
    root = repo_root()
    support_dir = root / args.support_dir
    output = root / args.output
    materialize_support(root, support_dir, output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
