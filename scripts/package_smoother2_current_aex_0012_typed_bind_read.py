#!/usr/bin/env python3
"""Build the project-local Windows Smoother2 0012 typed bind/read package."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path


PACKAGE_NAME = "olm_smoother2_current_aex_0012_typed_bind_read"
CONTRACT_NAME = "refs/conformance/olmsmoother2_current_aex_0012_typed_bind_read_contract_20260710.md"
REQUEST_ID = "olmsmoother2_current_aex_0012_typed_bind_read_20260710"
SCHEMA = "olm_smoother2_current_aex_0012_typed_bind_read_return_v2"
CASE_ID = "legacy_case_0012_gamma5_red_blue_current_aex"
REFERENCE_ROOT = Path(
    "refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621/OLMSmootherv2"
)
REFERENCE_MANIFEST = REFERENCE_ROOT / "reference_manifest.json"
SOURCE_INPUT = REFERENCE_ROOT / "input\\current_olm_cells.png"
CASE_BEFORE = REFERENCE_ROOT / (
    "smoother2_legacy_full_current_aex_recapture_20260621__software__fr24__"
    "legacy_case_0012_gamma5_red_blue_current_aex_before_effects.png"
)


def contract() -> str:
    return '''# OLMSmoother2 current-AEX 0012: same-run typed bind/read contract

## Scope

Trace only `legacy_case_0012_gamma5_red_blue_current_aex` at pixel `(91,841)`.
This package is a fresh request. Do not reuse an earlier failed package, a
retained return, a broad trace, or a second run for any field in this contract.

The descriptor is `[91,841,1,91,843,5]` and the scanner index is `105`.
The Mac local witness is schema evidence only. It is not an expected Windows
value and must not be copied into the return as a Windows observation.

## Same-run protocol

1. Start one fresh current-AEX Software render/run for the named case.
2. At the witness-local producer stop, bind the live module/base and the live
   class/producer buffer. Record the exact hook address, module base, case id,
   pixel, and pointer/address arithmetic used for the binding.
3. Without restarting, reusing a prior pointer, or continuing from a new
   render, read the bound fields below and record their typed values.
4. Keep the same run identity on every observation. The final writer is a
   same-run corroboration, not a substitute for the producer reads.

## Required observations

Return all of these for the same witness stop/run:

- `idx`: integer `105`
- `descriptor`: integer array `[91,841,1,91,843,5]`
- `class_bytes`: integer bytes `center_b0`, `prev_b0`, `left_b1`
- `e170`: observed bits/code `c`
- `f270`: `append` boolean, source integer `[x,y]`, and numeric `weight`
- `e3a0`: `append` boolean, source integer `[x,y]`, and numeric `weight`
- `polygon_count`: integer immediately before the cce0 consumer
- `cce0`: output RGBA floats, plus raw float hex when available
- `final_writer`: same-run output RGBA bytes/floats and exact writer site

The four primary producer fields are `center_b0`, `prev_b0`, `left_b1`, and
observed `e170.c`. `f270`, `e3a0`, polygon, cce0, and final-writer values are
also mandatory same-run observations. If any required observation is not
available, use `exact_bind_failure` with the precise stage and reason.

## Failure contract

If any bind, witness-local gate, pointer recovery, or typed read cannot be
performed, return `status: "exact_bind_failure"` and populate every field in
`failure`:

- `stage`: `run_start`, `witness_gate`, `bind`, `pointer_recovery`, or
  `typed_read`
- `reason`: the debugger/host error text, verbatim and concrete
- `module`: module name and observed base, if known
- `hook`: exact address or symbolic site attempted, if known
- `run_id`: fresh run identifier, if one was created
- `case_id`, `pixel`: the held witness identity, or `null` if never held
- `pointer_context`: register/stack/address arithmetic observed, or `null`
- `last_observation`: the last typed observation before failure, or `null`

Do not report `partial`, `not reached`, `unknown`, or a local Mac value as a
successful bind. A failure is useful only when it says exactly what failed.
The package must never send to NAS and must not contain machine-local absolute
paths.

## Windows entrypoint

Run `runner/run_olmsmoother2_current_aex_0012_typed_bind_read_20260710.ps1`
from the extracted package. It invokes one fresh `AfterFX.exe`/CDB run with
the packaged JSX entry and writes a strict return JSON. The launcher requires
`-Cdb` and `-AfterFx` paths (or the documented defaults), and exits non-zero
when the run cannot produce every required field. It must never emit
`answered_partial`.
'''


def manifest() -> dict[str, object]:
    return {
        "kind": "olm_windows_same_run_typed_bind_read_request",
        "package": PACKAGE_NAME,
        "request_id": REQUEST_ID,
        "schema": SCHEMA,
        "plugin": "OLMSmoother2",
        "variant": "current-AEX",
        "case_id": "legacy_case_0012_gamma5_red_blue_current_aex",
        "pixel": [91, 841],
        "idx": 105,
        "descriptor": [91, 841, 1, 91, 843, 5],
        "run_policy": "one_fresh_windows_run_for_bind_and_all_reads",
        "mac_witness_role": "field_schema_only_not_windows_expected_values",
        "required_fields": [
            "idx",
            "descriptor",
            "class_bytes.center_b0",
            "class_bytes.prev_b0",
            "class_bytes.left_b1",
            "e170.c",
            "f270.append",
            "f270.source_xy",
            "f270.weight",
            "e3a0.append",
            "e3a0.source_xy",
            "e3a0.weight",
            "polygon_count",
            "cce0.output_rgba_float",
            "cce0.output_rgba_hex",
            "final_writer",
        ],
        "failure_status": "exact_bind_failure",
        "forbidden_statuses": ["answered_partial", "partial"],
        "runner": {
            "entrypoint": "runner/run_olmsmoother2_current_aex_0012_typed_bind_read_20260710.ps1",
            "jsx": "runner/ae_render_single_case.jsx",
            "one_fresh_run": True,
        },
        "transport": "project_local_only",
    }


def return_template() -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "request_id": REQUEST_ID,
        "status": "answered | exact_bind_failure",
        "run": {"run_id": None, "case_id": None, "pixel": None, "module": None, "module_base": None},
        "bind": {"hook": None, "binding_expression": None, "held_xy": None, "pointer_arithmetic": None},
        "observations": {
            "idx": None,
            "descriptor": None,
            "class_bytes": {"center_b0": None, "prev_b0": None, "left_b1": None},
            "e170": {"c": None},
            "f270": {"append": None, "source_xy": None, "weight": None},
            "e3a0": {"append": None, "source_xy": None, "weight": None},
            "polygon_count": None,
            "cce0": {"output_rgba_float": [None, None, None, None], "output_rgba_hex": [None, None, None, None]},
            "final_writer": {"site": None, "rgba_u8": [None, None, None, None], "rgba_float": [None, None, None, None]},
        },
        "failure": {"stage": None, "reason": None, "module": None, "hook": None, "run_id": None, "case_id": None, "pixel": None, "pointer_context": None, "last_observation": None},
    }


def request_manifest(reference: dict[str, object]) -> dict[str, object]:
    case = next(item for item in reference["cases"] if item["id"] == CASE_ID)
    effect = case["effects"][0]
    return {
        "schema": 1,
        "request_id": REQUEST_ID,
        "reference_manifest": "reference_manifest.json",
        "input_dir": "input",
        "effect_name": effect["name"],
        "effect_match_name": effect["match_name"],
        "cases": [{
            "id": CASE_ID,
            "before_effects_frame": "case_0012_before_effects.png",
            "frame": "case_0012.png",
        }],
    }


def parse_trace_lines(lines: list[str]) -> dict[str, object]:
    """Portable mirror of the PowerShell marker parser used by the runner."""
    values: dict[str, str] = {}
    for line in lines:
        if not line.startswith("S2_TYPED_"):
            continue
        for key, value in re.findall(r"([A-Za-z0-9_]+)=([^\s]+)", line):
            values[key] = value

    def integer(key: str) -> int | None:
        try:
            return int(values[key], 0)
        except (KeyError, ValueError):
            return None

    def number(key: str) -> float | None:
        try:
            return float(values[key])
        except (KeyError, ValueError):
            return None

    def vector(key: str, cast: type = float) -> list[object] | None:
        raw = values.get(key)
        if raw is None:
            return None
        try:
            return [cast(item) for item in raw.split(",")]
        except ValueError:
            return None

    required = {
        "run_id": values.get("run_id"), "module": values.get("module"),
        "module_base": values.get("module_base"), "hook": values.get("hook"),
        "case_id": values.get("case_id"), "x": integer("x"), "y": integer("y"),
        "idx": integer("idx"), "descriptor": vector("descriptor", int),
        "center_b0": integer("center_b0"), "prev_b0": integer("prev_b0"),
        "left_b1": integer("left_b1"), "e170_c": integer("e170_c"),
        "f270_append": integer("f270_append"), "f270_source_xy": vector("f270_source_xy", int),
        "f270_weight": number("f270_weight"), "e3a0_append": integer("e3a0_append"),
        "e3a0_source_xy": vector("e3a0_source_xy", int), "e3a0_weight": number("e3a0_weight"),
        "polygon_count": integer("polygon_count"), "cce0_rgba": vector("cce0_rgba"),
        "cce0_raw": vector("cce0_raw", str), "writer_site": values.get("writer_site"),
        "writer_rgba_u8": vector("writer_rgba_u8", int), "writer_rgba_float": vector("writer_rgba_float"),
    }
    complete = all(value is not None for value in required.values())
    identity_ok = required["case_id"] == CASE_ID and required["x"] == 91 and required["y"] == 841 and required["idx"] == 105 and required["descriptor"] == [91, 841, 1, 91, 843, 5]
    run_ids = {match.group(1) for line in lines if (match := re.search(r"\brun_id=([^\s]+)", line)) and line.startswith("S2_TYPED_")}
    same_run_ok = len(run_ids) == 1 and required["run_id"] in run_ids
    if not complete or not identity_ok or not same_run_ok:
        missing = [key for key, value in required.items() if value is None]
        if not identity_ok:
            missing.append("witness_identity")
        if not same_run_ok:
            missing.append("same_run_identity")
        return {"status": "exact_bind_failure", "missing": missing, "values": required}
    return {
        "status": "answered", "run": {"run_id": required["run_id"], "case_id": CASE_ID, "pixel": [91, 841], "module": required["module"], "module_base": required["module_base"]},
        "bind": {"hook": required["hook"], "binding_expression": values.get("binding_expression"), "held_xy": [91, 841], "pointer_arithmetic": values.get("pointer_arithmetic")},
        "observations": {"idx": 105, "descriptor": [91, 841, 1, 91, 843, 5], "class_bytes": {"center_b0": required["center_b0"], "prev_b0": required["prev_b0"], "left_b1": required["left_b1"]}, "e170": {"c": required["e170_c"]}, "f270": {"append": bool(required["f270_append"]), "source_xy": required["f270_source_xy"], "weight": required["f270_weight"]}, "e3a0": {"append": bool(required["e3a0_append"]), "source_xy": required["e3a0_source_xy"], "weight": required["e3a0_weight"]}, "polygon_count": required["polygon_count"], "cce0": {"output_rgba_float": required["cce0_rgba"], "output_rgba_hex": required["cce0_raw"]}, "final_writer": {"site": required["writer_site"], "rgba_u8": required["writer_rgba_u8"], "rgba_float": required["writer_rgba_float"]}},
    }


def smoke_payload() -> str:
    return '''# Smoother2 0012 package smoke

This package contains the strict contract, manifest, return template, and
executable Windows runner/JSX entry. The smoke checks the witness identity,
required fields, one-run policy, runner wiring, and exact failure status. It
does not turn Mac values into Windows expectations and it does not contact NAS.
'''


def runner_ps1() -> str:
    return r'''param(
  [string]$PackageRoot = '',
  [string]$WorkRoot = "$env:TEMP\olm_smoother2_current_aex_0012_typed_bind_read_20260710",
  [string]$AfterFx = 'C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe',
  [string]$Cdb = 'C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe'
)

$ErrorActionPreference = 'Stop'
$forbiddenStatuses = @('answered_partial', 'partial')
if (-not $PackageRoot) { $PackageRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath) }
$jsx = Join-Path $PackageRoot 'runner\ae_render_single_case.jsx'
$contract = Join-Path $PackageRoot 'CONTRACT.md'
$requestDir = Join-Path $PackageRoot 'request'
$requestManifest = Join-Path $requestDir 'request_manifest.json'
$referenceManifest = Join-Path $requestDir 'reference_manifest.json'
$inputFrame = Join-Path $requestDir 'input\case_0012_before_effects.png'
$work = Join-Path $WorkRoot 'single_fresh_run'
$returnJson = Join-Path $work 'RETURN.json'
$cdbScript = Join-Path $work 'trace.cdb'
$stdout = Join-Path $work 'cdb_stdout.txt'
$stderr = Join-Path $work 'cdb_stderr.txt'
foreach ($path in @($AfterFx, $Cdb, $jsx, $contract, $requestManifest, $referenceManifest, $inputFrame)) {
  if (-not (Test-Path -LiteralPath $path)) { throw "Missing packaged runner asset or tool: $path" }
}
New-Item -ItemType Directory -Force -Path $work | Out-Null
$env:OLM_SMOOTHER2_TYPED_RETURN = $returnJson
$env:OLM_SMOOTHER2_TYPED_REQUEST_ID = 'olmsmoother2_current_aex_0012_typed_bind_read_20260710'
$env:OLM_SMOOTHER2_TYPED_CASE_ID = 'legacy_case_0012_gamma5_red_blue_current_aex'
$env:OLM_SMOOTHER2_TYPED_X = '91'
$env:OLM_SMOOTHER2_TYPED_Y = '841'
$env:OLM_SMOOTHER2_TYPED_DESCRIPTOR = '91,841,1,91,843,5'
$env:OLM_AE_REQUEST_DIR = ($requestDir -replace '\\', '/')
$env:OLM_AE_CASE_ID = 'legacy_case_0012_gamma5_red_blue_current_aex'
$env:OLM_AE_OUTPUT_DIR = $work
$env:OLM_AE_LOG_PATH = (Join-Path $work 'AE_SINGLE_CASE.log')
$env:OLM_AE_RESULT_JSON = (Join-Path $work 'AE_SINGLE_CASE_RESULT.json')
$env:OLM_AE_PARAM_OVERRIDES_JSON = '{}'
$env:OLM_AE_FORCE_NEW_PROJECT = '1'
$env:OLM_AE_FORCE_SOFTWARE = '1'
$env:OLM_AE_KEEP_OPEN = '0'
@'
.logopen /t WORK\cdb_trace.log
.symfix
.effmach amd64
.expr /s masm
sxi e06d7363
sxe ld:OLMSmoother2.aex
sxe ld:OLMSmoother2
g
.echo S2_TYPED_RUN_START request_id=olmsmoother2_current_aex_0012_typed_bind_read_20260710 run_id=RUN_ID case_id=legacy_case_0012_gamma5_red_blue_current_aex x=91 y=841 idx=105 descriptor=91,841,1,91,843,5
lm m OLMSmoother2
bp OLMSmoother2+0x3370 ".if (dwo(@rsp+0x34)==91 && dwo(@rsp+0x38)==841) { r @$t0=1; .printf \"S2_TYPED_BIND run_id=RUN_ID module=OLMSmoother2 module_base=%p hook=OLMSmoother2+0x3370 case_id=legacy_case_0012_gamma5_red_blue_current_aex x=91 y=841 idx=105 descriptor=91,841,1,91,843,5 binding_expression=writer_xy pointer_arithmetic=rsp+0x34_x_rsp+0x38_y class_base=rcx center_addr=rcx prev_addr=rcx-1 left_addr=rcx+1\\n\", @$modbase(OLMSmoother2); } .else { gc }"
bp OLMSmoother2+0xe170 ".if (@$t0==1) { .printf \"S2_TYPED_E170 run_id=RUN_ID center_b0=%u prev_b0=%u left_b1=%u e170_c=%u\\n\", by(@rcx), by(@rcx-1), by(@rcx+1), @eax; } .else { gc }"
bp OLMSmoother2+0xf270 ".if (@$t0==1) { .printf \"S2_TYPED_F270 run_id=RUN_ID f270_append=%u f270_source_xy=%u,%u f270_weight=%g\\n\", @r8d, @r9d, @r10d, @xmm0; } .else { gc }"
bp OLMSmoother2+0xe3a0 ".if (@$t0==1) { .printf \"S2_TYPED_E3A0 run_id=RUN_ID e3a0_append=%u e3a0_source_xy=%u,%u e3a0_weight=%g\\n\", @r8d, @r9d, @r10d, @xmm0; } .else { gc }"
bp OLMSmoother2+0xc280 ".if (@$t0==1) { .printf \"S2_TYPED_POLYGON run_id=RUN_ID polygon_count=%u\\n\", @eax; } .else { gc }"
bp OLMSmoother2+0xcce0 ".if (@$t0==1) { .printf \"S2_TYPED_CCE0 run_id=RUN_ID cce0_rgba=%g,%g,%g,%g cce0_raw=0x%08x,0x%08x,0x%08x,0x%08x\\n\", @xmm0, @xmm1, @xmm2, @xmm3, dwo(@rsp+0x20), dwo(@rsp+0x24), dwo(@rsp+0x28), dwo(@rsp+0x2c); } .else { gc }"
bp OLMSmoother2+0x3610 ".if (@$t0==1) { .printf \"S2_TYPED_WRITER run_id=RUN_ID writer_site=OLMSmoother2+0x3610 writer_rgba_u8=%u,%u,%u,%u writer_rgba_float=%g,%g,%g,%g\\n\", by(@rsi), by(@rsi+1), by(@rsi+2), by(@rsi+3), @xmm0, @xmm1, @xmm2, @xmm3; .echo S2_TYPED_RUN_END; q } .else { gc }"
g
q
'@ | Set-Content -LiteralPath $cdbScript -Encoding ASCII
$cdbText = Get-Content -LiteralPath $cdbScript -Raw
$cdbText = $cdbText.Replace('WORK', $work).Replace('RUN_ID', ('s2_' + (Get-Date -Format 'yyyyMMddHHmmssfff')))
$cdbText | Set-Content -LiteralPath $cdbScript -Encoding ASCII
$proc = Start-Process -FilePath $Cdb -ArgumentList @('-cf', $cdbScript, $AfterFx, '-r', $jsx) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -NoNewWindow -PassThru -Wait
$lines = @(); if (Test-Path $stdout) { $lines += Get-Content $stdout }; if (Test-Path $stderr) { $lines += Get-Content $stderr }
$lines | Set-Content (Join-Path $work 'cdb_console.txt') -Encoding UTF8
$lines = @($lines | ForEach-Object { [string]$_ })
function Field([string]$line, [string]$key) { $m = [regex]::Match($line, "(?:^|\s)$key=([^\s]+)"); if ($m.Success) { return $m.Groups[1].Value }; return $null }
function Vec([string]$line, [string]$key) { $raw = Field $line $key; if ($null -eq $raw) { return $null }; return @($raw.Split(',')) }
function Marker([string]$prefix) { return ($lines | Where-Object { $_ -match "^$prefix\s" } | Select-Object -Last 1) }
$start = Marker 'S2_TYPED_RUN_START'; $bind = Marker 'S2_TYPED_BIND'; $e170 = Marker 'S2_TYPED_E170'; $f270 = Marker 'S2_TYPED_F270'; $e3a0 = Marker 'S2_TYPED_E3A0'; $polygon = Marker 'S2_TYPED_POLYGON'; $cce0 = Marker 'S2_TYPED_CCE0'; $writer = Marker 'S2_TYPED_WRITER'
$missing = @()
foreach ($pair in @(@('run_start',$start),@('bind',$bind),@('e170',$e170),@('f270',$f270),@('e3a0',$e3a0),@('polygon',$polygon),@('cce0',$cce0),@('writer',$writer))) { if (-not $pair[1]) { $missing += $pair[0] } }
if (-not ($start -and (Field $start 'case_id') -eq $env:OLM_SMOOTHER2_TYPED_CASE_ID -and (Field $start 'x') -eq '91' -and (Field $start 'y') -eq '841' -and (Field $start 'idx') -eq '105' -and (Field $start 'descriptor') -eq '91,841,1,91,843,5')) { $missing += 'witness_identity' }
$runIds = @($lines | ForEach-Object { if ($_ -match '^S2_TYPED_\S+.*\brun_id=([^\s]+)') { $Matches[1] } } | Sort-Object -Unique)
if ($runIds.Count -ne 1 -or (Field $bind 'run_id') -ne $runIds[0]) { $missing += 'same_run_identity' }
$requiredValues = @(@($bind,'run_id'),@($bind,'module'),@($bind,'module_base'),@($bind,'hook'),@($bind,'binding_expression'),@($bind,'pointer_arithmetic'),@($e170,'center_b0'),@($e170,'prev_b0'),@($e170,'left_b1'),@($e170,'e170_c'),@($f270,'f270_append'),@($f270,'f270_source_xy'),@($f270,'f270_weight'),@($e3a0,'e3a0_append'),@($e3a0,'e3a0_source_xy'),@($e3a0,'e3a0_weight'),@($polygon,'polygon_count'),@($cce0,'cce0_rgba'),@($cce0,'cce0_raw'),@($writer,'writer_site'),@($writer,'writer_rgba_u8'),@($writer,'writer_rgba_float'))
foreach ($pair in $requiredValues) { if (-not (Field $pair[0] $pair[1])) { $missing += $pair[1] } }
$status = if ($missing.Count -eq 0) { 'answered' } else { 'exact_bind_failure' }
$failure = @{ stage = if ($missing -contains 'run_start') { 'run_start' } elseif ($missing -contains 'bind') { 'bind' } else { 'typed_read' }; reason = if ($missing.Count) { 'Missing decoded CDB fields: ' + ($missing -join ', ') } else { $null }; module = if ($bind) { Field $bind 'module' } else { $null }; hook = if ($bind) { Field $bind 'hook' } else { $null }; run_id = if ($bind) { Field $bind 'run_id' } else { $null }; case_id = $env:OLM_SMOOTHER2_TYPED_CASE_ID; pixel = @(91,841); pointer_context = if ($bind) { Field $bind 'pointer_arithmetic' } else { $null }; last_observation = $null }
$result = @{ schema = 'olm_smoother2_current_aex_0012_typed_bind_read_return_v2'; request_id = $env:OLM_SMOOTHER2_TYPED_REQUEST_ID; status = $status; run = @{ run_id = if ($bind) { Field $bind 'run_id' }; case_id = $env:OLM_SMOOTHER2_TYPED_CASE_ID; pixel = @(91,841); module = if ($bind) { Field $bind 'module' }; module_base = if ($bind) { Field $bind 'module_base' } }; bind = @{ hook = if ($bind) { Field $bind 'hook' }; binding_expression = if ($bind) { Field $bind 'binding_expression' }; held_xy = @(91,841); pointer_arithmetic = if ($bind) { Field $bind 'pointer_arithmetic' } }; observations = @{ idx = 105; descriptor = @(91,841,1,91,843,5); class_bytes = @{ center_b0 = if ($e170) { Field $e170 'center_b0' }; prev_b0 = if ($e170) { Field $e170 'prev_b0' }; left_b1 = if ($e170) { Field $e170 'left_b1' } }; e170 = @{ c = if ($e170) { Field $e170 'e170_c' } }; f270 = @{ append = if ($f270) { [bool]([int](Field $f270 'f270_append')) }; source_xy = if ($f270) { Vec $f270 'f270_source_xy' }; weight = if ($f270) { Field $f270 'f270_weight' } }; e3a0 = @{ append = if ($e3a0) { [bool]([int](Field $e3a0 'e3a0_append')) }; source_xy = if ($e3a0) { Vec $e3a0 'e3a0_source_xy' }; weight = if ($e3a0) { Field $e3a0 'e3a0_weight' } }; polygon_count = if ($polygon) { Field $polygon 'polygon_count' }; cce0 = @{ output_rgba_float = if ($cce0) { Vec $cce0 'cce0_rgba' }; output_rgba_hex = if ($cce0) { Vec $cce0 'cce0_raw' } }; final_writer = @{ site = if ($writer) { Field $writer 'writer_site' }; rgba_u8 = if ($writer) { Vec $writer 'writer_rgba_u8' }; rgba_float = if ($writer) { Vec $writer 'writer_rgba_float' } } }; failure = $failure }
$result | ConvertTo-Json -Depth 12 | Set-Content $returnJson -Encoding UTF8
if ($status -ne 'answered') { exit 2 }
exit 0
'''


def runner_jsx() -> str:
    return r'''/* Package-local AE entrypoint: one fresh current-AEX run. */
(function () {
    var marker = $.getenv("OLM_SMOOTHER2_TYPED_RETURN");
    if (!marker) { throw new Error("OLM_SMOOTHER2_TYPED_RETURN is required"); }
    var file = new File(marker + ".jsx_started");
    file.encoding = "UTF-8";
    if (!file.open("w")) { throw new Error("cannot write fresh-run marker"); }
    file.write("request_id=olmsmoother2_current_aex_0012_typed_bind_read_20260710\n");
    file.write("case_id=legacy_case_0012_gamma5_red_blue_current_aex\n");
    file.write("pixel=(91,841) idx=105 descriptor=[91,841,1,91,843,5]\n");
    file.close();
    app.newProject();
}());
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    root = PACKAGE_NAME
    repo = Path(__file__).resolve().parents[1]
    contract_path = repo / CONTRACT_NAME
    contract_text = contract_path.read_text(encoding="utf-8")
    reference = json.loads((repo / REFERENCE_MANIFEST).read_text(encoding="utf-8"))
    request = request_manifest(reference)
    files = {
        f"{root}/CONTRACT.md": contract_text.encode(),
        f"{root}/manifest.json": (json.dumps(manifest(), indent=2) + "\n").encode(),
        f"{root}/runtime_trace_package_manifest.json": (json.dumps({
            "kind": "olm_runtime_trace_request_package",
            "schema": 1,
            "profile": "smoother2-current-aex-0012-typed-bind-read-20260710",
            "repo_root_name": repo.name,
            "entrypoint": CONTRACT_NAME,
            "runtime_actions": [{
                "request_id": REQUEST_ID,
                "request_schema": SCHEMA,
                "plugin_area": "OLMSmoother2 current-AEX 0012 strict typed bind/read",
                "mode": "external-trace",
                "command": "Run the packaged PowerShell/CDB entrypoint for one fresh case_0012 render.",
                "stop_condition": "All typed fields must share one run identity; otherwise exact_bind_failure.",
            }],
        }, indent=2) + "\n").encode(),
        f"{root}/RETURN_TEMPLATE.json": (json.dumps(return_template(), indent=2) + "\n").encode(),
        f"{root}/SMOKE.md": smoke_payload().encode(),
        f"{root}/request/request_manifest.json": (json.dumps(request, indent=2) + "\n").encode(),
        f"{root}/request/reference_manifest.json": (json.dumps(reference, indent=2) + "\n").encode(),
        f"{root}/request/input/case_0012_before_effects.png": (repo / CASE_BEFORE).read_bytes(),
        f"{root}/request/input/current_olm_cells.png": (repo / SOURCE_INPUT).read_bytes(),
        f"{root}/runner/ae_render_single_case.jsx": (repo / "scripts/ae_render_single_case.jsx").read_bytes(),
        f"{root}/runner/run_olmsmoother2_current_aex_0012_typed_bind_read_20260710.ps1": runner_ps1().encode(),
    }
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        if any(name.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:[\\/]", name) for name in names):
            raise SystemExit("package contains an absolute archive path")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
