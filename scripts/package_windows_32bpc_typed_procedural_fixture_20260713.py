#!/usr/bin/env python3
"""Materialize the Windows 32bpc typed-procedural AE fixture package."""

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
PACKAGE_STEM = "olm_windows_32bpc_typed_procedural_fixture_20260713"
SUPPORT_DIR = ROOT / "refs" / "runtime_trace_support" / PACKAGE_STEM
OUTPUT_ZIP = SUPPORT_DIR / f"{PACKAGE_STEM}.zip"
FIXTURE_JSX = ROOT / "scripts" / "ae_generate_32bpc_typed_procedural_fixture.jsx"
COMPARE_FLOAT = ROOT / "scripts" / "compare_float_exr.py"
VERIFY_FLOAT = ROOT / "scripts" / "verify_32bpc_float_return.py"
CONFORMANCE_NOTE = ROOT / "refs" / "conformance" / "olmcolorkey_toondilate_32bpc_typed_procedural_fixture_package_20260713.md"
DESIGN_NOTE = ROOT / "refs" / "conformance" / "olmcolorkey_toondilate_32bpc_typed_procedural_fixture_design_20260713.md"
OUTPUT_TEMPLATE = "OLM EXR 32 Float"
REQUIRED_AE = "26.3"

SOURCE_LAYERS = [
    {"name": "solid_background", "kind": "solid", "bounds": [0, 0, 64, 64], "rgb": [0, 0, 0], "alpha": 1.0},
    {"name": "rect_integer_a25", "kind": "solid", "bounds": [4, 4, 20, 16], "rgb": [1, 0, 0], "alpha": 0.25},
    {"name": "rect_integer_a50", "kind": "solid", "bounds": [28, 4, 20, 16], "rgb": [0, 1, 0], "alpha": 0.5},
    {"name": "rect_integer_a75", "kind": "solid", "bounds": [4, 28, 20, 16], "rgb": [0, 0, 1], "alpha": 0.75},
    {"name": "rect_integer_a100", "kind": "solid", "bounds": [28, 28, 20, 16], "rgb": [1, 1, 1], "alpha": 1.0},
]

FIXTURE_CONTRACT = {
    "manifest_kind": "olm_32bpc_typed_procedural_fixture",
    "project_bits_per_channel": 32,
    "working_space": "None",
    "linear_blending": False,
    "dimensions": [64, 64],
    "frame": 0,
    "source_policy": "AE-generated solids only; no footage imported",
    "render_policy": "same comp, only branch enabled state changes",
    "source_layers": SOURCE_LAYERS,
    "output_names": {
        "no_effect": "effect_no_effect_00000.exr",
        "effect_on": "effect_effect_on_00000.exr",
    },
}

