#!/usr/bin/env python3
"""Audit KiraKira Highlight Radius/Color boundaries for Blur Modes 3 and 4.

This is deliberately evidence-only. It consumes the checked-in decomp/asm and
the bounded actual-AEX Mode 3 witness; it does not tune or compare PNGs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
MODE3 = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_output_actual_aex_20260713.json"
OUT_JSON = ROOT / "refs/conformance/olmkirakira_highlight_modes34_20260718.json"
OUT_MD = ROOT / "refs/conformance/olmkirakira_highlight_modes34_20260718.md"


def section(text: str, start: str, end: str) -> str:
    return text[text.index(start):text.index(end, text.index(start))]


def main() -> int:
    decomp = section(
        DECOMP.read_text(encoding="utf-8"),
        "// === FUN_18114f4a0 @ 18114f4a0 ===",
        "// === FUN_18114fd90 @ 18114fd90 ===",
    )
    asm = section(
        ASM.read_text(encoding="utf-8"),
        "; === FUN_18114f4a0 @ 18114f4a0 ===",
        "; === FUN_18114fd90 @ 18114fd90 ===",
    )
    inner_d = section(
        DECOMP.read_text(encoding="utf-8"),
        "// === FUN_181150790 @ 181150790 ===",
        "// === FUN_1811512a0 @ 1811512a0 ===",
    )
    inner_a = section(
        ASM.read_text(encoding="utf-8"),
        "; === FUN_181150790 @ 181150790 ===",
        "; === FUN_1811512a0 @ 1811512a0 ===",
    )
    source = SOURCE.read_text(encoding="utf-8")
    mode3 = json.loads(MODE3.read_text(encoding="utf-8"))

    # The fifth layer is the Highlight layer: the helper creates its odd
    # square kernel before dispatching on the blur mode.
    highlight_common = all(item in decomp for item in (
        "if ((int)uVar11 == 4)",
        "iVar6 = iVar6 * 2 + 1",
        "*pfVar8 = (float)(iVar6 * iVar6)",
    ))
    mode3_dispatch = all(item in decomp for item in (
        "if (param_10 == 3)",
        "FUN_181272ec0(&local_630,local_618,CONCAT44(iVar6,iVar6));",
        "break;",
    ))
    mode4_dispatch = all(item in decomp for item in (
        "if (param_10 != 4)",
        "FUN_181280bc0(local_618,&local_630,*puVar4 & 7,uVar14);",
    )) and decomp.count("FUN_181280bc0(local_618,&local_630,*puVar4 & 7,uVar14);") >= 3
    mode4_gain_update = "fVar13 = *pfVar8 * *pfVar8" in decomp

    # These are direct x86 facts from the exact mode-3 caller and the mode-4
    # inline loop. They guard against accidentally auditing a similarly named
    # helper in another AEX generation.
    asm_anchors = {
        "mode3_call": "18114fa27  CALL 0x181272ec0" in asm,
        "mode3_return_jump": "18114fa2c  JMP 0x18114fbbb" in asm,
        "mode4_three_box_calls": inner_a.count("CALL 0x181280bc0") >= 3,
        "mode4_odd_kernel": "181150979  LEA EAX,[RSI + 0x1]" in inner_a,
        "mode4_gain_update": "181150f3d  NEG R15D" in inner_a,
    }

    actual_execution = mode3.get("execution", {})
    output = mode3.get("output_capture", {}).get("output_array_after", {})
    mat = output.get("mat", {}) if isinstance(output, dict) else {}
    actual_witness = {
        "status": mode3.get("status"),
        "scope": "direct_FUN_181150790_helper_witness_not_full_fifth_layer_end_to_end",
        "aex_sha256": actual_execution.get("aex_sha256"),
        "helper": "0x181150790",
        "gaussian_entry": actual_execution.get("entry"),
        "caller_return": actual_execution.get("caller_return"),
        "entry_hit_count": actual_execution.get("entry_hit_count"),
        "return_hit_count": actual_execution.get("return_hit_count"),
        "input_shape": actual_execution.get("input_shape"),
        "size": (mode3.get("entry_capture") or [{}])[0].get("size"),
        "sigma_x": (mode3.get("entry_capture") or [{}])[0].get("sigma_x_f64"),
        "output_word_count": mat.get("word_count"),
        "output_nonzero_word_count": mat.get("nonzero_word_count"),
    }

    # Highlight Color is not loaded by FUN_18114f4a0's blur helper. It is a
    # later aggregation input. Therefore no Mode 3/4-specific color transform
    # is claimed by this audit.
    color_boundary = {
        "helper_reads_radius_layer_only": highlight_common,
        "helper_contains_highlight_color_load": False,
        "source_color_application": "AddColoredUnion(glow, highlight, info.highlight_color, scale)",
        "mode_specific_color_transform_proven": False,
    }
    facts = [
        "FUN_18114f4a0 treats uVar11 == 4 as the fifth layer, derives an odd square size (2r+1)^2, and stores that layer's scalar factor before blur dispatch.",
        "Mode 3 dispatches the fifth layer to FUN_181272ec0, whose embedded error path identifies it as OpenCV 4.5.5 GaussianBlur.",
        "The bounded actual-AEX Mode 3 helper witness reaches the Gaussian call and captures the returned CV_32FC1 buffer; it does not execute the full fifth-layer caller end-to-end.",
        "Mode 4 stays in FUN_18114f4a0's inline path and invokes FUN_181280bc0 three times, followed by a scalar gain update.",
        "Highlight Color is consumed by the later aggregation step, not by the mode-specific blur helper.",
    ]
    inferences = [
        "Mode 3 Highlight Radius requires GaussianBlur kernel/border/writeback equivalence; the current Mac box scaffold is not a grounded implementation of that mode.",
        "Mode 4 Highlight Radius requires the inline recurrence, pass order, edge policy, and gain/writeback semantics; the three-call observation is insufficient to implement it safely.",
        "No Mode 3/4-specific Highlight Color transform is justified by the recovered helper; color should remain a shared aggregation contract until a caller witness proves otherwise.",
    ]
    report = {
        "schema": 1,
        "kind": "olmkirakira_highlight_modes34_audit",
        "date": "2026-07-18",
        "status": "blocked_mode34_radius_semantics_color_shared_boundary",
        "ae_exact_claim": False,
        "production_edit": False,
        "binary": {"path": str(AEX.relative_to(ROOT)), "sha256": hashlib.sha256(AEX.read_bytes()).hexdigest()},
        "static": {
            "highlight_common": highlight_common,
            "mode3_dispatch": mode3_dispatch,
            "mode4_dispatch": mode4_dispatch,
            "mode4_gain_update": mode4_gain_update,
            "asm_anchors": asm_anchors,
        },
        "actual_aex_witness": actual_witness,
        "highlight_color_boundary": color_boundary,
        "FACT": facts,
        "INFERENCE": inferences,
        "next_evidence": {
            "mode3": "same-run actual-AEX capture with Highlight Radius values 0, 1, 2 and output of the fifth-layer buffer before color aggregation",
            "mode4": "same-run actual-AEX capture at the inline three-call body with radius and scalar/gain state at each writeback",
            "color": "one caller/aggregation witness varying only Highlight Color while holding the fifth-layer scalar fixed",
        },
    }
    if not all(asm_anchors.values()) or not all((highlight_common, mode3_dispatch, mode4_dispatch, mode4_gain_update)):
        raise AssertionError("missing binary anchor")
    if actual_witness["status"] != "captured" or actual_witness["output_word_count"] != 63:
        raise AssertionError(f"actual-AEX Mode 3 witness is not captured: {actual_witness}")
    if "if (highlight_radius > 0 && (info.blur_mode == 1 || info.blur_mode == 2))" not in source:
        raise AssertionError("production source no longer fail-closed for Mode 3/4 highlight")
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text("""# OLMKiraKira Highlight Modes 3/4 Audit (2026-07-18)

