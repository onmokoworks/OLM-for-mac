#!/usr/bin/env python3
"""Materialize the DG case0026 16bpc live field/source witness request package."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import struct
import zipfile
from pathlib import Path
from typing import Any


PACKAGE_STEM = "olmdistancegradation_case0026_16bpc_livefield_source_witness_20260713"
REQUEST_ID = PACKAGE_STEM
SCHEMA = "olmdistancegradation_case0026_16bpc_livefield_source_witness_return_v1"
SUPPORT_DIR = Path("refs/runtime_trace_support") / PACKAGE_STEM
OUTPUT_ZIP = Path("refs/runtime_trace_packages") / f"olm_runtime_trace_{PACKAGE_STEM}.zip"
CONTRACT_PATH = Path("refs/conformance/olmdistancegradation_case0026_16bpc_livefield_source_witness_contract_20260713.md")
REQUEST_ROOT = Path(
    "handoff/ae_pixel_validation_20260618/requests/"
    "ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625"
)
REQUEST_MANIFEST = REQUEST_ROOT / "request_manifest.json"
REFERENCE_MANIFEST = REQUEST_ROOT / "reference_manifest.json"
CASE_ID = "olmdistancegradation_extended__case_0026"
CASE_SHORT_ID = "case_0026"
CASE_BEFORE = (
    "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__"
    "olmdistancegradation_extended__case_0026_before_effects.png"
)
CASE_EXPECTED = (
    "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__"
    "olmdistancegradation_extended__case_0026.png"
)
AEX_PATH = "C:\\Program Files\\Adobe\\Common\\Plug-ins\\7.0\\MediaCore\\OLM\\DistanceGradation.aex"
AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
AEX_SIZE = 26289664
ROWBYTES = 15360
PIXEL_SIZE = 8
TARGET_POINTS = (
    (907, 222),
    (395, 477),
    (1589, 579),
    (898, 670),
)
CASE_TUPLE = {
    "in_out": 3,
    "inside_threshold": 158,
    "outside_threshold": 13,
    "use_background_color": 1,
    "invert": 1,
    "render_mode": 1,
    "interp_mode": 4,
    "power": 2.59740734100342,
    "gradation_rgba": [0.1098041459918, 0.0, 0.93333333730698, 1.0],
    "background_rgba": [1.0, 0.0, 0.0, 1.0],
}
CASE_TUPLE_BITS = {
    "power_bits": "0x40263bec",
    "grad_r_bits": "0x3de0e0ff",
    "grad_g_bits": "0x00000000",
    "grad_b_bits": "0x3f6eeeef",
    "bg_r_bits": "0x3f800000",
    "bg_g_bits": "0x00000000",
    "bg_b_bits": "0x00000000",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def float_bits(value: float) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


def package_manifest() -> dict[str, Any]:
    return {
        "kind": "olm_windows_livefield_source_witness_request",
        "package": PACKAGE_STEM,
        "request_id": REQUEST_ID,
        "schema": SCHEMA,
        "plugin": "OLMDistanceGradation",
        "variant": "current-AEX",
        "case_id": CASE_ID,
        "case_short_id": CASE_SHORT_ID,
        "target_points": [list(point) for point in TARGET_POINTS],
        "run_policy": "one_fresh_windows_run_for_all_four_points",
        "contract": CONTRACT_PATH.as_posix(),
        "aex_pin": {
            "path": AEX_PATH,
            "sha256": AEX_SHA256,
            "size": AEX_SIZE,
        },
        "ae_host_contract": {
            "renderer": "software",
            "bits_per_channel": 16,
        },
        "required_fields": [
            "run.run_id",
            "run.case_id",
            "run.renderer",
            "run.bits_per_channel",
            "run.current_aex.sha256",
            "points[].xy",
            "points[].case_tuple",
            "points[].source_addr",
            "points[].source_raw_words_agrb",
            "points[].field_addr",
            "points[].field_raw_words_agrb",
            "points[].field_word_at_rcx_plus_2",
            "points[].pre_output_words_agrb",
            "points[].post_output_words_agrb",
        ],
        "failure_status": "exact_bind_failure",
        "forbidden_statuses": ["answered_partial", "partial", "unknown"],
        "runner": {
            "entrypoint": f"{PACKAGE_STEM}/run_olmdistancegradation_case0026_16bpc_livefield_source_witness_20260713.ps1",
            "cdb_template": f"{PACKAGE_STEM}/case0026_livefield_source_witness.cdb.in",
            "jsx": f"{PACKAGE_STEM}/case/ae_render_single_case.jsx",
        },
        "case_tuple_expected": {
            **CASE_TUPLE,
            **CASE_TUPLE_BITS,
        },
    }


def runtime_trace_package_manifest(root: Path) -> dict[str, Any]:
    return {
        "kind": "olm_runtime_trace_request_package",
        "schema": 1,
        "profile": PACKAGE_STEM,
        "repo_root_name": root.name,
        "entrypoint": CONTRACT_PATH.as_posix(),
        "effect": "OLMDistanceGradation",
        "runtime_actions": [
            {
                "request_id": REQUEST_ID,
                "request_schema": SCHEMA,
                "plugin_area": "OLMDistanceGradation case0026 live field/source exact replay witness",
                "mode": "external-trace",
                "command": (
                    "Run one fresh current-AEX Software 16bpc render for case_0026 and "
                    "capture all four witness points in the same AE/CDB run."
                ),
                "stop_condition": (
                    "Return one run id shared by all four target coordinates, with live case tuple, "
                    "source raw A/G/R/B words, field raw A/G/R/B words, [RCX+2], and pre/post "
                    "FUN_181170480 output words; otherwise exact_bind_failure."
                ),
                "forbidden": [
                    "answered_partial",
                    "promote prior carry-store evidence as live field words",
                    "derive raw words from PNGs",
                    "Start-Process argument arrays in the packaged PS 5.1 runner",
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
            "renderer": "software",
            "bits_per_channel": 16,
            "current_aex": {
                "module": "DistanceGradation.aex",
                "path": AEX_PATH,
                "sha256": AEX_SHA256,
                "size": AEX_SIZE,
                "module_base": None,
            },
        },
        "points": [
            {
                "xy": [x, y],
                "case_tuple": {
                    **CASE_TUPLE,
                    **CASE_TUPLE_BITS,
                },
                "field_world": {
                    "base": None,
                    "header": None,
                    "rowbytes": ROWBYTES,
                    "pixel_size": PIXEL_SIZE,
                    "channel_layout": "PF_Pixel16 / 4xuint16 (A,G,R,B words)",
                },
                "field_addr": None,
                "field_raw_words_agrb": [None, None, None, None],
                "field_word_at_rcx_plus_2": None,
                "source_addr": None,
                "source_raw_words_agrb": [None, None, None, None],
                "output_addr": None,
                "pre_output_words_agrb": [None, None, None, None],
                "post_output_words_agrb": [None, None, None, None],
            }
            for x, y in TARGET_POINTS
        ],
        "failure": {
            "stage": None,
            "reason": None,
            "run_id": None,
            "case_id": CASE_ID,
            "missing": [],
            "last_observation": None,
        },
    }


def reduced_reference_manifest(reference: dict[str, Any]) -> dict[str, Any]:
    case = next(item for item in reference["cases"] if item["id"] == CASE_ID)
    return {
        "project": reference.get("project", {}),
        "comp": reference.get("comp", {}),
        "input_alpha_mode": reference.get("input_alpha_mode"),
        "current_reference_capture": reference.get("current_reference_capture", {}),
        "cases": [
            {
                "id": CASE_ID,
                "frame": "case_0026.png",
                "before_effects_frame": "case_0026_before_effects.png",
                "effects": case.get("effects", []),
            }
        ],
    }


def request_manifest(reference: dict[str, Any]) -> dict[str, Any]:
    effect = reference["cases"][0]["effects"][0]
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
                "before_effects_frame": "case_0026_before_effects.png",
                "frame": "case_0026.png",
            }
        ],
    }


def readme() -> str:
    points = ", ".join(f"({x},{y})" for x, y in TARGET_POINTS)
    return f"""# OLMDistanceGradation case0026 live field/source witness package

