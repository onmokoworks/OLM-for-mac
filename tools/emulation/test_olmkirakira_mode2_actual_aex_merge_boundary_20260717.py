#!/usr/bin/env python3
"""Execute the narrowest checked-in AEX Mode-2 merge boundary fixture.

This calls the actual Mode-2 aggregation target directly with one pixel and
five ray slots.  It intentionally stops at the target's float output: the
host compose and typed writer selection remain outside this fixture.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
REPORT = ROOT / "refs/conformance/olmkirakira_mode2_actual_aex_merge_boundary_20260717.json"
TARGET = 0x18114FFD0
COLOR_HELPER = 0x181232080
CLAMP = 0x181156740
WRITERS = (0x181230B90, 0x181230BD0, 0x181230C20)

sys.path.insert(0, str(ROOT / "tools" / "emulation"))
from aex_loader import AexLoader  # noqa: E402


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def bits(value: float) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


def make_case(rays: list[float], colors: list[float], flags: bytes) -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    ray_ptrs = []
    for ray in rays:
        address = loader.host_alloc(4)
        loader.write_bytes(address, struct.pack("<f", f32(ray)))
        ray_ptrs.append(address)
    ray_array = loader.host_alloc(5 * 8)
    loader.write_bytes(ray_array, struct.pack("<5Q", *ray_ptrs))
    color_array = loader.host_alloc(5 * 16)
    loader.write_bytes(color_array, struct.pack("<20f", *(colors * 5)))
    flag_array = loader.host_alloc(5)
    loader.write_bytes(flag_array, flags)
    ramp = loader.host_alloc(24)
    # One below-threshold ramp row is enough to exercise the helper without
    # introducing a broader color-table or host setup claim.
    loader.write_bytes(ramp, struct.pack("<I5f", 1, 0.0, 0.0, 1.0, 0.0, 0.0))
    output = loader.host_alloc(16)
    loader.write_bytes(output, b"\xa5" * 16)
    call = loader.call_function(
        TARGET,
        [0, ray_array, color_array, flag_array, ramp, 0, output, 1, 1],
        max_instructions=100_000,
    )
    observed = loader.read_f32_array(output, 4)
    return {
        "rays_f32_bits": [bits(v) for v in rays],
        "flags_hex": flags.hex(),
        "observed_output_rgba_f32_bits": [bits(v) for v in observed],
        "observed_output_rgba_f32": observed,
        "instructions": call["instructions"],
    }


def static_checks() -> dict[str, bool]:
    decomp = DECOMP.read_text(encoding="utf-8")
    asm = ASM.read_text(encoding="utf-8")
    d_start = decomp.index("// === FUN_18114ffd0 @ 18114ffd0 ===")
    d_end = decomp.index("// === FUN_1811501b0 @ 1811501b0 ===", d_start)
    a_start = asm.index("; === FUN_18114ffd0 @ 18114ffd0 ===")
    a_end = asm.index("; === FUN_1811501b0 @ 1811501b0 ===", a_start)
    d_body, a_body = decomp[d_start:d_end], asm[a_start:a_end]
    dispatch = decomp[decomp.index("// === FUN_18114f4a0 @ 18114f4a0 ==="):d_start]
    return {
        "mode2_target_and_dispatch": "param_15 == 2" in dispatch and f"FUN_{TARGET:x}" in d_body,
        "actual_aex_target_entry": f"{TARGET:x}  MOV RAX,RSP" in a_body,
        "five_ray_loop": "lVar9 = 5" in d_body and "SUB R15,0x1" in a_body,
        "threshold_branch": "fVar10 <= dVar1" in d_body and "JBE 0x1811500f2" in a_body,
        "conditional_merge_helper": f"FUN_{COLOR_HELPER:x}" in d_body and f"CALL 0x{COLOR_HELPER:x}" in a_body,
        "raw_rgb_alpha_accumulation": "param_7[3] = fVar10 + param_7[3]" in d_body,
        "four_clamps": d_body.count(f"FUN_{CLAMP:x}") >= 4 and a_body.count(f"CALL 0x{CLAMP:x}") == 4,
        "no_typed_writer_call": all(f"CALL 0x{address:x}" not in a_body for address in WRITERS),
    }


def main() -> int:
    static = static_checks()
    cases = {
        "raw_accumulation_control": make_case(
            [0.2, 0.0, 0.0, 0.0, 0.0], [0.0, 0.5, 0.75, 1.0], b"\0" * 5
        ),
        "merge_flag_color_helper": make_case(
            [0.2, 0.0, 0.0, 0.0, 0.0], [0.0, 0.5, 0.75, 1.0], b"\1\0\0\0\0"
        ),
        "five_active_ray_clamp": make_case(
            [0.8] * 5, [0.0, 0.9, 0.1, 0.0], b"\0" * 5
        ),
    }
    expected = {
        "raw_accumulation_control": ["0x3f000000", "0x3f400000", "0x3f800000", "0x3e4ccccd"],
        "merge_flag_color_helper": ["0x3f800000", "0x00000000", "0x00000000", "0x3e4ccccd"],
        "five_active_ray_clamp": ["0x3f800000", "0x3f000000", "0x00000000", "0x3f800000"],
    }
    actual = {name: case["observed_output_rgba_f32_bits"] == expected[name] for name, case in cases.items()}
    report = {
        "kind": "olmkirakira_mode2_actual_aex_merge_boundary",
        "schema": 1,
        "date": "2026-07-17",
        "status": "pass" if all(static.values()) and all(actual.values()) else "failed",
        "ae_exact_claim": False,
        "evidence_class": "actual checked-in AEX direct-call execution plus decomp/disassembly correlation",
        "inputs": {
            "aex": str(AEX.relative_to(ROOT)),
            "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
            "target": f"FUN_{TARGET:x} @ 0x{TARGET:x}",
            "conditional_color_helper": f"FUN_{COLOR_HELPER:x} @ 0x{COLOR_HELPER:x}",
            "fixture_shape": "one pixel, five one-float ray planes, five inline RGBA colors, five merge flags",
        },
        "static_checks": static,
        "actual_aex_checks": actual,
        "cases": cases,
        "facts": [
            "FACT: the actual pinned AEX Mode-2 target executes with one pixel and five ray slots.",
            "FACT: with flags clear, the active ray contributes selected RGB directly and raw ray value to alpha.",
            "FACT: setting one per-ray flag executes FUN_181232080 before the same accumulation site and changes the selected color.",
            "FACT: the target applies four clamps and returns float RGBA; it contains no PF8/PF16/PF32 writer call.",
            "FACT: the target compares ray values against DAT_181489990, which is 0.001 in the pinned AEX.",
        ],
        "inferences": [
            "INFERENCE: Merge Mode 2 is proven to affect aggregation dispatch and, within this target, the conditional per-ray color path.",
            "INFERENCE: this fixture does not establish a later host compose formula or typed writer selection.",
        ],
        "limits": [
            "Direct Unicorn invocation is not Windows/After Effects host execution.",
            "Final PNG bytes and AE exactness are intentionally not claimed.",
            "No production source or ledger was changed.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "static": f"{sum(static.values())}/{len(static)}", "actual_aex": f"{sum(actual.values())}/{len(actual)}", "report": str(REPORT)}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
