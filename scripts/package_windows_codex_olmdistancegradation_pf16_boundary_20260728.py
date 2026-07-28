#!/usr/bin/env python3
"""Build the immutable OLMDistanceGradation PF16 Windows boundary child."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.windows_witness.compiler import compile_witness
from tools.windows_witness.core import deterministic_zip, sha256_file


REQUEST_ID = "ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625"
JOB_ID = "olmdistancegradation_pf16_boundary_20260728_r1"
WITNESS_ID = "olmdistancegradation-pf16-direct-boundary-v1"
PROJECT_ID = "canonical-dg-extended-1920x1080-frame0-16bpc-software"
PLUGIN_ID = "DistanceGradation_2025_a1d317c0"
RUNTIME_ID = "AfterFX_25.2x131_desktop_CDB_x64"
EXPECTED_AE_VERSION = "25.2x131"
AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
CASE_MANIFEST_SHA256 = "7c4761b3b4de904c2a8baa8883c964f234943604414d2cd34bab107ccc43cf29"
REFERENCE_MANIFEST_SHA256 = "c4378358c8b4db2b2d5d12d0bf0b4142f141963538ca5ec4d86a49eeb8b9e71e"
INPUT_SHA256 = "4df66ca58088631115a48a7396d5f7f5b272866f8f6444a02c996751d1afc43c"
CLAIM_BOUNDARY = "direct_windows_aex_pf16_field_prestore_store_words_only"
UNRESOLVED_BOUNDARY = (
    "field_pack_producer_conversion_export_mapping_cli_and_ae_exactness_unresolved"
)
SOURCE_REQUEST = (
    ROOT
    / "handoff"
    / "ae_pixel_validation_20260618"
    / "requests"
    / "ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625"
)
SOURCE_RENDERER = (
    ROOT
    / "refs"
    / "windows_witness_specs"
    / "olmdistancegradation_case0026_16bpc_livefield_20260713"
    / "renderer.jsx"
)
TARGET = (
    ROOT
    / "refs"
    / "handoffs"
    / "windows_codex_batch_jobs_20260728"
    / JOB_ID
)


CASES: tuple[dict[str, Any], ...] = (
    {
        "code": "0012", "x": 438, "y": 0, "in_out": 3,
        "inside_threshold": 122, "outside_threshold": 204, "use_bg": 0,
        "invert": 0, "render_mode": 2, "interp_mode": 2,
        "power_bits": "0x3f800000", "claim_stage": "prestore_and_stored_pf16",
    },
    {
        "code": "0014", "x": 448, "y": 0, "in_out": 1,
        "inside_threshold": 424, "outside_threshold": 204, "use_bg": 0,
        "invert": 0, "render_mode": 2, "interp_mode": 2,
        "power_bits": "0x3f800000", "claim_stage": "prestore_and_stored_pf16",
    },
    {
        "code": "0024", "x": 232, "y": 328, "in_out": 3,
        "inside_threshold": 158, "outside_threshold": 17, "use_bg": 1,
        "invert": 0, "render_mode": 1, "interp_mode": 3,
        "power_bits": "0x3f800000", "claim_stage": "direct_field_staging_pf16",
    },
    {
        "code": "0025", "x": 3, "y": 0, "in_out": 3,
        "inside_threshold": 158, "outside_threshold": 13, "use_bg": 1,
        "invert": 1, "render_mode": 1, "interp_mode": 3,
        "power_bits": "0x3f800000", "claim_stage": "direct_field_staging_pf16",
    },
    {
        "code": "0026", "x": 907, "y": 222, "in_out": 3,
        "inside_threshold": 158, "outside_threshold": 13, "use_bg": 1,
        "invert": 1, "render_mode": 1, "interp_mode": 4,
        "power_bits": "0x40263bec", "claim_stage": "direct_field_staging_pf16",
    },
    {
        "code": "0027", "x": 1234, "y": 443, "in_out": 3,
        "inside_threshold": 158, "outside_threshold": 13, "use_bg": 1,
        "invert": 1, "render_mode": 2, "interp_mode": 4,
        "power_bits": "0x40263bec", "claim_stage": "direct_field_staging_pf16",
    },
)

IDENTITY_FIELDS = [
    "run_id", "ae_pid", "module_base", "aex_sha256", "project_bpc",
    "renderer", "case_id", "witness_id", "request_id", "project_id",
    "plugin_id", "runtime_id", "case_manifest_sha256",
    "reference_manifest_sha256", "input_sha256", "claim_boundary",
    "unresolved_boundary",
]

EVENT_IDENTITY = (
    "run_id={{RUN_ID}} ae_pid={{AE_PID}} module_base={{MODULE_BASE}} "
    "aex_sha256={{AEX_SHA256}} project_bpc={{PROJECT_BPC}} "
    "renderer={{RENDERER}} case_id={{CASE_ID}} "
    "witness_id={{CASE_VALUE:witness_id}} request_id={{CASE_VALUE:request_id}} "
    "project_id={{CASE_VALUE:project_id}} plugin_id={{CASE_VALUE:plugin_id}} "
    "runtime_id={{CASE_VALUE:runtime_id}} "
    "case_manifest_sha256={{CASE_VALUE:case_manifest_sha256}} "
    "reference_manifest_sha256={{CASE_VALUE:reference_manifest_sha256}} "
    "input_sha256={{CASE_VALUE:input_sha256}} "
    "claim_boundary={{CASE_VALUE:claim_boundary}} "
    "unresolved_boundary={{CASE_VALUE:unresolved_boundary}}"
)

CDB_TEMPLATE = f""".effmach amd64
.expr /s masm
sxi e06d7363
.logopen /t "{{{{TRACE_PATH}}}}"
r @$t0=0;r @$t1=0
bp {{{{ADDRESS:entry}}}} ".if (@edx==0n{{{{CASE_VALUE:x}}}} && @r8d==0n{{{{CASE_VALUE:y}}}}) {{r @$t0=1;r @$t1=poi(@rsp+0x28);.printf \\"{{{{CASE_VALUE:event_prefix}}}}_ENTRY {EVENT_IDENTITY} stage=entry hook_rva=1170480 x=%u y=%u output_addr=%p in_out=%u inside_threshold=%u outside_threshold=%u use_bg=%u invert=%u render_mode=%u interp_mode=%u power_bits=0x%08x same_run=1\\\\n\\",@edx,@r8d,@$t1,dwo(@rbx+0x94),dwo(@rbx+0xb8),dwo(@rbx+0xbc),by(@rbx+0xc0),by(@rbx+0xc1),dwo(@rbx+0xc8),dwo(@rbx+0xcc),dwo(@rbx+0xd0);gu}} .else {{gc}}"
bp {{{{ADDRESS:field_read}}}} ".if (@$t0==1 && @rdi==@$t1) {{.printf \\"{{{{CASE_VALUE:event_prefix}}}}_FIELD {EVENT_IDENTITY} stage=direct_field_read hook_rva=117057d x={{{{CASE_VALUE:x}}}} y={{{{CASE_VALUE:y}}}} output_addr=%p field_addr=%p field_words_agrb=%hu,%hu,%hu,%hu direct_field_staging_word=%hu capture_semantics=direct_memory_read_not_derived same_run=1\\\\n\\",@rdi,@rcx,wo(@rcx),wo(@rcx+2),wo(@rcx+4),wo(@rcx+6),wo(@rcx+2))}};gc"
bp {{{{ADDRESS:source_read}}}} ".if (@$t0==1 && @rdi==@$t1) {{.printf \\"{{{{CASE_VALUE:event_prefix}}}}_SOURCE {EVENT_IDENTITY} stage=direct_source_read hook_rva=11705f1 x={{{{CASE_VALUE:x}}}} y={{{{CASE_VALUE:y}}}} output_addr=%p source_addr=%p source_words_agrb=%hu,%hu,%hu,%hu capture_semantics=direct_memory_read_not_derived same_run=1\\\\n\\",@rdi,@rdx,wo(@rdx),wo(@rdx+2),wo(@rdx+4),wo(@rdx+6))}};gc"
bp {{{{ADDRESS:pre_store}}}} ".if (@$t0==1 && @rdi==@$t1) {{.printf \\"{{{{CASE_VALUE:event_prefix}}}}_PRESTORE {EVENT_IDENTITY} stage=direct_pre_store hook_rva=11707f4 x={{{{CASE_VALUE:x}}}} y={{{{CASE_VALUE:y}}}} output_addr=%p pre_store_argb_f32_bits=0x%08x,0x%08x,0x%08x,0x%08x pre_store_argb_f32=%g,%g,%g,%g capture_semantics=direct_register_bits_before_pf16_scale same_run=1\\\\n\\",@rdi,@xmm6,@xmm1,@xmm4,@xmm5,@xmm6,@xmm1,@xmm4,@xmm5)}};gc"
bp {{{{ADDRESS:stored}}}} ".if (@$t0==1 && @rdi==@$t1) {{.printf \\"{{{{CASE_VALUE:event_prefix}}}}_STORED {EVENT_IDENTITY} stage=direct_stored_pf16 hook_rva=117082b x={{{{CASE_VALUE:x}}}} y={{{{CASE_VALUE:y}}}} output_addr=%p stored_pf16_words_agrb=%hu,%hu,%hu,%hu capture_semantics=direct_output_memory_after_four_stores same_run=1\\\\n\\",@rdi,wo(@rdi),wo(@rdi+2),wo(@rdi+4),wo(@rdi+6);.detach;q}};gc"
.echo OLMDG_PF16_DIRECT_BREAKPOINTS_ARMED
g
"""


FAIL_CLOSED_RUNNER = rf"""param(
  [string]$PackageRoot = $PSScriptRoot,
  [string]$AexPath = '',
  [string]$AfterFxPath = '',
  [string]$CdbPath = ''
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$requestId = '{REQUEST_ID}'
$claimBoundary = '{CLAIM_BOUNDARY}'
$unresolvedBoundary = '{UNRESOLVED_BOUNDARY}'
$expectedAeVersion = '{EXPECTED_AE_VERSION}'
$expectedAexSha256 = '{AEX_SHA256}'
$expectedCaseManifestSha256 = '{CASE_MANIFEST_SHA256}'
$expectedReferenceManifestSha256 = '{REFERENCE_MANIFEST_SHA256}'
$evidenceRoot = Join-Path $PackageRoot 'evidence'
$workRoot = Join-Path $PackageRoot 'work_pf16_boundary_r1'
$innerRunner = Join-Path $PackageRoot 'artifacts\run_witness.ps1'
$contractPath = Join-Path $PackageRoot 'witness-contract.json'
$requestManifestPath = Join-Path $PackageRoot 'request\request_manifest.json'
$referenceManifestPath = Join-Path $PackageRoot 'request\reference_manifest.json'
$statusPath = Join-Path $evidenceRoot 'CHILD_STATUS.json'
$exitCode = 2

function Write-Json([string]$Path, [object]$Value) {{
  $Value | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $Path -Encoding UTF8 -ErrorAction Stop
}}
function New-Failure([string]$Stage, [string]$Reason) {{
  [ordered]@{{
    schema_version = 1
    status = 'exact_bind_failure'
    request_id = $requestId
    claim_boundary = $claimBoundary
    unresolved_boundary = $unresolvedBoundary
    ae_exact = $false
    conversion_exact = $false
    production_change_authorized = $false
    failure = [ordered]@{{
      stage = $Stage
      reason = $Reason
      missing_fields = @('direct_runtime_pf16_boundary_evidence')
    }}
  }}
}}
function Copy-Direct([string]$Source, [string]$Name, [bool]$Required) {{
  if (Test-Path -LiteralPath $Source -PathType Leaf) {{
    Copy-Item -LiteralPath $Source -Destination (Join-Path $evidenceRoot $Name) -Force -ErrorAction Stop
    return $true
  }}
  if ($Required) {{ throw "missing direct evidence: $Source" }}
  return $false
}}

try {{
  if (Test-Path -LiteralPath $evidenceRoot -or Test-Path -LiteralPath $workRoot) {{
    throw 'one-shot package contains stale evidence/work; extract a fresh immutable child'
  }}
  New-Item -ItemType Directory -Path $evidenceRoot,$workRoot -ErrorAction Stop | Out-Null
  $contract = Get-Content -LiteralPath $contractPath -Raw -ErrorAction Stop | ConvertFrom-Json
  if (!$AexPath) {{ $AexPath = [string]$contract.plugin.default_aex_path }}
  if (!$AfterFxPath) {{ $AfterFxPath = [string]$contract.host.afterfx_path }}
  if (!$CdbPath) {{ $CdbPath = [string]$contract.host.cdb_path }}
  foreach ($path in @($innerRunner,$AexPath,$AfterFxPath,$CdbPath,$requestManifestPath,$referenceManifestPath)) {{
    if (!(Test-Path -LiteralPath $path -PathType Leaf)) {{ throw "required file missing: $path" }}
  }}
  $aexHash = (Get-FileHash -LiteralPath $AexPath -Algorithm SHA256).Hash.ToLowerInvariant()
  $caseHash = (Get-FileHash -LiteralPath $requestManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
  $referenceHash = (Get-FileHash -LiteralPath $referenceManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($aexHash -cne $expectedAexSha256) {{ throw "AEX SHA-256 mismatch: $aexHash" }}
  if ($caseHash -cne $expectedCaseManifestSha256) {{ throw "case manifest SHA-256 mismatch: $caseHash" }}
  if ($referenceHash -cne $expectedReferenceManifestSha256) {{ throw "reference manifest SHA-256 mismatch: $referenceHash" }}
  $afterFxItem = Get-Item -LiteralPath $AfterFxPath -ErrorAction Stop
  $cdbItem = Get-Item -LiteralPath $CdbPath -ErrorAction Stop
  $arguments = @(
    '-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $innerRunner + '"'),
    '-PackageRoot',('"' + $PackageRoot + '"'),'-WorkRoot',('"' + $workRoot + '"'),
    '-AexPath',('"' + $AexPath + '"'),'-AfterFxPath',('"' + $AfterFxPath + '"'),
    '-CdbPath',('"' + $CdbPath + '"')
  )
  $stdoutPath = Join-Path $evidenceRoot 'INNER_RUNNER_STDOUT.txt'
  $stderrPath = Join-Path $evidenceRoot 'INNER_RUNNER_STDERR.txt'
  $process = Start-Process -FilePath 'powershell.exe' -ArgumentList $arguments `
    -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath `
    -PassThru -Wait -WindowStyle Hidden -ErrorAction Stop
  $run = Get-ChildItem -LiteralPath $workRoot -Directory -ErrorAction Stop |
    Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
  if ($null -eq $run) {{ throw "inner runner emitted no run directory; exit=$($process.ExitCode)" }}
  $innerStatus = Join-Path $run.FullName 'validation_status.json'
  $parsed = Get-Content -LiteralPath $innerStatus -Raw -ErrorAction Stop | ConvertFrom-Json
  Copy-Direct $innerStatus 'INNER_VALIDATION_STATUS.json' $true | Out-Null
  Copy-Direct (Join-Path $run.FullName 'combined_cdb_trace.txt') 'DIRECT_CDB_TRACE.txt' $true | Out-Null
  Copy-Direct (Join-Path $run.FullName 'runtime_identity.json') 'RUNTIME_IDENTITY.json' $true | Out-Null
  Copy-Direct (Join-Path $run.FullName 'RETURN_OLMDISTANCEGRADATION_PF16_BOUNDARY.json') 'DIRECT_BOUNDARY_RETURN.json' $true | Out-Null
  $aeResults = @()
  foreach ($code in @('0012','0014','0024','0025','0026','0027')) {{
    $caseId = 'olmdistancegradation_extended__case_' + $code
    $source = Join-Path $run.FullName ('ae_result_' + $caseId + '.json')
    $row = Get-Content -LiteralPath $source -Raw -ErrorAction Stop | ConvertFrom-Json
    if ([string]$row.ae_version -cne $expectedAeVersion) {{
      throw "AE application identity mismatch for $caseId: $([string]$row.ae_version)"
    }}
    if ([string]$row.status -cne 'ok' -or [int]$row.project_bits_per_channel -ne 16) {{
      throw "AE result identity mismatch for $caseId"
    }}
    Copy-Direct $source ('AE_RESULT_' + $code + '.json') $true | Out-Null
    $aeResults += [ordered]@{{
      case_id = $caseId
      ae_version = [string]$row.ae_version
      project_bits_per_channel = [int]$row.project_bits_per_channel
      project_working_space = [string]$row.project_working_space
      project_linear_blending = [bool]$row.project_linear_blending
    }}
  }}
  $attestation = [ordered]@{{
    schema_version = 1
    request_id = $requestId
    project_id = '{PROJECT_ID}'
    witness_id = '{WITNESS_ID}'
    plugin_id = '{PLUGIN_ID}'
    runtime_id = '{RUNTIME_ID}'
    request_manifest = [ordered]@{{ path=$requestManifestPath; sha256=$caseHash }}
    reference_manifest = [ordered]@{{ path=$referenceManifestPath; sha256=$referenceHash }}
    aex = [ordered]@{{ path=$AexPath; sha256=$aexHash }}
    afterfx = [ordered]@{{
      path=$AfterFxPath
      sha256=(Get-FileHash -LiteralPath $AfterFxPath -Algorithm SHA256).Hash.ToLowerInvariant()
      file_version=[string]$afterFxItem.VersionInfo.FileVersion
      product_version=[string]$afterFxItem.VersionInfo.ProductVersion
      expected_app_version=$expectedAeVersion
    }}
    cdb = [ordered]@{{
      path=$CdbPath
      sha256=(Get-FileHash -LiteralPath $CdbPath -Algorithm SHA256).Hash.ToLowerInvariant()
      file_version=[string]$cdbItem.VersionInfo.FileVersion
      product_version=[string]$cdbItem.VersionInfo.ProductVersion
    }}
    cases = $aeResults
    claim_boundary = $claimBoundary
    unresolved_boundary = $unresolvedBoundary
  }}
  Write-Json (Join-Path $evidenceRoot 'RUNTIME_ATTESTATION.json') $attestation
  if ($process.ExitCode -ne 0 -or [string]$parsed.status -cne 'answered') {{
    throw "inner runner terminal status=$([string]$parsed.status) exit=$($process.ExitCode)"
  }}
  Write-Json $statusPath ([ordered]@{{
    schema_version = 1
    status = 'answered'
    request_id = $requestId
    claim_boundary = $claimBoundary
    answered_meaning = 'direct runtime AEX PF16 field/source words, normalized pre-store float32 register bits, and stored PF16 words at the six bound coordinates only'
    raw_values_are_direct = $true
    derived_values_reported_as_raw = $false
    nearest_even_claimed = $false
    conversion_exact = $false
    export_mapping_exact = $false
    cli_exact = $false
    ae_exact = $false
    production_change_authorized = $false
    unresolved_boundary = $unresolvedBoundary
  }})
  $exitCode = 0
}} catch {{
  if (!(Test-Path -LiteralPath $evidenceRoot -PathType Container)) {{
    New-Item -ItemType Directory -Path $evidenceRoot -ErrorAction SilentlyContinue | Out-Null
  }}
  try {{ Write-Json $statusPath (New-Failure 'fail_closed_wrapper' $_.Exception.Message) }} catch {{}}
  $exitCode = 2
}}
if (Test-Path -LiteralPath $statusPath -PathType Leaf) {{
  Get-Content -LiteralPath $statusPath -Raw
}}
exit $exitCode
"""


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def identity_constraints() -> dict[str, dict[str, str]]:
    return {
        "witness_id": {"equals": WITNESS_ID},
        "request_id": {"equals": REQUEST_ID},
        "project_id": {"equals": PROJECT_ID},
        "plugin_id": {"equals": PLUGIN_ID},
        "runtime_id": {"equals": RUNTIME_ID},
        "case_manifest_sha256": {"equals": CASE_MANIFEST_SHA256},
        "reference_manifest_sha256": {"equals": REFERENCE_MANIFEST_SHA256},
        "input_sha256": {"equals": INPUT_SHA256},
        "claim_boundary": {"equals": CLAIM_BOUNDARY},
        "unresolved_boundary": {"equals": UNRESOLVED_BOUNDARY},
    }


def event(
    case: dict[str, Any],
    suffix: str,
    fields: list[str],
    constraints: dict[str, dict[str, str]],
) -> dict[str, Any]:
    case_id = f"olmdistancegradation_extended__case_{case['code']}"
    return {
        "name": f"case_{case['code']}_{suffix.lower()}",
        "prefix": f"DG16_{case['code']}_{suffix}",
        "cardinality": {"scope": "global", "min": 1, "max": 1},
        "required_fields": [*IDENTITY_FIELDS, *fields],
        "field_constraints": {
            **identity_constraints(),
            "case_id": {"equals": case_id},
            "x": {"equals": str(case["x"])},
            "y": {"equals": str(case["y"])},
            "same_run": {"equals": "1"},
            **constraints,
        },
    }


def case_events(case: dict[str, Any]) -> list[dict[str, Any]]:
    pointer = r"^(?:0x)?(?=[0-9a-fA-F`]*[1-9a-fA-F])[0-9a-fA-F`]+$"
    words = r"^[0-9]+(?:,[0-9]+){3}$"
    bits = r"^0x[0-9a-fA-F]{8}(?:,0x[0-9a-fA-F]{8}){3}$"
    floats = r"^[^, ]+(?:,[^, ]+){3}$"
    common = ["stage", "hook_rva", "x", "y", "output_addr", "same_run"]
    return [
        event(case, "ENTRY", [
            *common, "in_out", "inside_threshold", "outside_threshold",
            "use_bg", "invert", "render_mode", "interp_mode", "power_bits",
        ], {
            "stage": {"equals": "entry"}, "hook_rva": {"equals": "1170480"},
            "output_addr": {"pattern": pointer},
            "in_out": {"equals": str(case["in_out"])},
            "inside_threshold": {"equals": str(case["inside_threshold"])},
            "outside_threshold": {"equals": str(case["outside_threshold"])},
            "use_bg": {"equals": str(case["use_bg"])},
            "invert": {"equals": str(case["invert"])},
            "render_mode": {"equals": str(case["render_mode"])},
            "interp_mode": {"equals": str(case["interp_mode"])},
            "power_bits": {"equals": case["power_bits"]},
        }),
        event(case, "FIELD", [
            *common, "field_addr", "field_words_agrb",
            "direct_field_staging_word", "capture_semantics",
        ], {
            "stage": {"equals": "direct_field_read"},
            "hook_rva": {"equals": "117057d"},
            "output_addr": {"pattern": pointer}, "field_addr": {"pattern": pointer},
            "field_words_agrb": {"pattern": words},
            "direct_field_staging_word": {"pattern": r"^[0-9]+$"},
            "capture_semantics": {"equals": "direct_memory_read_not_derived"},
        }),
        event(case, "SOURCE", [
            *common, "source_addr", "source_words_agrb", "capture_semantics",
        ], {
            "stage": {"equals": "direct_source_read"},
            "hook_rva": {"equals": "11705f1"},
            "output_addr": {"pattern": pointer}, "source_addr": {"pattern": pointer},
            "source_words_agrb": {"pattern": words},
            "capture_semantics": {"equals": "direct_memory_read_not_derived"},
        }),
        event(case, "PRESTORE", [
            *common, "pre_store_argb_f32_bits", "pre_store_argb_f32",
            "capture_semantics",
        ], {
            "stage": {"equals": "direct_pre_store"},
            "hook_rva": {"equals": "11707f4"},
            "output_addr": {"pattern": pointer},
            "pre_store_argb_f32_bits": {"pattern": bits},
            "pre_store_argb_f32": {"pattern": floats},
            "capture_semantics": {
                "equals": "direct_register_bits_before_pf16_scale"
            },
        }),
        event(case, "STORED", [
            *common, "stored_pf16_words_agrb", "capture_semantics",
        ], {
            "stage": {"equals": "direct_stored_pf16"},
            "hook_rva": {"equals": "117082b"},
            "output_addr": {"pattern": pointer},
            "stored_pf16_words_agrb": {"pattern": words},
            "capture_semantics": {
                "equals": "direct_output_memory_after_four_stores"
            },
        }),
    ]


def spec() -> dict[str, Any]:
    cases = []
    events: list[dict[str, Any]] = []
    for case in CASES:
        case_id = f"olmdistancegradation_extended__case_{case['code']}"
        cases.append({
            "id": case_id,
            "bits_per_channel": 16,
            "cdb_template": "probe.cdb.in",
            "template_values": {
                "event_prefix": f"DG16_{case['code']}",
                "x": case["x"],
                "y": case["y"],
                "witness_id": WITNESS_ID,
                "request_id": REQUEST_ID,
                "project_id": PROJECT_ID,
                "plugin_id": PLUGIN_ID,
                "runtime_id": RUNTIME_ID,
                "case_manifest_sha256": CASE_MANIFEST_SHA256,
                "reference_manifest_sha256": REFERENCE_MANIFEST_SHA256,
                "input_sha256": INPUT_SHA256,
                "claim_boundary": CLAIM_BOUNDARY,
                "unresolved_boundary": UNRESOLVED_BOUNDARY,
            },
            "addresses": {
                "entry": "0x1170480",
                "field_read": "0x117057d",
                "source_read": "0x11705f1",
                "pre_store": "0x11707f4",
                "stored": "0x117082b",
            },
        })
        events.extend(case_events(case))
    return {
        "schema_version": 1,
        "description": (
            "Six-case canonical Windows 2025 AEX direct PF16 field/source, "
            "pre-store register, and stored-word boundary capture. No derived "
            "conversion or AE-exact claim."
        ),
        "request_id": REQUEST_ID,
        "run_id_prefix": "olmdg-pf16-direct-r1",
        "plugin": {
            "name": "OLM Distance Gradation",
            "module_filename": "DistanceGradation.aex",
            "aex_sha256": AEX_SHA256,
            "default_aex_path": (
                "C:\\Program Files\\Adobe\\Common\\Plug-ins\\7.0\\MediaCore"
                "\\OLM\\DistanceGradation.aex"
            ),
        },
        "host": {
            "afterfx_path": (
                "C:\\Program Files\\Adobe\\Adobe After Effects 2025"
                "\\Support Files\\AfterFX.exe"
            ),
            "cdb_path": (
                "C:\\Program Files (x86)\\Windows Kits\\10"
                "\\Debuggers\\x64\\cdb.exe"
            ),
        },
        "project": {
            "bits_per_channel": 16,
            "renderer": "Software",
            "environment": {
                "OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT": "1",
                "OLM_AE_FORCE_SOFTWARE": "1",
            },
        },
        "renderer": {"source": "renderer.jsx"},
        "request_assets": {"source": "request"},
        "cdb": {
            "armed_marker": "OLMDG_PF16_DIRECT_BREAKPOINTS_ARMED",
            "arm_timeout_seconds": 60,
            "capture_timeout_seconds": 600,
        },
        "cases": cases,
        "validation": {
            "identity_fields": IDENTITY_FIELDS,
            "events": events,
        },
        "return_bundle": {
            "json_name": "RETURN_OLMDISTANCEGRADATION_PF16_BOUNDARY.json",
            "zip_name": "RETURN_OLMDISTANCEGRADATION_PF16_BOUNDARY.zip",
            "include_logs": [],
        },
    }


def verify_sources() -> None:
    request = SOURCE_REQUEST / "request_manifest.json"
    reference = SOURCE_REQUEST / "reference_manifest.json"
    if sha256_file(request) != CASE_MANIFEST_SHA256:
        raise RuntimeError("canonical request manifest drifted")
    if sha256_file(reference) != REFERENCE_MANIFEST_SHA256:
        raise RuntimeError("canonical reference manifest drifted")
    request_doc = json.loads(request.read_text(encoding="utf-8-sig"))
    rows = {row["id"]: row for row in request_doc["cases"]}
    for case in CASES:
        case_id = f"olmdistancegradation_extended__case_{case['code']}"
        input_path = SOURCE_REQUEST / "input" / rows[case_id]["before_effects_frame"]
        if sha256_file(input_path) != INPUT_SHA256:
            raise RuntimeError(f"canonical input drifted for {case_id}")


def prepare_sources(work: Path) -> Path:
    verify_sources()
    spec_root = work / "spec"
    shutil.copytree(SOURCE_REQUEST, spec_root / "request")
    shutil.copy2(SOURCE_RENDERER, spec_root / "renderer.jsx")
    (spec_root / "probe.cdb.in").write_text(
        CDB_TEMPLATE, encoding="ascii", newline="\n"
    )
    spec_path = spec_root / "witness-spec.json"
    spec_path.write_bytes(canonical_json(spec()))
    return spec_path


def finalize_compiled_package(package_dir: Path, package_zip: Path) -> None:
    (package_dir / "run.ps1").write_text(
        FAIL_CLOSED_RUNNER, encoding="ascii", newline="\n"
    )
    readme_path = package_dir / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    readme += f"""

## Claim boundary

An `answered` result proves only direct Windows runtime observations from the
hash-pinned AEX at the six contract coordinates: PF16 field/source memory
words, normalized pre-store float32 register bits, and post-store PF16 output
memory. These are raw CDB observations, not values derived from a PNG, float
model, nearest-even rule, or Mac implementation.

`{UNRESOLVED_BOUNDARY}` remains unresolved. In particular, this child does not
claim the upstream field-pack conversion, true16 export mapping, CLI exactness,
AE exactness, or authorization for a production change.

Run `run.ps1`. The wrapper emits only direct regular evidence files for the
consolidated v2 parent. It never changes Adobe preferences or caches, clears
modal state, or performs broad AfterFX cleanup.
"""
    readme_path.write_text(readme, encoding="utf-8", newline="\n")
    package_manifest_path = package_dir / "package-manifest.json"
    generated = json.loads(package_manifest_path.read_text(encoding="utf-8"))
    inventory = []
    for path in sorted(
        (
            item for item in package_dir.rglob("*")
            if item.is_file() and item != package_manifest_path
        ),
        key=lambda item: item.relative_to(package_dir).as_posix(),
    ):
        inventory.append({
            "path": path.relative_to(package_dir).as_posix(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        })
    final_manifest = {
        "schema_version": 1,
        "kind": "windows_witness_generated_package",
        "request_id": REQUEST_ID,
        "contract": "witness-contract.json",
        "entrypoint": "run.ps1",
        "claim_boundary": CLAIM_BOUNDARY,
        "unresolved_boundary": UNRESOLVED_BOUNDARY,
        "case_manifest_sha256": CASE_MANIFEST_SHA256,
        "reference_manifest_sha256": REFERENCE_MANIFEST_SHA256,
        "files": inventory,
    }
    if "queue" in generated:
        final_manifest["queue"] = generated["queue"]
    package_manifest_path.write_bytes(canonical_json(final_manifest))
    deterministic_zip(package_dir, package_zip)


def build_bytes(work: Path) -> tuple[bytes, bytes, bytes]:
    spec_path = prepare_sources(work)
    package_dir = work / "compiled"
    package_zip = work / "package.zip"
    compile_witness(spec_path, package_dir, package_zip)
    finalize_compiled_package(package_dir, package_zip)
    package = package_zip.read_bytes()
    package_sha = sha256_bytes(package)
    manifest = {
        "schema": "windows_codex_batch_job_v1",
        "job_id": JOB_ID,
        "package": "package.zip",
        "package_sha256": package_sha,
        "entrypoint": "run.ps1",
        "failure_policy": "independent",
        "success_status": "answered",
        "failure_status": "exact_bind_failure",
        "request_id": REQUEST_ID,
        "description": (
            "Pinned OLMDistanceGradation 2025 AEX direct PF16 field/source, "
            "pre-store register and stored-word evidence for cases "
            "0012/0014/0024/0025/0026/0027. Conversion, export, CLI and AE "
            "exactness remain unresolved."
        ),
    }
    return (
        package,
        canonical_json(manifest),
        f"{package_sha}  package.zip\n".encode("ascii"),
    )


def result(package: bytes) -> dict[str, Any]:
    return {
        "status": "verified",
        "job_id": JOB_ID,
        "request_id": REQUEST_ID,
        "package_sha256": sha256_bytes(package),
        "claim_boundary": CLAIM_BOUNDARY,
        "unresolved_boundary": UNRESOLVED_BOUNDARY,
        "target": str(TARGET),
    }


def build_target() -> dict[str, Any]:
    if TARGET.exists():
        raise RuntimeError(f"immutable target already exists: {TARGET}; use --verify")
    with tempfile.TemporaryDirectory(prefix="olmdg_pf16_child_") as tmp:
        built = build_bytes(Path(tmp))
    TARGET.mkdir(parents=True)
    for name, data in zip(
        ("package.zip", "job_manifest.json", "package.zip.sha256"), built
    ):
        (TARGET / name).write_bytes(data)
    return result(built[0])


def verify_target() -> dict[str, Any]:
    paths = (
        TARGET / "package.zip",
        TARGET / "job_manifest.json",
        TARGET / "package.zip.sha256",
    )
    if any(not path.is_file() for path in paths):
        raise RuntimeError("immutable child target is incomplete")
    with tempfile.TemporaryDirectory(prefix="olmdg_pf16_verify_") as tmp:
        expected = build_bytes(Path(tmp))
    actual = tuple(path.read_bytes() for path in paths)
    if actual != expected:
        raise RuntimeError("immutable child target drifted from deterministic build")
    return result(actual[0])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    value = verify_target() if args.verify else build_target()
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
