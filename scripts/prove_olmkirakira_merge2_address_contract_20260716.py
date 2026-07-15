#!/usr/bin/env python3
"""Prove the bounded Merge-Mode-2 aggregation contract from the pinned AEX.

This is a static/model proof.  It does not execute the Windows AEX or claim
After Effects equivalence.  The model is intentionally independent of the
production renderer and only covers FUN_18114ffd0 and FUN_181156740.
"""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DECOMP = ROOT / "decomp" / "OLMKiraKira.aex.c.txt"
ASM = ROOT / "disasm" / "OLMKiraKira.aex.asm.txt"
DEFAULT_JSON = ROOT / "refs" / "conformance" / "olmkirakira_merge2_address_contract_20260716.json"
EPSILON = 1.0e-5


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def clamp_aex(value: float) -> float:
    """FUN_181156740: max(min(value, 1.0), 0.0), with float32 stages."""
    value = f32(value)
    return f32(max(0.0, min(1.0, value)))


def merge2_model(rays: Iterable[float], colors: Iterable[tuple[float, float, float]]) -> tuple[float, float, float, float]:
    output = [f32(0.0), f32(0.0), f32(0.0), f32(0.0)]
    for ray, color in zip(rays, colors):
        ray = f32(ray)
        if ray <= EPSILON:
            continue
        for channel in range(3):
            output[channel] = f32(output[channel] + f32(color[channel]))
        output[3] = f32(output[3] + ray)
    return tuple(clamp_aex(value) for value in output)  # type: ignore[return-value]


def static_checks() -> dict[str, bool]:
    decomp = DECOMP.read_text(encoding="utf-8")
    asm = ASM.read_text(encoding="utf-8")
    decomp_start = decomp.index("// === FUN_18114ffd0 @ 18114ffd0 ===")
    decomp_end = decomp.index("// === FUN_1811501b0 @ 1811501b0 ===", decomp_start)
    body = decomp[decomp_start:decomp_end]
    asm_start = asm.index("; === FUN_18114ffd0 @ 18114ffd0 ===")
    asm_end = asm.index("; === FUN_1811501b0 @ 1811501b0 ===", asm_start)
    asm_body = asm[asm_start:asm_end]
    return {
        "decomp_function_address": "FUN_18114ffd0 @ 18114ffd0" in body,
        "decomp_zero_fill": "FUN_181150250(param_7,iVar3 * 4" in body,
        "decomp_five_layer_loop": "lVar9 = 5" in body and "lVar9 = lVar9 + -1" in body,
        "decomp_epsilon_skip": "fVar10 <= dVar1" in body,
        "decomp_direct_rgb_add": "fStack_7c + *param_7" in body,
        "decomp_raw_alpha_add": "param_7[3] = fVar10 + param_7[3]" in body,
        "decomp_per_channel_clamp": body.count("FUN_181156740") >= 4,
        "asm_address": "18114ffd0  MOV RAX,RSP" in asm_body,
        "asm_direct_rgb_add": "ADDSS XMM2,dword ptr [RDI]" in asm_body,
        "asm_raw_alpha_add": "ADDSS XMM6,dword ptr [RDI + 0xc]" in asm_body,
        "asm_four_clamp_calls": asm_body.count("CALL 0x181156740") == 4,
    }


def model_checks() -> dict[str, bool]:
    colors = [(0.25, 0.5, 0.75)] * 5
    boundary_ray = f32(EPSILON + 1.0e-4)
    return {
        "zero_rays_are_noop": merge2_model([0.0] * 5, colors) == (0.0, 0.0, 0.0, 0.0),
        "positive_rays_add_rgb_and_alpha": merge2_model([0.2, 0.3, 0.0, 0.0, 0.0], colors)
        == (0.5, 1.0, 1.0, 0.5),
        "rgb_and_alpha_clamp_independently": merge2_model([0.8] * 5, [(0.9, 0.1, 0.0)] * 5)
        == (1.0, 0.5, 0.0, 1.0),
        "epsilon_boundary_skips": merge2_model([EPSILON, boundary_ray, 0.0, 0.0, 0.0], colors)
        == (f32(0.25), f32(0.5), f32(0.75), boundary_ray),
    }


def build_report() -> dict:
    static = static_checks()
    model = model_checks()
    return {
        "kind": "olmkirakira_merge2_address_contract",
        "schema": 1,
        "date": "2026-07-16",
        "status": "pass" if all(static.values()) and all(model.values()) else "failed",
        "scope": "Mac-only static AEX/decomp and independent float32 model; no PNG tuning",
        "evidence_class": {
            "static": "binary-grounded address/instruction evidence",
            "model": "independent float32 replay of the decompiled operation order",
            "ae_exact": False,
        },
        "inputs": {
            "decomp": str(DECOMP.relative_to(ROOT)),
            "disasm": str(ASM.relative_to(ROOT)),
            "target": "FUN_18114ffd0 @ 0x18114ffd0",
            "clamp_target": "FUN_181156740 @ 0x181156740",
        },
        "static_checks": static,
        "model_checks": model,
        "facts": [
            "The mode-2 vtable target is a distinct function at 0x18114ffd0.",
            "Its output is zero-filled, then five ray layers are visited per pixel.",
            "Active layers add selected RGB directly and add raw ray to alpha.",
            "The four output channels are clamped independently through 0x181156740.",
        ],
        "limits": [
            "The proof does not establish the later source/glow compose formula for Merge Mode 2.",
            "The proof does not execute the Windows AEX or establish AE exactness.",
            "The model uses an explicit epsilon placeholder because DAT_181489990's numeric value is not resolved here.",
        ],
        "next_witness_design": {
            "host": "one Mac-prepared, Windows-executed AE Software witness only when available; do not infer from PNG",
            "cases": ["one nonzero short ray", "one zero-ray control", "five active rays with RGB sum above 1"],
            "breakpoints": [
                "0x18114ffd0 entry: bind module base and selected vtable slot",
                "0x181150250 return: bind output RGBA float address and zero-fill",
                "0x181150080: capture ray pointer, ray float, and selected color pointer for one pixel",
                "0x181150112: capture pre-clamp RGBA float",
                "0x181156740 entry/return: capture each channel clamp input/output",
            ],
            "acceptance": "same-run target/hash/base, five-layer order, raw additive pre-clamp values, and four clamp returns; final PNG is non-authoritative",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON)
    args = parser.parse_args()
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "static": sum(report["static_checks"].values()), "model": sum(report["model_checks"].values()), "output": str(args.output)}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
