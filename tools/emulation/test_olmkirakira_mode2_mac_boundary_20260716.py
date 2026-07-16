#!/usr/bin/env python3
"""Bounded Mac-only Mode-2 float/compose/writeback fixture.

This is an executable local model of the checked-in Mac source boundary.  It
does not load a plug-in, bind an AE host, or assert AE exactness.
"""

from __future__ import annotations

import math
import struct
from pathlib import Path

from aex_loader import AexLoader


ROOT = Path(__file__).resolve().parents[2]
MAC_SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
MODE2_WITNESS = ROOT / "refs/conformance/olmkirakira_mode2_compose_witness_20260716.json"
AEX_PATH = ROOT / "plugins_2025/OLMKiraKira.aex"
AEX_PF8_SCALE = 0x1814D65A8
AEX_PF16_SCALE = 0x1814D65AC


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def f32_hex(value: float) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


def cpp_lround(value: float) -> int:
    # Values are non-negative in this fixture; this is C++ lround's halfway
    # rule, unlike Python's bankers-rounding round().
    return math.floor(value + 0.5)


def screen_over(source_rgb: tuple[float, float, float], glow_rgba: tuple[float, float, float, float],
                source_opacity: float, glow_opacity: float) -> tuple[float, float, float, float]:
    src_a = f32(source_opacity * 1.0)
    glow_a = f32(max(0.0, min(1.0, f32(glow_rgba[3] * glow_opacity))))
    result = []
    for src, glow in zip(source_rgb, glow_rgba[:3]):
        src = f32(src)
        glow = f32(glow)
        result.append(f32(1.0 - f32(f32(1.0 - src) * f32(1.0 - f32(glow * glow_a)))))
    return (*result, f32(src_a))


def writeback(rgba: tuple[float, float, float, float], scale: int | None) -> tuple[int | float, ...]:
    if scale is None:
        return tuple(f32(max(0.0, min(1.0, value))) for value in rgba)
    return tuple(cpp_lround(max(0.0, min(1.0, value)) * scale) for value in rgba)


def main() -> int:
    source = MAC_SOURCE.read_text(encoding="utf-8")
    evidence = __import__("json").loads(MODE2_WITNESS.read_text(encoding="utf-8"))
    loader = AexLoader(str(AEX_PATH), fast=True)
    aex_pf8_scale = struct.unpack("<f", bytes(loader.uc.mem_read(AEX_PF8_SCALE, 4)))[0]
    aex_pf16_scale = struct.unpack("<f", bytes(loader.uc.mem_read(AEX_PF16_SCALE, 4)))[0]
    static = {
        "mac_reads_normalized_8bpc": "p.red / 255.0f" in source and "p.alpha / 255.0f" in source,
        "mac_reads_normalized_16bpc": "p.red / static_cast<float>(PF_MAX_CHAN16)" in source and "p.alpha / static_cast<float>(PF_MAX_CHAN16)" in source,
        "mac_reads_float32": "return {p.red, p.green, p.blue, p.alpha};" in source,
        "mac_screen_over_rgb": "1.0f - (1.0f - src.r) * (1.0f - Clamp01(glow[idx].r * glow_a))" in source,
        "mac_source_alpha_only": "out.a = src_a;" in source,
        "mac_pf8_lround": "Clamp01(p.a) * 255.0f" in source and "Clamp01(p.r) * 255.0f" in source,
        "mac_pf16_lround": "Clamp01(p.a) * PF_MAX_CHAN16" in source and "Clamp01(p.r) * PF_MAX_CHAN16" in source,
        "mac_pf32_clamp": "out.alpha = Clamp01(p.a);" in source and "out.red   = Clamp01(p.r);" in source,
        "mode2_witness_pass": evidence["status"] == "pass" and evidence["ae_exact_claim"] is False,
        "aex_pf8_scale_255": aex_pf8_scale == 255.0,
        "aex_pf16_scale_32768": aex_pf16_scale == 32768.0,
    }

    # The Mode-2 witness's one_short_ray post-clamp float is the local glow
    # input. Source is a checked-in Mac compose-boundary style opaque gray pixel.
    mode2_glow = tuple(
        struct.unpack("<f", struct.pack("<I", int(bits, 16)))[0]
        for bits in evidence["cases"]["one_short_ray"]["post_clamp_f32"]
    )
    source_rgb = tuple(f32(30.0 / 255.0) for _ in range(3))
    composed = screen_over(source_rgb, mode2_glow, 1.0, 1.0)
    result = {
        "mode2_post_clamp_rgba_f32": [f32_hex(value) for value in mode2_glow],
        "compose_inputs": {
            "source_rgba_f32": [f32_hex(value) for value in (*source_rgb, 1.0)],
            "source_opacity": 1.0,
            "glow_opacity": 1.0,
            "formula": "rgb=1-(1-source.rgb)*(1-glow.rgb*clamp(glow.a*glow_opacity)); alpha=source.a*source_opacity",
        },
        "pre_writeback_rgba_f32": [f32_hex(value) for value in composed],
        "pre_writeback_rgba_decimal": list(composed),
        "conversion": {
            "PF8": writeback(composed, 255),
            "PF16": writeback(composed, 32768),
            "PF32": [f32_hex(value) for value in writeback(composed, None)],
        },
        "static_checks": static,
        "facts": [
            "FACT: the Mode-2 input float comes from the checked-in post-clamp one_short_ray witness.",
            "FACT: the Mac source contains the normalized-channel, screen-over, source-alpha, and typed writer expressions checked above.",
            "FACT: PF8/PF16 use C++ lround after clamp and PF32 clamps normalized float channels in this Mac source.",
            "FACT: the checked-in AEX writer constants are 255.0 for PF8 and 32768.0 for PF16.",
        ],
        "inferences": [
            "INFERENCE: this Python replay is a bounded local fixture for the operation order; it is not a host-bound execution trace.",
            "INFERENCE: the derived PF8/PF16/PF32 tuples are expected Mac-source results for these supplied inputs, not AE output claims.",
        ],
        "limits": [
            "No production source, host binding, writer address, PNG, Windows result, or AE exactness is claimed.",
        ],
    }
    failed = [name for name, passed in static.items() if not passed]
    print(__import__("json").dumps(result, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