Status: **blocked_mode34_radius_semantics_color_shared_boundary**
AE exact: **false**
Production edit: **none**

## Result

The fifth layer is statically identified as Highlight. Its radius becomes an
odd square kernel, `(2r+1) x (2r+1)`, before the blur-mode dispatch.

| Mode | Recovered path | What is proven | What remains unproven |
| --- | --- | --- | --- |
| 3 | `FUN_181272ec0` | Direct helper witness reaches embedded OpenCV 4.5.5 `GaussianBlur` and returns 63 `CV_32FC1` words | full fifth-layer caller binding, kernel/border/writeback contract for all Highlight Radius values, and pre-aggregation Highlight buffer |
| 4 | inline body in `FUN_18114f4a0` | Three `FUN_181280bc0` calls and a scalar gain update are present | recurrence, pass order, edge policy, gain normalization, and writeback contract |

## Highlight Color

The recovered blur helper handles a scalar layer buffer. It does not load the
Highlight Color there. The color is applied later by the shared aggregation
operation (`AddColoredUnion` in the Mac port). No Mode 3/4-specific color
transform is proven, so this audit does not change color handling.

## Evidence

- Static sources: `decomp/OLMKiraKira.aex.c.txt`, `disasm/OLMKiraKira.aex.asm.txt`.
- Actual-AEX witness: `refs/conformance/olmkirakira_mode3_gaussian_output_actual_aex_20260713.json`.
- Witness scope: direct `FUN_181150790` helper invocation; it is not a full `FUN_18114f4a0` fifth-layer end-to-end capture.
- Mode 3 call: `0x18114fa27 -> 0x181272ec0`, return capture at `0x181151105`.
- Mode 4 body: `0x181150979..0x181150f3a`, with three calls to `0x181280bc0`.

## Decision

Do not replace the current Mode 3/4 placeholder with a conventional Gaussian,
recursive blur, or PNG-tuned approximation. The production source remains
fail-closed for Highlight Radius in Modes 3/4. The next useful Windows/AEX
witness is a same-run capture of the fifth-layer buffer before color
aggregation, followed by a separate Highlight Color-only caller witness.

## Re-run

`python3 tools/emulation/audit_olmkirakira_highlight_modes34_20260718.py`

`python3 tools/emulation/test_olmkirakira_highlight_modes34_20260718.py`
""", encoding="utf-8")
    print("PASS_OLMKIRAKIRA_HIGHLIGHT_MODES34_AUDIT")
    print(json.dumps({"status": report["status"], "mode3": actual_witness, "production_edit": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
