#!/usr/bin/env python3
"""Smoke the single Windows ColorKey+ToonDilate control request package."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "scripts/package_windows_colorkey_toondilate_32bpc_control_20260715.py"
PENDING_REQUESTS = {
    "olmcolorkey_typed_procedural_64x64": "olm_bitdepth_32bpc_colorkey_float_20260710",
    "olmtoondilate_typed_procedural_64x64": "olm_bitdepth_32bpc_toondilate_float_20260710",
}
EXPECTED_INTENT = {
    "channels": "RGB+Alpha",
    "sample_type": "32-bit float",
    "preserve_rgb": True,
    "linear_light_conversion": False,
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_windows_control_smoke_") as raw:
        temp = Path(raw)
        support = temp / "support"
        archive = temp / "control.zip"
        subprocess.run(
            [sys.executable, str(GENERATOR), "--support-dir", str(support), "--output", str(archive)],
            cwd=ROOT,
            check=True,
            text=True,
        )
        request = json.loads((support / "request/request_manifest.json").read_text(encoding="utf-8"))
        assert request["kind"] == "olm_windows_single_control_request"
        assert request["fulfills_request_ids"] == list(PENDING_REQUESTS.values())
        assert request["output_template"] == "OLM EXR 32 Float"
        assert request["required_ae"] == {"major_minor": "26.3", "renderer": "SOFTWARE"}
        assert request["project"] == {"bits_per_channel": 32, "working_space": "None", "linear_blending": False}
        assert request["input_contract"]["external_footage"] is False
        assert request["input_contract"]["same_comp_control"] is True
        module_contract = request["output_module_contract"]
        assert module_contract["capture_required"] is True
        assert module_contract["capture_api"] == "OutputModule.getSettings(GetSettingsFormat.STRING)"
        assert module_contract["semantic_intent"] == EXPECTED_INTENT
        assert "localized" in module_contract["semantic_verification"]
        assert module_contract["same_hash_required"] == [
            "no_effect_vs_effect_on_per_case",
            "colorkey_vs_toondilate",
        ]
        fixture = support / "fixture" / request["input_contract"]["fixture_script"]
        assert digest(fixture) == request["input_contract"]["fixture_script_sha256"]
        fixture_text = fixture.read_text(encoding="utf-8")
        apply_index = fixture_text.index("module.applyTemplate(template);")
        capture_index = fixture_text.index("captureOutputModuleSettings(module, outputDir, filename, template)", apply_index)
        file_index = fixture_text.index("module.file = sequenceFile;", capture_index)
        assert apply_index < capture_index < file_index
        assert "settings = module.getSettings(GetSettingsFormat.STRING);" in fixture_text
        for token in (
            "stableJson",
            "Output Module settings capture is empty",
            "no-effect and effect-on Output Module settings differ",
            "output_module_settings",
            "same_settings_serialization",
            "RGB+Alpha",
            "32-bit float",
            "preserve_rgb: true",
            "linear_light_conversion: false",
            "localized getSettings keys and values are captured verbatim and not semantically parsed",
        ):
            assert token in fixture_text, token
        assert len(request["cases"]) == 2
        assert {case["aex"]["filename"] for case in request["cases"]} == {"OLMColorKey.aex", "OLMToonDilate.aex"}
        assert all(len(case["aex"]["sha256"]) == 64 for case in request["cases"])
        assert all(case["controls"] == {"no_effect": True, "effect_on": True, "output_format": "FLOAT EXR"} for case in request["cases"])
        assert {case["id"]: case["fulfills_request_id"] for case in request["cases"]} == PENDING_REQUESTS
        assert request["pending_request_resolution"]["initial_state"] == "pending"
        assert "keep both request IDs pending" in request["pending_request_resolution"]["partial_return_policy"]

        for request_id in PENDING_REQUESTS.values():
            pending_path = ROOT / "refs/reference_requests" / f"{request_id}.json"
            pending = json.loads(pending_path.read_text(encoding="utf-8"))
            assert pending["request_id"] == request_id

        intake = json.loads((support / "request/combined_intake_metadata.json").read_text(encoding="utf-8"))
        assert intake["fulfills_request_ids"] == list(PENDING_REQUESTS.values())
        assert intake["case_mapping"] == PENDING_REQUESTS
        assert intake["required_case_count"] == 2
        assert intake["required_no_effect_control_count"] == 2
        assert intake["required_shared_output_module_settings_hash"] is True

        runner = (support / "run_windows_typed_procedural_fixture_20260713.ps1").read_text(encoding="utf-8")
        for token in (
            "plugin_hash_mismatch",
            "OLMColorKey.aex",
            "OLMToonDilate.aex",
            "project_gpu_accel_type.current_name",
            "effect_no_effect_00000.exr",
            "effect_effect_on_00000.exr",
            "OLM EXR 32 Float",
            "effect_no_effect_output_module_settings.json",
            "effect_effect_on_output_module_settings.json",
            "output_module_settings_hash_mismatch",
            "cross_plugin_output_module_settings_hash_mismatch",
            "invalid_output_module_settings_json",
            "invalid_output_module_settings_payload",
            "captured_settings = $NoEffectSettingsRecord.settings",
            "output_module_settings_sha256",
            "pending_requests_answered = $false",
            "pending_request_resolution_eligible = $false",
            "pending_request_resolution_eligible = $true",
        ):
            assert token in runner, token
        assert "GpuAccelType.SOFTWARE" in fixture_text
        for request_id in PENDING_REQUESTS.values():
            assert request_id in runner

        return_template = json.loads((support / "RETURN_MANIFEST_TEMPLATE.json").read_text(encoding="utf-8"))
        assert return_template["fulfills_request_ids"] == list(PENDING_REQUESTS.values())
        assert return_template["pending_requests_answered"] is False
        assert return_template["pending_request_resolution_eligible"] is False
        assert all(case["output_module"]["semantic_intent"] == EXPECTED_INTENT for case in return_template["cases"])
        assert all(case["output_module"]["settings_sha256"] == "" for case in return_template["cases"])

        comparator = (support / "compare_cross_host_typed_procedural_fixture.py").read_text(encoding="utf-8")
        for token in (
            "EXPECTED_FULFILLS_REQUEST_IDS",
            "pending_requests_answered",
            "pending_request_resolution_eligible",
            "shared Output Module settings SHA-256 is missing",
            "Output Module settings hash is not shared across plugin cases",
            "embedded and captured Output Module settings differ",
            "output_module_settings_sha256",
        ):
            assert token in comparator, token
        assert zipfile.is_zipfile(archive)
        with zipfile.ZipFile(archive) as zipped:
            assert zipped.testzip() is None
            names = set(zipped.namelist())
            assert any(name.endswith("/request/request_manifest.json") for name in names)
            assert any(name.endswith("/request/input_hashes.json") for name in names)
            assert any(name.endswith("/request/combined_intake_metadata.json") for name in names)

        package = json.loads((support / "manifest.json").read_text(encoding="utf-8"))
        assert package["combined_intake_metadata"] == "request/combined_intake_metadata.json"
        for row in package["files"]:
            path = support / row["path"]
            assert path.stat().st_size == row["size_bytes"]
            assert digest(path) == row["sha256"]

        tampered = json.loads(json.dumps(request))
        tampered["cases"][1]["aex"]["sha256"] = "0" * 64
        assert tampered["cases"][1]["aex"]["sha256"] != request["cases"][1]["aex"]["sha256"]

    print("[OK] single Windows ColorKey+ToonDilate control package smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
