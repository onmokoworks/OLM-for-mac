#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "refs/conformance/olmcolorkey_32bpc_case0002_ae_exact_20260727.json"
SPEC = ROOT / "refs/reference_requests/olm_bitdepth_32bpc_colorkey_float_20260710.json"


def assert_default_vector() -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    case = next(row for row in spec["cases"] if row["id"] == "olmcolorkey__case_0002")
    params = [
        row
        for row in case["params_full"]
        if row["match_name"] not in {"ADBE Effect Mask Opacity", "ADBE Force CPU GPU"}
    ]
    assert len(case["params_full"]) == 219
    assert len(params) == 217

    scalar_defaults = {
        "Color Keep": 0,
        "Premultiplied Color": 0,
        "Color Space": 1,
        "Force Lower Precision": 1,
        "Per Color": 0,
        "Per Component": 0,
        "Amount": 0,
        "Distance Type": 1,
        "Direction": 2,
        "Number of Colors": 1,
        "Enable Replace": 0,
    }
    checked = 0
    for param in params:
        name = param["name"]
        value = param["value"]
        if name in scalar_defaults:
            assert value == scalar_defaults[name], param
        elif name.startswith("Threshold"):
            assert value == 0, param
        elif name.startswith("Use Replace Color "):
            assert value == 0, param
        elif name.startswith("Use Color "):
            assert value == (1 if name == "Use Color 1" else 0), param
        elif name.startswith("Replace Color ") or name.startswith("Color "):
            assert value == [0, 0, 0, 1], param
        else:
            raise AssertionError(param)
        checked += 1
    assert checked == 217


def main() -> None:
    assert_default_vector()
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert data["status"] == "ae_exact"
    assert data["case_id"] == "olmcolorkey__case_0002"
    assert data["scope"] == "declared 32bpc default-parameter no-op case only"

    project = data["project_contract"]
    assert project["bits_per_channel"] == 32
    assert project["renderer_raw"] == 1816
    assert project["working_space_raw"] == "None"
    assert project["linear_blending"] is False
    assert project["sample_type"] == "FLOAT"
    assert project["profile"] == "Preserve RGB"

    binding = data["project_binding"]
    assert binding["normalized_files_byte_identical"] is True
    assert binding["render_queue_item_count"] == 2

    params = data["parameter_contract"]
    assert params["render_parameter_count"] == 217
    assert params["all_render_parameters_are_declared_defaults"] is True
    assert params["windows_aerender_conversion_warning"] is True
    assert "do not reuse" in params["warning_disposition"]
    assert params["critical_defaults"]["Threshold"] == 0
    assert params["critical_defaults"]["Edge Thin Amount"] == 0
    assert params["critical_defaults"]["Edge Blur Amount"] == 0

    mac = data["mac"]
    windows = data["windows"]
    assert mac["plugin_macho_sha256"] == (
        "c3026c5facbdf227bec55c24e7257f0f94db5ddf94ce26cfb5b593681b5ed0ae"
    )
    assert windows["plugin_aex_sha256"] == (
        "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"
    )
    assert windows["afterfx_com_pid"] == windows["aex_image_event_pid"]
    assert windows["render_exit_code"] == 0
    assert windows["image_load_event_count"] == 2

    comparisons = data["raw_float32_comparisons"]
    assert comparisons["sample_words_per_frame"] == 8_294_400
    for label, result in comparisons.items():
        if label == "sample_words_per_frame":
            continue
        assert result["mismatched_values"] == 0, label
        assert result["max_raw_u32_delta"] == 0, label

    attribution = data["attribution"]
    assert attribution["case_behavior"] == "declared no-op"
    assert attribution["effect_loaded_on_both_hosts"] is True
    assert attribution["same_contract_control_and_effect_required"] is True
    assert attribution["cli_exact_used_as_ae_substitute"] is False
    assert data["limitations"][0] == "This promotes only case_0002."
    print("[PASS] OLMColorKey 32bpc case_0002 AE exact evidence")


if __name__ == "__main__":
    main()