This package is scoped to one fresh Windows current-AEX Software 16bpc run of
`{CASE_ID}`.

Required witness points: {points}

The return is valid only when all four points share one AE/CDB run id and each
point carries:

- the live case tuple bound from the callback's parameter block
- source raw `A,G,R,B` words
- field raw `A,G,R,B` words plus `[RCX+2]`
- pre-call output words and post-call output words around `FUN_181170480`

Any missing point or field is `exact_bind_failure`. Partial answers are
forbidden.

The packaged runner relays through Windows PowerShell 5.1 with one explicit
quoted `ArgumentList` string. Do not replace it with an argument array.
"""


def cdb_template() -> str:
    point_checks = " || ".join(f"(@edx=={x} && @r8=={y})" for x, y in TARGET_POINTS)
    return rf""".logopen /t WORKDIR\cdb_trace.log
.symfix
.effmach amd64
.expr /s masm
sxi e06d7363
.echo OLMDG_LFS_RUN_START request_id={REQUEST_ID} run_id=RUN_ID case_id={CASE_SHORT_ID}
r @$t0 = 0
r @$t1 = 0
r @$t2 = 0
r @$t6 = 0
r @$t7 = 0
bu DistanceGradation+0x1170480 ".block {{ r @$t0=0; r @$t1=0; r @$t2=0; r @$t6=@edx; r @$t7=@r8; .if (dwo(@rbx+0x94)==3 && dwo(@rbx+0xb8)==158 && dwo(@rbx+0xbc)==13 && by(@rbx+0xc0)==1 && by(@rbx+0xc1)==1 && dwo(@rbx+0xc8)==1 && dwo(@rbx+0xcc)==4 && dwo(@rbx+0xd0)==0x40263bec && dwo(@rbx+0xa0)==0x3de0e0ff && dwo(@rbx+0x9c)==0x0 && dwo(@rbx+0xa4)==0x3f6eeeef && dwo(@rbx+0xb0)==0x3f800000 && dwo(@rbx+0xac)==0x0 && dwo(@rbx+0xb4)==0x0) {{ .if ({point_checks}) {{ r @$t0=1; r @$t1=poi(@rsp+0x28); r @$t2=poi(@rsp); .printf \"OLMDG_LFS_ENTRY run_id=RUN_ID case_id={CASE_SHORT_ID} x=%u y=%u module_base=%p output=%p pre_output_words_agrb=%hu,%hu,%hu,%hu in_out=%u inside_threshold=%u outside_threshold=%u use_bg=%u invert=%u render_mode=%u interp_mode=%u power_bits=0x%08x grad_r_bits=0x%08x grad_g_bits=0x%08x grad_b_bits=0x%08x bg_r_bits=0x%08x bg_g_bits=0x%08x bg_b_bits=0x%08x\n\", @$t6, @$t7, @rip-0x1170480, @$t1, poi(@$t1), poi(@$t1+2), poi(@$t1+4), poi(@$t1+6), dwo(@rbx+0x94), dwo(@rbx+0xb8), dwo(@rbx+0xbc), by(@rbx+0xc0), by(@rbx+0xc1), dwo(@rbx+0xc8), dwo(@rbx+0xcc), dwo(@rbx+0xd0), dwo(@rbx+0xa0), dwo(@rbx+0x9c), dwo(@rbx+0xa4), dwo(@rbx+0xb0), dwo(@rbx+0xac), dwo(@rbx+0xb4); bp /1 @$t2 \".printf \\\"OLMDG_LFS_RETURN run_id=RUN_ID case_id={CASE_SHORT_ID} x=%u y=%u output=%p post_output_words_agrb=%hu,%hu,%hu,%hu\\\\n\\\", @$t6, @$t7, @$t1, poi(@$t1), poi(@$t1+2), poi(@$t1+4), poi(@$t1+6); r @$t0=0; r @$t1=0; r @$t2=0; gc\"; }} }}; gc }}"
bu DistanceGradation+0x117057d ".if (@$t0==1) {{ .printf \"OLMDG_LFS_FIELD run_id=RUN_ID case_id={CASE_SHORT_ID} x=%u y=%u rcx=%p rcx_plus2_word=%hu field_words_agrb=%hu,%hu,%hu,%hu field_base=%p field_header=%p field_rowbytes={ROWBYTES} field_pixel_size={PIXEL_SIZE}\n\", @$t6, @$t7, @rcx, poi(@rcx+2), poi(@rcx), poi(@rcx+2), poi(@rcx+4), poi(@rcx+6), @r10+0x18, @r10; }}; gc"
bu DistanceGradation+0x11705f1 ".if (@$t0==1) {{ .printf \"OLMDG_LFS_SOURCE run_id=RUN_ID case_id={CASE_SHORT_ID} x=%u y=%u rdx=%p source_words_agrb=%hu,%hu,%hu,%hu\n\", @$t6, @$t7, @rdx, poi(@rdx), poi(@rdx+2), poi(@rdx+4), poi(@rdx+6); }}; gc"
g
.echo OLMDG_LFS_RUN_END request_id={REQUEST_ID} run_id=RUN_ID
.logclose
q
"""


def runner_ps1() -> str:
    expected_points = ",".join(f"{x}:{y}" for x, y in TARGET_POINTS)
    return rf"""param(
  [string]$PackageRoot = '',
  [string]$WorkRoot = "$env:TEMP\{PACKAGE_STEM}",
  [string]$AfterFx = 'C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe',
  [string]$Cdb = 'C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe',
  [string]$PowerShell51 = 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
  [switch]$SkipPowerShell51Relay,
  [switch]$ParseOnly,
  [string]$TracePath = ''
)

