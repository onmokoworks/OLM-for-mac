#!/usr/bin/env python3
"""Fail-closed SmartRender-to-installed connection audit for OLMRadialBlur."""

import hashlib, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
PF32_REPORT = ROOT / "refs/conformance/olmradialblur_zoom_pf32_small_actual_aex_20260805.json"
REPORT = ROOT / "refs/conformance/olmradialblur_smartrender_fullpath_connection_20260805.json"
BINARY = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMRadialBlur.plugin/Contents/MacOS/OLMRadialBlur"
EXPECTED_BINARY = "2e079e3c168666c2f3509f8d4c90ab107301880bce43f538cf4e16bcb8047732"


def main():
    source = SOURCE.read_text()
    smart = source[source.index("SmartRender(PF_InData"):source.index("extern \"C\" DllExport", source.index("SmartRender(PF_InData"))]
    effect = source[source.index("EffectMain("):]
    gates = {
        "effectmain_dispatches_smart_render": "case PF_Cmd_SMART_RENDER:" in effect and "SmartRender(in_data" in effect,
        "checkout_input_then_output": smart.index("checkout_layer_pixels") < smart.index("checkout_output"),
        "all_public_params_checked_out": "for (int i = 1; i < OLMRADIALBLUR_NUM_PARAMS; ++i)" in smart and "PF_CHECKOUT_PARAM" in smart,
        "pre_render_dimensions_consumed": "pre_render_data" in smart and "pre->comp_width" in smart and "pre->comp_height" in smart,
        "smart_bitdepth_routes_renderworld": "RenderWorld(input_world, output_world, info, extra->input->bitdepth)" in smart,
        "input_checked_in": "checkin_layer_pixels" in smart,
    }
    pf32 = json.loads(PF32_REPORT.read_text())
    binary_hash = hashlib.sha256(BINARY.read_bytes()).hexdigest() if BINARY.is_file() else None
    arch = subprocess.run(["lipo", "-archs", str(BINARY)], capture_output=True, text=True).stdout.split() if BINARY.is_file() else []
    gates.update({
        "pf32_actual_to_renderworld_exact": pf32.get("status") == "exact" and pf32.get("production_dispatch", "").startswith("final compared output is emitted by OLMRadialBlurTestRenderWorld"),
        "pf32_pre_post_output_exact": all(pf32.get("matches", {}).values()),
        "installed_identity_exact": binary_hash == EXPECTED_BINARY,
        "installed_universal": sorted(arch) == ["arm64", "x86_64"],
    })
    report = {
        "kind": "olmradialblur_smartrender_fullpath_connection_20260805",
        "status": "connected" if all(gates.values()) else "blocked",
        "connection": ["EffectMain(PF_Cmd_SMART_RENDER)", "SmartRender callbacks/param checkout", "RenderWorld(bitdepth=32)", "RenderZoomTyped<PF_PixelFloat>", "pre/post planes", "FUN_180017490 writer", "current installed Universal binary"],
        "gates": gates,
        "installed": {"path": str(BINARY), "sha256": binary_hash, "architectures": arch},
        "actual_production_evidence": str(PF32_REPORT.relative_to(ROOT)),
        "claim_boundary": "AE-free compositional connection: public adapter structure is fail-closed source-audited and the exact RenderWorld path is executed; no AE process or host callback ABI is claimed dynamically.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "connected" else 1


if __name__ == "__main__":
    raise SystemExit(main())
