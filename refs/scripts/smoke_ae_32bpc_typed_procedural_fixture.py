#!/usr/bin/env python3
"""Guard the AE-only 32bpc procedural fixture contract."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
JSX = ROOT / "scripts" / "ae_generate_32bpc_typed_procedural_fixture.jsx"


def main() -> int:
    source = JSX.read_text(encoding="utf-8")
    required = (
        "OLM_AE_TYPED_FIXTURE_OUTPUT_DIR",
        "OLM_AE_TYPED_FIXTURE_TEMPLATE",
        "OLM_AE_TYPED_FIXTURE_PROJECT_PATH",
        "project.bitsPerChannel = 32",
        'project.workingSpace = ""',
        "project.linearBlending = false",
        'project.items.addComp("OLM_TYPED_SOURCE_64x64"',
        'sourceComp.layers.addSolid([0.0, 0.0, 0.0], "solid_background"',
        'name: "rect_integer_a25", x: 4, y: 4, width: 20, height: 16',
        'name: "rect_integer_a50", x: 28, y: 4, width: 20, height: 16',
        'name: "rect_integer_a75", x: 4, y: 28, width: 20, height: 16',
        'name: "rect_integer_a100", x: 28, y: 28, width: 20, height: 16',
        'effectName !== "OLM Color Key" && effectName !== "OLM Toon Dilate"',
        'addProperty(effectName)',
        'renderOne(renderComp, outputDir, "effect_no_effect.exr"',
        'renderOne(renderComp, outputDir, "effect_effect_on.exr"',
        'sourceLayer.enabled = false;',
        'effectLayer.enabled = true;',
        r'\"source_policy\": \"AE-generated solids only; no footage imported\"',
        r'\"render_policy\": \"same comp, only branch enabled state changes\"',
        r'\"reject missing no-effect or effect-on EXR\"',
    )
    missing = [needle for needle in required if needle not in source]
    if missing:
        raise SystemExit(f"typed procedural fixture contract missing: {missing}")
    forbidden = ("importFile", "ImportOptions", "readText(")
    found_forbidden = [needle for needle in forbidden if needle in source]
    if found_forbidden:
        raise SystemExit(f"fixture must not import/read pixel sources: {found_forbidden}")
    if source.count("requireEmpty(") < 4:
        raise SystemExit("fixture must fail closed on stale/missing outputs")
    if source.count("fail(") < 8:
        raise SystemExit("fixture failure guards are unexpectedly sparse")
    print("[OK] AE-only 32bpc typed procedural fixture contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