$ErrorActionPreference = 'Stop'
$RequestId = '{REQUEST_ID}'
$ExpectedAexSha256 = '{AEX_SHA256}'
$ExpectedAexSize = {AEX_SIZE}L
$ExpectedPoints = @('{expected_points}'.Split(','))
$ExpectedCaseId = '{CASE_SHORT_ID}'
$ExpectedCaseFullId = '{CASE_ID}'
$Runner = Join-Path (if($PackageRoot){{$PackageRoot}}else{{Split-Path -Parent $PSCommandPath}}) 'case\ae_render_single_case.jsx'

function Field([string]$line, [string]$key) {{
  $m = [regex]::Match($line, "(?:^|\s)$key=([^\s]+)")
  if ($m.Success) {{ return $m.Groups[1].Value }}
  return $null
}}

function VecInt([string]$line, [string]$key) {{
  $raw = Field $line $key
  if ($null -eq $raw) {{ return $null }}
  return @($raw.Split(',') | ForEach-Object {{ [int]$_ }})
}}

function Marker([string[]]$lines, [string]$prefix) {{
  return @($lines | Where-Object {{ $_ -match "^$prefix\s" }})
}}

function New-Failure([string]$stage, [string]$reason, [object[]]$missing, [string]$last, [string]$runId='') {{
  return [ordered]@{{
    schema = '{SCHEMA}'
    request_id = $RequestId
    status = 'exact_bind_failure'
    run = [ordered]@{{
      run_id = if($runId){{$runId}}else{{$null}}
      case_id = $ExpectedCaseFullId
      renderer = 'software'
      bits_per_channel = 16
      current_aex = [ordered]@{{
        module = 'DistanceGradation.aex'
        path = '{AEX_PATH}'
        sha256 = '{AEX_SHA256}'
        size = {AEX_SIZE}
        module_base = $null
      }}
    }}
    points = @()
    failure = [ordered]@{{
      stage = $stage
      reason = $reason
      run_id = if($runId){{$runId}}else{{$null}}
      case_id = $ExpectedCaseFullId
      missing = @($missing)
      last_observation = $last
    }}
  }}
}}

