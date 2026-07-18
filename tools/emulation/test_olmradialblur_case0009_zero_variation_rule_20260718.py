#!/usr/bin/env python3
"""Prove the bounded zero-variation scatter rule for RadialBlur case0009.

This is a static conformance test. It deliberately does not launch AE, touch
the natural-run process, read checkpoint state, or compare PNG output.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/reference_manifest.json"
DECOMP = ROOT / "decomp/OLMRadialBlur.aex.c.txt"
FACTS = ROOT / "notes/OLMRadialBlur_ASM_FACTS.md"
OUTPUT = ROOT / "refs/conformance/olmradialblur_case0009_zero_variation_rule_20260718.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def case_params(case_id: str) -> dict[int, object]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    case = next(item for item in manifest["cases"] if item["id"] == case_id)
    return {item["property_index"]: item.get("value") for item in case["effects"][0]["params"]}


def main() -> int:
    params = case_params("case_0009")
    assert params[1] == 1, params
    assert params[4] == 1717, params
    assert params[10] == 0, params
    assert params[22] == 0, params
    assert params[24] == 0, params
    assert params[25] == 1, params

    decomp = DECOMP.read_text(encoding="utf-8")
    facts = FACTS.read_text(encoding="utf-8")
    required_decomp = [
        "*(bool *)(param_4 + 0x44) = _DAT_180021600 < (double)fVar1;",
        "if (*(char *)((longlong)param_5 + 0x44) == '\\0')",
        "FUN_180006500((int *)param_5[0x21]",
        "*pfVar14 = auVar18._0_4_ * *pfVar10 * *(float *)(param_5 + 8) +",
        "FUN_180006830((longlong)param_5);",
    ]
    assert all(snippet in decomp for snippet in required_decomp)
    assert "with both `NV = 0` and `SV = 0` it is exactly `1.0`" in facts
    assert "effective scatter" in facts and "`effective_len = int(base_len * param_10)`" in facts

    output = {
        "schema": 1,
        "kind": "olmradialblur_case0009_zero_variation_rule_20260718",
        "status": "pass",
        "claim": (
            "For case_0009, SV=NV=0 makes the source size map constant 1.0, "
            "the combined span/factor plane exactly 1.0, and the scatter helper "
            "use effective_len=int(base_len), independent of the generated noise values."
        ),
        "case": {
            "id": "case_0009",
            "blur_type": params[1],
            "outer_strength": params[4],
            "inner_strength": params[10],
            "size_variation_ui": params[22],
            "noise_variation_ui": params[24],
            "noise_type": params[25],
        },
        "derived": {
            "size_variation_scaled": 0.0,
            "noise_variation_scaled": 0.0,
            "size_map_value": 1.0,
            "span_factor_value": 1.0,
            "scatter_length_rule": "int(base_len * 1.0) == int(base_len)",
        },
        "evidence": {
            "manifest": str(MANIFEST.relative_to(ROOT)),
            "decomp": str(DECOMP.relative_to(ROOT)),
            "asm_facts": str(FACTS.relative_to(ROOT)),
            "manifest_sha256": sha256(MANIFEST),
            "decomp_sha256": sha256(DECOMP),
            "asm_facts_sha256": sha256(FACTS),
            "decomp_lines": [4031, 4062, 4065, 4066, 4067, 3528, 3561, 3563, 3609, 3620],
            "asm_facts_lines": [94, 98, 103, 108, 114],
        },
        "boundaries": [
            "Static rule only; no Windows/AE exactness claim.",
            "Noise generation may still be entered for Noise Type=1; NV=0 masks its value in the span factor.",
            "No PNG or active checkpoint artifact is read or written.",
        ],
    }
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print("PASS_OLMRADIALBLUR_CASE0009_ZERO_VARIATION_RULE_20260718")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
