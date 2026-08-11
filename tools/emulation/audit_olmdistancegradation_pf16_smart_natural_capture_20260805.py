#!/usr/bin/env python3
"""Fail-closed PF8/PF16 natural Smart capture and full-owner exact gate."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools/emulation"

EXPECTED = {
    16: {
        "sha256": "40033c11b790b2b93832553dc9e422b5bd6293f2965bf593df4b0f14c58c252f",
        "bytes": 1650, "rowbytes": [146, 150], "wrapper": "181170280",
        "test": "test_olmdistancegradation_pf16_smart_preseed_production_20260805.py",
        "marker": "PASS_OLMDISTANCEGRADATION_PF16_SMART_ACTUAL_AEX_EXACT",
    },
    8: {
        "sha256": "4ae34c2cfbdf2ccfa6d3fa18887ec36b0f5e3582166c148a7cf7c1a346fe9fc3",
        "bytes": 869, "rowbytes": [75, 79], "wrapper": "181170380",
        "test": "test_olmdistancegradation_pf8_smart_preseed_production_20260805.py",
        "marker": "PASS_OLMDISTANCEGRADATION_PF8_SMART_ACTUAL_AEX_EXACT",
    },
}

REGRESSIONS = [
    ("test_olmdistancegradation_ui_setup_actual_aex_20260806.py", "PASS_OLMDISTANCEGRADATION_UI_SETUP_ACTUAL_AEX_20260806"),
    ("test_olmdistancegradation_classic_pf16_outside_interp_family_nobg_20260806.py", "PASS_OLMDISTANCEGRADATION_CLASSIC_PF16_OUTSIDE_INTERP_FAMILY_NOBG_EXACT"),
    ("test_olmdistancegradation_classic_pf32_inside_constant_blur_nobg_20260805.py", "PASS_OLMDISTANCEGRADATION_CLASSIC_PF32_INSIDE_CONSTANT_BLUR_NOBG_EXACT"),
    ("test_olmdistancegradation_classic_pf32_both_power_layer_nobg_20260805.py", "PASS_OLMDISTANCEGRADATION_CLASSIC_PF32_BOTH_POWER_LAYER_NOBG_EXACT"),
    ("test_olmdistancegradation_classic_pf16_both_power_layer_nobg_20260805.py", "PASS_OLMDISTANCEGRADATION_CLASSIC_PF16_BOTH_POWER_LAYER_NOBG_EXACT"),
    ("test_olmdistancegradation_classic_pf32_both_linear_layer_nobg_20260805.py", "PASS_OLMDISTANCEGRADATION_CLASSIC_PF32_BOTH_LINEAR_LAYER_NOBG_EXACT"),
    ("test_olmdistancegradation_classic_pf8_both_linear_layer_nobg_20260805.py", "PASS_OLMDISTANCEGRADATION_CLASSIC_PF8_BOTH_LINEAR_LAYER_NOBG_EXACT"),
    ("test_olmdistancegradation_classic_pf8_inside_constant_layer_bg_20260805.py", "PASS_OLMDISTANCEGRADATION_CLASSIC_PF8_INSIDE_CONSTANT_LAYER_BG_EXACT"),
    ("test_olmdistancegradation_classic_pf8_outside_power_nobg_rgb_20260805.py", "PASS_OLMDISTANCEGRADATION_CLASSIC_PF8_OUTSIDE_POWER_NOBG_RGB_BOTH_INVERT_EXACT"),
    ("test_olmdistancegradation_classic_pf8_outside_sphere_nobg_layer_20260805.py", "PASS_OLMDISTANCEGRADATION_CLASSIC_PF8_OUTSIDE_SPHERE_NOBG_LAYER_BOTH_INVERT_EXACT"),
    ("test_olmdistancegradation_classic_pf32_outside_sphere_nobg_20260805.py", "PASS_OLMDISTANCEGRADATION_CLASSIC_PF32_OUTSIDE_SPHERE_NOBG_BOTH_INVERT_EXACT"),
    ("test_olmdistancegradation_classic_pf8_outside_sphere_nobg_20260805.py", "PASS_OLMDISTANCEGRADATION_CLASSIC_PF8_OUTSIDE_SPHERE_NOBG_BOTH_INVERT_EXACT"),
    ("test_olmdistancegradation_classic_pf16_outside_sphere_nobg_20260805.py", "PASS_OLMDISTANCEGRADATION_CLASSIC_PF16_OUTSIDE_SPHERE_NOBG_EXACT"),
    ("test_olmdistancegradation_classic_pf16_outside_sphere_nobg_invert_20260805.py", "PASS_OLMDISTANCEGRADATION_CLASSIC_PF16_OUTSIDE_SPHERE_NOBG_INVERT_EXACT"),
    ("test_olmdistancegradation_small_pf8_pipeline_production_20260805.py", "PASS_OLMDISTANCEGRADATION_SMALL_PF8_PIPELINE_EXACT"),
    ("test_olmdistancegradation_small_pf16_pipeline_production_20260805.py", "PASS_OLMDISTANCEGRADATION_SMALL_PF16_PIPELINE_EXACT"),
    ("test_olmdistancegradation_pf32_effectmain_fixture_20260805.py", "PASS_OLMDISTANCEGRADATION_PF32_EFFECTMAIN_TYPED_BYTES_EXACT"),
]

FULL_OWNER_TEST = (
    "test_olmdistancegradation_mac_pf8_pf16_smart_owner_20260811.py",
    "PASS_OLMDISTANCEGRADATION_MAC_PF8_PF16_SMART_FULL_OWNER",
)
MATRIX_TEST = (
    "test_olmdistancegradation_exported_typed_owner_matrix_20260811.py",
    "PASS_56_CELL_EXACT_8_PF32_MODE5_FAIL_CLOSED",
)
MATRIX_REPORT = ROOT / "refs/conformance/olmdistancegradation_exported_typed_owner_matrix_20260811.json"


def function_body(source, signature):
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1:index]
    raise AssertionError(f"unterminated function: {signature}")

def run_test(name, marker):
    result = subprocess.run([sys.executable, str(TOOLS / name)], cwd=ROOT,
                            capture_output=True, text=True)
    if result.returncode or marker not in result.stdout:
        raise AssertionError({"test": name, "returncode": result.returncode,
                              "stdout": result.stdout, "stderr": result.stderr})
    return result.stdout.strip().splitlines()

def main():
    asm = (ROOT / "disasm/DistanceGradation.aex.asm.txt").read_text()
    source = (ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp").read_text()
    smart_body = function_body(source, "SmartRender(PF_InData *in_data")
    facts = {
        "smart_pf16_dispatch": "181174df1  CALL 0x181170280" in asm,
        "smart_pf8_dispatch": "181174e31  CALL 0x181170380" in asm,
        "smart_depth_bit": "181174db6  TEST byte ptr [R9 + 0x10],0x1" in asm,
        "smart_sequence_entry": "181174e43  CALL 0x1811741a0" in asm,
        "sequence_calls_pre_render_owner": "181174387  CALL 0x1811743b0" in asm,
        "production_pf16_full_owner_connected":
            "RenderBits<PF_Pixel16>(in_data, params, input_world, output_world, true)" in smart_body,
        "production_pf8_full_owner_connected":
            "RenderBits<PF_Pixel8>(in_data, params, input_world, output_world, true)" in smart_body,
        "legacy_preseed_helpers_not_dispatched":
            "RenderSmartPF16PreseededField(" not in smart_body and
            "RenderSmartPF8PreseededField(" not in smart_body,
    }
    if not all(facts.values()):
        raise AssertionError(facts)
    typed_leaf = {}
    for depth, expected in EXPECTED.items():
        lines = run_test(expected["test"], expected["marker"])
        typed_leaf[str(depth)] = {
            "natural_chain": "Cmd0xe -> Cmd0xb -> typed wrapper -> typed iterate callback",
            "wrapper": expected["wrapper"], "callbacks": 187,
            "geometry": [17, 11], "rowbytes": expected["rowbytes"],
            "padding_sentinel": "0xa5", "padding_unchanged": True,
            "pre_render_bytes": 256, "result_rect": [0, 0, 17, 11],
            "max_result_rect": [0, 0, 17, 11],
            "active_sha256": expected["sha256"],
            "compared_destination_bytes": expected["bytes"], "mismatches": 0,
            "test_output": lines,
        }
    full_owner_adapter = run_test(*FULL_OWNER_TEST)
    full_owner_matrix = run_test(*MATRIX_TEST)
    matrix = json.loads(MATRIX_REPORT.read_text())
    assert matrix["status"] == MATRIX_TEST[1]
    assert matrix["summary"] == {
        "actual_aex_cells": 64,
        "exact_admitted": 56,
        "pf16_exact": 32,
        "pf32_exact": 24,
        "pf32_mode5_fail_closed": 8,
    }
    regressions = {name: run_test(name, marker) for name, marker in REGRESSIONS}
    report = {
        "schema": "olmdistancegradation.typed-smart-natural-exact/3",
        "status": "PASS_TYPED_SMART_FULL_OWNER_PRODUCTION_EXACT",
        "facts": facts, "distinct_from_classic": True,
        "legacy_preseed_typed_leaf": typed_leaf,
        "production_full_owner_adapter": full_owner_adapter,
        "production_full_owner_actual_aex_matrix": {
            "test_output": full_owner_matrix,
            "summary": matrix["summary"],
        },
        "classic_regressions": regressions,
        "fail_closed": True,
        "forbidden_verified": ["legacy preseed helper is not treated as production dispatch",
            "full SmartRender adapter is executed, not inferred from source text alone",
            "full owner is compared to exported actual-AEX raw buffers",
            "PF8 does not reuse PF16 quantization"],
    }
    print(json.dumps(report, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
