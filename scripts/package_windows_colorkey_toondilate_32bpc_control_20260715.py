#!/usr/bin/env python3
"""Build the single fail-closed Windows 32bpc control request package."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "package_windows_32bpc_typed_procedural_fixture_20260713.py"
FIXTURE_NAME = "ae_generate_32bpc_windows_control_fixture.jsx"
PACKAGE_STEM = "olm_windows_colorkey_toondilate_32bpc_control_20260715"
OUTPUT_ZIP = ROOT / "refs" / "runtime_trace_packages" / f"{PACKAGE_STEM}.zip"
SUPPORT_DIR = OUTPUT_ZIP.with_suffix("")
OUTPUT_MODULE_CAPTURE_API = "OutputModule.getSettings(GetSettingsFormat.STRING)"
OUTPUT_MODULE_SEMANTIC_INTENT = {
    "channels": "RGB+Alpha",
    "sample_type": "32-bit float",
    "preserve_rgb": True,
    "linear_light_conversion": False,
}
OUTPUT_MODULE_SEMANTIC_VERIFICATION = (
    "declared intent only; localized getSettings keys and values are captured verbatim and not semantically parsed"
)
PENDING_REQUEST_IDS = [
    "olm_bitdepth_32bpc_colorkey_float_20260710",
    "olm_bitdepth_32bpc_toondilate_float_20260710",
]

SOURCE_LAYERS = [
    {"name": "solid_background", "kind": "solid", "bounds": [0, 0, 64, 64], "rgb": [0, 0, 0], "alpha": 1.0},
    {"name": "rect_integer_a25", "kind": "solid", "bounds": [4, 4, 20, 16], "rgb": [1, 0, 0], "alpha": 0.25},
    {"name": "rect_integer_a50", "kind": "solid", "bounds": [28, 4, 20, 16], "rgb": [0, 1, 0], "alpha": 0.5},
    {"name": "rect_integer_a75", "kind": "solid", "bounds": [4, 28, 20, 16], "rgb": [0, 0, 1], "alpha": 0.75},
    {"name": "rect_integer_a100", "kind": "solid", "bounds": [28, 28, 20, 16], "rgb": [1, 1, 1], "alpha": 1.0},
]

CASES = [
    {
        "id": "olmcolorkey_typed_procedural_64x64",
        "effect": "OLM Color Key",
        "plugin_name": "OLMColorKey.aex",
        "plugin_sha256": "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c",
        "mac_plugin_name": "OLMColorKey.plugin",
    },
    {
        "id": "olmtoondilate_typed_procedural_64x64",
        "effect": "OLM Toon Dilate",
        "plugin_name": "OLMToonDilate.aex",
        "plugin_sha256": "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3",
        "mac_plugin_name": "OLMToonDilate.plugin",
    },
]


def load_base():
    spec = importlib.util.spec_from_file_location("base_typed_package", BASE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {BASE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, anchor: str, replacement: str, label: str) -> str:
    if anchor not in text:
        raise RuntimeError(f"{label} anchor drifted")
    return text.replace(anchor, replacement, 1)


def fixture_source(base: Path) -> str:
    source = base.read_text(encoding="utf-8")

    stable_capture_helpers = r'''

    function stableJson(value) {
        if (value === null) return "null";
        var kind = typeof value;
        if (kind === "string") return quote(value);
        if (kind === "number") {
            if (!isFinite(value)) fail("non-finite Output Module setting");
            return String(value);
        }
        if (kind === "boolean") return value ? "true" : "false";
        if (value instanceof Array) {
            var arrayParts = [];
            for (var arrayIndex = 0; arrayIndex < value.length; arrayIndex++) {
                arrayParts.push(stableJson(value[arrayIndex]));
            }
            return "[" + arrayParts.join(",") + "]";
        }
        if (kind === "object") {
            var keys = [];
            for (var key in value) {
                if (value.hasOwnProperty(key)) keys.push(key);
            }
            keys.sort();
            var objectParts = [];
            for (var keyIndex = 0; keyIndex < keys.length; keyIndex++) {
                objectParts.push(quote(keys[keyIndex]) + ":" + stableJson(value[keys[keyIndex]]));
            }
            return "{" + objectParts.join(",") + "}";
        }
        fail("unsupported Output Module setting value type " + kind);
    }

    function captureOutputModuleSettings(module, outputDir, filename, template) {
        if (!module.getSettings || typeof GetSettingsFormat === "undefined" ||
            typeof GetSettingsFormat.STRING === "undefined") {
            fail("OutputModule.getSettings(GetSettingsFormat.STRING) is unavailable");
        }
        var settings = null;
        try {
            settings = module.getSettings(GetSettingsFormat.STRING);
        } catch (settingsError) {
            fail("cannot capture Output Module settings: " + settingsError.toString());
        }
        if (!settings || typeof settings !== "object") fail("Output Module settings capture is empty");
        var settingsSerialization = stableJson(settings);
        if (settingsSerialization === "{}") fail("Output Module settings capture has no fields");
        var payload = {
            kind: "olm_output_module_settings_capture",
            schema_version: 1,
            output_template: template,
            capture_api: "OutputModule.getSettings(GetSettingsFormat.STRING)",
            semantic_intent: {
                channels: "RGB+Alpha",
                sample_type: "32-bit float",
                preserve_rgb: true,
                linear_light_conversion: false
            },
            semantic_verification: "declared intent only; localized getSettings keys and values are captured verbatim and not semantically parsed",
            settings: settings
        };
        var settingsName = filename.replace(/\.exr$/i, "_output_module_settings.json");
        var settingsFile = new File(outputDir + "/" + settingsName);
        requireEmpty(settingsFile.fsName, overwrite);
        writeText(settingsFile.fsName, stableJson(payload) + "\n");
        return {path: settingsFile.fsName, name: settingsName, serialization: settingsSerialization};
    }
'''
    helper_anchor = "    function ensureFolder(path) {\n"
    if helper_anchor not in source:
        raise RuntimeError("fixture helper anchor drifted")
    source = source.replace(helper_anchor, stable_capture_helpers + "\n" + helper_anchor, 1)

    render_anchor = "        module.applyTemplate(template);\n        module.file = sequenceFile;\n"
    if render_anchor not in source:
        raise RuntimeError("fixture applyTemplate anchor drifted")
    source = source.replace(
        render_anchor,
        "        module.applyTemplate(template);\n"
        "        var settingsCapture = captureOutputModuleSettings(module, outputDir, filename, template);\n"
        "        capturedOutputModuleSettings.push(settingsCapture);\n"
        "        module.file = sequenceFile;\n",
        1,
    )

    output_dir_anchor = '    var outputDir = getenv("OLM_AE_TYPED_FIXTURE_OUTPUT_DIR");\n'
    if output_dir_anchor not in source:
        raise RuntimeError("fixture output directory anchor drifted")
    source = source.replace(output_dir_anchor, "    var capturedOutputModuleSettings = [];\n" + output_dir_anchor, 1)

    render_pair_anchor = '''        var effectOn = renderOne(renderComp, outputDir, "effect_effect_on.exr", template);

        var manifest = "{\\n" +
'''
    if render_pair_anchor not in source:
        raise RuntimeError("fixture render pair anchor drifted")
    source = source.replace(
        render_pair_anchor,
        '''        var effectOn = renderOne(renderComp, outputDir, "effect_effect_on.exr", template);
        if (capturedOutputModuleSettings.length !== 2) fail("expected two Output Module settings captures");
        if (capturedOutputModuleSettings[0].serialization !== capturedOutputModuleSettings[1].serialization) {
            fail("no-effect and effect-on Output Module settings differ");
        }

        var manifest = "{\\n" +
''',
        1,
    )

    source = source.replace(
        'project.linearBlending = false;\n',
        'project.linearBlending = false;\n'
        '        try { project.gpuAccelType = GpuAccelType.SOFTWARE; } catch (gpuError) { fail("cannot set SOFTWARE renderer: " + gpuError.toString()); }\n'
        '        if (String(project.gpuAccelType).toUpperCase() !== "SOFTWARE") fail("renderer is not SOFTWARE");\n',
        1,
    )
    source = source.replace(
        '"  \\\"linear_blending\\\": false,\\n" +\n',
        '"  \\\"linear_blending\\\": false,\\n" +\n'
        '            "  \\\"project_gpu_accel_type\\\": {\\\"current_name\\\": \\\"SOFTWARE\\\"},\\n" +\n',
        1,
    )
    output_names_anchor = '''            "    \\\"effect_on\\\": \\\"effect_effect_on_00000.exr\\\"\\n" +
            "  },\\n" +
'''
    if output_names_anchor not in source:
        raise RuntimeError("fixture output names anchor drifted")
    source = source.replace(
        output_names_anchor,
        output_names_anchor
        + '''            "  \\\"output_module\\\": {\\n" +
            "    \\\"template_name\\\": " + quote(template) + ",\\n" +
            "    \\\"capture_api\\\": \\\"OutputModule.getSettings(GetSettingsFormat.STRING)\\\",\\n" +
            "    \\\"semantic_intent\\\": {\\\"channels\\\": \\\"RGB+Alpha\\\", \\\"sample_type\\\": \\\"32-bit float\\\", \\\"preserve_rgb\\\": true, \\\"linear_light_conversion\\\": false},\\n" +
            "    \\\"semantic_verification\\\": \\\"declared intent only; localized getSettings keys and values are captured verbatim and not semantically parsed\\\",\\n" +
            "    \\\"settings_files\\\": {\\\"no_effect\\\": \\\"effect_no_effect_output_module_settings.json\\\", \\\"effect_on\\\": \\\"effect_effect_on_output_module_settings.json\\\"},\\n" +
            "    \\\"same_settings_serialization\\\": true\\n" +
            "  },\\n" +
''',
        1,
    )

    result_outputs_anchor = '        result.outputs = [noEffect.fsName, effectOn.fsName];\n'
    if result_outputs_anchor not in source:
        raise RuntimeError("fixture result outputs anchor drifted")
    source = source.replace(
        result_outputs_anchor,
        result_outputs_anchor
        + '        result.output_module_settings = [capturedOutputModuleSettings[0].path, capturedOutputModuleSettings[1].path];\n',
        1,
    )
    result_object_anchor = '        outputs: [],\n        error: ""\n'
    if result_object_anchor not in source:
        raise RuntimeError("fixture result object anchor drifted")
    source = source.replace(result_object_anchor, '        outputs: [],\n        output_module_settings: [],\n        error: ""\n', 1)
    result_json_anchor = '            "  \\\"outputs\\\": [" + (result.outputs.length ? quote(result.outputs[0]) + "," + quote(result.outputs[1]) : "") + "],\\n" +\n'
    if result_json_anchor not in source:
        raise RuntimeError("fixture result JSON anchor drifted")
    source = source.replace(
        result_json_anchor,
        result_json_anchor
        + '            "  \\\"output_module_settings\\\": [" + (result.output_module_settings.length ? quote(result.output_module_settings[0]) + "," + quote(result.output_module_settings[1]) : "") + "],\\n" +\n',
        1,
    )
    if (
        "GpuAccelType.SOFTWARE" not in source
        or "project_gpu_accel_type" not in source
        or "module.getSettings(GetSettingsFormat.STRING)" not in source
        or "same_settings_serialization" not in source
    ):
        raise RuntimeError("fixture hardening did not apply")
    return source


def request_manifest(fixture_sha: str, recipe_sha: str) -> dict[str, Any]:
    contract = {
        "manifest_kind": "olm_32bpc_typed_procedural_fixture",
        "project_bits_per_channel": 32,
        "working_space": "None",
        "linear_blending": False,
        "renderer": "SOFTWARE",
        "dimensions": [64, 64],
        "frame": 0,
        "source_policy": "AE-generated solids only; no footage imported",
        "render_policy": "same comp, only branch enabled state changes",
        "source_layers": SOURCE_LAYERS,
        "output_names": {"no_effect": "effect_no_effect_00000.exr", "effect_on": "effect_effect_on_00000.exr"},
    }
    return {
        "kind": "olm_windows_single_control_request",
        "schema": 1,
        "request_id": PACKAGE_STEM,
        "status": "request-only; no AE exact claim",
        "fulfills_request_ids": PENDING_REQUEST_IDS,
        "required_ae": {"major_minor": "26.3", "renderer": "SOFTWARE"},
        "project": {"bits_per_channel": 32, "working_space": "None", "linear_blending": False},
        "output_template": "OLM EXR 32 Float",
        "output_module_contract": {
            "capture_required": True,
            "capture_api": OUTPUT_MODULE_CAPTURE_API,
            "serialization": "recursive JSON with lexicographically sorted object keys",
            "semantic_intent": OUTPUT_MODULE_SEMANTIC_INTENT,
            "semantic_verification": OUTPUT_MODULE_SEMANTIC_VERIFICATION,
            "hash_algorithm": "sha256",
            "same_hash_required": ["no_effect_vs_effect_on_per_case", "colorkey_vs_toondilate"],
        },
        "acceptance_gate": {
            "comparison": "Windows AE Software vs Mac AE",
            "required": "max_diff=0",
            "evidence_boundary": "AE render records only; CLI/emulation is intermediate evidence",
        },
        "input_contract": {
            "kind": "ae_generated_typed_procedural_source",
            "fixture_script": FIXTURE_NAME,
            "fixture_script_sha256": fixture_sha,
            "source_recipe_sha256": recipe_sha,
            "external_footage": False,
            "same_comp_control": True,
        },
        "fixture_contract": contract,
        "cases": [
            {
                "id": case["id"],
                "effect": case["effect"],
                "fulfills_request_id": PENDING_REQUEST_IDS[index],
                "aex": {"filename": case["plugin_name"], "sha256": case["plugin_sha256"]},
                "mac_binding": {"filename": case["mac_plugin_name"]},
                "input_hashes": {"fixture_script_sha256": fixture_sha, "source_recipe_sha256": recipe_sha},
                "controls": {"no_effect": True, "effect_on": True, "output_format": "FLOAT EXR"},
            }
            for index, case in enumerate(CASES)
        ],
        "pending_request_resolution": {
            "initial_state": "pending",
            "answer_only_when": [
                "both mapped plugin cases are present and passed",
                "both no-effect FLOAT EXR controls are present and passed",
                "each no-effect/effect-on pair has one identical Output Module settings hash",
                "the settings hash is identical across both plugin cases",
            ],
            "partial_return_policy": "keep both request IDs pending; do not silently mark either answered",
        },
        "fail_closed": [
            "reject stale or missing artifacts",
            "reject any AEX filename or SHA-256 mismatch",
            "reject AE version, renderer, 32bpc, color, or output-template drift",
            "reject missing same-comp no-effect FLOAT EXR control",
            "reject unavailable, empty, or unequal applied Output Module settings captures",
            "reject imported footage or source recipe hash drift",
            "do not interpret CLI/emulation output as AE evidence",
        ],
    }


def materialize(support_dir: Path, output_zip: Path) -> None:
    base = load_base()
    with tempfile.TemporaryDirectory(prefix=PACKAGE_STEM + "_") as td:
        stage = Path(td) / PACKAGE_STEM
        base.write_support_tree(stage)
        old_fixture = stage / "fixture" / base.FIXTURE_JSX.name
        hardened = fixture_source(old_fixture)
        old_fixture.unlink()
        fixture = stage / "fixture" / FIXTURE_NAME
        fixture.write_text(hardened, encoding="utf-8")
        fixture_sha = sha256(fixture)
        recipe_sha = hashlib.sha256(json.dumps(SOURCE_LAYERS, separators=(",", ":"), sort_keys=True).encode()).hexdigest()

        manifest = request_manifest(fixture_sha, recipe_sha)
        (stage / "request").mkdir()
        (stage / "request" / "request_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (stage / "request" / "input_hashes.json").write_text(json.dumps(manifest["input_contract"], indent=2) + "\n", encoding="utf-8")
        (stage / "request" / "combined_intake_metadata.json").write_text(
            json.dumps(
                {
                    "kind": "olm_combined_pending_request_intake_binding",
                    "schema": 1,
                    "combined_request_id": PACKAGE_STEM,
                    "fulfills_request_ids": PENDING_REQUEST_IDS,
                    "case_mapping": {
                        case["id"]: PENDING_REQUEST_IDS[index] for index, case in enumerate(CASES)
                    },
                    "resolution": manifest["pending_request_resolution"],
                    "required_return_status": "rendered",
                    "required_case_count": 2,
                    "required_no_effect_control_count": 2,
                    "required_shared_output_module_settings_hash": True,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        for template_name in ("RETURN_MANIFEST_TEMPLATE.json", "MAC_REFERENCE_RECORD_TEMPLATE.json"):
            template_path = stage / template_name
            template = json.loads(template_path.read_text(encoding="utf-8"))
            template["fulfills_request_ids"] = PENDING_REQUEST_IDS
            template["pending_requests_answered"] = False
            template["pending_request_resolution_eligible"] = False
            template["output_module_settings_sha256"] = ""
            for index, case in enumerate(template["cases"]):
                case["fulfills_request_id"] = PENDING_REQUEST_IDS[index]
                case["no_effect_control_passed"] = False
                case["output_module"] = {
                    "template_name": "OLM EXR 32 Float",
                    "capture_api": OUTPUT_MODULE_CAPTURE_API,
                    "semantic_intent": OUTPUT_MODULE_SEMANTIC_INTENT,
                    "semantic_verification": OUTPUT_MODULE_SEMANTIC_VERIFICATION,
                    "settings_sha256": "",
                    "captured_settings": {},
                    "settings": {
                        "no_effect": {"path": "", "sha256": ""},
                        "effect_on": {"path": "", "sha256": ""},
                    },
                }
            template_path.write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")

        package_manifest = json.loads((stage / "manifest.json").read_text(encoding="utf-8"))
        package_manifest["package"] = PACKAGE_STEM
        package_manifest["request_manifest"] = "request/request_manifest.json"
        package_manifest["combined_intake_metadata"] = "request/combined_intake_metadata.json"
        package_manifest["fixture_jsx"] = {"path": f"fixture/{FIXTURE_NAME}", "sha256": fixture_sha}
        package_manifest["input_hashes"] = manifest["input_contract"]
        package_manifest["cases"] = manifest["cases"]
        (stage / "manifest.json").write_text(json.dumps(package_manifest, indent=2) + "\n", encoding="utf-8")

        readme = stage / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8")
            + "\nThis dated package is the single ColorKey+ToonDilate Windows control request. "
            "The request manifest binds both AEX contracts, fixture/source hashes, AE project controls, "
            "and same-comp no-effect FLOAT EXR outputs. It is evidence collection only; CLI/emulation is not AE evidence.\n"
            "Applied Output Module settings are captured through getSettings(STRING), serialized with sorted keys, "
            "and SHA-256-bound in the Windows return. RGB+Alpha, 32-bit float, Preserve RGB on, and linear-light "
            "conversion off are declared intent; localized setting labels are retained but not parsed as proof. "
            "The combined return maps to both 20260710 pending request IDs and remains non-answering until intake "
            "confirms the full two-case control gate.\n",
            encoding="utf-8",
        )

        # Keep the proven runner, but point its packaged fixture and its recorded fixture hash at this request.
        runner = stage / "run_windows_typed_procedural_fixture_20260713.ps1"
        runner_text = runner.read_text(encoding="utf-8")
        runner_text = runner_text.replace("ae_generate_32bpc_typed_procedural_fixture.jsx", FIXTURE_NAME)
        runner_text = runner_text.replace(base.sha256(base.FIXTURE_JSX), fixture_sha)
        runner_cases = [
            {
                "id": case["id"],
                "effect": case["effect"],
                "plugin_name": case["plugin_name"],
                "plugin_sha256": case["plugin_sha256"],
                "fulfills_request_id": PENDING_REQUEST_IDS[index],
            }
            for index, case in enumerate(CASES)
        ]
        runner_text = replace_once(
            runner_text,
            json.dumps(base.CASES, separators=(",", ":")),
            json.dumps(runner_cases, separators=(",", ":")),
            "runner cases",
        )
        runner_text = runner_text.replace(
            'if ([bool]$manifest.linear_blending -ne [bool]$ExpectedContract.linear_blending) {',
            'if ([bool]$manifest.linear_blending -ne [bool]$ExpectedContract.linear_blending -or $manifest.project_gpu_accel_type.current_name -ne "SOFTWARE") {',
        )
        runner_text = replace_once(
            runner_text,
            f'$FixtureSha = "{fixture_sha}"\n',
            f'$FixtureSha = "{fixture_sha}"\n'
            f'$ExpectedOutputModuleCaptureApi = "{OUTPUT_MODULE_CAPTURE_API}"\n'
            f'$ExpectedSemanticVerification = "{OUTPUT_MODULE_SEMANTIC_VERIFICATION}"\n'
            '$FulfillsRequestIds = @("olm_bitdepth_32bpc_colorkey_float_20260710", "olm_bitdepth_32bpc_toondilate_float_20260710")\n',
            "runner output module constants",
        )
        runner_text = replace_once(
            runner_text,
            "    fixture_jsx_sha256 = $FixtureSha\n    cases = @()\n",
            "    fixture_jsx_sha256 = $FixtureSha\n"
            "    fulfills_request_ids = @($FulfillsRequestIds)\n"
            "    pending_requests_answered = $false\n"
            "    pending_request_resolution_eligible = $false\n"
            "    cases = @()\n",
            "runner failure lineage",
        )
        runner_text = replace_once(
            runner_text,
            '$Records = @()\n$LastAeVersion = ""\n',
            '$Records = @()\n$LastAeVersion = ""\n$SharedOutputModuleSettingsSha256 = ""\n',
            "runner shared settings hash",
        )
        runner_text = replace_once(
            runner_text,
            'foreach ($path in @($ProjectPath, $ResultPath, $ManifestPath, (Join-Path $CaseRoot "effect_no_effect_00000.exr"), (Join-Path $CaseRoot "effect_effect_on_00000.exr"))) {',
            'foreach ($path in @($ProjectPath, $ResultPath, $ManifestPath, (Join-Path $CaseRoot "effect_no_effect_00000.exr"), (Join-Path $CaseRoot "effect_effect_on_00000.exr"), (Join-Path $CaseRoot "effect_no_effect_output_module_settings.json"), (Join-Path $CaseRoot "effect_effect_on_output_module_settings.json"))) {',
            "runner stale settings cleanup",
        )
        output_anchor = '''  $NoEffect = Join-Path $CaseRoot $ExpectedContract.output_names.no_effect
  $EffectOn = Join-Path $CaseRoot $ExpectedContract.output_names.effect_on
  foreach ($path in @($NoEffect, $EffectOn, $ProjectPath)) {
'''
        output_replacement = '''  if ($manifest.output_module.template_name -cne $ExpectedTemplate -or
      $manifest.output_module.capture_api -cne $ExpectedOutputModuleCaptureApi -or
      $manifest.output_module.semantic_verification -cne $ExpectedSemanticVerification -or
      -not [bool]$manifest.output_module.same_settings_serialization) {
    Stop-AfterFX
    Fail "output_module_contract_mismatch" "$($case.id) Output Module capture metadata mismatch"
  }
  $intent = $manifest.output_module.semantic_intent
  if ($intent.channels -cne "RGB+Alpha" -or $intent.sample_type -cne "32-bit float" -or
      -not [bool]$intent.preserve_rgb -or [bool]$intent.linear_light_conversion) {
    Stop-AfterFX
    Fail "output_module_intent_mismatch" "$($case.id) Output Module semantic intent mismatch"
  }
  if ($manifest.output_module.settings_files.no_effect -cne "effect_no_effect_output_module_settings.json" -or
      $manifest.output_module.settings_files.effect_on -cne "effect_effect_on_output_module_settings.json") {
    Stop-AfterFX
    Fail "output_module_settings_path_mismatch" "$($case.id) Output Module settings filenames drifted"
  }
  $NoEffect = Join-Path $CaseRoot $ExpectedContract.output_names.no_effect
  $EffectOn = Join-Path $CaseRoot $ExpectedContract.output_names.effect_on
  $NoEffectSettings = Join-Path $CaseRoot $manifest.output_module.settings_files.no_effect
  $EffectOnSettings = Join-Path $CaseRoot $manifest.output_module.settings_files.effect_on
  foreach ($path in @($NoEffect, $EffectOn, $NoEffectSettings, $EffectOnSettings, $ProjectPath)) {
'''
        runner_text = replace_once(runner_text, output_anchor, output_replacement, "runner settings validation")
        required_artifacts_end = '''  }
  $Records += [ordered]@{
'''
        settings_hash_block = '''  }
  if (-not $result.output_module_settings -or $result.output_module_settings.Count -ne 2) {
    Stop-AfterFX
    Fail "missing_output_module_settings_metadata" "$($case.id) result did not bind both settings captures"
  }
  try {
    $NoEffectSettingsRecord = Get-Content -LiteralPath $NoEffectSettings -Raw | ConvertFrom-Json
    $EffectOnSettingsRecord = Get-Content -LiteralPath $EffectOnSettings -Raw | ConvertFrom-Json
  } catch {
    Stop-AfterFX
    Fail "invalid_output_module_settings_json" "$($case.id) cannot parse Output Module settings capture: $($_.Exception.Message)"
  }
  foreach ($settingsRecord in @($NoEffectSettingsRecord, $EffectOnSettingsRecord)) {
    if ($settingsRecord.kind -cne "olm_output_module_settings_capture" -or
        $settingsRecord.schema_version -ne 1 -or
        $settingsRecord.output_template -cne $ExpectedTemplate -or
        $settingsRecord.capture_api -cne $ExpectedOutputModuleCaptureApi -or
        $settingsRecord.semantic_verification -cne $ExpectedSemanticVerification -or
        -not $settingsRecord.settings -or $settingsRecord.settings.PSObject.Properties.Count -lt 1) {
      Stop-AfterFX
      Fail "invalid_output_module_settings_payload" "$($case.id) Output Module settings capture payload is incomplete or drifted"
    }
    $settingsIntent = $settingsRecord.semantic_intent
    if ($settingsIntent.channels -cne "RGB+Alpha" -or $settingsIntent.sample_type -cne "32-bit float" -or
        -not [bool]$settingsIntent.preserve_rgb -or [bool]$settingsIntent.linear_light_conversion) {
      Stop-AfterFX
      Fail "invalid_output_module_settings_intent" "$($case.id) settings capture semantic intent drifted"
    }
  }
  $NoEffectSettingsHash = (Get-FileHash -LiteralPath $NoEffectSettings -Algorithm SHA256).Hash.ToLowerInvariant()
  $EffectOnSettingsHash = (Get-FileHash -LiteralPath $EffectOnSettings -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($NoEffectSettingsHash -ne $EffectOnSettingsHash) {
    Stop-AfterFX
    Fail "output_module_settings_hash_mismatch" "$($case.id) no-effect/effect-on settings hashes differ"
  }
  if (-not $SharedOutputModuleSettingsSha256) {
    $SharedOutputModuleSettingsSha256 = $NoEffectSettingsHash
  } elseif ($SharedOutputModuleSettingsSha256 -ne $NoEffectSettingsHash) {
    Stop-AfterFX
    Fail "cross_plugin_output_module_settings_hash_mismatch" "$($case.id) settings hash differs across plugin cases"
  }
  $Records += [ordered]@{
'''
        runner_text = replace_once(runner_text, required_artifacts_end, settings_hash_block, "runner settings hashes")
        runner_text = replace_once(
            runner_text,
            "    id = $case.id\n    effect = $case.effect\n    plugin = $PluginRecords[$case.id]\n",
            "    id = $case.id\n"
            "    effect = $case.effect\n"
            "    fulfills_request_id = $case.fulfills_request_id\n"
            "    no_effect_control_passed = $true\n"
            "    plugin = $PluginRecords[$case.id]\n"
            "    output_module = [ordered]@{\n"
            "      template_name = $ExpectedTemplate\n"
            "      capture_api = $ExpectedOutputModuleCaptureApi\n"
            "      semantic_intent = $intent\n"
            "      semantic_verification = $ExpectedSemanticVerification\n"
            "      settings_sha256 = $NoEffectSettingsHash\n"
            "      captured_settings = $NoEffectSettingsRecord.settings\n"
            "      settings = [ordered]@{\n"
            "        no_effect = [ordered]@{ path = (Resolve-Path $NoEffectSettings).Path.Substring((Resolve-Path $RunRoot).Path.Length + 1).Replace(\"\\\", \"/\"); sha256 = $NoEffectSettingsHash }\n"
            "        effect_on = [ordered]@{ path = (Resolve-Path $EffectOnSettings).Path.Substring((Resolve-Path $RunRoot).Path.Length + 1).Replace(\"\\\", \"/\"); sha256 = $EffectOnSettingsHash }\n"
            "      }\n"
            "    }\n",
            "runner case output module record",
        )
        runner_text = replace_once(
            runner_text,
            "  fixture_jsx_sha256 = $FixtureSha\n  cases = $Records\n",
            "  fixture_jsx_sha256 = $FixtureSha\n"
            "  fulfills_request_ids = @($FulfillsRequestIds)\n"
            "  pending_requests_answered = $false\n"
            "  pending_request_resolution_eligible = $true\n"
            "  pending_request_resolution_note = \"eligible only because both cases, both no-effect controls, and one shared Output Module settings hash passed; intake must decide status\"\n"
            "  output_module_settings_sha256 = $SharedOutputModuleSettingsSha256\n"
            "  cases = $Records\n",
            "runner success lineage",
        )
        runner.write_text(runner_text, encoding="utf-8")

        compare_path = stage / "compare_cross_host_typed_procedural_fixture.py"
        compare_source = compare_path.read_text(encoding="utf-8")
        compare_source = replace_once(
            compare_source,
            'EXPECTED_KIND = "olm_32bpc_typed_procedural_render_record"\n',
            'EXPECTED_KIND = "olm_32bpc_typed_procedural_render_record"\n'
            f'EXPECTED_FULFILLS_REQUEST_IDS = {PENDING_REQUEST_IDS!r}\n'
            f'EXPECTED_CASE_REQUEST_IDS = {dict(zip((case["id"] for case in CASES), PENDING_REQUEST_IDS))!r}\n'
            f'EXPECTED_OUTPUT_MODULE_CAPTURE_API = {OUTPUT_MODULE_CAPTURE_API!r}\n'
            f'EXPECTED_OUTPUT_MODULE_INTENT = {OUTPUT_MODULE_SEMANTIC_INTENT!r}\n'
            f'EXPECTED_SEMANTIC_VERIFICATION = {OUTPUT_MODULE_SEMANTIC_VERIFICATION!r}\n',
            "compare constants",
        )
        compare_source = replace_once(
            compare_source,
            '''    if not isinstance(record.get("fixture_jsx_sha256"), str) or len(record["fixture_jsx_sha256"]) != 64:
        raise VerificationError("render record fixture_jsx_sha256 missing or invalid")
    cases = record.get("cases")
''',
            '''    if not isinstance(record.get("fixture_jsx_sha256"), str) or len(record["fixture_jsx_sha256"]) != 64:
        raise VerificationError("render record fixture_jsx_sha256 missing or invalid")
    if record.get("fulfills_request_ids") != EXPECTED_FULFILLS_REQUEST_IDS:
        raise VerificationError("render record pending-request lineage is missing or drifted")
    if record.get("pending_requests_answered") is not False:
        raise VerificationError("render record must not silently mark pending requests answered")
    if record.get("pending_request_resolution_eligible") is not True:
        raise VerificationError("render record did not pass the combined pending-request gate")
    shared_settings_sha = record.get("output_module_settings_sha256")
    if not isinstance(shared_settings_sha, str) or len(shared_settings_sha) != 64:
        raise VerificationError("render record shared Output Module settings SHA-256 is missing")
    cases = record.get("cases")
''',
            "compare record settings contract",
        )
        compare_source = replace_once(
            compare_source,
            '''        outputs = case.get("outputs")
        if not isinstance(outputs, dict):
''',
            '''        expected_request_id = EXPECTED_CASE_REQUEST_IDS.get(case["id"])
        if case.get("fulfills_request_id") != expected_request_id:
            raise VerificationError(f"{case['id']}: pending-request case mapping drifted")
        if case.get("no_effect_control_passed") is not True:
            raise VerificationError(f"{case['id']}: no-effect control did not pass")
        output_module = case.get("output_module")
        if not isinstance(output_module, dict):
            raise VerificationError(f"{case['id']}: Output Module metadata is missing")
        if output_module.get("template_name") != "OLM EXR 32 Float":
            raise VerificationError(f"{case['id']}: Output Module template name drifted")
        if output_module.get("capture_api") != EXPECTED_OUTPUT_MODULE_CAPTURE_API:
            raise VerificationError(f"{case['id']}: Output Module capture API drifted")
        if output_module.get("semantic_intent") != EXPECTED_OUTPUT_MODULE_INTENT:
            raise VerificationError(f"{case['id']}: Output Module semantic intent drifted")
        if output_module.get("semantic_verification") != EXPECTED_SEMANTIC_VERIFICATION:
            raise VerificationError(f"{case['id']}: Output Module semantic-verification boundary drifted")
        if output_module.get("settings_sha256") != shared_settings_sha:
            raise VerificationError(f"{case['id']}: Output Module settings hash is not shared across plugin cases")
        captured_settings = output_module.get("captured_settings")
        if not isinstance(captured_settings, dict) or not captured_settings:
            raise VerificationError(f"{case['id']}: captured Output Module settings are missing")
        settings_rows = output_module.get("settings")
        if not isinstance(settings_rows, dict):
            raise VerificationError(f"{case['id']}: Output Module settings artifacts are missing")
        for settings_role in ("no_effect", "effect_on"):
            settings_row = settings_rows.get(settings_role)
            if not isinstance(settings_row, dict) or not isinstance(settings_row.get("path"), str):
                raise VerificationError(f"{case['id']}: Output Module {settings_role} settings path is missing")
            settings_path = (root / settings_row["path"]).resolve()
            if not settings_path.is_file():
                raise VerificationError(f"{case['id']}: Output Module {settings_role} settings file is missing")
            settings_actual_sha = sha256(settings_path)
            if settings_row.get("sha256") != settings_actual_sha or settings_actual_sha != shared_settings_sha:
                raise VerificationError(f"{case['id']}: Output Module {settings_role} settings hash drifted")
            settings_payload = json.loads(settings_path.read_text(encoding="utf-8-sig"))
            if settings_payload.get("kind") != "olm_output_module_settings_capture":
                raise VerificationError(f"{case['id']}: Output Module {settings_role} settings kind drifted")
            if settings_payload.get("capture_api") != EXPECTED_OUTPUT_MODULE_CAPTURE_API:
                raise VerificationError(f"{case['id']}: Output Module {settings_role} capture API drifted")
            if settings_payload.get("semantic_intent") != EXPECTED_OUTPUT_MODULE_INTENT:
                raise VerificationError(f"{case['id']}: Output Module {settings_role} semantic intent drifted")
            if settings_payload.get("semantic_verification") != EXPECTED_SEMANTIC_VERIFICATION:
                raise VerificationError(f"{case['id']}: Output Module {settings_role} semantic boundary drifted")
            if settings_payload.get("settings") != captured_settings:
                raise VerificationError(f"{case['id']}: embedded and captured Output Module settings differ")
        outputs = case.get("outputs")
        if not isinstance(outputs, dict):
''',
            "compare case settings contract",
        )
        compare_source = replace_once(
            compare_source,
            '''            "fixture_contract": contract,
            "outputs": normalized_outputs,
''',
            '''            "fixture_contract": contract,
            "output_module": output_module,
            "outputs": normalized_outputs,
''',
            "compare normalized settings record",
        )
        compare_source = replace_once(
            compare_source,
            '''                "right_internal_delta": right_delta,
                "status": "raw-float-bits-exact",
''',
            '''                "right_internal_delta": right_delta,
                "output_module_settings_sha256": {
                    left_record["platform"]: left_case["output_module"]["settings_sha256"],
                    right_record["platform"]: right_case["output_module"]["settings_sha256"],
                },
                "status": "raw-float-bits-exact",
''',
            "compare result settings hashes",
        )
        compare_path.write_text(compare_source, encoding="utf-8")

        package_manifest["files"] = [
            {"path": path.relative_to(stage).as_posix(), "sha256": sha256(path), "size_bytes": path.stat().st_size}
            for path in sorted(stage.rglob("*"))
            if path.is_file() and path.name != "manifest.json"
        ]
        (stage / "manifest.json").write_text(json.dumps(package_manifest, indent=2) + "\n", encoding="utf-8")

        support_dir.parent.mkdir(parents=True, exist_ok=True)
        if support_dir.exists():
            shutil.rmtree(support_dir)
        shutil.copytree(stage, support_dir)
        output_zip.parent.mkdir(parents=True, exist_ok=True)
        if output_zip.exists():
            output_zip.unlink()
        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    archive.write(path, f"{PACKAGE_STEM}/{path.relative_to(stage).as_posix()}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--support-dir", type=Path, default=SUPPORT_DIR)
    parser.add_argument("--output", type=Path, default=OUTPUT_ZIP)
    args = parser.parse_args()
    materialize(args.support_dir if args.support_dir.is_absolute() else ROOT / args.support_dir, args.output if args.output.is_absolute() else ROOT / args.output)
    print(f"[OK] support={args.support_dir} zip={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