function Convert-TraceToReturn([string]$path) {{
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {{
    return New-Failure 'trace' "missing trace: $path" @('trace') ''
  }}
  $lines = @((Get-Content -LiteralPath $path) | ForEach-Object {{ [string]$_ }})
  $records = @{{}}
  $lastObservation = $null
  foreach($line in $lines){{
    if($line -match '^OLMDG_LFS_(ENTRY|FIELD|SOURCE|RETURN)\s'){{
      $kind = $Matches[1]
      $caseId = Field $line 'case_id'
      $x = Field $line 'x'
      $y = Field $line 'y'
      if(-not $caseId -or -not $x -or -not $y){{ continue }}
      $key = "$caseId|$x|$y"
      if(-not $records.ContainsKey($key)){{
        $records[$key] = [ordered]@{{
          run_id = Field $line 'run_id'
          case_id = $caseId
          x = [int]$x
          y = [int]$y
        }}
      }}
      switch($kind){{
        'ENTRY' {{
          $records[$key]['module_base'] = Field $line 'module_base'
          $records[$key]['output_addr'] = Field $line 'output'
          $records[$key]['pre_output_words_agrb'] = VecInt $line 'pre_output_words_agrb'
          $records[$key]['in_out'] = [int](Field $line 'in_out')
          $records[$key]['inside_threshold'] = [int](Field $line 'inside_threshold')
          $records[$key]['outside_threshold'] = [int](Field $line 'outside_threshold')
          $records[$key]['use_bg'] = [int](Field $line 'use_bg')
          $records[$key]['invert'] = [int](Field $line 'invert')
          $records[$key]['render_mode'] = [int](Field $line 'render_mode')
          $records[$key]['interp_mode'] = [int](Field $line 'interp_mode')
          foreach($name in @('power_bits','grad_r_bits','grad_g_bits','grad_b_bits','bg_r_bits','bg_g_bits','bg_b_bits')){{
            $records[$key][$name] = Field $line $name
          }}
        }}
        'FIELD' {{
          $records[$key]['field_addr'] = Field $line 'rcx'
          $records[$key]['field_word_at_rcx_plus_2'] = [int](Field $line 'rcx_plus2_word')
          $records[$key]['field_raw_words_agrb'] = VecInt $line 'field_words_agrb'
          $records[$key]['field_base'] = Field $line 'field_base'
          $records[$key]['field_header'] = Field $line 'field_header'
          $records[$key]['field_rowbytes'] = [int](Field $line 'field_rowbytes')
          $records[$key]['field_pixel_size'] = [int](Field $line 'field_pixel_size')
        }}
        'SOURCE' {{
          $records[$key]['source_addr'] = Field $line 'rdx'
          $records[$key]['source_raw_words_agrb'] = VecInt $line 'source_words_agrb'
        }}
        'RETURN' {{
          $records[$key]['output_addr_after'] = Field $line 'output'
          $records[$key]['post_output_words_agrb'] = VecInt $line 'post_output_words_agrb'
        }}
      }}
      $lastObservation = $kind.ToLowerInvariant()
    }}
  }}

  $missing = @()
  $expectedKeys = @('{CASE_SHORT_ID}|907|222','{CASE_SHORT_ID}|395|477','{CASE_SHORT_ID}|1589|579','{CASE_SHORT_ID}|898|670')
  foreach($key in $expectedKeys){{
    if(-not $records.ContainsKey($key)){{ $missing += "missing:$key" }}
  }}
  $recordList = @($records.Values)
  $runIds = @($recordList | ForEach-Object {{ $_['run_id'] }} | Where-Object {{ $_ }} | Select-Object -Unique)
  if($recordList.Count -ne 4){{ $missing += "record_count=$($recordList.Count)" }}
  if($runIds.Count -ne 1){{ $missing += 'same_run_identity' }}
  foreach($record in $recordList){{
    if($record['case_id'] -ne '{CASE_SHORT_ID}'){{ $missing += "case_id:$($record['case_id'])" }}
    $coord = "$($record['x']):$($record['y'])"
    if($ExpectedPoints -notcontains $coord){{ $missing += "unexpected_xy:$coord" }}
    foreach($fieldName in @(
      'module_base','output_addr','pre_output_words_agrb',
      'field_addr','field_word_at_rcx_plus_2','field_raw_words_agrb','field_base','field_header','field_rowbytes','field_pixel_size',
      'source_addr','source_raw_words_agrb','post_output_words_agrb',
      'power_bits','grad_r_bits','grad_g_bits','grad_b_bits','bg_r_bits','bg_g_bits','bg_b_bits'
    )){{
      if(-not $record.ContainsKey($fieldName) -or $null -eq $record[$fieldName]){{ $missing += "$coord:$fieldName" }}
    }}
    if(($record['pre_output_words_agrb'] -is [array]) -and $record['pre_output_words_agrb'].Count -ne 4){{ $missing += "$coord:pre_output_words_agrb_span" }}
    if(($record['field_raw_words_agrb'] -is [array]) -and $record['field_raw_words_agrb'].Count -ne 4){{ $missing += "$coord:field_raw_words_agrb_span" }}
    if(($record['source_raw_words_agrb'] -is [array]) -and $record['source_raw_words_agrb'].Count -ne 4){{ $missing += "$coord:source_raw_words_agrb_span" }}
    if(($record['post_output_words_agrb'] -is [array]) -and $record['post_output_words_agrb'].Count -ne 4){{ $missing += "$coord:post_output_words_agrb_span" }}
    if($record['in_out'] -ne 3 -or $record['inside_threshold'] -ne 158 -or $record['outside_threshold'] -ne 13 -or $record['use_bg'] -ne 1 -or $record['invert'] -ne 1 -or $record['render_mode'] -ne 1 -or $record['interp_mode'] -ne 4){{ $missing += "$coord:case_tuple_ints" }}
    if($record['power_bits'] -ne '{CASE_TUPLE_BITS["power_bits"]}' -or $record['grad_r_bits'] -ne '{CASE_TUPLE_BITS["grad_r_bits"]}' -or $record['grad_g_bits'] -ne '{CASE_TUPLE_BITS["grad_g_bits"]}' -or $record['grad_b_bits'] -ne '{CASE_TUPLE_BITS["grad_b_bits"]}' -or $record['bg_r_bits'] -ne '{CASE_TUPLE_BITS["bg_r_bits"]}' -or $record['bg_g_bits'] -ne '{CASE_TUPLE_BITS["bg_g_bits"]}' -or $record['bg_b_bits'] -ne '{CASE_TUPLE_BITS["bg_b_bits"]}'){{ $missing += "$coord:case_tuple_bits" }}
  }}
  if($missing.Count -gt 0){{
    return New-Failure 'typed_capture' 'missing or mismatched live case0026 witness fields' $missing $lastObservation (if($runIds.Count -ge 1){{$runIds[0]}}else{{''}})
  }}

  $points = @()
  foreach($xy in @(@(907,222),@(395,477),@(1589,579),@(898,670))){{
    $key = "{CASE_SHORT_ID}|$($xy[0])|$($xy[1])"
    $record = $records[$key]
    $points += [ordered]@{{
      xy = @($xy[0], $xy[1])
      case_tuple = [ordered]@{{
        in_out = 3
        inside_threshold = 158
        outside_threshold = 13
        use_background_color = 1
        invert = 1
        render_mode = 1
        interp_mode = 4
        power_bits = '{CASE_TUPLE_BITS["power_bits"]}'
        grad_r_bits = '{CASE_TUPLE_BITS["grad_r_bits"]}'
        grad_g_bits = '{CASE_TUPLE_BITS["grad_g_bits"]}'
        grad_b_bits = '{CASE_TUPLE_BITS["grad_b_bits"]}'
        bg_r_bits = '{CASE_TUPLE_BITS["bg_r_bits"]}'
        bg_g_bits = '{CASE_TUPLE_BITS["bg_g_bits"]}'
        bg_b_bits = '{CASE_TUPLE_BITS["bg_b_bits"]}'
      }}
      field_world = [ordered]@{{
        base = $record['field_base']
        header = $record['field_header']
        rowbytes = $record['field_rowbytes']
        pixel_size = $record['field_pixel_size']
        channel_layout = 'PF_Pixel16 / 4xuint16 (A,G,R,B words)'
      }}
      field_addr = $record['field_addr']
      field_raw_words_agrb = $record['field_raw_words_agrb']
      field_word_at_rcx_plus_2 = $record['field_word_at_rcx_plus_2']
      source_addr = $record['source_addr']
      source_raw_words_agrb = $record['source_raw_words_agrb']
      output_addr = $record['output_addr']
      pre_output_words_agrb = $record['pre_output_words_agrb']
      post_output_words_agrb = $record['post_output_words_agrb']
    }}
  }}
  return [ordered]@{{
    schema = '{SCHEMA}'
    request_id = $RequestId
    status = 'answered'
    run = [ordered]@{{
      run_id = $runIds[0]
      case_id = $ExpectedCaseFullId
      renderer = 'software'
      bits_per_channel = 16
      current_aex = [ordered]@{{
        module = 'DistanceGradation.aex'
        path = '{AEX_PATH}'
        sha256 = '{AEX_SHA256}'
        size = {AEX_SIZE}
        module_base = $recordList[0]['module_base']
      }}
    }}
    points = $points
  }}
}}

