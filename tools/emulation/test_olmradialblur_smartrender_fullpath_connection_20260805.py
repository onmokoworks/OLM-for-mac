#!/usr/bin/env python3
"""Fail-closed SmartRender-to-installed connection audit for OLMRadialBlur."""

import json, subprocess
from pathlib import Path
from olm_installed_identity import MANIFEST, verified_binary

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
PF32_REPORT = ROOT / "refs/conformance/olmradialblur_zoom_pf32_small_actual_aex_20260805.json"
REPORT = ROOT / "refs/conformance/olmradialblur_smartrender_fullpath_connection_20260805.json"


def main():
    source = SOURCE.read_text()
    smart = source[source.index("SmartRender(PF_InData"):source.index("extern \"C\" DllExport", source.index("SmartRender(PF_InData"))]
    effect = source[source.index("EffectMain("):]
    gates = {
        "effectmain_dispatches_smart_render": "case PF_Cmd_SMART_RENDER:" in effect and "SmartRender(in_data" in effect,
        "checkout_input_then_output": smart.index("checkout_layer_pixels") < smart.index("checkout_output"),
        "all_public_params_checked_out": "for (int i = 1; !err && i < OLMRADIALBLUR_NUM_PARAMS; ++i)" in smart and "PF_CHECKOUT_PARAM" in smart,
        "pre_render_dimensions_consumed": "pre_render_data" in smart and "pre->comp_width" in smart and "pre->comp_height" in smart,
        "smart_bitdepth_routes_staged_renderworld": "RenderWorld(input_world, &staged_world, noise_world, info" in smart,
        "input_checked_in": (
            "input_checked_out = err == PF_Err_NONE;" in smart and
            "if (input_checked_out)" in smart and
            "OLMRADIALBLUR_INPUT" in smart and "checkin_layer_pixels" in smart),
        "noise_checked_in_when_checked_out": (
            "noise_checked_out = err == PF_Err_NONE;" in smart and
            "if (noise_checked_out)" in smart and
            "OLMRADIALBLUR_NOISE_LAYER" in smart and "checkin_layer_pixels" in smart),
        "cleanup_precedes_atomic_commit": (
            smart.index("if (thrown) std::rethrow_exception(thrown)") <
            smart.index("if (!err && render_complete)") and
            "staged_output" in smart and "active_row_bytes" in smart),
    }
    pf32 = json.loads(PF32_REPORT.read_text())
    binary, row = verified_binary("OLMRadialBlur")
    arch = subprocess.run(["lipo", "-archs", str(binary)], capture_output=True, text=True, check=True).stdout.split()
    subprocess.run(["codesign", "--verify", "--deep", "--strict", row["installed_bundle"]], check=True)
    gates.update({
        "pf32_actual_to_renderworld_exact": pf32.get("status") == "exact" and pf32.get("production_dispatch", "").startswith("final compared output is emitted by OLMRadialBlurTestRenderWorld"),
        "pf32_pre_post_output_exact": all(pf32.get("matches", {}).values()),
        "installed_identity_exact": True,
        "installed_universal": set(arch) == {"arm64", "x86_64"},
    })
    report = {
        "kind": "olmradialblur_smartrender_fullpath_connection_20260805",
        "status": "current_source_connected_installed_identity_separate" if all(gates.values()) else "blocked",
        "connection": ["EffectMain(PF_Cmd_SMART_RENDER)", "SmartRender callbacks/param checkout", "private staged RenderWorld(bitdepth=32)", "cleanup", "active-row commit"],
        "gates": gates,
        "installed": {"path": str(binary), "sha256": row["sha256"], "architectures": arch, "identity_manifest": str(MANIFEST.relative_to(ROOT))},
        "actual_production_evidence": str(PF32_REPORT.relative_to(ROOT)),
        "claim_boundary": "AE-free current-source compositional audit plus a separate historical installed-identity check. The current cleanup candidate is not installed, so no source-to-installed equality, AE process, native host callback ABI, or new numerical tuple is claimed.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "current_source_connected_installed_identity_separate" else 1


if __name__ == "__main__":
    raise SystemExit(main())
