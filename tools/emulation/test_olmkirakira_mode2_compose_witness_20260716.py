#!/usr/bin/env python3
"""Run the smallest local Mode-2 inner-compose witness.

This deliberately stops inside FUN_18114ffd0.  It is a static AEX/decomp
check plus an independent one-pixel float32 model, not a production render or
an After Effects/Windows claim.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DECOMP = ROOT / "decomp" / "OLMKiraKira.aex.c.txt"
ASM = ROOT / "disasm" / "OLMKiraKira.aex.asm.txt"
AEX = ROOT / "aex" / "OLMKiraKira" / "Plugins" / "64" / "2025" / "OLMKiraKira.aex"
OUTPUT = ROOT / "refs" / "conformance" / "olmkirakira_mode2_compose_witness_20260716.json"
THRESHOLD_ADDRESS = 0x181489990

sys.path.insert(0, str(ROOT / "tools" / "emulation"))
from aex_loader import AexLoader  # noqa: E402


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def bits(value: float) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


def clamp(value: float) -> float:
    return f32(max(0.0, min(1.0, f32(value))))


def model(rays: list[float], colors: list[tuple[float, float, float]], threshold: float = 0.0) -> dict:
    pre = [f32(0.0)] * 4
    active = []
    for index, (ray, color) in enumerate(zip(rays, colors)):
        ray = f32(ray)
        if ray <= threshold:
            active.append({"index": index, "ray": bits(ray), "skipped": True})
            continue
        for channel in range(3):
            pre[channel] = f32(pre[channel] + f32(color[channel]))
        pre[3] = f32(pre[3] + ray)
        active.append({"index": index, "ray": bits(ray), "skipped": False})
    post = [clamp(value) for value in pre]
    return {
        "active_or_skipped": active,
        "pre_clamp_f32": [bits(value) for value in pre],
        "post_clamp_f32": [bits(value) for value in post],
    }


def static_checks() -> dict[str, bool]:
    decomp = DECOMP.read_text(encoding="utf-8")
    asm = ASM.read_text(encoding="utf-8")
    d_start = decomp.index("// === FUN_18114ffd0 @ 18114ffd0 ===")
    d_end = decomp.index("// === FUN_1811501b0 @ 1811501b0 ===", d_start)
    a_start = asm.index("; === FUN_18114ffd0 @ 18114ffd0 ===")
    a_end = asm.index("; === FUN_1811501b0 @ 1811501b0 ===", a_start)
    d_body = decomp[d_start:d_end]
    a_body = asm[a_start:a_end]
    return {
        "target_marker": "FUN_18114ffd0 @ 18114ffd0" in d_body and "FUN_18114ffd0 @ 18114ffd0" in a_body,
        "zero_fill_before_iteration": "FUN_181150250(param_7,iVar3 * 4" in d_body and "CALL 0x181150250" in a_body,
        "five_ray_iterations": "lVar9 = 5" in d_body and "MOV R15D,0x5" in a_body and "SUB R15,0x1" in a_body,
        "threshold_skip": "fVar10 <= dVar1" in d_body and "COMISD XMM0,XMM7" in a_body and "JBE 0x1811500f2" in a_body,
        "raw_rgb_add": "fStack_7c + *param_7" in d_body and "ADDSS XMM2,dword ptr [RDI]" in a_body,
        "raw_alpha_add": "param_7[3] = fVar10 + param_7[3]" in d_body and "ADDSS XMM6,dword ptr [RDI + 0xc]" in a_body,
        "four_independent_clamps": d_body.count("FUN_181156740") >= 4 and a_body.count("CALL 0x181156740") == 4,
    }


def read_threshold() -> tuple[float, str]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    raw = loader.read_bytes(THRESHOLD_ADDRESS, 8)
    return struct.unpack("<d", raw)[0], raw.hex()


def model_checks(threshold: float) -> tuple[dict[str, bool], dict[str, dict]]:
    colors = [(0.25, 0.5, 0.75)] * 5
    cases = {
        "zero_ray_control": ([0.0] * 5, colors),
        "one_short_ray": ([0.2, 0.0, 0.0, 0.0, 0.0], colors),
        "threshold_boundary": ([0.0005, 0.002, 0.0, 0.0, 0.0], colors),
        "five_active_saturating": ([0.8] * 5, [(0.9, 0.1, 0.0)] * 5),
    }
    observed = {
        name: model(rays, case_colors, threshold)
        for name, (rays, case_colors) in cases.items()
    }
    checks = {
        "zero_ray_is_noop": observed["zero_ray_control"]["post_clamp_f32"] == ["0x00000000"] * 4,
        "short_ray_adds_raw_rgb_alpha": observed["one_short_ray"]["pre_clamp_f32"] == [
            "0x3e800000", "0x3f000000", "0x3f400000", "0x3e4ccccd"
        ],
        "binary_threshold_skips_below_and_accepts_above": observed["threshold_boundary"]["pre_clamp_f32"] == [
            "0x3e800000", "0x3f000000", "0x3f400000", "0x3b03126f"
        ],
        "five_active_rays_clamp_independently": observed["five_active_saturating"]["post_clamp_f32"] == [
            "0x3f800000", "0x3f000000", "0x00000000", "0x3f800000"
        ],
    }
    return checks, observed


def main() -> int:
    static = static_checks()
    threshold, threshold_raw = read_threshold()
    model_result, cases = model_checks(threshold)
    report = {
        "kind": "olmkirakira_mode2_compose_witness",
        "schema": 1,
        "date": "2026-07-16",
        "status": "pass" if all(static.values()) and all(model_result.values()) else "failed",
        "ae_exact_claim": False,
        "scope": "one-pixel inner Mode-2 FUN_18114ffd0 aggregation/compose boundary; no PNG tuning",
        "inputs": {
            "decomp": str(DECOMP.relative_to(ROOT)),
            "disasm": str(ASM.relative_to(ROOT)),
            "aex": str(AEX.relative_to(ROOT)),
            "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
            "decomp_sha256": hashlib.sha256(DECOMP.read_bytes()).hexdigest(),
            "disasm_sha256": hashlib.sha256(ASM.read_bytes()).hexdigest(),
            "target": "FUN_18114ffd0 @ 0x18114ffd0",
            "clamp": "FUN_181156740 @ 0x181156740",
            "threshold": {
                "address": f"0x{THRESHOLD_ADDRESS:x}",
                "raw_le_f64": threshold_raw,
                "value": threshold,
            },
        },
        "static_checks": static,
        "model_checks": model_result,
        "cases": cases,
        "facts": [
            "FACT: the target zero-fills the output and visits five ray slots per pixel.",
            "FACT: active slots add selected RGB directly and raw ray value to alpha before four channel clamps.",
            "FACT: the AEX compares ray value against DAT_181489990 before the active-slot path.",
            "FACT: DAT_181489990 is the little-endian float64 value 0.001 in the pinned AEX.",
        ],
        "inferences": [
            "INFERENCE: the independent float32 replay is a faithful local witness of this bounded operation order.",
            "INFERENCE: the independent float32 replay is bounded to the pinned AEX threshold and observed operation order.",
        ],
        "limits": [
            "This does not prove later source/glow composition, host binding, Windows output, or AE exactness.",
            "Final PNG bytes are intentionally outside the witness.",
        ],
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "static": sum(static.values()), "model": sum(model_result.values()), "output": str(OUTPUT)}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