if($ParseOnly){{
  if(-not $TracePath){{ throw 'ParseOnly requires -TracePath' }}
  (Convert-TraceToReturn $TracePath) | ConvertTo-Json -Depth 12
  exit 0
}}

$isDesktop = $PSVersionTable.PSEdition -eq 'Desktop'
$isPs51 = $isDesktop -and $PSVersionTable.PSVersion.Major -eq 5
if(-not $SkipPowerShell51Relay -and -not $isPs51){{
  if(-not (Test-Path -LiteralPath $PowerShell51 -PathType Leaf)){{ throw "PowerShell 5.1 missing: $PowerShell51" }}
  $relayArgs = '-NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '" -PackageRoot "' + $PackageRoot + '" -WorkRoot "' + $WorkRoot + '" -AfterFx "' + $AfterFx + '" -Cdb "' + $Cdb + '" -PowerShell51 "' + $PowerShell51 + '" -SkipPowerShell51Relay'
  if($ParseOnly){{ $relayArgs += ' -ParseOnly -TracePath "' + $TracePath + '"' }}
  $relay = Start-Process -FilePath $PowerShell51 -ArgumentList $relayArgs -NoNewWindow -PassThru -Wait
  exit $relay.ExitCode
}}

if(-not $PackageRoot){{ $PackageRoot = Split-Path -Parent $PSCommandPath }}
$caseRoot = Join-Path $PackageRoot 'case'
$jsx = Join-Path $caseRoot 'ae_render_single_case.jsx'
$requestDir = $caseRoot
$work = Join-Path $WorkRoot 'single_fresh_run'
$trace = Join-Path $work 'cdb_trace.log'
$stdout = Join-Path $work 'cdb_stdout.txt'
$stderr = Join-Path $work 'cdb_stderr.txt'
$returnJson = Join-Path $work 'RETURN_RUNTIME_TRACE.json'
$aeLog = Join-Path $work 'AE_SINGLE_CASE.log'
$aeResult = Join-Path $work 'AE_SINGLE_CASE_RESULT.json'
$cdbTemplate = Join-Path $PackageRoot 'case0026_livefield_source_witness.cdb.in'
$cdbScript = Join-Path $work 'case0026_livefield_source_witness.cdb'
foreach($path in @($AfterFx,$Cdb,$jsx,$cdbTemplate,(Join-Path $requestDir 'request_manifest.json'),(Join-Path $requestDir 'reference_manifest.json'),(Join-Path $requestDir 'input\case_0026_before_effects.png'))){{
  if(-not (Test-Path -LiteralPath $path -PathType Leaf)){{ throw "Missing packaged runner asset or tool: $path" }}
}}
if(-not (Test-Path -LiteralPath '{AEX_PATH}' -PathType Leaf)){{ throw "Pinned AEX missing: {AEX_PATH}" }}
$aex = Get-Item -LiteralPath '{AEX_PATH}'
$aexSha256 = (Get-FileHash -LiteralPath '{AEX_PATH}' -Algorithm SHA256).Hash.ToLowerInvariant()
if($aex.Length -ne $ExpectedAexSize -or $aexSha256 -ne $ExpectedAexSha256){{
  throw "Pinned AEX identity mismatch: size=$($aex.Length) sha256=$aexSha256"
}}
New-Item -ItemType Directory -Force -Path $work | Out-Null
$env:OLM_AE_REQUEST_DIR = ($requestDir -replace '\\', '/')
$env:OLM_AE_CASE_ID = '{CASE_ID}'
$env:OLM_AE_OUTPUT_DIR = $work
$env:OLM_AE_LOG_PATH = $aeLog
$env:OLM_AE_RESULT_JSON = $aeResult
$env:OLM_AE_PARAM_OVERRIDES_JSON = '{{}}'
$env:OLM_AE_FORCE_NEW_PROJECT = '1'
$env:OLM_AE_FORCE_SOFTWARE = '1'
$env:OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT = '1'
$env:OLM_AE_KEEP_OPEN = '0'
$runId = 'dglfs_' + (Get-Date -Format 'yyyyMMddHHmmssfff')
$template = Get-Content -LiteralPath $cdbTemplate -Raw
$template = $template.Replace('WORKDIR', $work).Replace('RUN_ID', $runId)
$template | Set-Content -LiteralPath $cdbScript -Encoding ASCII
$cdbArgs = '-cf "' + $cdbScript + '" "' + $AfterFx + '" -r "' + $jsx + '"'
$proc = Start-Process -FilePath $Cdb -ArgumentList $cdbArgs -RedirectStandardOutput $stdout -RedirectStandardError $stderr -NoNewWindow -PassThru -Wait
$parsed = Convert-TraceToReturn $trace
if($parsed.status -eq 'answered'){{
  if(-not (Test-Path -LiteralPath $aeResult -PathType Leaf)){{
    $parsed = New-Failure 'ae_result' 'AE result JSON missing after trace run' @('AE_SINGLE_CASE_RESULT.json') 'return' $runId
  }} else {{
    $result = Get-Content -LiteralPath $aeResult -Raw | ConvertFrom-Json
    if($result.status -ne 'ok' -or [int]$result.project_bits_per_channel -ne 16){{
      $parsed = New-Failure 'ae_host_contract' "AE host contract mismatch: status=$($result.status) bits=$($result.project_bits_per_channel)" @('project_bits_per_channel') 'return' $runId
    }} elseif(-not (Test-Path -LiteralPath $aeLog -PathType Leaf) -or -not ((Get-Content -LiteralPath $aeLog -Raw) -match 'gpuAccelType=SOFTWARE')){{
      $parsed = New-Failure 'ae_host_contract' 'AE log does not confirm Software renderer' @('gpuAccelType=SOFTWARE') 'return' $runId
    }}
  }}
}}
$parsed | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $returnJson -Encoding UTF8
$parsed | ConvertTo-Json -Depth 12
if($parsed.status -ne 'answered'){{ exit 2 }}
exit 0
"""


def _parse_fields(line: str) -> dict[str, str]:
    return {key: value for key, value in re.findall(r"([A-Za-z0-9_]+)=([^\s]+)", line)}


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value, 0)
    except ValueError:
        return None


def _parse_vector(value: str | None) -> list[int] | None:
    if value is None:
        return None
    try:
        return [int(item, 0) for item in value.split(",")]
    except ValueError:
        return None


def parse_trace_lines(lines: list[str]) -> dict[str, Any]:
    records: dict[tuple[str, int, int], dict[str, Any]] = {}
    run_ids: set[str] = set()
    last_observation: str | None = None
    for line in lines:
        if not line.startswith("OLMDG_LFS_"):
            continue
        fields = _parse_fields(line)
        prefix = line.split(" ", 1)[0]
        run_id = fields.get("run_id")
        if run_id:
            run_ids.add(run_id)
        if prefix.endswith("RUN_START") or prefix.endswith("RUN_END"):
            continue
        case_id = fields.get("case_id")
        x = _parse_int(fields.get("x"))
        y = _parse_int(fields.get("y"))
        if case_id is None or x is None or y is None:
            continue
        key = (case_id, x, y)
        record = records.setdefault(key, {"case_id": case_id, "xy": [x, y], "run_id": run_id})
        if prefix.endswith("ENTRY"):
            record.update(
                {
                    "module_base": fields.get("module_base"),
                    "output_addr": fields.get("output"),
                    "pre_output_words_agrb": _parse_vector(fields.get("pre_output_words_agrb")),
                    "in_out": _parse_int(fields.get("in_out")),
                    "inside_threshold": _parse_int(fields.get("inside_threshold")),
                    "outside_threshold": _parse_int(fields.get("outside_threshold")),
                    "use_bg": _parse_int(fields.get("use_bg")),
                    "invert": _parse_int(fields.get("invert")),
                    "render_mode": _parse_int(fields.get("render_mode")),
                    "interp_mode": _parse_int(fields.get("interp_mode")),
                    "power_bits": fields.get("power_bits"),
                    "grad_r_bits": fields.get("grad_r_bits"),
                    "grad_g_bits": fields.get("grad_g_bits"),
                    "grad_b_bits": fields.get("grad_b_bits"),
                    "bg_r_bits": fields.get("bg_r_bits"),
                    "bg_g_bits": fields.get("bg_g_bits"),
                    "bg_b_bits": fields.get("bg_b_bits"),
                }
            )
            last_observation = "entry"
        elif prefix.endswith("FIELD"):
            record.update(
                {
                    "field_addr": fields.get("rcx"),
                    "field_word_at_rcx_plus_2": _parse_int(fields.get("rcx_plus2_word")),
                    "field_raw_words_agrb": _parse_vector(fields.get("field_words_agrb")),
                    "field_base": fields.get("field_base"),
                    "field_header": fields.get("field_header"),
                    "field_rowbytes": _parse_int(fields.get("field_rowbytes")),
                    "field_pixel_size": _parse_int(fields.get("field_pixel_size")),
                }
            )
            last_observation = "field"
        elif prefix.endswith("SOURCE"):
            record.update(
                {
                    "source_addr": fields.get("rdx"),
                    "source_raw_words_agrb": _parse_vector(fields.get("source_words_agrb")),
                }
            )
            last_observation = "source"
        elif prefix.endswith("RETURN"):
            record.update(
                {
                    "output_addr_after": fields.get("output"),
                    "post_output_words_agrb": _parse_vector(fields.get("post_output_words_agrb")),
                }
            )
            last_observation = "return"

    missing: list[str] = []
    expected = {(CASE_SHORT_ID, x, y) for x, y in TARGET_POINTS}
    seen = set(records.keys())
    for case_id, x, y in sorted(expected - seen):
        missing.append(f"missing:{case_id}|{x}|{y}")
    if len(records) != 4:
        missing.append(f"record_count={len(records)}")
    if len(run_ids) != 1:
        missing.append("same_run_identity")

    for key, record in records.items():
        case_id, x, y = key
        coord = f"{x}:{y}"
        if case_id != CASE_SHORT_ID:
            missing.append(f"{coord}:case_id")
        for field_name in (
            "module_base",
            "output_addr",
            "pre_output_words_agrb",
            "field_addr",
            "field_word_at_rcx_plus_2",
            "field_raw_words_agrb",
            "field_base",
            "field_header",
            "field_rowbytes",
            "field_pixel_size",
            "source_addr",
            "source_raw_words_agrb",
            "post_output_words_agrb",
            "power_bits",
            "grad_r_bits",
            "grad_g_bits",
            "grad_b_bits",
            "bg_r_bits",
            "bg_g_bits",
            "bg_b_bits",
        ):
            if record.get(field_name) is None:
                missing.append(f"{coord}:{field_name}")
        for vector_name in (
            "pre_output_words_agrb",
            "field_raw_words_agrb",
            "source_raw_words_agrb",
            "post_output_words_agrb",
        ):
            vector = record.get(vector_name)
            if vector is not None and len(vector) != 4:
                missing.append(f"{coord}:{vector_name}_span")
        if (
            record.get("in_out") != CASE_TUPLE["in_out"]
            or record.get("inside_threshold") != CASE_TUPLE["inside_threshold"]
            or record.get("outside_threshold") != CASE_TUPLE["outside_threshold"]
            or record.get("use_bg") != CASE_TUPLE["use_background_color"]
            or record.get("invert") != CASE_TUPLE["invert"]
            or record.get("render_mode") != CASE_TUPLE["render_mode"]
            or record.get("interp_mode") != CASE_TUPLE["interp_mode"]
        ):
            missing.append(f"{coord}:case_tuple_ints")
        for bit_name, expected_bits in CASE_TUPLE_BITS.items():
            if record.get(bit_name) != expected_bits:
                missing.append(f"{coord}:{bit_name}")

    run_id = next(iter(run_ids)) if len(run_ids) == 1 else None
    if missing:
        return {
            "schema": SCHEMA,
            "request_id": REQUEST_ID,
            "status": "exact_bind_failure",
            "run": {
                "run_id": run_id,
                "case_id": CASE_ID,
                "renderer": "software",
                "bits_per_channel": 16,
                "current_aex": {
                    "module": "DistanceGradation.aex",
                    "path": AEX_PATH,
                    "sha256": AEX_SHA256,
                    "size": AEX_SIZE,
                    "module_base": None,
                },
            },
            "points": [],
            "failure": {
                "stage": "typed_capture",
                "reason": "missing or mismatched live case0026 witness fields",
                "run_id": run_id,
                "case_id": CASE_ID,
                "missing": missing,
                "last_observation": last_observation,
            },
        }

    points = []
    first_base = None
    for x, y in TARGET_POINTS:
        record = records[(CASE_SHORT_ID, x, y)]
        if first_base is None:
            first_base = record["module_base"]
        points.append(
            {
                "xy": [x, y],
                "case_tuple": {
                    "in_out": CASE_TUPLE["in_out"],
                    "inside_threshold": CASE_TUPLE["inside_threshold"],
                    "outside_threshold": CASE_TUPLE["outside_threshold"],
                    "use_background_color": CASE_TUPLE["use_background_color"],
                    "invert": CASE_TUPLE["invert"],
                    "render_mode": CASE_TUPLE["render_mode"],
                    "interp_mode": CASE_TUPLE["interp_mode"],
                    **CASE_TUPLE_BITS,
                },
                "field_world": {
                    "base": record["field_base"],
                    "header": record["field_header"],
                    "rowbytes": record["field_rowbytes"],
                    "pixel_size": record["field_pixel_size"],
                    "channel_layout": "PF_Pixel16 / 4xuint16 (A,G,R,B words)",
                },
                "field_addr": record["field_addr"],
                "field_raw_words_agrb": record["field_raw_words_agrb"],
                "field_word_at_rcx_plus_2": record["field_word_at_rcx_plus_2"],
                "source_addr": record["source_addr"],
                "source_raw_words_agrb": record["source_raw_words_agrb"],
                "output_addr": record["output_addr"],
                "pre_output_words_agrb": record["pre_output_words_agrb"],
                "post_output_words_agrb": record["post_output_words_agrb"],
            }
        )

    return {
        "schema": SCHEMA,
        "request_id": REQUEST_ID,
        "status": "answered",
        "run": {
            "run_id": run_id,
            "case_id": CASE_ID,
            "renderer": "software",
            "bits_per_channel": 16,
            "current_aex": {
                "module": "DistanceGradation.aex",
                "path": AEX_PATH,
                "sha256": AEX_SHA256,
                "size": AEX_SIZE,
                "module_base": first_base,
            },
        },
        "points": points,
    }


def materialize_support(root: Path, support_dir: Path, zip_path: Path) -> None:
    if support_dir.exists():
        shutil.rmtree(support_dir)
    support_dir.mkdir(parents=True, exist_ok=True)
    (support_dir / "case" / "input").mkdir(parents=True, exist_ok=True)
    (support_dir / "case" / "expected").mkdir(parents=True, exist_ok=True)

    full_reference = json.loads((root / REFERENCE_MANIFEST).read_text(encoding="utf-8"))
    reference = reduced_reference_manifest(full_reference)
    request = request_manifest(reference)

    files: dict[Path, bytes] = {
        support_dir / "CONTRACT.md": (root / CONTRACT_PATH).read_bytes(),
        support_dir / "README.md": readme().encode("utf-8"),
        support_dir / "manifest.json": (json.dumps(package_manifest(), indent=2) + "\n").encode("utf-8"),
        support_dir / "runtime_trace_package_manifest.json": (
            json.dumps(runtime_trace_package_manifest(root), indent=2) + "\n"
        ).encode("utf-8"),
        support_dir / "RETURN_RUNTIME_TRACE_TEMPLATE.json": (
            json.dumps(return_template(), indent=2) + "\n"
        ).encode("utf-8"),
        support_dir / "case0026_livefield_source_witness.cdb.in": cdb_template().encode("utf-8"),
        support_dir / "run_olmdistancegradation_case0026_16bpc_livefield_source_witness_20260713.ps1": runner_ps1().encode(
            "utf-8"
        ),
        support_dir / "case" / "request_manifest.json": (json.dumps(request, indent=2) + "\n").encode("utf-8"),
        support_dir / "case" / "reference_manifest.json": (json.dumps(reference, indent=2) + "\n").encode("utf-8"),
        support_dir / "case" / "ae_render_single_case.jsx": (root / "scripts/ae_render_single_case.jsx").read_bytes(),
        support_dir / "case" / "input" / "case_0026_before_effects.png": (root / REQUEST_ROOT / "input" / CASE_BEFORE).read_bytes(),
        support_dir / "case" / "expected" / "case_0026.png": (root / REQUEST_ROOT / "expected" / CASE_EXPECTED).read_bytes(),
    }
    for path, data in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(support_dir.rglob("*")):
            if path.is_dir() or path == zip_path:
                continue
            archive.write(path, f"{PACKAGE_STEM}/{path.relative_to(support_dir).as_posix()}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--support-dir", type=Path, default=SUPPORT_DIR)
    parser.add_argument("--output", type=Path, default=OUTPUT_ZIP)
    args = parser.parse_args()
    root = repo_root()
    support_dir = args.support_dir if args.support_dir.is_absolute() else root / args.support_dir
    output = args.output if args.output.is_absolute() else root / args.output
    materialize_support(root, support_dir, output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
