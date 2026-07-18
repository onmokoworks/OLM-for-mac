#!/usr/bin/env python3
"""Build the isolated Mac OLMToonDilate 32bpc validation package."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKAGE = ROOT / "refs/runtime_trace_packages/windows_witness_olmtoondilate_32bpc_typed_procedural_samecomp_20260713"
STEM = "olmtoondilate_mac_32bpc_validation_20260715"
PLUGIN_BINARY = ROOT / "mac/OLMToonDilate/Mac/build/Debug/OLMToonDilate.plugin/Contents/MacOS/OLMToonDilate"
PLUGIN_SOURCE_PATHS = (
    ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp",
    ROOT / "mac/OLMToonDilate/OLMToonDilate.h",
    ROOT / "mac/OLMToonDilate/OLMToonDilatePiPL.r",
    ROOT / "mac/OLMToonDilate/Mac/OLMToonDilate.xcodeproj/project.pbxproj",
)
CONTRACT = {
    "manifest_kind": "olm_32bpc_typed_procedural_fixture",
    "project_bits_per_channel": 32,
    "working_space": "None",
    "linear_blending": False,
    "renderer": "SOFTWARE",
    "dimensions": [64, 64],
    "frame": 0,
    "source_policy": "AE-generated solids only; no footage imported",
    "render_policy": "same comp, only branch enabled state changes",
    "source_layers": [
        {"name": "solid_background", "kind": "solid", "bounds": [0, 0, 64, 64], "rgb": [0, 0, 0], "alpha": 1.0},
        {"name": "rect_integer_a25", "kind": "solid", "bounds": [4, 4, 20, 16], "rgb": [1, 0, 0], "alpha": 0.25},
        {"name": "rect_integer_a50", "kind": "solid", "bounds": [28, 4, 20, 16], "rgb": [0, 1, 0], "alpha": 0.5},
        {"name": "rect_integer_a75", "kind": "solid", "bounds": [4, 28, 20, 16], "rgb": [0, 0, 1], "alpha": 0.75},
        {"name": "rect_integer_a100", "kind": "solid", "bounds": [28, 28, 20, 16], "rgb": [1, 1, 1], "alpha": 1.0},
    ],
    "output_names": {"no_effect": "effect_no_effect_00000.exr", "effect_on": "effect_effect_on_00000.exr"},
}
PARAMETERS = [{"name": "Search Radius", "match_name": "ADBE OLMToonDilate-0001", "property_index": 1,
              "property_value_type": "OneD", "minimum": 0.0, "maximum": 100.0, "value": 13.0,
              "readback_tolerance": 0.0001}]
INTENT = {"channels": "RGB+Alpha", "sample_type": "32-bit float", "preserve_rgb": True, "linear_light_conversion": False}
SEMANTIC_VERIFICATION = "declared intent only; localized getSettings keys and values are captured verbatim and not semantically parsed"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_source() -> str:
    source = (SOURCE_PACKAGE / "request/fixture/ae_generate_32bpc_typed_procedural_fixture.jsx").read_text(encoding="utf-8")
    source = source.replace('var effectName = getenv("OLM_AE_TYPED_FIXTURE_EFFECT") || "OLM Color Key";',
                            'var effectName = getenv("OLM_AE_TYPED_FIXTURE_EFFECT") || "OLM Toon Dilate";')
    source = source.replace('var suppressStarted = false;', 'var suppressStarted = false;\n    var settingsCaptures = [];')
    anchor = '        module.applyTemplate(template);\n        module.file = sequenceFile;'
    replacement = '''        module.applyTemplate(template);
        if (!module.getSettings || typeof GetSettingsFormat === "undefined" || typeof GetSettingsFormat.STRING === "undefined") fail("OutputModule settings API unavailable");
        var capturedSettings = module.getSettings(GetSettingsFormat.STRING);
        if (!capturedSettings) fail("OutputModule settings capture is empty");
        var settingsPath = outputDir + "/" + filename.replace(/\\.exr$/i, "_output_module_settings.json");
        writeText(settingsPath, JSON.stringify({kind: "olm_output_module_settings_capture", schema_version: 1,
            output_template: template, capture_api: "OutputModule.getSettings(GetSettingsFormat.STRING)",
            semantic_intent: {channels: "RGB+Alpha", sample_type: "32-bit float", preserve_rgb: true, linear_light_conversion: false},
            semantic_verification: "declared intent only; localized getSettings keys and values are captured verbatim and not semantically parsed",
            settings: capturedSettings}, null, 2) + "\\n");
        settingsCaptures.push({path: settingsPath, settings: capturedSettings});
        module.file = sequenceFile;'''
    if anchor not in source:
        raise RuntimeError("fixture render anchor drifted")
    source = source.replace(anchor, replacement, 1)
    source = source.replace('project.linearBlending = false;',
                            'project.linearBlending = false;\n        try { project.gpuAccelType = GpuAccelType.SOFTWARE; } catch (e) { fail("cannot set SOFTWARE renderer"); }')
    source = source.replace('var effectOn = renderOne(renderComp, outputDir, "effect_effect_on.exr", template);',
                            'var effectOn = renderOne(renderComp, outputDir, "effect_effect_on.exr", template);\n        if (settingsCaptures.length !== 2) fail("expected no-effect and effect-on settings captures");\n        if (JSON.stringify(settingsCaptures[0].settings) !== JSON.stringify(settingsCaptures[1].settings)) fail("OutputModule settings differ between controls");')
    return source


def write_package(root: Path) -> dict:
    if not PLUGIN_BINARY.is_file():
        raise RuntimeError("current ToonDilate candidate binary is missing; build the plugin first")
    # The package is intentionally bound to the build present at packaging time.
    # A fixed digest here made every later rebuild look invalid even when the
    # source and candidate were deliberately changed together.
    plugin_sha256 = digest(PLUGIN_BINARY)
    (root / "fixture").mkdir(parents=True)
    fixture = root / "fixture/ae_generate_32bpc_olmtoondilate_fixture.jsx"
    fixture.write_text(fixture_source(), encoding="utf-8")
    request = {
        "kind": "olmtoondilate_mac_32bpc_validation_request", "schema": 1,
        "status": "request-only; no AE exact claim", "request_id": STEM,
        "required_ae": {"major_minor": "26.3", "renderer": "SOFTWARE"},
        "project": {"bits_per_channel": 32, "working_space": "None", "linear_blending": False},
        "output_template": "OLM EXR 32 Float", "fixture_contract": CONTRACT,
        "input_contract": {"kind": "ae_generated_typed_procedural_source", "external_footage": False,
                            "same_comp_control": True, "parameter": PARAMETERS[0]},
        "output_module_contract": {"capture_required": True, "capture_api": "OutputModule.getSettings(GetSettingsFormat.STRING)",
            "semantic_intent": INTENT, "semantic_verification": SEMANTIC_VERIFICATION, "hash_algorithm": "sha256",
            "same_hash_required": ["no_effect_vs_effect_on"]},
        "case": {"id": "olmtoondilate_typed_procedural_64x64", "effect": "OLM Toon Dilate",
                 "plugin": {"name": "OLMToonDilate.plugin", "binary": "Contents/MacOS/OLMToonDilate",
                            "sha256": plugin_sha256,
                            "candidate_provenance": {"source_sha256": {
                                str(path.relative_to(ROOT)): digest(path) for path in PLUGIN_SOURCE_PATHS
                            }, "build_architectures": ["arm64", "x86_64"]}},
                 "parameters": PARAMETERS, "outputs": CONTRACT["output_names"]},
        "acceptance_gate": {"comparison": "Mac AE vs Windows AE Software", "required": "raw FLOAT EXR bits exact",
                             "evidence_boundary": "AE render records only; CLI/emulation is intermediate evidence"},
        "fail_closed": ["reject existing AfterFX before launch", "reject plugin identity/hash mismatch",
                        "reject AE/version/project/renderer/template drift", "reject missing controls or settings captures",
                        "reject exact status until cross-host return comparison passes"]}
    (root / "request_manifest.json").write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shutil.copy2(ROOT / "refs/runtime_trace_packages/olm_windows_colorkey_toondilate_32bpc_control_20260715/fixture/verify_32bpc_float_return.py", root / "verify_32bpc_float_return.py")
    shutil.copy2(ROOT / "refs/runtime_trace_packages/olm_windows_colorkey_toondilate_32bpc_control_20260715/fixture/compare_float_exr.py", root / "compare_float_exr.py")
    return request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "refs/runtime_trace_packages" / STEM)
    parser.add_argument("--zip", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="toondilate_mac_package_") as temp:
        stage = Path(temp) / STEM
        request = write_package(stage)
        for name, text in {
            "README.md": "# OLMToonDilate Mac 32bpc validation\n\nThis package is request/runner/report material only. It does not install or launch After Effects during packaging. The runner refuses an exact claim until a Windows return is compared to the Mac record with raw FLOAT EXR equality.\n",
            "REPORT_TEMPLATE.json": json.dumps({"kind": "olmtoondilate_mac_32bpc_validation_report", "schema": 1, "status": "blocked", "reason": "cross_host_return_compare_required", "ae_exact": False}, indent=2) + "\n",
        }.items():
            (stage / name).write_text(text, encoding="utf-8")
        shutil.copy2(ROOT / "refs/scripts/run_olmtoondilate_mac_32bpc_validation_20260715.py", stage / "run_mac_validation.py")
        shutil.copy2(ROOT / "refs/scripts/compare_olmtoondilate_mac_32bpc_validation_20260715.py", stage / "compare_cross_host.py")
        args.output_dir.parent.mkdir(parents=True, exist_ok=True)
        if args.output_dir.exists(): shutil.rmtree(args.output_dir)
        shutil.copytree(stage, args.output_dir)
        if args.zip:
            args.zip.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(args.zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(args.output_dir.rglob("*")):
                    if path.is_file():
                        arcname = (Path(STEM) / path.relative_to(args.output_dir)).as_posix()
                        info = zipfile.ZipInfo(arcname, date_time=(2026, 1, 1, 0, 0, 0))
                        info.compress_type = zipfile.ZIP_DEFLATED
                        info.external_attr = 0o644 << 16
                        archive.writestr(info, path.read_bytes())
    print(json.dumps({"status": "ok", "package": str(args.output_dir), "request_id": request["request_id"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