CASES = [
    {
        "id": "olmcolorkey_typed_procedural_64x64",
        "effect": "OLM Color Key",
        "plugin_name": "OLMColorKey.aex",
        "plugin_sha256": "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c",
    },
    {
        "id": "olmtoondilate_typed_procedural_64x64",
        "effect": "OLM Toon Dilate",
        "plugin_name": "OLMToonDilate.aex",
        "plugin_sha256": "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def contract_markdown() -> str:
    return """# Windows 32bpc Typed Procedural Fixture Package Contract

Scope: package a fail-closed Windows runner around the existing
`ae_generate_32bpc_typed_procedural_fixture.jsx` contract without touching the
fixture generator itself.

## Audited facts from the existing fixture

- source pixels are generated entirely inside AE from one black solid plus four
  integer-bounded solids at `64x64`
- the render contract is fixed to `32bpc`, working space `None`, and linear
  blending `false`
- the control/effect comparison is rendered from one comp by toggling only the
  enabled state of two precomp layers
- the JSX refuses stale outputs, unsupported effects, imported footage, and
  project-state drift
- the JSX also requires an empty AE project and empty render queue

## Packaging consequence

Because the JSX saves a project and fails if AE is not empty, the Windows
runner must fail closed when `AfterFX.exe` is already running and must kill the
fresh AE process after each case. Each effect therefore runs in its own clean
AE process.

## Packaged behavior

The package contains:

- the exact audited fixture JSX
- a PowerShell runner for Windows AE 26.3
- a generic render-record template
- a standalone raw-float EXR comparator plus EXR verifier helpers

The runner hashes the caller-supplied `OLMColorKey.aex` and
`OLMToonDilate.aex`, renders both `no_effect` and `effect_on` for each effect,
verifies the returned fixture manifest against the expected `64x64` source
recipe, records SHA-256 values for every output, and emits
`return_manifest.json`.

The packaged comparator accepts two render records, typically one macOS
reference record and one Windows return record, and fails closed unless:

- both records declare the same fixture contract and fixture JSX SHA-256
- both records declare `32bpc`, working space `None`, linear blending `false`,
  and output template `OLM EXR 32 Float`
- both records contain the same effect case set
- each referenced EXR is present, uncompressed, FLOAT, RGBA, and `64x64`
- both `no_effect` and `effect_on` outputs are raw-float-bit exact per case
"""


def readme() -> str:
    return f"""# Windows 32bpc typed procedural fixture

Run this package on Windows from a clean AE session:

`powershell -ExecutionPolicy Bypass -File .\\run_windows_typed_procedural_fixture_20260713.ps1 -AfterFX <AfterFX.exe> -ColorKeyAex <OLMColorKey.aex> -ToonDilateAex <OLMToonDilate.aex>`

The runner refuses to proceed if `AfterFX.exe` is already running. That is
intentional: the bundled JSX requires an empty project and empty render queue,
so each effect case is rendered in its own fresh AE process and the process is
stopped after the case completes.

Outputs:

- `run\\cases\\...\\effect_no_effect_00000.exr`
- `run\\cases\\...\\effect_effect_on_00000.exr`
- `run\\return_manifest.json`
- `olm_windows_32bpc_typed_procedural_fixture_return.zip`

Cross-host compare after a macOS reference record exists:

`python compare_cross_host_typed_procedural_fixture.py <mac_record_dir_or_zip> <windows_return_dir_or_zip> --json`

The compare helper fails closed unless both hosts used the same bundled fixture
contract and both EXR outputs are raw-float-bit exact for `no_effect` and
`effect_on`.
"""


def package_manifest() -> dict[str, Any]:
    return {
        "kind": "olm_windows_32bpc_typed_procedural_request",
        "schema": 1,
        "package": PACKAGE_STEM,
        "created_at": "2026-07-13",
        "required_ae_major_minor": REQUIRED_AE,
        "output_template": OUTPUT_TEMPLATE,
        "fixture_jsx": {
            "path": "fixture/ae_generate_32bpc_typed_procedural_fixture.jsx",
            "sha256": sha256(FIXTURE_JSX),
        },
        "fixture_contract": FIXTURE_CONTRACT,
        "cases": CASES,
        "runner": {
            "entrypoint": "run_windows_typed_procedural_fixture_20260713.ps1",
            "return_manifest": "RETURN_MANIFEST_TEMPLATE.json",
        },
        "compare_helper": {
            "entrypoint": "compare_cross_host_typed_procedural_fixture.py",
            "mode": "raw-float-bits-exact",
            "requires": [
                "one macOS render record or zip",
                "one Windows render record or zip",
            ],
        },
        "fail_closed": [
            "reject running AfterFX process before launch",
            "reject plugin hash mismatch",
            "reject AE version drift outside 26.3",
            "reject missing or contract-drifted fixture manifest",
            "reject missing no-effect/effect-on EXR outputs",
            "reject compare unless both records share the same fixture JSX and contract",
            "reject compare unless both no-effect and effect-on EXRs are raw-float-bit exact",
        ],
    }


def return_manifest_template(platform: str, role: str) -> dict[str, Any]:
    return {
        "kind": "olm_32bpc_typed_procedural_render_record",
        "schema": 1,
        "platform": platform,
        "record_role": role,
        "required_ae_major_minor": REQUIRED_AE,
        "ae_version": "",
        "output_template": OUTPUT_TEMPLATE,
        "fixture_jsx_sha256": sha256(FIXTURE_JSX),
        "cases": [
            {
                "id": case["id"],
                "effect": case["effect"],
                "plugin": {
                    "name": case["plugin_name"],
                    "path": "",
                    "sha256": case["plugin_sha256"] if platform == "windows" else "",
                },
                "fixture_contract": FIXTURE_CONTRACT,
                "outputs": {
                    "no_effect": {"path": "", "sha256": ""},
                    "effect_on": {"path": "", "sha256": ""},
                },
            }
            for case in CASES
        ],
    }


def compare_helper() -> str:
    return """#!/usr/bin/env python3
\"\"\"Fail-closed compare for typed-procedural 32bpc render records.\"\"\"

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "fixture"))

from compare_float_exr import compare  # noqa: E402
from verify_32bpc_float_return import VerificationError, inspect_float_rgba_exr  # noqa: E402


EXPECTED_KIND = "olm_32bpc_typed_procedural_render_record"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_zip(path: Path) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if path.is_dir():
        return path.resolve(), None
    if path.is_file() and path.suffix.lower() == ".zip":
        temp = tempfile.TemporaryDirectory(prefix="typed_proc_compare_")
        root = Path(temp.name)
        with zipfile.ZipFile(path) as archive:
            archive.extractall(root)
        children = [item for item in root.iterdir()]
        if len(children) == 1 and children[0].is_dir():
            return children[0], temp
        return root, temp
    if path.is_file() and path.suffix.lower() == ".json":
        return path.parent.resolve(), None
    raise VerificationError(f"unsupported compare input: {path}")


def load_record(locator: Path) -> tuple[dict[str, Any], Path, tempfile.TemporaryDirectory[str] | None]:
    root, temp = extract_zip(locator)
    candidates = []
    if locator.is_file() and locator.suffix.lower() == ".json":
        candidates.append(locator.resolve())
    candidates.extend(
        path
        for name in ("return_manifest.json", "reference_manifest.json", "render_record.json")
        for path in root.rglob(name)
    )
    if not candidates:
        raise VerificationError(f"{locator}: no render record found")
    record_path = sorted(candidates)[0]
    payload = json.loads(record_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict) or payload.get("kind") != EXPECTED_KIND:
        raise VerificationError(f"{record_path}: unexpected record kind")
    return payload, record_path.parent, temp


def require_case_map(record: dict[str, Any], root: Path) -> dict[str, dict[str, Any]]:
    if record.get("schema") != 1:
        raise VerificationError("render record schema must be 1")
    if record.get("required_ae_major_minor") != "26.3":
        raise VerificationError("render record must pin AE 26.3")
    if record.get("output_template") != "OLM EXR 32 Float":
        raise VerificationError("render record must pin OLM EXR 32 Float")
    platform = record.get("platform")
    if platform not in {"windows", "macos"}:
        raise VerificationError("render record platform must be windows or macos")
    if not isinstance(record.get("fixture_jsx_sha256"), str) or len(record["fixture_jsx_sha256"]) != 64:
        raise VerificationError("render record fixture_jsx_sha256 missing or invalid")
    cases = record.get("cases")
    if not isinstance(cases, list) or not cases:
        raise VerificationError("render record has no cases")
    output: dict[str, dict[str, Any]] = {}
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise VerificationError("case id is required")
        if not isinstance(case.get("effect"), str) or not case["effect"]:
            raise VerificationError(f"{case.get('id')}: effect is required")
        plugin = case.get("plugin")
        if not isinstance(plugin, dict) or not isinstance(plugin.get("name"), str):
            raise VerificationError(f"{case['id']}: plugin metadata is required")
        contract = case.get("fixture_contract")
        if not isinstance(contract, dict):
            raise VerificationError(f"{case['id']}: fixture_contract is required")
        required_pairs = {
            "manifest_kind": "olm_32bpc_typed_procedural_fixture",
            "project_bits_per_channel": 32,
            "working_space": "None",
            "linear_blending": False,
            "frame": 0,
            "source_policy": "AE-generated solids only; no footage imported",
            "render_policy": "same comp, only branch enabled state changes",
        }
        for key, expected in required_pairs.items():
            if contract.get(key) != expected:
                raise VerificationError(f"{case['id']}: fixture_contract.{key} mismatch")
        if contract.get("dimensions") != [64, 64]:
            raise VerificationError(f"{case['id']}: fixture dimensions must be [64, 64]")
        if contract.get("output_names") != {
            "no_effect": "effect_no_effect_00000.exr",
            "effect_on": "effect_effect_on_00000.exr",
        }:
            raise VerificationError(f"{case['id']}: fixture output names mismatch")
        layers = contract.get("source_layers")
        if not isinstance(layers, list) or len(layers) != 5:
            raise VerificationError(f"{case['id']}: fixture source_layers mismatch")
        outputs = case.get("outputs")
        if not isinstance(outputs, dict):
            raise VerificationError(f"{case['id']}: outputs object missing")
        normalized_outputs: dict[str, dict[str, Any]] = {}
        for name in ("no_effect", "effect_on"):
            row = outputs.get(name)
            if not isinstance(row, dict):
                raise VerificationError(f"{case['id']}: outputs.{name} missing")
            rel = row.get("path")
            stated_sha = row.get("sha256")
            if not isinstance(rel, str) or not rel:
                raise VerificationError(f"{case['id']}: outputs.{name}.path missing")
            if not isinstance(stated_sha, str) or len(stated_sha) != 64:
                raise VerificationError(f"{case['id']}: outputs.{name}.sha256 missing")
            path = (root / rel).resolve()
            if not path.is_file():
                raise VerificationError(f"{case['id']}: outputs.{name} file missing: {rel}")
            actual_sha = sha256(path)
            if actual_sha != stated_sha.lower():
                raise VerificationError(f"{case['id']}: outputs.{name} sha256 mismatch")
            inspected = inspect_float_rgba_exr(path, expected_dimensions=(64, 64))
            normalized_outputs[name] = {
                "path": path,
                "sha256": actual_sha,
                "inspection": inspected,
            }
        output[case["id"]] = {
            "id": case["id"],
            "effect": case["effect"],
            "plugin": plugin,
            "fixture_contract": contract,
            "outputs": normalized_outputs,
        }
    return output


def compare_records(left_record: dict[str, Any], left_root: Path, right_record: dict[str, Any], right_root: Path) -> dict[str, Any]:
    if left_record.get("platform") == right_record.get("platform"):
        raise VerificationError("compare requires two different platforms")
    if left_record.get("fixture_jsx_sha256") != right_record.get("fixture_jsx_sha256"):
        raise VerificationError("fixture_jsx_sha256 mismatch between hosts")
    left_cases = require_case_map(left_record, left_root)
    right_cases = require_case_map(right_record, right_root)
    if set(left_cases) != set(right_cases):
        raise VerificationError("case sets differ between records")
    results = []
    for case_id in sorted(left_cases):
        left_case = left_cases[case_id]
        right_case = right_cases[case_id]
        if left_case["effect"] != right_case["effect"]:
            raise VerificationError(f"{case_id}: effect name mismatch")
        if left_case["fixture_contract"] != right_case["fixture_contract"]:
            raise VerificationError(f"{case_id}: fixture contract mismatch")
        no_effect = compare(left_case["outputs"]["no_effect"]["path"], right_case["outputs"]["no_effect"]["path"])
        effect_on = compare(left_case["outputs"]["effect_on"]["path"], right_case["outputs"]["effect_on"]["path"])
        left_delta = compare(left_case["outputs"]["no_effect"]["path"], left_case["outputs"]["effect_on"]["path"])
        right_delta = compare(right_case["outputs"]["no_effect"]["path"], right_case["outputs"]["effect_on"]["path"])
        if no_effect["mismatched_values"] != 0:
            raise VerificationError(f"{case_id}: no_effect is not raw-float-bit exact across hosts")
        if effect_on["mismatched_values"] != 0:
            raise VerificationError(f"{case_id}: effect_on is not raw-float-bit exact across hosts")
        results.append(
            {
                "id": case_id,
                "effect": left_case["effect"],
                "platforms": [left_record["platform"], right_record["platform"]],
                "no_effect_cross_host": no_effect,
                "effect_on_cross_host": effect_on,
                "left_internal_delta": left_delta,
                "right_internal_delta": right_delta,
                "status": "raw-float-bits-exact",
            }
        )
    return {
        "status": "pass",
        "fixture_jsx_sha256": left_record["fixture_jsx_sha256"],
        "platforms": [left_record["platform"], right_record["platform"]],
        "cases": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    temp_objects: list[tempfile.TemporaryDirectory[str]] = []
    try:
        left_record, left_root, left_temp = load_record(args.left)
        right_record, right_root, right_temp = load_record(args.right)
        if left_temp is not None:
            temp_objects.append(left_temp)
        if right_temp is not None:
            temp_objects.append(right_temp)
        result = compare_records(left_record, left_root, right_record, right_root)
    except (OSError, ValueError, KeyError, VerificationError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    finally:
        for temp in temp_objects:
            temp.cleanup()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for case in result["cases"]:
            print(
                f"[PASS] {case['id']} no_effect={case['no_effect_cross_host']['mismatched_values']} "
                f"effect_on={case['effect_on_cross_host']['mismatched_values']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def runner_ps1() -> str:
    cases_json = json.dumps(CASES, separators=(",", ":"))
    contract_json = json.dumps(FIXTURE_CONTRACT, separators=(",", ":"))
    jsx_sha = sha256(FIXTURE_JSX)
    return rf"""param(
  [Parameter(Mandatory=$true)][string]$AfterFX,
  [Parameter(Mandatory=$true)][string]$ColorKeyAex,
  [Parameter(Mandatory=$true)][string]$ToonDilateAex,
  [Parameter(Mandatory=$false)][string]$OutputDir = "",
  [Parameter(Mandatory=$false)][int]$TimeoutSeconds = 300
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $PSCommandPath
$FixtureJsx = Join-Path $PackageRoot "fixture\ae_generate_32bpc_typed_procedural_fixture.jsx"
$RunRoot = if ($OutputDir) {{ $OutputDir }} else {{ Join-Path $PackageRoot "run" }}
$ReturnJson = Join-Path $RunRoot "return_manifest.json"
$ExpectedTemplate = "{OUTPUT_TEMPLATE}"
$ExpectedAe = "{REQUIRED_AE}"
$FixtureSha = "{jsx_sha}"
$ExpectedContract = ConvertFrom-Json @'
{contract_json}
'@
$Cases = ConvertFrom-Json @'
{cases_json}
'@

function Write-Json([string]$Path, $Value) {{
  $Value | ConvertTo-Json -Depth 50 | Set-Content -Encoding UTF8 $Path
}}

function Fail([string]$Status, [string]$Message) {{
  New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
  Write-Json $ReturnJson ([ordered]@{{
    kind = "olm_32bpc_typed_procedural_render_record"
    schema = 1
    platform = "windows"
    record_role = "return"
    status = $Status
    error = $Message
    required_ae_major_minor = $ExpectedAe
    output_template = $ExpectedTemplate
    fixture_jsx_sha256 = $FixtureSha
    cases = @()
  }})
  throw "$Status`: $Message"
}}

function Wait-ForFile([string]$Path, [int]$Seconds) {{
  $deadline = (Get-Date).AddSeconds($Seconds)
  while ((Get-Date) -lt $deadline) {{
    if (Test-Path -LiteralPath $Path -PathType Leaf) {{ return }}
    Start-Sleep -Milliseconds 500
  }}
  throw "timeout waiting for $Path"
}}

function Stop-AfterFX {{
  Get-Process -Name "AfterFX" -ErrorAction SilentlyContinue | Stop-Process -Force
  Start-Sleep -Seconds 2
}}

if (Get-Process -Name "AfterFX" -ErrorAction SilentlyContinue) {{
  Fail "afterfx_running" "Close After Effects before running the typed procedural package"
}}
foreach ($path in @($AfterFX, $FixtureJsx)) {{
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {{
    Fail "missing_asset" "Missing packaged runner asset or tool: $path"
  }}
}}
$PluginMap = @{{
  "OLMColorKey.aex" = $ColorKeyAex
  "OLMToonDilate.aex" = $ToonDilateAex
}}
$PluginRecords = @{{}}
foreach ($case in $Cases) {{
  $pluginPath = $PluginMap[$case.plugin_name]
  if (-not (Test-Path -LiteralPath $pluginPath -PathType Leaf)) {{
    Fail "missing_plugin" "$($case.plugin_name) missing"
  }}
  $hash = (Get-FileHash -LiteralPath $pluginPath -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($hash -ne $case.plugin_sha256) {{
    Fail "plugin_hash_mismatch" "$($case.plugin_name) sha256 $hash != $($case.plugin_sha256)"
  }}
  $PluginRecords[$case.id] = [ordered]@{{
    name = $case.plugin_name
    path = (Resolve-Path $pluginPath).Path
    sha256 = $hash
  }}
}}

New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
$Records = @()
$LastAeVersion = ""
foreach ($case in $Cases) {{
  Stop-AfterFX
  if (Get-Process -Name "AfterFX" -ErrorAction SilentlyContinue) {{
    Fail "afterfx_shutdown_failed" "AfterFX still running before case $($case.id)"
  }}
  $CaseRoot = Join-Path $RunRoot ("cases\" + $case.id)
  New-Item -ItemType Directory -Force -Path $CaseRoot | Out-Null
  $ProjectPath = Join-Path $CaseRoot "fixture.aep"
  $ResultPath = Join-Path $CaseRoot "fixture_result.json"
  $ManifestPath = Join-Path $CaseRoot "fixture_manifest.json"
  foreach ($path in @($ProjectPath, $ResultPath, $ManifestPath, (Join-Path $CaseRoot "effect_no_effect_00000.exr"), (Join-Path $CaseRoot "effect_effect_on_00000.exr"))) {{
    if (Test-Path -LiteralPath $path) {{ Remove-Item -LiteralPath $path -Force }}
  }}
  $env:OLM_AE_TYPED_FIXTURE_OUTPUT_DIR = $CaseRoot
  $env:OLM_AE_TYPED_FIXTURE_TEMPLATE = $ExpectedTemplate
  $env:OLM_AE_TYPED_FIXTURE_PROJECT_PATH = $ProjectPath
  $env:OLM_AE_TYPED_FIXTURE_EFFECT = $case.effect
  $env:OLM_AE_TYPED_FIXTURE_OVERWRITE = "1"
  $process = Start-Process -FilePath $AfterFX -ArgumentList ('-r "' + $FixtureJsx + '"') -PassThru
  try {{
    Wait-ForFile $ResultPath $TimeoutSeconds
  }} catch {{
    try {{ if ($process -and -not $process.HasExited) {{ $process | Stop-Process -Force }} }} catch {{}}
    Fail "render_timeout" "$($case.id) did not produce fixture_result.json within $TimeoutSeconds seconds"
  }}
  $result = Get-Content -LiteralPath $ResultPath -Raw | ConvertFrom-Json
  if ($result.status -ne "ok") {{
    Stop-AfterFX
    Fail "render_failed" "$($case.id) returned status=$($result.status) error=$($result.error)"
  }}
  $LastAeVersion = $result.ae_version
  if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {{
    Stop-AfterFX
    Fail "missing_manifest" "$($case.id) did not produce fixture_manifest.json"
  }}
  $manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
  if ($result.ae_version -notlike "$ExpectedAe*") {{
    Stop-AfterFX
    Fail "wrong_ae_version" "$($case.id) expected AE $ExpectedAe, got $($result.ae_version)"
  }}
  if ($manifest.kind -ne $ExpectedContract.manifest_kind) {{
    Stop-AfterFX
    Fail "contract_mismatch" "$($case.id) manifest kind mismatch"
  }}
  if ($manifest.project_bits_per_channel -ne $ExpectedContract.project_bits_per_channel) {{
    Stop-AfterFX
    Fail "contract_mismatch" "$($case.id) bitsPerChannel mismatch"
  }}
  if ($manifest.working_space -ne $ExpectedContract.working_space) {{
    Stop-AfterFX
    Fail "contract_mismatch" "$($case.id) working space mismatch"
  }}
  if ([bool]$manifest.linear_blending -ne [bool]$ExpectedContract.linear_blending) {{
    Stop-AfterFX
    Fail "contract_mismatch" "$($case.id) linear blending mismatch"
  }}
  if (($manifest.dimensions | ConvertTo-Json -Compress) -ne ($ExpectedContract.dimensions | ConvertTo-Json -Compress)) {{
    Stop-AfterFX
    Fail "contract_mismatch" "$($case.id) dimensions mismatch"
  }}
  if ($manifest.frame -ne $ExpectedContract.frame) {{
    Stop-AfterFX
    Fail "contract_mismatch" "$($case.id) frame mismatch"
  }}
  if ($manifest.source_policy -ne $ExpectedContract.source_policy -or $manifest.render_policy -ne $ExpectedContract.render_policy) {{
    Stop-AfterFX
    Fail "contract_mismatch" "$($case.id) source/render policy mismatch"
  }}
  if (($manifest.source_layers | ConvertTo-Json -Depth 20 -Compress) -ne ($ExpectedContract.source_layers | ConvertTo-Json -Depth 20 -Compress)) {{
    Stop-AfterFX
    Fail "contract_mismatch" "$($case.id) source_layers mismatch"
  }}
  if (($manifest.outputs | ConvertTo-Json -Compress) -ne ($ExpectedContract.output_names | ConvertTo-Json -Compress)) {{
    Stop-AfterFX
    Fail "contract_mismatch" "$($case.id) output_names mismatch"
  }}
  $NoEffect = Join-Path $CaseRoot $ExpectedContract.output_names.no_effect
  $EffectOn = Join-Path $CaseRoot $ExpectedContract.output_names.effect_on
  foreach ($path in @($NoEffect, $EffectOn, $ProjectPath)) {{
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {{
      Stop-AfterFX
      Fail "missing_artifact" "$($case.id) missing required artifact $path"
    }}
  }}
  $Records += [ordered]@{{
    id = $case.id
    effect = $case.effect
    plugin = $PluginRecords[$case.id]
    fixture_contract = [ordered]@{{
      manifest_kind = $ExpectedContract.manifest_kind
      project_bits_per_channel = $ExpectedContract.project_bits_per_channel
      working_space = $ExpectedContract.working_space
      linear_blending = [bool]$ExpectedContract.linear_blending
      dimensions = @($ExpectedContract.dimensions)
      frame = $ExpectedContract.frame
      source_policy = $ExpectedContract.source_policy
      render_policy = $ExpectedContract.render_policy
      source_layers = $ExpectedContract.source_layers
      output_names = [ordered]@{{
        no_effect = $ExpectedContract.output_names.no_effect
        effect_on = $ExpectedContract.output_names.effect_on
      }}
    }}
    outputs = [ordered]@{{
      no_effect = [ordered]@{{
        path = (Resolve-Path $NoEffect).Path.Substring((Resolve-Path $RunRoot).Path.Length + 1).Replace("\", "/")
        sha256 = (Get-FileHash -LiteralPath $NoEffect -Algorithm SHA256).Hash.ToLowerInvariant()
      }}
      effect_on = [ordered]@{{
        path = (Resolve-Path $EffectOn).Path.Substring((Resolve-Path $RunRoot).Path.Length + 1).Replace("\", "/")
        sha256 = (Get-FileHash -LiteralPath $EffectOn -Algorithm SHA256).Hash.ToLowerInvariant()
      }}
    }}
  }}
  Stop-AfterFX
}}

$Record = [ordered]@{{
  kind = "olm_32bpc_typed_procedural_render_record"
  schema = 1
  platform = "windows"
  record_role = "return"
  status = "rendered"
  required_ae_major_minor = $ExpectedAe
  ae_version = $LastAeVersion
  output_template = $ExpectedTemplate
  fixture_jsx_sha256 = $FixtureSha
  cases = $Records
}}
Write-Json $ReturnJson $Record
$Zip = Join-Path (Split-Path $RunRoot -Parent) "olm_windows_32bpc_typed_procedural_fixture_return.zip"
if (Test-Path -LiteralPath $Zip) {{ Remove-Item -LiteralPath $Zip -Force }}
Compress-Archive -Path (Join-Path $RunRoot "*") -DestinationPath $Zip
Write-Host "OK return=$Zip"
"""


def write_support_tree(stage: Path) -> None:
    (stage / "fixture").mkdir(parents=True, exist_ok=True)
    (stage / "CONTRACT.md").write_text(contract_markdown(), encoding="utf-8")
    (stage / "README.md").write_text(readme(), encoding="utf-8")
    write_json(stage / "manifest.json", package_manifest())
    write_json(stage / "RETURN_MANIFEST_TEMPLATE.json", return_manifest_template("windows", "return"))
    write_json(stage / "MAC_REFERENCE_RECORD_TEMPLATE.json", return_manifest_template("macos", "reference"))
    (stage / "compare_cross_host_typed_procedural_fixture.py").write_text(compare_helper(), encoding="utf-8")
    (stage / "run_windows_typed_procedural_fixture_20260713.ps1").write_text(runner_ps1(), encoding="utf-8")
    shutil.copy2(FIXTURE_JSX, stage / "fixture" / FIXTURE_JSX.name)
    shutil.copy2(COMPARE_FLOAT, stage / "fixture" / COMPARE_FLOAT.name)
    shutil.copy2(VERIFY_FLOAT, stage / "fixture" / VERIFY_FLOAT.name)


def materialize(support_dir: Path, output_zip: Path) -> None:
    with tempfile.TemporaryDirectory(prefix=PACKAGE_STEM + "_") as tmp_name:
        stage = Path(tmp_name) / PACKAGE_STEM
        write_support_tree(stage)
        support_dir.parent.mkdir(parents=True, exist_ok=True)
        if support_dir.exists():
            shutil.rmtree(support_dir)
        shutil.copytree(stage, support_dir)
        output_zip.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    archive.write(path, f"{PACKAGE_STEM}/{path.relative_to(stage).as_posix()}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--support-dir", type=Path, default=SUPPORT_DIR)
    parser.add_argument("--output", type=Path, default=OUTPUT_ZIP)
    args = parser.parse_args()
    support_dir = args.support_dir if args.support_dir.is_absolute() else ROOT / args.support_dir
    output_zip = args.output if args.output.is_absolute() else ROOT / args.output
    if not FIXTURE_JSX.is_file():
        raise SystemExit(f"missing fixture JSX: {FIXTURE_JSX}")
    if not COMPARE_FLOAT.is_file() or not VERIFY_FLOAT.is_file():
        raise SystemExit("missing float compare helpers")
    if not DESIGN_NOTE.is_file():
        raise SystemExit(f"missing prerequisite design note: {DESIGN_NOTE}")
    if not CONFORMANCE_NOTE.is_file():
        raise SystemExit(f"missing prerequisite package note: {CONFORMANCE_NOTE}")
    materialize(support_dir, output_zip)
    print(f"[OK] support={support_dir} zip={output_zip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
